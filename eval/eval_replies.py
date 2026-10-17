"""How often does Gemma's guest reply get a number wrong, and what does the checker do about it?

For every row of data/eval.jsonl that needs no clarification, build the quote Munshi would send (no comps:
base rate; risk cycles 10% / 35% / 60% so all three advance tiers appear), ask Gemma for the quote reply
exactly as production does, and run munshi.reply.check_draft on it. Rejected drafts get the production
hinted retry. Writes results/reply_eval.{json,md}. ~1.1 Gemma calls per row (~70 calls for the eval set).

  python -m eval.eval_replies
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from datetime import date
from pathlib import Path

from munshi import config as cfg
from munshi import policy, reply
from munshi.llm import ProviderError, RateLimited
from munshi.schema import HoldPolicy, Inquiry
from munshi.tracing import init_sentry

ROOT = Path(__file__).resolve().parent.parent
RISKS = (0.10, 0.35, 0.60)


def call(fn, *args):
    for _ in range(5):
        try:
            return fn(*args)
        except RateLimited as e:
            time.sleep(e.retry_after_s)
        except ProviderError:
            time.sleep(5)
    raise RuntimeError("Gemma unavailable 5x")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    init_sentry("eval")
    rows = [json.loads(ln) for ln in (ROOT / "data" / "eval.jsonl").read_text(encoding="utf-8").splitlines() if ln]
    rows = [r for r in rows if not r["label"]["needs_clarification"] and r["label"]["check_in"]][: a.limit]
    hotel, out = cfg.HOTEL_NAME, []
    for i, r in enumerate(rows):
        inq = Inquiry.model_validate(r["label"])
        quote = policy.make_quote(inq, None, RISKS[i % len(RISKS)], HoldPolicy())
        first = call(reply.draft, inq, quote, "quote", hotel)
        p1 = reply.check_draft(first.text, inq, quote, "quote", hotel)
        rec = {"id": r["id"], "language": inq.language, "first_problems": p1, "first_text": first.text.strip(),
               "latency_s": first.latency_s, "words": len(first.text.split())}
        if p1:
            second = call(reply.draft, inq, quote, "quote", hotel, "; ".join(p1))
            p2 = reply.check_draft(second.text, inq, quote, "quote", hotel)
            rec |= {"retry_problems": p2, "retry_text": second.text.strip()}
        rec["sent"] = "gemma" if not p1 or not rec["retry_problems"] else "template"
        out.append(rec)
        print(r["id"], "OK" if not p1 else f"REJECTED {p1} -> {'OK' if rec['sent'] == 'gemma' else 'template'}")

    n = len(out)
    first_bad = [x for x in out if x["first_problems"]]
    kinds = Counter(p.split(":")[0].split(" (")[0] for x in first_bad for p in x["first_problems"])
    summary = {"n": n, "first_pass": n - len(first_bad), "rejected_first": len(first_bad),
               "fixed_by_retry": sum(1 for x in first_bad if x["sent"] == "gemma"),
               "template": sum(1 for x in out if x["sent"] == "template"), "problem_kinds": dict(kinds),
               "by_language": {lang: {"n": sum(1 for x in out if x["language"] == lang),
                                      "rejected_first": sum(1 for x in first_bad if x["language"] == lang)}
                               for lang in sorted({x["language"] for x in out})},
               "latency_p50_s": statistics.median(x["latency_s"] for x in out), "model": cfg.GEMMA_MODEL}
    (ROOT / "results" / "reply_eval.json").write_text(json.dumps({"summary": summary, "rows": out}, indent=2,
                                                                 ensure_ascii=False))
    md = [f"Gemma ({cfg.GEMMA_MODEL}) quote replies for {n} eval inquiries, checked by munshi.reply.check_draft.", "",
          "| Drafts | Passed first time | Rejected | Fixed by one hinted retry | Sent as template |",
          "|---:|---:|---:|---:|---:|",
          f"| {n} | {summary['first_pass']} | {summary['rejected_first']} | {summary['fixed_by_retry']} | "
          f"{summary['template']} |", "", "Rejections by reason: " +
          (", ".join(f"{k} {v}" for k, v in kinds.most_common()) or "none"), "",
          "| Language | Drafts | Rejected first time |", "|---|---:|---:|"]
    md += [f"| {k} | {v['n']} | {v['rejected_first']} |" for k, v in summary["by_language"].items()]
    md += ["", "Examples of rejected first drafts:", ""]
    md += [f"- `{x['id']}` ({'; '.join(x['first_problems'])}): {x['first_text']}" for x in first_bad[:5]]
    (ROOT / "results" / "reply_eval.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
