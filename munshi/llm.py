"""OpenAI-SDK clients for Gemma 4 (Gemini API) and the Tinker fine-tune, plus one call wrapper.

Every call is timed, token-counted, priced and wrapped in a Sentry gen_ai.chat span.
Tinker default path: render the prompt locally with the SAME chat template used in training
(enable_thinking=False) and call /completions, so serving matches training token for token.
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass
from functools import lru_cache

import openai
from openai import OpenAI

from munshi import config as cfg
from munshi.tracing import chat_span, record_usage


class RateLimited(Exception):
    def __init__(self, provider: str, retry_after_s: float):
        super().__init__(f"{provider} rate limited; retry after {retry_after_s:.0f}s")
        self.provider, self.retry_after_s = provider, retry_after_s


class ProviderError(Exception):
    """Transient upstream failure (5xx, timeout, connection)."""


class NotConfigured(Exception):
    """Missing or rejected key / model path: retrying cannot help, so the workflow falls back at once."""


@dataclass
class LLMResult:
    text: str
    model: str
    provider: str
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float       # what this call actually cost
    list_cost_usd: float  # what it would cost at a paid list price (Gemma) / same as cost (Tinker)


class _MinInterval:
    """Process-wide limiter: Gemma free tier is ~15 RPM, so space calls >= 60/RPM seconds."""

    def __init__(self, rpm: float):
        self.gap, self.lock, self.next_t = 60.0 / max(rpm, 0.1), threading.Lock(), 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            sleep_for = max(0.0, self.next_t - now)
            self.next_t = max(now, self.next_t) + self.gap
        if sleep_for:
            time.sleep(sleep_for)


_gemma_gate = _MinInterval(cfg.GEMMA_RPM)
_gemma_opts = {"json_mode": cfg.GEMMA_JSON_MODE, "thinking": True}  # dropped on HTTP 400


@lru_cache(maxsize=1)
def gemma_client() -> OpenAI:
    # max_retries=0: Temporal owns retries (visible in the Web UI), not the SDK.
    return OpenAI(api_key=cfg.GEMINI_API_KEY, base_url=cfg.GEMINI_BASE_URL, max_retries=0, timeout=60)


@lru_cache(maxsize=1)
def tinker_client() -> OpenAI:
    return OpenAI(api_key=cfg.TINKER_API_KEY, base_url=cfg.TINKER_OAI_BASE_URL, max_retries=0, timeout=60)


@lru_cache(maxsize=1)
def qwen_tokenizer():
    from transformers import AutoTokenizer  # tokenizer files only (~30 MB); no torch needed

    return AutoTokenizer.from_pretrained(cfg.TINKER_BASE_MODEL)


def render_prompt(messages: list[dict]) -> str:
    return qwen_tokenizer().apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)


def _retry_after(err: openai.APIStatusError, default: float = 20.0) -> float:
    try:
        return float(err.response.headers.get("retry-after", default))
    except (TypeError, ValueError):
        return default


def _translate(provider: str, err: Exception) -> Exception:
    if isinstance(err, openai.RateLimitError):
        return RateLimited(provider, _retry_after(err))
    if isinstance(err, (openai.AuthenticationError, openai.PermissionDeniedError)):
        return NotConfigured(f"{provider}: {err}")
    if isinstance(err, (openai.APITimeoutError, openai.APIConnectionError, openai.InternalServerError)):
        return ProviderError(f"{provider}: {err}")
    return err


def _usage(resp) -> tuple[int, int]:
    u = getattr(resp, "usage", None)
    return (getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0) if u else (0, 0)


def call_gemma(messages: list[dict], *, json_mode: bool = False, max_tokens: int = 512,
               temperature: float = 0.2) -> LLMResult:
    if not cfg.GEMINI_API_KEY:
        raise NotConfigured("GEMINI_API_KEY is empty (.env)")
    _gemma_gate.wait()
    kwargs: dict = {"model": cfg.GEMMA_MODEL, "messages": messages,
                    "max_tokens": max_tokens, "temperature": temperature}
    if json_mode and _gemma_opts["json_mode"]:
        kwargs["response_format"] = {"type": "json_object"}
    if _gemma_opts["thinking"]:
        kwargs["extra_body"] = {"extra_body": {"google": {"thinking_config": {
            "thinking_level": cfg.GEMMA_THINKING_LEVEL}}}}
    with chat_span(cfg.GEMMA_MODEL, "gcp.gemini") as span:
        t0 = time.perf_counter()
        try:
            resp = gemma_client().chat.completions.create(**kwargs)
        except openai.BadRequestError:
            # JSON mode / thinking_config on Gemma via the OpenAI layer is undocumented: drop and retry once.
            if "response_format" not in kwargs and "extra_body" not in kwargs:
                raise
            _gemma_opts["json_mode"] = _gemma_opts["thinking"] = False
            kwargs.pop("response_format", None), kwargs.pop("extra_body", None)
            resp = gemma_client().chat.completions.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            span.set_status("internal_error")
            raise _translate("gemma", e) from e
        latency = time.perf_counter() - t0
        tin, tout = _usage(resp)
        cost = (tin * cfg.GEMMA_ACTUAL_PRICE[0] + tout * cfg.GEMMA_ACTUAL_PRICE[1]) / 1e6
        list_cost = (tin * cfg.GEMMA_LIST_PRICE[0] + tout * cfg.GEMMA_LIST_PRICE[1]) / 1e6
        record_usage(span, input_tokens=tin, output_tokens=tout, cost_usd=cost, response_model=resp.model)
    return LLMResult(resp.choices[0].message.content or "", cfg.GEMMA_MODEL, "gemma", latency,
                     tin, tout, cost, list_cost)


def call_tinker(messages: list[dict], *, max_tokens: int = 256, model_path: str | None = None) -> LLMResult:
    model = model_path or cfg.TINKER_MODEL_PATH
    if not model:
        raise NotConfigured("TINKER_MODEL_PATH is empty: train first (train/tinker_sft.py) and paste the path")
    if not cfg.TINKER_API_KEY:
        raise NotConfigured("TINKER_API_KEY is empty (.env)")
    prefill_p, sample_p, _ = cfg.TINKER_PRICES[cfg.TINKER_BASE_MODEL]
    label = "munshi-parser-" + cfg.TINKER_BASE_MODEL.split("/")[-1].lower() + "-lora"  # groups well in Sentry
    with chat_span(label, "tinker") as span:
        span.set_data("munshi.tinker_path", model)
        t0 = time.perf_counter()
        try:
            if cfg.TINKER_USE_CHAT_ENDPOINT:
                resp = tinker_client().chat.completions.create(
                    model=model, messages=messages, max_tokens=max_tokens, temperature=0.0,
                    reasoning_effort="none")
                text = resp.choices[0].message.content or ""
            else:
                resp = tinker_client().completions.create(
                    model=model, prompt=render_prompt(messages), max_tokens=max_tokens,
                    temperature=0.0, stop=["<|im_end|>"])
                text = resp.choices[0].text or ""
        except Exception as e:  # noqa: BLE001
            span.set_status("internal_error")
            raise _translate("tinker", e) from e
        latency = time.perf_counter() - t0
        tin, tout = _usage(resp)
        if not tin:  # usage not returned by the beta endpoint -> count locally with the same tokenizer
            tok = qwen_tokenizer()
            tin = len(tok.encode(render_prompt(messages), add_special_tokens=False))
            tout = len(tok.encode(text, add_special_tokens=False)) + 1  # +1 for <|im_end|>
            span.set_data("munshi.tokens_counted_locally", True)
        cost = (tin * prefill_p + tout * sample_p) / 1e6
        record_usage(span, input_tokens=tin, output_tokens=tout, cost_usd=cost)
    return LLMResult(text, model, "tinker", latency, tin, tout, cost, cost)


_JSON_RE = re.compile(r"\{.*\}", re.S)


def extract_json(text: str) -> dict:
    """Tolerates ```json fences, leading prose and stray <think> blocks."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = _JSON_RE.search(text)
    if not m:
        raise ValueError(f"no JSON object in model output: {text[:120]!r}")
    return json.loads(m.group(0))
