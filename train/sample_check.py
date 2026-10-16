"""Smoke-test the fine-tune through the OpenAI-compatible endpoint (the same path production uses).

  python -m train.sample_check "kal 3 log 1 room 2 raat"
  python -m train.sample_check --base "kal 3 log"   # untuned base model via native SamplingClient (before/after)
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import date

from munshi import config as cfg
from munshi.llm import call_tinker, extract_json, render_prompt
from munshi.parser import messages_for


async def sample_base(prompt: str) -> str:
    import tinker

    sc = await tinker.ServiceClient().create_sampling_client_async(base_model=cfg.TINKER_BASE_MODEL)
    tok = sc.get_tokenizer()
    res = await sc.sample_async(prompt=tinker.ModelInput.from_ints(tok.encode(prompt, add_special_tokens=False)),
                                num_samples=1,
                                sampling_params=tinker.SamplingParams(max_tokens=200, temperature=0.0,
                                                                      stop=["<|im_end|>"]))
    return tok.decode(res.sequences[0].tokens, skip_special_tokens=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("message")
    ap.add_argument("--base", action="store_true")
    a = ap.parse_args()
    msgs = messages_for("tinker", a.message, date.today())
    if a.base:
        text = asyncio.run(sample_base(render_prompt(msgs)))
    else:
        res = call_tinker(msgs)
        text = res.text
        print(f"latency {res.latency_s:.2f}s  tokens {res.input_tokens}+{res.output_tokens}  ${res.cost_usd:.6f}")
    print(text)
    try:
        print("valid JSON:", extract_json(text))
    except ValueError as e:
        print("INVALID:", e)
