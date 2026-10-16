"""Parser eval: Gemma 4 zero-shot (baseline) vs the Tinker fine-tune on the SAME held-out set.

Metrics (all computed here, nothing hard-coded):
  * field accuracy per field + exact-match rate, overall and on the Roman-Urdu slice
    (label.language in {roman_urdu, mixed}); invalid JSON counts as all-fields-wrong
  * p50 / p90 latency (wall clock per request, from this machine in Pakistan)
  * cost per 1,000 messages: actual (Gemma free tier = $0) and at list price (Gemma: OpenRouter paid
    price; Tinker: prefill+sample price x measured tokens)
Writes results/parser_eval.json and results/parser_eval.md. Uses data/eval.jsonl (copy the format
of data/eval_template.jsonl; 60-100 hand-labelled, real where possible, NEVER from train.jsonl).
Gemma is rate-limited to ~14 RPM, so 100 messages take ~7-8 min.

  python -m eval.eval_parser --models gemma tinker
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import date
from pathlib import Path

from munshi.llm import RateLimited
from munshi.parser import parse_message
from munshi.schema import PARSED_FIELDS, Inquiry
from munshi.tracing import init_sentry

ROOT = Path(__file__).resolve().parent.parent
RU = {"roman_urdu", "mixed"}


def pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def run_model(provider: str, rows: list[dict]) -> dict:
    per_row = []
    for r in rows:
        today, gold = date.fromisoformat(r["today"]), Inquiry.model_validate(r["label"])
        for _ in range(5):
            try:
                pred, res = parse_message(r["message"], today, provider)
                rec = {"ok": True, "latency_s": res.latency_s, "in": res.input_tokens, "out": res.output_tokens,
                       "cost": res.cost_usd, "list_cost": res.list_cost_usd, "model": res.model}
                break
            except RateLimited as e:
                time.sleep(e.retry_after_s)
            except Exception as e:  # noqa: BLE001  (invalid output counts as wrong)
                pred, rec = None, {"ok": False, "error": str(e)[:200]}
                break
        else:
            pred, rec = None, {"ok": False, "error": "rate limited 5x"}
        rec["id"], rec["ru"] = r.get("id"), gold.language in RU
        rec["fields"] = {f: (pred is not None and getattr(pred, f) == getattr(gold, f)) for f in PARSED_FIELDS}
        per_row.append(rec)
        print(provider, rec["id"], "OK" if rec["ok"] else "FAIL", sum(rec["fields"].values()), "/", len(PARSED_FIELDS))
    return {"rows": per_row, **summarise(per_row)}


def summarise(rows: list[dict]) -> dict:
    def acc(sub):
        if not sub:
            return None
        return {"n": len(sub),
                "exact_match": sum(all(r["fields"].values()) for r in sub) / len(sub),
                "field_acc_mean": statistics.mean(sum(r["fields"].values()) / len(PARSED_FIELDS) for r in sub),
                "per_field": {f: sum(r["fields"][f] for r in sub) / len(sub) for f in PARSED_FIELDS},
                "valid_json": sum(r["ok"] for r in sub) / len(sub)}
    ok = [r for r in rows if r["ok"]]
    lat = [r["latency_s"] for r in ok]
    n = max(len(ok), 1)
    return {"overall": acc(rows), "roman_urdu": acc([r for r in rows if r["ru"]]),
            "latency_p50_s": pct(lat, 0.5), "latency_p90_s": pct(lat, 0.9),
            "avg_tokens_in": sum(r["in"] for r in ok) / n, "avg_tokens_out": sum(r["out"] for r in ok) / n,
            "cost_per_1k_usd": 1000 * sum(r["cost"] for r in ok) / n,
            "list_cost_per_1k_usd": 1000 * sum(r["list_cost"] for r in ok) / n,
            "model": ok[0]["model"] if ok else None}


def fmt(x, p=False):
    return "n/a" if x is None else (f"{x:.1%}" if p else f"{x:.4g}")


def table(results: dict) -> str:
    rows = ["| Model | N | Exact match | Mean field acc | Roman-Urdu exact | Valid JSON | p50 s | p90 s | $/1k actual | $/1k list |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, r in results.items():
        o, ru = r["overall"], r["roman_urdu"] or {}
        rows.append(f"| {name} ({r['model']}) | {o['n']} | {fmt(o['exact_match'], 1)} | {fmt(o['field_acc_mean'], 1)} | "
                    f"{fmt(ru.get('exact_match'), 1)} | {fmt(o['valid_json'], 1)} | {fmt(r['latency_p50_s'])} | "
                    f"{fmt(r['latency_p90_s'])} | {fmt(r['cost_per_1k_usd'])} | {fmt(r['list_cost_per_1k_usd'])} |")
    rows += ["", "Per-field accuracy:", "", "| Field | " + " | ".join(results) + " |",
             "|---|" + "---:|" * len(results)]
    for f in PARSED_FIELDS:
        rows.append(f"| {f} | " + " | ".join(fmt(r["overall"]["per_field"][f], 1) for r in results.values()) + " |")
    return "\n".join(rows) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default=str(ROOT / "data" / "eval.jsonl"))
    ap.add_argument("--models", nargs="+", default=["gemma", "tinker"], choices=["gemma", "tinker"])
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    init_sentry("eval")
    rows = [json.loads(ln) for ln in Path(a.eval).read_text(encoding="utf-8").splitlines() if ln.strip()][: a.limit]
    results = {m: run_model(m, rows) for m in a.models}
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "parser_eval.json").write_text(json.dumps({"eval_file": a.eval, "n": len(rows), "results": results},
                                                     indent=2, default=str))
    md = table(results)
    (out / "parser_eval.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
