"""No-show/cancel model eval: TabPFN-3.5 vs LogisticRegression vs HistGradientBoosting on
"small hotel" training sets (default 300 rows) x 10 seeds, scored by ROC-AUC on one fixed held-out set.

Held-out set: 2,000 rows drawn once (seed 12345) and excluded from every training sample.
TabPFN calls: 10 fits + 10 predicts = 20 API calls (well inside 60/min). Writes results/risk_eval.json
and results/risk_eval.md. Honest caveat for the post: Portuguese hotels 2015-17, not Pakistani data.

  python -m eval.eval_risk --rows 300 --seeds 10
  python -m eval.eval_risk --models logreg hgb --name risk_baselines   # offline run without a TabPFN token
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score

from munshi import config as cfg
from munshi.risk import FEATURES, TARGET, as_category, features_from_bookings, make_hgb, make_logreg, make_tabpfn

ROOT = Path(__file__).resolve().parent.parent
MAKERS = {"tabpfn": make_tabpfn, "logreg": make_logreg, "hgb": make_hgb}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=300)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--test-rows", type=int, default=2000)
    ap.add_argument("--models", nargs="+", default=["tabpfn", "logreg", "hgb"], choices=list(MAKERS))
    ap.add_argument("--name", default="risk_eval", help="output file stem under results/")
    a = ap.parse_args()
    df = features_from_bookings(pd.read_csv(cfg.BOOKINGS_CSV))
    test = df.sample(n=a.test_rows, random_state=12345)
    pool = df.drop(test.index)
    scores: dict[str, list[float]] = {m: [] for m in a.models}
    fit_s: dict[str, list[float]] = {m: [] for m in a.models}
    for seed in range(a.seeds):
        tr = pool.sample(n=a.rows, random_state=seed)
        for m in a.models:
            Xtr, Xte = tr[FEATURES], test[FEATURES]
            if m == "hgb":
                Xtr, Xte = as_category(Xtr), as_category(Xte)
            t0 = time.perf_counter()
            model = MAKERS[m]().fit(Xtr, tr[TARGET])
            p = model.predict_proba(Xte)[:, 1]
            fit_s[m].append(time.perf_counter() - t0)
            scores[m].append(roc_auc_score(test[TARGET], p))
            print(f"seed {seed} {m}: AUC {scores[m][-1]:.4f}")
    summary = {m: {"auc_mean": statistics.mean(v), "auc_std": statistics.stdev(v) if len(v) > 1 else 0.0,
                   "auc_min": min(v), "auc_max": max(v), "wins": 0, "fit_predict_s_mean": statistics.mean(fit_s[m]),
                   "per_seed": v} for m, v in scores.items()}
    for s in range(a.seeds):
        best = max(a.models, key=lambda m: scores[m][s])
        summary[best]["wins"] += 1
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    meta = {"train_rows": a.rows, "seeds": a.seeds, "test_rows": a.test_rows, "features": FEATURES,
            "test_base_rate": float(test[TARGET].mean()), "tabpfn_version": cfg.TABPFN_VERSION}
    (out / f"{a.name}.json").write_text(json.dumps({"meta": meta, "results": summary}, indent=2))
    md = [f"Train rows: {a.rows} x {a.seeds} seeds; fixed test set {a.test_rows} rows "
          f"(cancel rate {meta['test_base_rate']:.1%}).", "",
          "| Model | ROC-AUC mean | std | min | max | seeds won | s per fit+predict |", "|---|---:|---:|---:|---:|---:|---:|"]
    for m, s in sorted(summary.items(), key=lambda kv: -kv[1]["auc_mean"]):
        md.append(f"| {m} | {s['auc_mean']:.4f} | {s['auc_std']:.4f} | {s['auc_min']:.4f} | {s['auc_max']:.4f} | "
                  f"{s['wins']}/{a.seeds} | {s['fit_predict_s_mean']:.2f} |")
    (out / f"{a.name}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
