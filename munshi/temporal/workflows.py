"""RoomHoldWorkflow (one per inquiry) and NightlyBriefWorkflow (run by a Temporal Schedule).

Workflow code must be deterministic: no I/O, no datetime.now() (use workflow.now()), no random.
Everything non-deterministic is an activity. Imports go through imports_passed_through().
GOTCHA (hit in testing): write `from munshi.temporal.activities import ...` (full dotted name). The form
`from munshi.temporal import activities` resolves through the sandboxed parent package, so passthrough is
skipped, activities.py is re-imported inside the sandbox and config.py's Path.resolve() is rejected.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta, timezone

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from munshi import policy
    from munshi.schema import (ArrivalsQuery, Booking, Brief, BriefInput, BriefRequest, CompsInput,
                               CompsResult, DepositInfo, DraftInput, GuestReply, HoldInput, HoldStatus, ParseInput,
                               RescoreInput, RiskInput)
    from munshi.temporal.activities import (draft_reply, fetch_comps, list_arrivals, parse_inquiry,
                                            record_booking, rescore_arrivals, score_risk, write_brief)

PKT = timezone(timedelta(hours=5))
# Gemma free tier ~15 RPM -> 429s; back off and honour Retry-After (activities set next_retry_delay).
GEMMA_RETRY = RetryPolicy(initial_interval=timedelta(seconds=5), backoff_coefficient=2.0,
                          maximum_interval=timedelta(seconds=60), maximum_attempts=6,
                          non_retryable_error_types=["BadModelOutput"])
TINKER_RETRY = RetryPolicy(initial_interval=timedelta(seconds=2), maximum_interval=timedelta(seconds=20),
                           maximum_attempts=3, non_retryable_error_types=["BadModelOutput"])
TABPFN_RETRY = RetryPolicy(initial_interval=timedelta(seconds=2), maximum_interval=timedelta(seconds=30),
                           maximum_attempts=5)
SERPAPI_RETRY = RetryPolicy(initial_interval=timedelta(seconds=3), maximum_interval=timedelta(seconds=30),
                            maximum_attempts=4)
T_MODEL = timedelta(seconds=90)  # start_to_close per attempt


@workflow.defn
class RoomHoldWorkflow:
    def __init__(self) -> None:
        self.status = HoldStatus()
        self.deposit: DepositInfo | None = None
        self.replies: list[str] = []

    @workflow.signal
    def deposit_received(self, info: DepositInfo) -> None:
        self.deposit = policy.add_deposit(self.deposit, info)
        self.status.deposit = self.deposit

    @workflow.signal
    def guest_reply(self, reply: GuestReply) -> None:
        self.replies.append(reply.text)

    def _advance_paid(self) -> bool:
        return self.deposit is not None and self.deposit.amount_pkr >= self.status.quote.advance_pkr

    @workflow.query
    def get_status(self) -> HoldStatus:
        return self.status

    async def _parse(self, inp: HoldInput, message: str):
        args = dict(message=message, today=inp.today, trace_headers=inp.trace_headers)
        if inp.parser_provider == "tinker":
            try:
                return await workflow.execute_activity(
                    parse_inquiry, ParseInput(provider="tinker", **args),
                    start_to_close_timeout=T_MODEL, retry_policy=TINKER_RETRY, summary="parse (Tinker LoRA)")
            except ActivityError:
                if not inp.allow_gemma_fallback:
                    return None  # -> owner reviews it by hand; raw text never goes to Google
                workflow.logger.warning("Tinker parser failed; falling back to Gemma 4 baseline")
        return await workflow.execute_activity(
            parse_inquiry, ParseInput(provider="gemma", **args),
            start_to_close_timeout=T_MODEL, retry_policy=GEMMA_RETRY, summary="parse (Gemma 4)")

    async def _draft(self, inp: HoldInput, kind: str) -> str:
        try:
            out = await workflow.execute_activity(
                draft_reply, DraftInput(inquiry=self.status.parsed, quote=self.status.quote, kind=kind,
                                             hotel_name=inp.hotel_name, trace_headers=inp.trace_headers),
                start_to_close_timeout=T_MODEL, retry_policy=GEMMA_RETRY, summary=f"draft {kind} (Gemma 4)")
            self.status.attempts[f"draft_{kind}"] = out.attempt
            return out.text
        except ActivityError:
            return policy.template_reply(self.status.parsed, self.status.quote, kind)

    @workflow.run
    async def run(self, inp: HoldInput) -> HoldStatus:
        st, pol = self.status, inp.policy
        message, used = inp.message, 0
        st.guest_message = inp.message
        for round_ in range(pol.max_clarify_rounds + 1):
            st.stage = "parsing"
            parsed = await self._parse(inp, message)
            if parsed is None:
                st.stage, st.outcome, st.draft = "done", "needs_clarification", "(parser failed: owner to reply by hand)"
                return st
            st.parsed, st.parser_model, st.attempts["parse"] = parsed.inquiry, parsed.model, parsed.attempt
            if not parsed.inquiry.needs_clarification and parsed.inquiry.check_in:
                break
            st.draft = policy.clarification_text(parsed.inquiry)
            st.questions.append(st.draft)
            if round_ == pol.max_clarify_rounds:
                st.stage, st.outcome = "done", "needs_clarification"
                return st
            # Ask, wait for the guest's answer, then re-parse the whole conversation so far.
            st.stage = "awaiting guest reply"
            st.reply_expires_at = workflow.now() + policy.clarify_duration(pol)
            try:
                await workflow.wait_condition(lambda n=used: len(self.replies) > n,
                                              timeout=policy.clarify_duration(pol), timeout_summary="guest reply")
            except asyncio.TimeoutError:
                st.stage, st.outcome = "done", "needs_clarification"
                return st
            used, st.reply_expires_at = len(self.replies), None
            st.guest_replies = self.replies[:used]
            message = "\n".join([inp.message, *st.guest_replies])

        st.stage = "scoring + rates"
        risk_in = RiskInput(inquiry=parsed.inquiry, today=inp.today, guest=inp.guest,
                            trace_headers=inp.trace_headers)
        comps_task = asyncio.ensure_future(workflow.execute_activity(
            fetch_comps, CompsInput(check_in=parsed.inquiry.check_in, nights=parsed.inquiry.nights or 1,
                                         adults=min(parsed.inquiry.guests or 2, 4), trace_headers=inp.trace_headers),
            start_to_close_timeout=timedelta(seconds=60), retry_policy=SERPAPI_RETRY, summary="comps (SerpApi)"))
        try:
            st.risk = await workflow.execute_activity(score_risk, risk_in, start_to_close_timeout=T_MODEL,
                                                      retry_policy=TABPFN_RETRY, summary="risk (TabPFN)")
        except ActivityError:
            risk_in.prefer = "logreg"
            st.risk = await workflow.execute_activity(score_risk, risk_in, start_to_close_timeout=T_MODEL,
                                                      retry_policy=TABPFN_RETRY, summary="risk (fallback)")
        st.attempts["risk"] = st.risk.attempt
        try:
            st.comps = await comps_task
            st.attempts["comps"] = st.comps.attempt
        except ActivityError:
            st.comps = CompsResult(source="error")

        st.quote = policy.make_quote(parsed.inquiry, st.comps.median_nightly_pkr, st.risk.p_cancel, pol)
        st.stage = "drafting"
        st.draft = await self._draft(inp, "quote")

        hold = policy.hold_duration(st.risk.p_cancel, pol)
        st.hold_expires_at = workflow.now() + hold
        st.stage = "holding"
        try:
            await workflow.wait_condition(self._advance_paid, timeout=hold, timeout_summary="room hold")
        except asyncio.TimeoutError:
            st.outcome, st.stage = "released", "following up"
            st.followup = await self._draft(inp, "released")
            st.stage = "done"
            return st

        st.deposit, st.outcome, st.stage = self.deposit, "confirmed", "following up"
        await workflow.execute_activity(
            record_booking,
            Booking(workflow_id=workflow.info().workflow_id, inquiry=parsed.inquiry, quote=st.quote,
                    p_cancel=st.risk.p_cancel, deposit=self.deposit, booked_on=inp.today,
                    confirmed_at=workflow.now()),
            start_to_close_timeout=timedelta(seconds=10))
        st.followup = await self._draft(inp, "confirmed")
        st.stage = "done"
        return st


@workflow.defn
class NightlyBriefWorkflow:
    @workflow.run
    async def run(self, inp: BriefInput) -> Brief:
        now_pkt = workflow.now().astimezone(PKT)
        today, tomorrow = now_pkt.date(), (now_pkt + timedelta(days=1)).date()
        bookings = await workflow.execute_activity(list_arrivals, ArrivalsQuery(day=tomorrow),
                                                   start_to_close_timeout=timedelta(seconds=10))
        arrivals = []
        if bookings:
            rescore_in = RescoreInput(bookings=bookings, today=today, policy=inp.policy)
            try:
                arrivals = await workflow.execute_activity(
                    rescore_arrivals, rescore_in, start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=TABPFN_RETRY, summary="rescore (TabPFN)")
            except ActivityError:  # same fallback as RoomHoldWorkflow: the brief must still go out
                rescore_in.prefer = "logreg"
                arrivals = await workflow.execute_activity(
                    rescore_arrivals, rescore_in, start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=TABPFN_RETRY, summary="rescore (fallback)")
        try:
            comps = await workflow.execute_activity(
                fetch_comps, CompsInput(check_in=tomorrow, nights=1, adults=2),
                start_to_close_timeout=timedelta(seconds=60), retry_policy=SERPAPI_RETRY)
        except ActivityError:
            comps = CompsResult(source="error")
        return await workflow.execute_activity(
            write_brief, BriefRequest(day=tomorrow, arrivals=arrivals, comps=comps, hotel_name=inp.hotel_name),
            start_to_close_timeout=timedelta(seconds=10))
