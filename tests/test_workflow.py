"""RoomHoldWorkflow against a real local Temporal dev server, with the model/API activities mocked.

Uses the `temporal` CLI on PATH (no download). Skipped if it is not installed.
"""
from __future__ import annotations

import asyncio
import shutil
import uuid
from datetime import date, datetime, timezone

import pytest
from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from munshi import policy
from munshi.schema import (ArrivalRisk, ArrivalsQuery, Booking, Brief, BriefInput, BriefRequest, CompsInput,
                           CompsResult, DepositInfo, DraftInput, DraftOutput, GuestReply, HoldInput, HoldPolicy,
                           Inquiry, ParseInput, ParseOutput, RescoreInput, RiskInput, RiskResult)
from munshi.temporal.workflows import NightlyBriefWorkflow, RoomHoldWorkflow

TEMPORAL = shutil.which("temporal")
pytestmark = pytest.mark.skipif(not TEMPORAL, reason="temporal CLI not on PATH")
TODAY = date(2026, 10, 16)
QUEUE = "munshi-test"


class Mocks:
    """Fake activities registered under the real activity names; behaviour set per test."""

    def __init__(self, inquiry: Inquiry | list[Inquiry], p_cancel: float = 0.1, tinker_fails: bool = False,
                 tabpfn_fails: bool = False):
        # a list = one parse result per round (clarification tests); the last one repeats
        self.inquiries = inquiry if isinstance(inquiry, list) else [inquiry]
        self.p, self.tinker_fails, self.tabpfn_fails = p_cancel, tinker_fails, tabpfn_fails
        self.calls: list[str] = []
        self.messages: list[str] = []
        self.bookings: list[Booking] = []

    def activities(self):
        @activity.defn(name="parse_inquiry")
        async def parse_inquiry(inp: ParseInput) -> ParseOutput:
            self.calls.append(f"parse:{inp.provider}")
            self.messages.append(inp.message)
            if inp.provider == "tinker" and self.tinker_fails:
                raise ApplicationError("bad json", type="BadModelOutput", non_retryable=True)
            inquiry = self.inquiries[min(len(self.messages), len(self.inquiries)) - 1]
            return ParseOutput(inquiry=inquiry, model=f"mock-{inp.provider}", latency_s=0.01,
                               input_tokens=10, output_tokens=10, cost_usd=0.0)

        @activity.defn(name="score_risk")
        async def score_risk(inp: RiskInput) -> RiskResult:
            self.calls.append(f"risk:{inp.prefer}")
            if inp.prefer == "tabpfn" and self.tabpfn_fails:
                raise ApplicationError("tabpfn down", non_retryable=True)
            return RiskResult(p_cancel=self.p, model=f"mock-{inp.prefer}", features={})

        @activity.defn(name="fetch_comps")
        async def fetch_comps(inp: CompsInput) -> CompsResult:
            self.calls.append("comps")
            return CompsResult(median_nightly_pkr=9000, source="cache")

        @activity.defn(name="draft_reply")
        async def draft_reply(inp: DraftInput) -> DraftOutput:
            self.calls.append(f"draft:{inp.kind}")
            return DraftOutput(text=f"mock {inp.kind}", model="mock-gemma", latency_s=0.01)

        @activity.defn(name="record_booking")
        async def record_booking(b: Booking) -> None:
            self.calls.append("record")
            self.bookings.append(b)

        return [parse_inquiry, score_risk, fetch_comps, draft_reply, record_booking]


@pytest.fixture(scope="module")
def env():
    loop = asyncio.new_event_loop()
    e = loop.run_until_complete(WorkflowEnvironment.start_local(
        data_converter=pydantic_data_converter, dev_server_existing_path=TEMPORAL))
    yield loop, e
    loop.run_until_complete(e.shutdown())
    loop.close()


def deposit(amount: int, ref: str = "t"):
    return RoomHoldWorkflow.deposit_received, DepositInfo(amount_pkr=amount, reference=ref)


def reply(text: str):
    return RoomHoldWorkflow.guest_reply, GuestReply(text=text)


def run(env, mocks: Mocks, demo_speed: float, deposit_after_s: float | None = None,
        signals: list[tuple[float, tuple]] = (), message: str = "kal 2 log 1 room 2 raat"):
    """signals: (seconds after start, (signal, arg)) in time order."""
    loop, e = env
    if deposit_after_s is not None:
        signals = [(deposit_after_s, deposit(5000))]

    async def go():
        async with Worker(e.client, task_queue=QUEUE, workflows=[RoomHoldWorkflow], activities=mocks.activities()):
            h = await e.client.start_workflow(
                RoomHoldWorkflow.run,
                HoldInput(message=message, today=TODAY, policy=HoldPolicy(demo_speed=demo_speed)),
                id=f"test-{uuid.uuid4().hex[:8]}", task_queue=QUEUE)
            t0 = loop.time()
            for at, (sig, arg) in signals:
                await asyncio.sleep(max(0.0, t0 + at - loop.time()))
                await h.signal(sig, arg)
            return await h.result()

    return loop.run_until_complete(asyncio.wait_for(go(), 60))


OK = Inquiry(check_in=date(2026, 10, 17), nights=2, guests=2, rooms=1)


def test_deposit_confirms_and_records(env):
    m = Mocks(OK, p_cancel=0.1)
    st = run(env, m, demo_speed=1, deposit_after_s=1.5)  # 12 h hold: only the signal can end it
    assert st.outcome == "confirmed" and st.followup == "mock confirmed"
    assert st.quote.nightly_pkr == 8550 and st.quote.total_pkr == 17100  # 5% under the 9,000 median
    assert len(m.bookings) == 1 and m.bookings[0].deposit.amount_pkr == 5000


