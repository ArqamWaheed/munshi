"""Temporal activities: every side effect (model calls, APIs, files) lives here, never in workflows.

Sync functions -> the worker runs them in a ThreadPoolExecutor. Each activity:
  * resumes the Sentry trace carried in its input and groups spans by workflow id (Conversations),
  * turns a 429 into ApplicationError(type="RateLimited", next_retry_delay=Retry-After),
  * marks deterministic failures non-retryable,
  * reports activity.info().attempt so the UI/post can count retries absorbed.
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta, timezone

import sentry_sdk
from sentry_sdk.ai import set_conversation_id
from temporalio import activity
from temporalio.exceptions import ApplicationError

from munshi import comps as comps_mod
from munshi import config as cfg
from munshi import parser, reply, risk
from munshi.llm import ProviderError, RateLimited
from munshi.policy import risk_band
from munshi.schema import (ArrivalRisk, ArrivalsQuery, Booking, Brief, BriefRequest, CompsInput,
                           CompsResult, DraftInput, DraftOutput, ParseInput, ParseOutput, RescoreInput,
                           RiskInput, RiskResult)
from munshi.tracing import activity_transaction, agent_span, init_sentry, tool_span


def _guard(name: str, trace_headers: dict, fn):
    init_sentry("worker")
    info = activity.info()
    set_conversation_id(info.workflow_id)
    with activity_transaction(name, trace_headers, info.attempt):
        if cfg.INJECT_FAILURE_RATE and info.attempt == 1 and random.random() < cfg.INJECT_FAILURE_RATE:
            raise ApplicationError(f"injected failure in {name} (demo)", type="InjectedFailure")
        try:
            return fn(info.attempt)
        except RateLimited as e:
            sentry_sdk.capture_exception(e)
            raise ApplicationError(str(e), type="RateLimited",
                                   next_retry_delay=timedelta(seconds=e.retry_after_s)) from e
        except parser.BadModelOutput as e:
            sentry_sdk.capture_exception(e)
            raise ApplicationError(str(e), type="BadModelOutput", non_retryable=True) from e
        except (ProviderError, comps_mod.CompsUnavailable) as e:
            sentry_sdk.capture_exception(e)
            raise  # plain exception = retryable under the activity's RetryPolicy


@activity.defn
def parse_inquiry(inp: ParseInput) -> ParseOutput:
    def run(attempt: int) -> ParseOutput:
        with agent_span("Munshi parser"):
            inq, res = parser.parse_message(inp.message, inp.today, inp.provider)
        return ParseOutput(inquiry=inq, model=res.model, latency_s=res.latency_s, input_tokens=res.input_tokens,
                           output_tokens=res.output_tokens, cost_usd=res.cost_usd, attempt=attempt)
    return _guard("parse_inquiry", inp.trace_headers, run)


@activity.defn
def score_risk(inp: RiskInput) -> RiskResult:
    def run(attempt: int) -> RiskResult:
        with tool_span(f"{inp.prefer}.predict_proba") as span:
            p, model, feats = risk.score(inp.inquiry, inp.today, inp.guest, prefer=inp.prefer)
            span.set_data("munshi.p_cancel", p)
        return RiskResult(p_cancel=p, model=model, features=feats, attempt=attempt)
    return _guard("score_risk", inp.trace_headers, run)


@activity.defn
def fetch_comps(inp: CompsInput) -> CompsResult:
    def run(attempt: int) -> CompsResult:
        with tool_span("serpapi.google_hotels") as span:
            out = comps_mod.fetch(inp.check_in, inp.nights, inp.adults)
            span.set_data("munshi.comps.source", out.source)
            span.set_data("munshi.comps.count", len(out.comps))
        out.attempt = attempt
        return out
    return _guard("fetch_comps", inp.trace_headers, run)


@activity.defn
def draft_reply(inp: DraftInput) -> DraftOutput:
    def run(attempt: int) -> DraftOutput:
        with agent_span("Munshi writer"):
            res = reply.draft(inp.inquiry, inp.quote, inp.kind, inp.hotel_name or cfg.HOTEL_NAME)
        return DraftOutput(text=res.text.strip(), model=res.model, latency_s=res.latency_s, attempt=attempt)
    return _guard("draft_reply", inp.trace_headers, run)


@activity.defn
def record_booking(b: Booking) -> None:
    """Append-only local register (one hotel; Temporal history is the audit log). Idempotent by workflow id."""
    cfg.BOOKINGS_LOG.parent.mkdir(parents=True, exist_ok=True)
    if cfg.BOOKINGS_LOG.exists() and b.workflow_id in cfg.BOOKINGS_LOG.read_text(encoding="utf-8"):
        return
    with cfg.BOOKINGS_LOG.open("a", encoding="utf-8") as f:
        f.write(b.model_dump_json() + "\n")


@activity.defn
def list_arrivals(q: ArrivalsQuery) -> list[Booking]:
    if not cfg.BOOKINGS_LOG.exists():
        return []
    rows = [Booking.model_validate_json(ln) for ln in cfg.BOOKINGS_LOG.read_text(encoding="utf-8").splitlines() if ln]
    return [b for b in rows if b.inquiry.check_in == q.day]


@activity.defn
def rescore_arrivals(inp: RescoreInput) -> list[ArrivalRisk]:
    def run(attempt: int) -> list[ArrivalRisk]:
        out = []
        for b in inp.bookings:
            with tool_span("tabpfn.predict_proba"):
                p, _, _ = risk.score(b.inquiry, inp.today, risk.GuestContext(), prefer="tabpfn")
            # TODO: once the deposit is paid, re-score with deposit_type="Non Refund"/"Refundable" if your
            # own register shows that matters; the public dataset's deposit effect is counter-intuitive.
            out.append(ArrivalRisk(booking=b, p_cancel=p, band=risk_band(p, inp.policy)))
        return out
    return _guard("rescore_arrivals", inp.trace_headers, run)


@activity.defn
def write_brief(req: BriefRequest) -> Brief:
    """Deterministic markdown brief (no LLM: saves Gemma RPM and nothing personal leaves the machine)."""
    lines = [f"# {req.hotel_name or cfg.HOTEL_NAME}: arrivals for {req.day:%a %d %b %Y}", ""]
    if req.arrivals:
        lines += ["| Rooms | Nights | Guests | Total Rs | Advance paid Rs | P(cancel) | Flag |",
                  "|---:|---:|---:|---:|---:|---:|---|"]
        for a in sorted(req.arrivals, key=lambda a: -a.p_cancel):
            q, paid = a.booking.quote, (a.booking.deposit.amount_pkr if a.booking.deposit else 0)
            flag = "CALL GUEST" if a.band == "high" else ""
            lines.append(f"| {q.rooms} | {q.nights} | {a.booking.inquiry.guests} | {q.total_pkr:,} | {paid:,} | "
                         f"{a.p_cancel:.0%} | {flag} |")
    else:
        lines.append("No confirmed arrivals.")
    lines += ["", f"## Nearby rates tonight ({req.comps.source})"]
    for c in req.comps.comps:
        lines.append(f"- {c.name}: Rs {c.nightly_pkr:,}" + (f" ({c.rating}/5)" if c.rating else ""))
    if req.comps.median_nightly_pkr:
        lines.append(f"\nMedian nearby: Rs {req.comps.median_nightly_pkr:,}/night.")
    text = "\n".join(lines) + "\n"
    cfg.BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    path = cfg.BRIEFS_DIR / f"brief-{req.day.isoformat()}.md"
    path.write_text(text, encoding="utf-8")
    return Brief(day=req.day, arrivals=len(req.arrivals), path=str(path), text=text)


ALL_ACTIVITIES = [parse_inquiry, score_risk, fetch_comps, draft_reply, record_booking,
                  list_arrivals, rescore_arrivals, write_brief]


def pkt_now() -> datetime:  # for CLIs only (never call from workflow code)
    return datetime.now(timezone(timedelta(hours=5)))


def pkt_today() -> date:
    return pkt_now().date()


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, default=str, ensure_ascii=False)
