"""Sentry setup + gen_ai span helpers (manual instrumentation).

Verified on sentry-sdk 2.72.0: the auto OpenAIIntegration DOES wrap calls to any base_url but labels
them gen_ai.system="openai" and can't price tinker:// or free-tier calls, so it is disabled and spans
are created by hand. NOTE: start_span(attributes=...) raises TypeError on 2.72.0 -> use set_data().
There is no Sentry integration for Temporal: the trace is carried in each activity's input
(trace_headers) and resumed with continue_trace().
"""
from __future__ import annotations

import contextlib
from typing import Iterator

import sentry_sdk
from sentry_sdk.integrations.openai import OpenAIIntegration

from munshi import config as cfg

_inited = False


def init_sentry(component: str) -> None:
    global _inited
    if _inited:
        return
    sentry_sdk.init(
        dsn=cfg.SENTRY_DSN or None,  # None = SDK is a no-op
        traces_sample_rate=1.0,
        send_default_pii=False,  # data minimisation: no prompts/replies leave the machine via Sentry
        environment=cfg.SENTRY_ENV,
        release="munshi@0.1.0",
        server_name=component,
        disabled_integrations=[OpenAIIntegration()],
    )
    sentry_sdk.set_tag("component", component)
    _inited = True


def current_trace_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if tp := sentry_sdk.get_traceparent():
        headers["sentry-trace"] = tp
    if bg := sentry_sdk.get_baggage():
        headers["baggage"] = bg
    return headers


@contextlib.contextmanager
def activity_transaction(name: str, trace_headers: dict[str, str] | None, attempt: int = 1) -> Iterator:
    tx = sentry_sdk.continue_trace(trace_headers or {}, op="temporal.activity", name=name)
    with sentry_sdk.start_transaction(tx) as t:
        t.set_tag("temporal.activity", name)
        t.set_tag("temporal.attempt", attempt)
        yield t


@contextlib.contextmanager
def agent_span(agent_name: str = "Munshi") -> Iterator:
    with sentry_sdk.start_span(op="gen_ai.invoke_agent", name=f"invoke_agent {agent_name}") as s:
        s.set_data("gen_ai.operation.name", "invoke_agent")
        s.set_data("gen_ai.agent.name", agent_name)
        yield s


@contextlib.contextmanager
def chat_span(model: str, provider: str, agent_name: str = "Munshi") -> Iterator:
    with sentry_sdk.start_span(op="gen_ai.chat", name=f"chat {model}") as s:
        s.set_data("gen_ai.operation.name", "chat")
        s.set_data("gen_ai.request.model", model)
        s.set_data("gen_ai.provider.name", provider)
        s.set_data("gen_ai.agent.name", agent_name)
        yield s


def record_usage(span, *, input_tokens: int, output_tokens: int, cost_usd: float,
                 response_model: str | None = None) -> None:
    span.set_data("gen_ai.usage.input_tokens", input_tokens)
    span.set_data("gen_ai.usage.output_tokens", output_tokens)
    span.set_data("gen_ai.usage.total_tokens", input_tokens + output_tokens)
    span.set_data("gen_ai.cost.total_tokens", float(cost_usd))  # USD; Sentry keeps custom cost
    if response_model:
        span.set_data("gen_ai.response.model", response_model)


@contextlib.contextmanager
def tool_span(tool_name: str) -> Iterator:
    with sentry_sdk.start_span(op="gen_ai.execute_tool", name=f"execute_tool {tool_name}") as s:
        s.set_data("gen_ai.operation.name", "execute_tool")
        s.set_data("gen_ai.tool.name", tool_name)
        yield s