def test_no_deposit_releases_after_hold(env):
    m = Mocks(OK, p_cancel=0.6)  # high risk: 2 h hold, x3600 demo speed = 2 s
    st = run(env, m, demo_speed=3600)
    assert st.outcome == "released" and st.quote.risk_band == "high" and st.followup == "mock released"
    assert "record" not in m.calls


ASK = Inquiry(guests=3, needs_clarification=True, clarification_question="Kis date ko aana hai?")


def test_missing_date_asks_instead_of_quoting(env):
    m = Mocks(ASK)
    st = run(env, m, demo_speed=86400)  # 24 h wait for the guest's answer -> 1 s, nobody answers
    assert st.outcome == "needs_clarification" and st.quote is None
    assert st.questions == ["Kis date ko aana hai?"] and st.draft == "Kis date ko aana hai?"
    assert m.calls == ["parse:tinker"]


def test_guest_answer_is_reparsed_with_the_original_message(env):
    m = Mocks([ASK, OK], p_cancel=0.1)
    st = run(env, m, demo_speed=1, signals=[(1.0, reply("kal se 2 raat")), (2.5, deposit(5000))])
    assert m.messages == ["kal 2 log 1 room 2 raat", "kal 2 log 1 room 2 raat\nkal se 2 raat"]
    assert st.outcome == "confirmed" and st.guest_replies == ["kal se 2 raat"]
    assert st.questions == ["Kis date ko aana hai?"] and st.draft == "mock quote"


def test_gives_up_after_max_clarification_rounds(env):
    m = Mocks(ASK)  # never becomes parseable; default max_clarify_rounds = 2
    st = run(env, m, demo_speed=1, signals=[(0.5, reply("pata nahi")), (1.5, reply("baad mein batata hoon"))])
    assert st.outcome == "needs_clarification" and len(st.questions) == 3
    assert m.calls == ["parse:tinker"] * 3


def test_partial_deposits_add_up_to_the_advance(env):
    m = Mocks(OK, p_cancel=0.1)  # low risk: advance = 20% of 17,100 rounded up to 500 = 3,500
    st = run(env, m, demo_speed=1, signals=[(1.5, deposit(2000, "JC-1")), (2.0, deposit(1500, "JC-2"))])
    assert st.quote.advance_pkr == 3500 and st.outcome == "confirmed"
    assert m.bookings[0].deposit.amount_pkr == 3500 and m.bookings[0].deposit.reference == "JC-1, JC-2"


def test_short_deposit_does_not_confirm(env):
    m = Mocks(OK, p_cancel=0.6)  # high risk: 2 h hold -> 2 s; advance 50% of 17,100 -> 9,000
    st = run(env, m, demo_speed=3600, signals=[(1.0, deposit(2000))])
    assert st.outcome == "released" and st.deposit.amount_pkr == 2000  # owner sees what to refund
    assert "record" not in m.calls


def test_tinker_failure_never_sends_raw_text_to_gemma(env):
    m = Mocks(OK, tinker_fails=True)
    st = run(env, m, demo_speed=1)
    assert st.outcome == "needs_clarification"
    assert "parse:gemma" not in m.calls  # allow_gemma_fallback defaults to False


def test_tabpfn_failure_falls_back_to_logreg(env):
    m = Mocks(OK, p_cancel=0.6, tabpfn_fails=True)
    st = run(env, m, demo_speed=3600)
    assert st.risk.model == "mock-logreg" and st.outcome == "released"


def test_brief_falls_back_to_logreg_when_tabpfn_fails(env):
    loop, e = env
    booked = Booking(workflow_id="hold-x", inquiry=OK, quote=policy.make_quote(OK, None, 0.1, HoldPolicy()),
                     p_cancel=0.1, booked_on=TODAY, confirmed_at=datetime(2026, 10, 16, tzinfo=timezone.utc))
    calls: list[str] = []

    @activity.defn(name="list_arrivals")
    async def list_arrivals(q: ArrivalsQuery) -> list[Booking]:
        return [booked]

    @activity.defn(name="rescore_arrivals")
    async def rescore_arrivals(inp: RescoreInput) -> list[ArrivalRisk]:
        calls.append(inp.prefer)
        if inp.prefer == "tabpfn":
            raise ApplicationError("no token", type="NotConfigured", non_retryable=True)
        return [ArrivalRisk(booking=b, p_cancel=0.3, band="medium") for b in inp.bookings]

    @activity.defn(name="fetch_comps")
    async def fetch_comps(inp: CompsInput) -> CompsResult:
        return CompsResult(source="disabled")

    @activity.defn(name="write_brief")
    async def write_brief(req: BriefRequest) -> Brief:
        return Brief(day=req.day, arrivals=len(req.arrivals), path="-", text="")

    async def go():
        async with Worker(e.client, task_queue=QUEUE, workflows=[NightlyBriefWorkflow],
                          activities=[list_arrivals, rescore_arrivals, fetch_comps, write_brief]):
            return await e.client.execute_workflow(NightlyBriefWorkflow.run, BriefInput(),
                                                   id=f"test-brief-{uuid.uuid4().hex[:8]}", task_queue=QUEUE)

    brief = loop.run_until_complete(asyncio.wait_for(go(), 60))
    assert brief.arrivals == 1 and calls == ["tabpfn", "logreg"]
