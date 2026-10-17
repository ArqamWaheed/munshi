"""Parser eval: Gemma 4 zero-shot (baseline) vs the Tinker fine-tune on the SAME held-out set.

Metrics (all computed here, nothing hard-coded):
  * field accuracy per field + exact-match rate, overall and on the Roman-Urdu slice
    (label.language in {roman_urdu, mixed}); invalid JSON counts as all-fields-wrong
  * booking exact match: every parsed field except `language`. The roman_urdu/mixed boundary is an eval
    convention the teacher's SPEC_PROMPT never stated (data/seed_templates.md), and it only picks the
    reply style. Decided before any parser results existed; full exact match is still reported.
  * p50 / p90 latency (wall clock per request, from this machine in Pakistan)
  * cost per 1,000 messages: actual (Gemma free tier = $0) and at list price (Gemma: OpenRouter paid
    price; Tinker: prefill+sample price x measured tokens)
Models: tinker (the fine-tune) against three baselines: gemma (Gemma 4 + the long SPEC_PROMPT, i.e. the
teacher), base (untuned Qwen3.5-4B + the same short prompt the fine-tune uses: isolates the training) and
base_spec (untuned Qwen3.5-4B + SPEC_PROMPT: "couldn't you just prompt it?"). A reply missing any schema key
counts as invalid. Statistics: 95% bootstrap CIs (10,000 resamples of rows, seed 0) and exact two-sided
McNemar tests on the same rows, tinker vs each baseline.
Writes results/parser_eval.json and results/parser_eval.md. Uses data/eval.jsonl (copy the format
of data/eval_template.jsonl; 60-100 hand-labelled, real where possible, NEVER from train.jsonl).
Gemma is rate-limited to ~14 RPM, so 100 messages take ~7-8 min.

  python -m eval.eval_parser --models gemma tinker
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from datetime import date
from pathlib import Path

import numpy as np

from munshi import config as cfg
from munshi.llm import ProviderError, RateLimited
from munshi.parser import parse_message
from munshi.schema import PARSED_FIELDS, Inquiry
from munshi.tracing import init_sentry

ROOT = Path(__file__).resolve().parent.parent
RU = {"roman_urdu", "mixed"}
BOOKING_FIELDS = tuple(f for f in PARSED_FIELDS if f != "language")


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
            except ProviderError:  # upstream 5xx/timeout is not the model's answer: retry, don't score it wrong
                time.sleep(5)
            except Exception as e:  # noqa: BLE001  (invalid output counts as wrong)
                pred, rec = None, {"ok": False, "error": str(e)[:200]}
                break
        else:
            pred, rec = None, {"ok": False, "error": "rate limited / upstream error 5x"}
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
                "booking_exact": sum(all(r["fields"][f] for f in BOOKING_FIELDS) for r in sub) / len(sub),
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


def booking_ok(r: dict) -> bool:
    return all(r["fields"][f] for f in BOOKING_FIELDS)


def exact_ok(r: dict) -> bool:
    return all(r["fields"].values())


def bootstrap_ci(xs: list[bool], n_boot: int = 10_000, seed: int = 0) -> tuple[float, float]:
    a = np.asarray(xs, dtype=float)
    means = a[np.random.default_rng(seed).integers(0, len(a), (n_boot, len(a)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def mcnemar(a: list[bool], b: list[bool]) -> dict:
    """Exact two-sided McNemar on paired outcomes: only rows where exactly one model is right count."""
    only_a = sum(x and not y for x, y in zip(a, b))
    only_b = sum(y and not x for x, y in zip(a, b))
    n = only_a + only_b
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(only_a, only_b) + 1)) / 2 ** n) if n else 1.0
    return {"only_first": only_a, "only_second": only_b, "p": p}


def stats(results: dict) -> dict:
    out = {"ci": {}, "vs_tinker": {}}
    for name, r in results.items():
        out["ci"][name] = {k: bootstrap_ci([f(x) for x in r["rows"]]) for k, f in
                           (("booking_exact", booking_ok), ("exact_match", exact_ok))}
    if "tinker" in results:
        t = results["tinker"]["rows"]
        for name, r in results.items():
            if name != "tinker":
                out["vs_tinker"][name] = {k: mcnemar([f(x) for x in t], [f(x) for x in r["rows"]])
                                          for k, f in (("booking_exact", booking_ok), ("exact_match", exact_ok))}
    return out


def stats_table(results: dict, st: dict) -> str:
    rows = ["", "Booking exact match with 95% bootstrap CI:", "", "| Model | Booking exact | 95% CI |", "|---|---:|---|"]
    for name, r in results.items():
        lo, hi = st["ci"][name]["booking_exact"]
        rows.append(f"| {name} | {fmt(r['overall']['booking_exact'], 1)} | {lo:.1%} to {hi:.1%} |")
    if st["vs_tinker"]:
        rows += ["", "Paired exact McNemar, fine-tune vs each baseline (same rows):", "",
                 "| Comparison | Metric | Only fine-tune right | Only baseline right | p |", "|---|---|---:|---:|---:|"]
        for name, by in st["vs_tinker"].items():
            for metric, m in by.items():
                rows.append(f"| tinker vs {name} | {metric} | {m['only_first']} | {m['only_second']} | {m['p']:.3g} |")
    return "\n".join(rows) + "\n"


def fmt(x, p=False):
    return "n/a" if x is None else (f"{x:.1%}" if p else f"{x:.4g}")


def table(results: dict) -> str:
    rows = ["| Model | N | Booking exact | Exact match | Mean field acc | Roman-Urdu booking exact | Valid JSON | p50 s | "
            "p90 s | $/1k actual | $/1k list |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, r in results.items():
        o, ru = r["overall"], r["roman_urdu"] or {}
        rows.append(f"| {name} ({r['model']}) | {o['n']} | {fmt(o['booking_exact'], 1)} | {fmt(o['exact_match'], 1)} | "
                    f"{fmt(o['field_acc_mean'], 1)} | {fmt(ru.get('booking_exact'), 1)} | {fmt(o['valid_json'], 1)} | {fmt(r['latency_p50_s'])} | "
                    f"{fmt(r['latency_p90_s'])} | {fmt(r['cost_per_1k_usd'])} | {fmt(r['list_cost_per_1k_usd'])} |")
    rows += ["", "Per-field accuracy:", "", "| Field | " + " | ".join(results) + " |",
             "|---|" + "---:|" * len(results)]
    for f in PARSED_FIELDS:
        rows.append(f"| {f} | " + " | ".join(fmt(r["overall"]["per_field"][f], 1) for r in results.values()) + " |")
    return "\n".join(rows) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default=str(ROOT / "data" / "eval.jsonl"))
    ap.add_argument("--models", nargs="+", default=["gemma", "base", "base_spec", "tinker"],
                    choices=["gemma", "base", "base_spec", "tinker"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--tinker-path", help="evaluate this tinker:// sampler path instead of TINKER_MODEL_PATH")
    ap.add_argument("--out", default="parser_eval", help="output file stem under results/")
    a = ap.parse_args()
    init_sentry("eval")
    if a.tinker_path:
        cfg.TINKER_MODEL_PATH = a.tinker_path
    rows = [json.loads(ln) for ln in Path(a.eval).read_text(encoding="utf-8").splitlines() if ln.strip()][: a.limit]
    results = {m: run_model(m, rows) for m in a.models}
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    st = stats(results)
    (out / f"{a.out}.json").write_text(json.dumps({"eval_file": a.eval, "n": len(rows), "results": results,
                                                      "stats": st}, indent=2, default=str))
    md = table(results) + stats_table(results, st)
    (out / f"{a.out}.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
