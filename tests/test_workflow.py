"""RoomHoldWorkflow against a real local Temporal dev server, with the model/API activities mocked.

Uses the `temporal` CLI on PATH (no download). Skipped if it is not installed.
"""
from __future__ import annotations

import asyncio
import shutil
import uuid
from datetime import date

import pytest
from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from munshi.schema import (Booking, CompsInput, CompsResult, DepositInfo, DraftInput, DraftOutput, HoldInput,
                           HoldPolicy, Inquiry, ParseInput, ParseOutput, RiskInput, RiskResult)
from munshi.temporal.workflows import RoomHoldWorkflow

TEMPORAL = shutil.which("temporal")
pytestmark = pytest.mark.skipif(not TEMPORAL, reason="temporal CLI not on PATH")
TODAY = date(2026, 10, 16)
QUEUE = "munshi-test"


class Mocks:
    """Fake activities registered under the real activity names; behaviour set per test."""

    def __init__(self, inquiry: Inquiry, p_cancel: float = 0.1, tinker_fails: bool = False,
                 tabpfn_fails: bool = False):
        self.inquiry, self.p, self.tinker_fails, self.tabpfn_fails = inquiry, p_cancel, tinker_fails, tabpfn_fails
        self.calls: list[str] = []
        self.bookings: list[Booking] = []

    def activities(self):
        @activity.defn(name="parse_inquiry")
        async def parse_inquiry(inp: ParseInput) -> ParseOutput:
            self.calls.append(f"parse:{inp.provider}")
            if inp.provider == "tinker" and self.tinker_fails:
                raise ApplicationError("bad json", type="BadModelOutput", non_retryable=True)
            return ParseOutput(inquiry=self.inquiry, model=f"mock-{inp.provider}", latency_s=0.01,
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


def run(env, mocks: Mocks, demo_speed: float, deposit_after_s: float | None = None):
    loop, e = env

    async def go():
        async with Worker(e.client, task_queue=QUEUE, workflows=[RoomHoldWorkflow], activities=mocks.activities()):
            h = await e.client.start_workflow(
                RoomHoldWorkflow.run,
                HoldInput(message="kal 2 log 1 room 2 raat", today=TODAY,
                          policy=HoldPolicy(demo_speed=demo_speed)),
                id=f"test-{uuid.uuid4().hex[:8]}", task_queue=QUEUE)
            if deposit_after_s is not None:
                await asyncio.sleep(deposit_after_s)
                await h.signal(RoomHoldWorkflow.deposit_received, DepositInfo(amount_pkr=5000, reference="t"))
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


def test_missing_date_asks_instead_of_quoting(env):
    m = Mocks(Inquiry(guests=3, needs_clarification=True))
    st = run(env, m, demo_speed=1)
    assert st.outcome == "needs_clarification" and st.quote is None
    assert m.calls == ["parse:tinker"]


def test_tinker_failure_never_sends_raw_text_to_gemma(env):
    m = Mocks(OK, tinker_fails=True)
    st = run(env, m, demo_speed=1)
    assert st.outcome == "needs_clarification"
    assert "parse:gemma" not in m.calls  # allow_gemma_fallback defaults to False


def test_tabpfn_failure_falls_back_to_logreg(env):
    m = Mocks(OK, p_cancel=0.6, tabpfn_fails=True)
    st = run(env, m, demo_speed=3600)
    assert st.risk.model == "mock-logreg" and st.outcome == "released"
