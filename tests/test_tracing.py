"""Sentry instrumentation, offline: a real activity runs under a capturing transport (no DSN, no network).

Checks the trace shape the post relies on: the activity transaction continues the starter's trace, the
gen_ai.chat span carries model, tokens and custom cost, the conversation id is the workflow id, and no
prompt or reply text leaves the machine.
NOTE (sentry-sdk 2.72): gen_ai.* spans are NOT in the transaction's span list; the SDK sends them as separate
v2 "span" envelope items, parented to the activity transaction.
"""
from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

import pytest
import sentry_sdk
from sentry_sdk.integrations.openai import OpenAIIntegration
from sentry_sdk.transport import Transport
from temporalio.testing import ActivityEnvironment

from munshi import config as cfg
from munshi import llm, tracing
from munshi.schema import DraftInput, Inquiry, Quote
from munshi.temporal.activities import draft_reply

REPLY = "Kal se 2 raat, total Rs 16,000."


class Capture(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.events: list[dict] = []
        self.spans: list[dict] = []  # v2 span items, attributes flattened to {key: value}
        self.raw: list[bytes] = []

    def capture_envelope(self, envelope) -> None:
        for item in envelope.items:
            body = item.payload.get_bytes()
            self.raw.append(body)
            if item.type == "transaction":
                self.events.append(json.loads(body))
            elif item.type == "span":
                for sp in json.loads(body)["items"]:
                    sp["attrs"] = {k: v["value"] for k, v in sp.pop("attributes", {}).items()}
                    self.spans.append(sp)


@pytest.fixture
def captured(monkeypatch):
    cap = Capture()
    sentry_sdk.init(dsn="https://public@example.invalid/1", transport=cap, traces_sample_rate=1.0,
                    send_default_pii=False, disabled_integrations=[OpenAIIntegration()])
    monkeypatch.setattr(tracing, "_inited", True)  # keep _guard's init_sentry() from re-initialising
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=REPLY))],
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30), model=cfg.GEMMA_MODEL))))
    monkeypatch.setattr(llm, "gemma_client", lambda: fake)
    monkeypatch.setattr(cfg, "GEMINI_API_KEY", "test-key")
    yield cap
    sentry_sdk.init(dsn=None)  # back to a no-op client for the other tests


def test_activity_trace_shape(captured):
    with sentry_sdk.start_transaction(op="munshi.inquiry", name="new WhatsApp inquiry") as starter:
        headers = tracing.current_trace_headers()
    inq = Inquiry(check_in=date(2026, 10, 18), nights=2, guests=2, rooms=1)
    quote = Quote(nightly_pkr=8000, nights=2, rooms=1, total_pkr=16000, advance_pkr=3500, hold_hours=12,
                  risk_band="low")
    out = ActivityEnvironment().run(draft_reply, DraftInput(inquiry=inq, quote=quote, trace_headers=headers))
    assert out.text == REPLY
    sentry_sdk.flush()

    tx = next(e for e in captured.events if e["transaction"] == "draft_reply")
    assert tx["contexts"]["trace"]["trace_id"] == starter.trace_id  # one distributed trace per inquiry
    assert tx["tags"]["temporal.activity"] == "draft_reply" and str(tx["tags"]["temporal.attempt"]) == "1"
    spans = {s["attrs"]["sentry.op"]: s for s in captured.spans}
    agent, chat = spans["gen_ai.invoke_agent"], spans["gen_ai.chat"]
    assert agent["parent_span_id"] == tx["contexts"]["trace"]["span_id"]
    assert chat["parent_span_id"] == agent["span_id"] and chat["trace_id"] == starter.trace_id
    d = chat["attrs"]
    assert d["gen_ai.request.model"] == cfg.GEMMA_MODEL and d["gen_ai.provider.name"] == "gcp.gemini"
    assert (d["gen_ai.usage.input_tokens"], d["gen_ai.usage.output_tokens"]) == (120, 30)
    assert d["gen_ai.cost.total_tokens"] == 0.0  # free tier: actual cost, not list price
    assert d["gen_ai.conversation.id"] == "test"  # ActivityEnvironment's workflow id
    assert not any(REPLY.encode() in b for b in captured.raw)  # send_default_pii=False: no reply text sent
