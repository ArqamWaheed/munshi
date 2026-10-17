"""Before training: leakage and overlap checks, then a random sample for the hand spot-check.

  python -m data.check_data            # exits 1 if any eval message (normalised) appears in train/dev
Writes results/spot_check.md: 30 random training rows with their teacher labels, to mark right/wrong by hand.
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name: str) -> list[dict]:
    p = HERE / name
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []


def norm(text: str) -> str:
    return re.sub(r"[^\w]+", " ", text.lower()).strip()


def main() -> None:
    train, dev, ev = load("train.jsonl"), load("dev.jsonl"), load("eval.jsonl")
    ev_norm = {norm(r["message"]): r["id"] for r in ev}
    leaks = [(r["message"], ev_norm[norm(r["message"])]) for r in train + dev if norm(r["message"]) in ev_norm]
    overlap = {norm(r["message"]) for r in train} & {norm(r["message"]) for r in dev}
    dupes = sum(c - 1 for c in Counter(norm(r["message"]) for r in train).values() if c > 1)
    langs = Counter(r["label"]["language"] for r in train)
    clar = sum(r["label"]["needs_clarification"] for r in train)
    print(f"train {len(train)}, dev {len(dev)}, eval {len(ev)}")
    print(f"eval leaks into train/dev: {len(leaks)} {leaks[:3]}")
    print(f"train/dev overlap (normalised): {len(overlap)}; duplicate train rows (normalised): {dupes}")
    print(f"train languages: {dict(langs)}; needs_clarification: {clar} ({clar / max(len(train), 1):.0%})")

    rng = random.Random(7)
    sample = rng.sample(train, min(30, len(train)))
    md = ["# Teacher-label spot check (30 random rows of data/train.jsonl, seed 7)", "",
          "Mark each row [x] if every field is right under the conventions in data/seed_templates.md; otherwise",
          "write what is wrong. The error rate is the honest label-noise number for the post.", ""]
    for i, r in enumerate(sample, 1):
        lab = {k: v for k, v in r["label"].items() if k != "clarification_question" and v not in (None, "any")}
        md.append(f"{i}. [ ] TODAY {r['today']}: `{r['message']}`  \n   -> {json.dumps(lab, ensure_ascii=False)}")
    (ROOT / "results" / "spot_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote results/spot_check.md")
    sys.exit(1 if leaks else 0)


if __name__ == "__main__":
    main()
