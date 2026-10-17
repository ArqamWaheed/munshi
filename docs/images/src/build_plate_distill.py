"""Writes plate-distill.html from results/ (booking-field exact match), so every figure is read, not typed.

Run 1: parser_eval_baselines.json (Gemma, base_spec) and parser_eval.json (the fine-tune, v2 adapter).
Run 2: parser_eval_r2_tinker_side.json. Run 3: parser_eval_r3.json. Fresh: parser_eval_fresh.json.
Run: python docs/images/src/build_plate_distill.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
R = ROOT / "results"


def booking(fname: str, model: str):
    p = R / fname
    if not p.exists():
        return None
    res = json.loads(p.read_text())["results"].get(model)
    if not res:
        return None
    rows = res["rows"]
    ok = sum(all(v for k, v in r["fields"].items() if k != "language") for r in rows)
    return ok, len(rows)


def pct(x):
    return "n/a" if x is None else f"{100 * x[0] / x[1]:.1f}%"


def frac(x):
    return "n/a" if x is None else f"{x[0]} / {x[1]}"


rows = [
    ("Qwen3.5-4B + Munshi LoRA", "68-token prompt", "tinker",
     [booking("parser_eval.json", "tinker"), booking("parser_eval_r2_tinker_side.json", "tinker"), booking("parser_eval_r3.json", "tinker"),
      booking("parser_eval_fresh.json", "tinker")], True),
    ("Gemma 4, the teacher", "532-token rulebook", "gemma",
     [booking("parser_eval_baselines.json", "gemma"), None, booking("parser_eval_r3.json", "gemma"),
      booking("parser_eval_fresh.json", "gemma")], False),
    ("Qwen3.5-4B, untuned", "532-token rulebook", "base_spec",
     [booking("parser_eval_baselines.json", "base_spec"), booking("parser_eval_r2_tinker_side.json", "base_spec"),
      booking("parser_eval_r3.json", "base_spec"), booking("parser_eval_fresh.json", "base_spec")], False),
]

trs = []
for name, prompt, _, cells, ft in rows:
    tds = "".join(f'<td class="n{" hi" if ft and i >= 2 else ""}">{pct(c) if i < 3 else frac(c)}</td>'
                  for i, c in enumerate(cells))
    trs.append(f'<tr class="{"ft" if ft else ""}"><td><b>{name}</b><span class="muted">{prompt}</span></td>{tds}</tr>')

html = f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="brand.css"><style>
h1{{font-size:80px;white-space:nowrap}}
.sub{{font-size:28px;margin-top:14px}}
table{{position:absolute;left:88px;right:88px;top:300px;width:1424px;border-collapse:collapse}}
th{{font-weight:600;font-size:24px;color:var(--muted);text-align:right;padding:0 22px 20px;line-height:1.25;vertical-align:bottom}}
th.code{{color:var(--signal)}}
th:first-child,td:first-child{{text-align:left}}
td{{padding:24px 22px;border-top:2px solid var(--line);font-size:28px}}
td b{{display:block;font-weight:700}} td span{{font-size:20px}}
td.n{{text-align:right;font-family:"JetBrains Mono",monospace;font-size:38px}}
tr.ft td{{background:var(--night2)}}
td.hi{{background:var(--red)!important;font-weight:700}}
</style></head><body><div class="page">
<h1 class="disp">The student lost. Then code did the counting.</h1>
<div class="sub muted">Booking fields exactly right. 80 hand-labelled messages, then 30 written after the rules froze.</div>
<table>
<tr><th>Parser</th><th>Run 1<br>no rules</th><th class="code">Run 2<br>+ dates in code</th><th class="code">Run 3<br>+ counts in code</th><th class="code">Fresh 30<br>rules frozen, run once</th></tr>
{"".join(trs)}
</table>
<div class="foot">Models read. Code decides.</div>
</div></body></html>
"""
(Path(__file__).parent / "plate-distill.html").write_text(html, encoding="utf-8")
print("\n".join(f"{n}: " + ", ".join(pct(c) for c in cells) for n, _, _, cells, _ in rows))
