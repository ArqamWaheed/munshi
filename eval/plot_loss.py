"""Train/dev NLL curve from results/train_log.json -> results/train_loss.svg (plain SVG, no matplotlib).

  python -m eval.plot_loss
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, PAD_L, PAD_R, PAD_T, PAD_B = 640, 360, 56, 120, 40, 44
SERIES = [("train_nll", "train NLL", "#0d6b5f"), ("dev_nll", "dev NLL", "#b54708")]


def render(log: dict) -> str:
    rows = log["log"]
    steps = [r["step"] for r in rows]
    ys = [r[k] for r in rows for k, _, _ in SERIES if k in r]
    x0, x1, y1 = min(steps), max(max(steps), 1), max(ys) * 1.05
    sx = lambda s: PAD_L + (s - x0) / max(x1 - x0, 1) * (W - PAD_L - PAD_R)  # noqa: E731
    sy = lambda y: PAD_T + (1 - y / y1) * (H - PAD_T - PAD_B)  # noqa: E731
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,sans-serif" '
           f'font-size="12"><rect width="{W}" height="{H}" fill="#fff"/>',
           f'<text x="{PAD_L}" y="22" font-size="14" font-weight="600">{log["base_model"]} LoRA r{log["rank"]}: '
           f'{log["examples"]} examples, {log["epochs"]} epochs</text>']
    for i in range(5):  # y grid
        y = y1 * i / 4
        out.append(f'<line x1="{PAD_L}" x2="{W - PAD_R}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" stroke="#e3ded4"/>'
                   f'<text x="{PAD_L - 8}" y="{sy(y) + 4:.1f}" text-anchor="end" fill="#6b665e">{y:.2f}</text>')
    epoch_starts = sorted({r["step"] for r in rows if r["step"] == min(q["step"] for q in rows if q["epoch"] == r["epoch"])})
    for s in epoch_starts[1:]:
        out.append(f'<line x1="{sx(s):.1f}" x2="{sx(s):.1f}" y1="{PAD_T}" y2="{H - PAD_B}" stroke="#c9c3b8" '
                   f'stroke-dasharray="3 3"/>')
    out.append(f'<text x="{(PAD_L + W - PAD_R) / 2}" y="{H - 10}" text-anchor="middle" fill="#6b665e">step '
               f'(dashed = new epoch)</text>')
    for i, (key, label, color) in enumerate(SERIES):
        pts = [(sx(r["step"]), sy(r[key])) for r in rows if key in r]
        if not pts:
            continue
        out.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="'
                   + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
        if len(pts) < 20:
            out += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>' for x, y in pts]
        last = [r[key] for r in rows if key in r][-1]
        out.append(f'<text x="{W - PAD_R + 10}" y="{PAD_T + 16 + i * 18}" fill="{color}">{label} {last:.3f}</text>')
    return "\n".join(out + ["</svg>"]) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, default=ROOT / "results" / "train_log.json")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "train_loss.svg")
    a = ap.parse_args()
    a.out.write_text(render(json.loads(a.log.read_text())), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
