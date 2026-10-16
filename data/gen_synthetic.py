"""Gemma 4 as TEACHER: generate labelled synthetic inquiries -> data/train.jsonl (+ data/dev.jsonl).

Two-step per batch: (1) Gemma writes N new WhatsApp-style messages from the seeds; (2) Gemma labels
each message with the long SPEC prompt; we validate with pydantic and drop anything invalid.
Rate-limited to GEMMA_RPM (free tier ~15 RPM, ~1,500 RPD): 1,000 labelled rows ~= 1,100 calls ~= 80 min.
Resumable: re-running appends until --target is reached. Never put real guest messages in seeds.

  python -m data.gen_synthetic --target 900
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
from datetime import date, timedelta
from pathlib import Path

from munshi.llm import RateLimited, call_gemma, extract_json
from munshi.parser import SPEC_PROMPT, normalise, user_turn
from munshi.tracing import init_sentry

HERE = Path(__file__).resolve().parent
GEN_PROMPT = """You write realistic WhatsApp messages that guests send to small hotels in Pakistan
(Murree, Naran, Swat, Islamabad). Mix Roman Urdu and English as real people do, with typos, missing
punctuation, "kal", "parso", "2 log", "advance kitni", budgets like "8k"/"8 hazar". About 15% should
omit the date or the number of guests. Vary room types, nights (1-5), group sizes (1-12).
Return a JSON object {{"messages": [ ... {n} strings ... ]}}. Seeds for style:\n{seeds}"""


def seeds() -> list[str]:
    text = (HERE / "seed_templates.md").read_text(encoding="utf-8")
    return [re.sub(r"\s*\(.*?\)\s*$", "", ln[2:]).strip() for ln in text.splitlines() if ln.startswith("- ")]


def existing(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln] if path.exists() else []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=900)
    ap.add_argument("--batch", type=int, default=12)
    ap.add_argument("--dev-frac", type=float, default=0.1)
    a = ap.parse_args()
    init_sentry("teacher")
    train_p, dev_p = HERE / "train.jsonl", HERE / "dev.jsonl"
    seen = {r["message"] for r in existing(train_p) + existing(dev_p)}
    rng, pool = random.Random(), seeds()
    while len(seen) < a.target:
        try:
            gen = call_gemma([{"role": "user", "content": GEN_PROMPT.format(
                n=a.batch, seeds="\n".join(rng.sample(pool, min(6, len(pool)))))}],
                json_mode=True, max_tokens=1500, temperature=1.0)
            msgs = [m for m in extract_json(gen.text).get("messages", []) if isinstance(m, str) and m not in seen]
        except RateLimited as e:
            print("429, sleeping", e.retry_after_s)
            time.sleep(e.retry_after_s)
            continue
        except Exception as e:  # noqa: BLE001
            print("gen failed:", e)
            continue
        for m in msgs:
            today = date(2026, 10, 1) + timedelta(days=rng.randrange(0, 60))  # vary TODAY so dates generalise
            try:
                lab = call_gemma([{"role": "system", "content": SPEC_PROMPT},
                                  {"role": "user", "content": user_turn(m, today)}],
                                 json_mode=True, max_tokens=300, temperature=0.0)
                inq = normalise(extract_json(lab.text), today)
            except Exception as e:  # noqa: BLE001  (bad label -> drop the row)
                print("label dropped:", str(e)[:80])
                continue
            row = {"today": today.isoformat(), "message": m, "label": inq.model_dump(mode="json"),
                   "source": "gemma-teacher"}
            with (dev_p if rng.random() < a.dev_frac else train_p).open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            seen.add(m)
        print(f"{len(seen)}/{a.target}")
    print("done. SPOT-CHECK 30 random labels by hand before training; fix or delete bad ones.")


if __name__ == "__main__":
    main()
