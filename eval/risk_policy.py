"""Do the risk scores mean what they say, and does pricing the advance by risk beat a flat advance?

Same split as eval_risk (fixed 2,000-row test set, seed 12345; 300-row "small hotel" training samples).
1. Calibration: per hold-policy band (<25%, 25-50%, >=50%) the share of bookings, mean predicted risk and the
   actual cancel rate; plus Brier score and expected calibration error (10 equal-width bins).
2. Policy: the advance a guest pays is kept if they cancel. Value = nights x ADR from the dataset. Compares
   flat advances with Munshi's tiers (20/30/50% by band) on: share of cancelled value kept, and the advance
   asked of guests who did turn up (the friction honest guests pay). Expressed as % of booking value, since
   the dataset's ADR is in EUR (Portuguese hotels, 2015-17), not PKR.

  python -m eval.risk_policy --seeds 5
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

from munshi import config as cfg
from munshi.risk import FEATURES, TARGET, features_from_bookings, make_logreg, make_tabpfn
from munshi.schema import HoldPolicy

ROOT = Path(__file__).resolve().parent.parent
MAKERS = {"tabpfn": make_tabpfn, "logreg": make_logreg}
POL = HoldPolicy()
BANDS = [("low", 0.0, POL.low_threshold, POL.advance_low), ("medium", POL.low_threshold, POL.high_threshold,
         POL.advance_mid), ("high", POL.high_threshold, 1.01, POL.advance_high)]


def band_of(p: np.ndarray) -> np.ndarray:
    return np.select([p >= POL.high_threshold, p >= POL.low_threshold], ["high", "medium"], "low")


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    idx = np.minimum((p * bins).astype(int), bins - 1)
    return float(sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).mean()
                     for b in range(bins) if (idx == b).any()))


def policy(adv: np.ndarray, y: np.ndarray, value: np.ndarray) -> dict:
    """adv = advance fraction per booking. Kept = advance of cancelled bookings / their value."""
    c, s = y == 1, y == 0
    return {"kept_pct_of_cancelled_value": float((adv[c] * value[c]).sum() / value[c].sum()),
            "asked_pct_of_shown_value": float((adv[s] * value[s]).sum() / value[s].sum()),
            "share_asked_50pct": float((adv >= 0.5).mean())}


def evaluate(p: np.ndarray, y: np.ndarray, value: np.ndarray) -> dict:
    b = band_of(p)
    bands = {name: {"share": float((b == name).mean()), "mean_pred": float(p[b == name].mean()) if (b == name).any()
                    else None, "actual": float(y[b == name].mean()) if (b == name).any() else None,
                    "share_of_cancels": float(((b == name) & (y == 1)).sum() / max((y == 1).sum(), 1))}
             for name, *_ in BANDS}
    tiers = np.select([b == "high", b == "medium"], [POL.advance_high, POL.advance_mid], POL.advance_low)
    return {"brier": float(((p - y) ** 2).mean()), "ece": ece(p, y), "bands": bands,
            "policy_tiered": policy(tiers, y, value)}


def mean_dicts(ds: list[dict]) -> dict:
    """Element-wise mean of nested dicts of floats (None-safe)."""
    out = {}
    for k, v in ds[0].items():
        if isinstance(v, dict):
            out[k] = mean_dicts([d[k] for d in ds])
        else:
            vals = [d[k] for d in ds if d[k] is not None]
            out[k] = statistics.mean(vals) if vals else None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=300)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--test-rows", type=int, default=2000)
    ap.add_argument("--models", nargs="+", default=list(MAKERS), choices=list(MAKERS))
    a = ap.parse_args()
    raw = pd.read_csv(cfg.BOOKINGS_CSV)
    df = features_from_bookings(raw)
    test = df.sample(n=a.test_rows, random_state=12345)
    pool = df.drop(test.index)
    y = test[TARGET].to_numpy()
    r = raw.loc[test.index]
    value = ((r["stays_in_weekend_nights"] + r["stays_in_week_nights"]).clip(lower=1) * r["adr"].clip(lower=0)).to_numpy()

    per_model: dict[str, list[dict]] = {m: [] for m in a.models}
    for seed in range(a.seeds):
        tr = pool.sample(n=a.rows, random_state=seed)
        for m in a.models:
            p = MAKERS[m]().fit(tr[FEATURES], tr[TARGET]).predict_proba(test[FEATURES])[:, 1]
            per_model[m].append(evaluate(np.asarray(p, dtype=float), y, value))
            print(f"seed {seed} {m}: brier {per_model[m][-1]['brier']:.4f}")
    results = {m: mean_dicts(v) for m, v in per_model.items()}
    flat = {f"flat_{int(f * 100)}": policy(np.full(len(y), f), y, value) for f in (0.2, 0.3, 0.5)}

    out = ROOT / "results"
    meta = {"train_rows": a.rows, "seeds": a.seeds, "test_rows": a.test_rows, "test_cancel_rate": float(y.mean()),
            "policy": {name: {"from": lo, "to": hi, "advance": adv} for name, lo, hi, adv in BANDS}}
    (out / "risk_policy.json").write_text(json.dumps({"meta": meta, "models": results, "flat": flat}, indent=2))

    md = [f"Test set {a.test_rows} bookings (cancel rate {y.mean():.1%}); each model trained on {a.rows} rows, "
          f"mean over {a.seeds} seeds.", "", "**Calibration by hold band**", "",
          "| Model | Band | Share of bookings | Mean predicted | Actually cancelled | Share of all cancels |",
          "|---|---|---:|---:|---:|---:|"]
    for m, res in results.items():
        for name, *_ in BANDS:
            bd = res["bands"][name]
            fmt = lambda x: "n/a" if x is None else f"{x:.0%}"  # noqa: E731
            md.append(f"| {m} | {name} | {fmt(bd['share'])} | {fmt(bd['mean_pred'])} | {fmt(bd['actual'])} | "
                      f"{fmt(bd['share_of_cancels'])} |")
    md += ["", "| Model | Brier (lower better) | ECE (lower better) |", "|---|---:|---:|"]
    md += [f"| {m} | {res['brier']:.4f} | {res['ece']:.3f} |" for m, res in results.items()]
    md += ["", "**Advance policy** (advance kept when a guest cancels; % of booking value)", "",
           "| Policy | Kept from cancelled bookings | Asked of guests who came | Guests asked 50% |",
           "|---|---:|---:|---:|"]
    rows = [(k, v) for k, v in flat.items()] + [(f"tiered by {m}", res["policy_tiered"]) for m, res in results.items()]
    md += [f"| {k} | {v['kept_pct_of_cancelled_value']:.1%} | {v['asked_pct_of_shown_value']:.1%} | "
           f"{v['share_asked_50pct']:.0%} |" for k, v in rows]
    (out / "risk_policy.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
