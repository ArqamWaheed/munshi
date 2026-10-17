"""Generates compositions/frames/NN-*.html (one <template> each) for the Munshi promo.

Shared look from frame.md: paper #F4EDE0 ledger ground, teal ink #0D5C52, sun #E3A21A, ember #A23B2A.
Fonts are local files in assets/fonts (Latin subsets: arrows go in JetBrains Mono, which has U+2192).
Every number on screen comes from munshi/results (see STORYBOARD.md).
Run: python build_frames.py
"""
from pathlib import Path

OUT = Path(__file__).parent / "compositions" / "frames"
INK, PAPER, SUN, EMBER, DARK = "#0D5C52", "#F4EDE0", "#E3A21A", "#A23B2A", "#1D1B18"

FONTS = """
@font-face{font-family:"Cormorant Garamond";src:url(assets/fonts/cormorant-garamond-latin-400-normal.woff2) format("woff2");font-weight:400}
@font-face{font-family:"Cormorant Garamond";src:url(assets/fonts/cormorant-garamond-latin-700-normal.woff2) format("woff2");font-weight:700}
@font-face{font-family:"Inter";src:url(assets/fonts/inter-latin-400-normal.woff2) format("woff2");font-weight:400}
@font-face{font-family:"Inter";src:url(assets/fonts/inter-latin-600-normal.woff2) format("woff2");font-weight:600}
@font-face{font-family:"Inter";src:url(assets/fonts/inter-latin-700-normal.woff2) format("woff2");font-weight:700}
@font-face{font-family:"JetBrains Mono";src:url(assets/fonts/JetBrainsMono-400.woff2) format("woff2");font-weight:400}
@font-face{font-family:"JetBrains Mono";src:url(assets/fonts/JetBrainsMono-700.woff2) format("woff2");font-weight:700}
@font-face{font-family:"Caveat";src:url(assets/fonts/caveat-latin-700-normal.woff2) format("woff2");font-weight:700}
"""


def frame(fid: str, dur: float, css: str, body: str, js: str, bloom=("62%", "48%", "980px")) -> str:
    bx, by, bs = bloom
    p = fid  # prefix for ids/classes
    return f"""<template>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
{FONTS}
#root{{position:absolute;inset:0;overflow:hidden;font-family:"Inter",sans-serif;color:{INK}}}
.{p}-bg{{position:absolute;inset:0;background:{PAPER}}}
.{p}-lines{{position:absolute;inset:0;background:repeating-linear-gradient(to bottom,transparent 0 51px,rgba(13,92,82,.07) 51px 52px)}}
.{p}-margin{{position:absolute;top:0;bottom:0;left:112px;width:2px;background:rgba(162,59,42,.35)}}
.{p}-bloom{{position:absolute;left:{bx};top:{by};width:{bs};height:{bs};margin-left:calc({bs} / -2);margin-top:calc({bs} / -2);
  border-radius:50%;background:radial-gradient(circle,rgba(227,162,26,.42) 0%,rgba(244,217,159,.34) 34%,rgba(240,202,124,.12) 58%,transparent 72%)}}
.{p}-abs{{position:absolute}}
.{p}-serif{{font-family:"Cormorant Garamond",serif;font-weight:400;letter-spacing:-.01em}}
.{p}-mono{{font-family:"JetBrains Mono",monospace}}
.{p}-hand{{font-family:"Caveat",cursive;font-weight:700;color:{EMBER}}}
.{p}-kicker{{font-family:"JetBrains Mono",monospace;font-size:22px;letter-spacing:.22em;text-transform:uppercase;opacity:.8}}
{css}
</style>
<div id="root" data-composition-id="{fid}" data-width="1920" data-height="1080">
  <div class="clip {p}-bg" id="{p}-bg" data-start="0" data-duration="{dur}" data-track-index="0">
    <div class="{p}-lines"></div><div class="{p}-margin"></div><div class="{p}-bloom" id="{p}-bloom"></div>
  </div>
{body}
</div>
<script>
(function(){{
  const tl = gsap.timeline({{ paused: true }});
  const $ = (s) => document.querySelector('[data-composition-id="{fid}"] ' + s);
  const $$ = (s) => Array.from(document.querySelectorAll('[data-composition-id="{fid}"] ' + s));
  tl.fromTo($('#{p}-bloom'), {{ scale: 0.85, opacity: 0.6 }}, {{ scale: 1, opacity: 1, duration: {dur}, ease: "none" }}, 0);
{js}
  tl.set({{}}, {{}}, {dur});
  window.__timelines = window.__timelines || {{}};
  window.__timelines["{fid}"] = tl;
}})();
</script>
</template>
"""


def words(text: str, cls: str, extra_cls=None) -> str:
    """Wrap each word in a span (seek-safe per-word reveals). extra_cls: {word_index: class}."""
    extra_cls = extra_cls or {}
    return " ".join(f'<span class="{cls}{(" " + extra_cls[i]) if i in extra_cls else ""}">{w}</span>' for i, w in enumerate(text.split(" ")))


frames = {}

# ── 1. 11:40 pm ────────────────────────────────────────────────────────────────
F = "01-midnight-message"
msg = "AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. rate kya hai? advance kitni?"
frames[F] = (5, f"""
.{F}-clock{{left:180px;top:300px;font-size:250px;line-height:.9}}
.{F}-sub{{left:190px;top:250px}}
.{F}-note{{left:190px;top:560px;font-size:46px}}
.{F}-phone{{left:1180px;top:70px;width:560px;height:800px;border:3px solid {INK};border-radius:58px;background:#FFFDF8;overflow:hidden}}
.{F}-head{{height:118px;background:{INK};color:{PAPER};padding:46px 34px 0;display:flex;gap:18px;align-items:center}}
.{F}-avatar{{width:52px;height:52px;border-radius:50%;background:{SUN}}}
.{F}-name{{font-size:28px;font-weight:600}} .{F}-num{{font-size:20px;opacity:.75;font-family:"JetBrains Mono",monospace}}
.{F}-chat{{position:absolute;top:118px;left:0;right:0;bottom:0;background:#EFEAE2;padding:40px 30px}}
.{F}-bubble{{background:#fff;border-radius:6px 26px 26px 26px;padding:26px 30px;font-size:34px;line-height:1.38;color:#1D1B18;width:430px;box-shadow:0 1px 0 rgba(0,0,0,.08)}}
.{F}-w{{display:inline}}
.{F}-time{{font-family:"JetBrains Mono",monospace;font-size:18px;color:#7B766B;text-align:right;margin-top:10px}}
.{F}-badge{{left:1680px;top:52px;width:86px;height:86px;border-radius:50%;background:{EMBER};color:#fff;font:700 34px/86px "Inter";text-align:center}}
""", f"""
  <div class="{F}-abs {F}-kicker {F}-sub" id="{F}-sub">a hotel owner's phone, tonight</div>
  <div class="{F}-abs {F}-serif {F}-clock" id="{F}-clock">11:40 PM</div>
  <div class="{F}-abs {F}-hand {F}-note" id="{F}-note">a new booking. and 42 others.</div>
  <div class="{F}-abs {F}-phone" id="{F}-phone">
    <div class="{F}-head"><div class="{F}-avatar"></div><div><div class="{F}-name">Guest</div><div class="{F}-num">+92 3•• •••••••</div></div></div>
    <div class="{F}-chat"><div class="{F}-bubble" id="{F}-bubble">{words(msg, F + "-w")}<div class="{F}-time">11:40 PM</div></div></div>
  </div>
  <div class="{F}-abs {F}-badge" id="{F}-badge">1</div>
""", f"""
  tl.fromTo($('#{F}-clock'), {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.9, ease: "power3.out" }}, 0.05);
  tl.fromTo($('#{F}-sub'), {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.6 }}, 0.35);
  tl.fromTo($('#{F}-phone'), {{ y: 120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 1.0);
  tl.fromTo($('#{F}-bubble'), {{ scale: 0.9, opacity: 0, transformOrigin: "0% 0%" }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "power3.out" }}, 1.45);
  const ws = $$('.{F}-w');
  ws.forEach((w, i) => tl.fromTo(w, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.05 }}, 1.6 + i * (2.5 / ws.length)));
  tl.fromTo($('#{F}-badge'), {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, 1.1);
  const n = {{ v: 1 }};
  tl.to(n, {{ v: 43, duration: 0.8, ease: "power2.in", onUpdate: () => {{ $('#{F}-badge').textContent = Math.round(n.v); }} }}, 4.2);
  tl.fromTo($('#{F}-note'), {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, 4.2);
""", ("28%", "42%", "1000px"))

# ── 2. Nobody holds the clock ─────────────────────────────────────────────────
F = "02-nobody-holds-the-clock"
lines = ["Rate quoted from memory.", "Advance never chased.", "Room sits empty."]
frames[F] = (4, f"""
.{F}-line{{left:0;right:0;text-align:center;font-size:120px}}
.{F}-txt{{position:relative;display:inline-block}}
.{F}-strike{{position:absolute;left:-14px;right:-14px;top:56%;height:8px;background:{EMBER};border-radius:4px;transform-origin:0 50%}}
""", "\n".join(f'  <div class="{F}-abs {F}-serif {F}-line" id="{F}-l{i}" style="top:{200 + i * 190}px"><span class="{F}-txt">{t}<span class="{F}-strike" id="{F}-s{i}"></span></span></div>'
               for i, t in enumerate(lines)), "\n".join(f"""
  tl.fromTo($('#{F}-l{i}'), {{ y: 50, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power3.out" }}, {0.05 + i * 1.12});
  tl.fromTo($('#{F}-s{i}'), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power2.inOut" }}, {0.62 + i * 1.12});"""
  + (f"\n  tl.to($('#{F}-l{i}'), {{ opacity: 0.4, duration: 0.4 }}, {1.17 + i * 1.12});" if i < 2 else "")
  for i in range(3)), ("50%", "48%", "1100px"))

# ── 3. Munshi ─────────────────────────────────────────────────────────────────
F = "03-munshi"
frames[F] = (4, f"""
.{F}-swipe{{left:560px;top:418px;width:800px;height:150px;background:{SUN};border-radius:18px 60px 24px 50px;transform-origin:0 50%;transform:rotate(-2deg)}}
.{F}-word{{left:0;right:0;top:300px;text-align:center;font-size:300px;font-weight:700;line-height:1}}
.{F}-k{{left:0;right:0;top:250px;text-align:center}}
.{F}-tag{{left:0;right:0;top:660px;text-align:center;font-size:66px;font-style:italic}}
""", f"""
  <div class="{F}-abs {F}-swipe" id="{F}-swipe"></div>
  <div class="{F}-abs {F}-kicker {F}-k" id="{F}-k">a whatsapp front desk for small hotels</div>
  <div class="{F}-abs {F}-serif {F}-word" id="{F}-word">Munshi</div>
  <div class="{F}-abs {F}-serif {F}-tag" id="{F}-tag">the front desk that holds the clock.</div>
""", f"""
  tl.fromTo($('#{F}-swipe'), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.8, ease: "power3.inOut" }}, 0.0);
  tl.fromTo($('#{F}-word'), {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "power3.out" }}, 0.35);
  tl.fromTo($('#{F}-k'), {{ opacity: 0, y: 12 }}, {{ opacity: 0.8, y: 0, duration: 0.5 }}, 1.2);
  tl.fromTo($('#{F}-tag'), {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 1.5);
""", ("50%", "46%", "1300px"))

# ── 4. It reads Roman Urdu ────────────────────────────────────────────────────
F = "04-reads-roman-urdu"
tok = {1: "kal", 2: "2 log", 5: "1 room", 7: "2 raat"}  # display order of the flies below
msg4 = (f'AoA, <span class="{F}-T" id="{F}-T0">kal</span> <span class="{F}-T" id="{F}-T1">2 log</span> ke liye '
        f'<span class="{F}-T" id="{F}-T3">1 room</span> chahiye <span class="{F}-T" id="{F}-T2">2 raat</span> ke liye. rate kya hai? advance kitni?')
fields = [("check_in", '"2026-10-18"'), ("guests", "2"), ("nights", "2"), ("rooms", "1")]
frames[F] = (7, f"""
.{F}-h{{left:180px;top:110px;font-size:92px}}
.{F}-bubble{{left:180px;top:330px;width:720px;background:#fff;border-radius:6px 28px 28px 28px;padding:30px 36px;font-size:40px;line-height:1.5;color:#1D1B18;box-shadow:0 1px 0 rgba(0,0,0,.08)}}
.{F}-T{{border-radius:8px;padding:0 6px;margin:0 -6px}}
.{F}-card{{left:1040px;top:300px;width:700px;border:2px solid {INK};border-radius:18px;background:#FFFDF8;padding:34px 40px;font-size:36px;line-height:1.75}}
.{F}-key{{color:{INK}}} .{F}-val{{color:{EMBER};font-weight:700}}
.{F}-chip{{left:520px;top:450px;background:{SUN};color:#1D1B18;border-radius:10px;padding:4px 14px;font-size:34px;font-weight:700}}
.{F}-foot{{left:1040px;top:720px;font-size:24px;opacity:.85}}
.{F}-arrow{{left:930px;top:470px;font-size:64px;color:#B07E14}}
""", f"""
  <div class="{F}-abs {F}-serif {F}-h" id="{F}-h">A fine-tuned 4B reads it.</div>
  <div class="{F}-abs {F}-bubble" id="{F}-bubble">{msg4}</div>
  <div class="{F}-abs {F}-mono {F}-arrow" id="{F}-arrow">→</div>
  <div class="{F}-abs {F}-mono {F}-card" id="{F}-card">{{<br>""" + "<br>".join(
      f'&nbsp;&nbsp;<span class="{F}-key">"{k}"</span>: <span class="{F}-val" id="{F}-v{i}">{v}</span>{"," if i < 3 else ""}' for i, (k, v) in enumerate(fields))
  + f"""<br>}}</div>
""" + "\n".join(f'  <div class="{F}-abs {F}-chip" id="{F}-c{i}" data-layout-allow-overlap>{t}</div>' for i, t in enumerate(["kal", "2 log", "2 raat", "1 room"])) + f"""
  <div class="{F}-abs {F}-mono {F}-foot" id="{F}-foot">Qwen3.5-4B + LoRA on Tinker · dates resolved in code</div>
""", f"""
  tl.fromTo($('#{F}-h'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "power3.out" }}, 0.05);
  tl.fromTo($('#{F}-bubble'), {{ x: -40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 0.3);
  tl.fromTo($('#{F}-card'), {{ x: 40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 0.8);
  tl.fromTo($('#{F}-arrow'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 1.0);
  for (let i = 0; i < 4; i++) tl.set($('#{F}-v' + i), {{ opacity: 0 }}, 0);
  const targets = [[1240, 360], [1210, 425], [1210, 488], [1200, 551]];
  const starts = [[300, 340], [400, 340], [560, 400], [210, 400]];
  for (let i = 0; i < 4; i++) {{
    const t0 = 1.6 + i * 1.0;
    tl.fromTo($('#{F}-T' + i), {{ backgroundColor: "rgba(227,162,26,0)" }}, {{ backgroundColor: "rgba(227,162,26,.85)", duration: 0.25 }}, t0);
    tl.fromTo($('#{F}-c' + i), {{ x: starts[i][0] - 520, y: starts[i][1] - 450, opacity: 0, scale: 0.8 }},
      {{ x: starts[i][0] - 520, y: starts[i][1] - 450, opacity: 1, scale: 1, duration: 0.15 }}, t0 + 0.15);
    tl.to($('#{F}-c' + i), {{ x: targets[i][0] - 520, y: targets[i][1] - 450, duration: 0.55, ease: "power3.inOut" }}, t0 + 0.3);
    tl.to($('#{F}-c' + i), {{ opacity: 0, duration: 0.12 }}, t0 + 0.85);
    tl.fromTo($('#{F}-v' + i), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15 }}, t0 + 0.8);
  }}
  tl.fromTo($('#{F}-foot'), {{ opacity: 0, y: 10 }}, {{ opacity: 0.85, y: 0, duration: 0.5 }}, 5.4);
""", ("70%", "45%", "1100px"))

# ── 5. It prices the risk ─────────────────────────────────────────────────────
F = "05-prices-the-risk"
frames[F] = (7, f"""
.{F}-shot{{left:200px;top:90px;width:1520px;border:2px solid {INK};border-radius:20px;overflow:hidden;background:#fff;transform-origin:83% 52%}}
.{F}-shot img{{display:block;width:100%}}
.{F}-dim{{position:absolute;inset:0;background:{PAPER}}}
.{F}-pct{{left:220px;top:110px;font-size:330px;font-weight:700;line-height:1}}
.{F}-pl{{left:240px;top:470px;font-size:30px}}
.{F}-tiers{{left:960px;top:150px;display:flex;flex-direction:column;gap:26px}}
.{F}-tier{{width:700px;border:2px solid {INK};border-radius:16px;padding:22px 30px;font-size:34px;display:flex;justify-content:space-between;background:#FFFDF8}}
.{F}-tier.on{{background:{SUN};border-color:{SUN};color:#1D1B18}}
.{F}-res{{left:960px;top:640px;font-size:74px}}
.{F}-src{{left:240px;top:540px;font-size:22px;opacity:.75}}
""", f"""
  <div class="{F}-abs {F}-shot" id="{F}-shot" data-layout-allow-overflow><img src="assets/app-quote.jpg" alt=""></div>
  <div class="{F}-abs {F}-dim" id="{F}-dim"></div>
  <div class="{F}-abs {F}-serif {F}-pct" id="{F}-pct">0%</div>
  <div class="{F}-abs {F}-kicker {F}-pl" id="{F}-pl">cancel risk · TabPFN-3.5</div>
  <div class="{F}-abs {F}-mono {F}-src" id="{F}-src">from a 300-booking register</div>
  <div class="{F}-abs {F}-tiers" id="{F}-tiers">
    <div class="{F}-tier {F}-mono" id="{F}-t0"><span>low risk</span><span>20% · 12 h</span></div>
    <div class="{F}-tier {F}-mono" id="{F}-t1"><span>medium</span><span>30% · 6 h</span></div>
    <div class="{F}-tier {F}-mono" id="{F}-t2"><span>high risk</span><span>50% · 2 h</span></div>
  </div>
  <div class="{F}-abs {F}-serif {F}-res" id="{F}-res">Advance Rs 3,500 · hold 12 h</div>
""", f"""
  tl.fromTo($('#{F}-shot'), {{ opacity: 0, y: 30, scale: 1 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 0.0);
  tl.to($('#{F}-shot'), {{ scale: 1.55, duration: 1.6, ease: "power2.inOut" }}, 0.35);
  tl.fromTo($('#{F}-dim'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, 1.8);
  tl.fromTo($('#{F}-pct'), {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }}, 1.9);
  const p = {{ v: 0 }};
  tl.to(p, {{ v: 5, duration: 1.4, ease: "power2.out", onUpdate: () => {{ $('#{F}-pct').textContent = Math.round(p.v) + "%"; }} }}, 2.0);
  tl.fromTo($('#{F}-pl'), {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.5 }}, 2.4);
  tl.fromTo($('#{F}-src'), {{ opacity: 0 }}, {{ opacity: 0.75, duration: 0.5 }}, 2.8);
  for (let i = 0; i < 3; i++) tl.fromTo($('#{F}-t' + i), {{ x: 60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, 3.6 + i * 0.45);
  tl.call(() => {{}}, null, 5.2);
  tl.fromTo($('#{F}-t0'), {{ backgroundColor: "#FFFDF8", borderColor: "{INK}" }}, {{ backgroundColor: "{SUN}", borderColor: "{SUN}", duration: 0.3 }}, 5.2);
  tl.fromTo($('#{F}-res'), {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 5.45);
""", ("30%", "35%", "1000px"))

# ── 6. Gemma writes, code checks ──────────────────────────────────────────────
F = "06-gemma-writes-code-checks"
reply = ("Aapki 18 October ki booking ke liye 1 room available hai. 2 nights ka total NUM0 Rs banta hai. "
         "Booking confirm karne ke liye NUM1 Rs advance jama karwana hoga. Hum ye room sirf NUM2 ghanto ke liye hold kar sakte hain.")
nums = ["16,000", "3,500", "12"]
html_words = []
for w in reply.split(" "):
    if w.startswith("NUM"):
        i = int(w[3])
        html_words.append(f'<span class="{F}-w {F}-num" id="{F}-n{i}">{nums[i]}<span class="{F}-ul" id="{F}-u{i}"></span>'
                          f'<svg class="{F}-ck" id="{F}-k{i}" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="{SUN}"/>'
                          f'<path d="M6.5 12.5l3.6 3.6 7.4-8" fill="none" stroke="#1D1B18" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>')
    else:
        html_words.append(f'<span class="{F}-w">{w}</span>')
frames[F] = (5, f"""
.{F}-lab{{left:180px;top:130px;font-size:30px}}
.{F}-lab2{{left:180px;top:130px;font-size:30px;color:{EMBER}}}
.{F}-bubble{{left:240px;top:230px;width:1360px;background:#D9FDD3;border-radius:28px 6px 28px 28px;padding:44px 54px;font-size:52px;line-height:1.5;color:#1D1B18}}
.{F}-num{{position:relative;display:inline-block;font-weight:700;isolation:isolate}}
.{F}-ul{{position:absolute;left:-4px;right:-4px;bottom:4px;height:10px;background:{SUN};opacity:.85;transform-origin:0 50%;z-index:-1}}
.{F}-ck{{position:absolute;right:-26px;top:-20px;width:40px;height:40px}}
.{F}-who{{left:240px;top:820px;font-size:24px;opacity:.75}}
""", f"""
  <div class="{F}-abs {F}-kicker {F}-lab" id="{F}-lab">gemma 4 writes the reply</div>
  <div class="{F}-abs {F}-kicker {F}-lab2" id="{F}-lab2">code checks every number</div>
  <div class="{F}-abs {F}-bubble" id="{F}-bubble">{" ".join(html_words)}</div>
""", f"""
  tl.fromTo($('#{F}-lab'), {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.4 }}, 0.0);
  tl.fromTo($('#{F}-bubble'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, 0.05);
  const ws = $$('.{F}-w');
  ws.forEach((w, i) => tl.fromTo(w, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.04 }}, 0.2 + i * (2.3 / ws.length)));
  tl.to($('#{F}-lab'), {{ opacity: 0, duration: 0.15 }}, 2.55);
  tl.fromTo($('#{F}-lab2'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, 2.62);
  for (let i = 0; i < 3; i++) {{
    tl.fromTo($('#{F}-u' + i), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power2.out" }}, 2.8 + i * 0.5);
    tl.fromTo($('#{F}-k' + i), {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, 2.85 + i * 0.5);
  }}
""", ("50%", "40%", "1300px"))

# ── 7. The hold ───────────────────────────────────────────────────────────────
F = "07-the-hold"
frames[F] = (8, f"""
.{F}-h{{left:180px;top:100px;font-size:92px}}
.{F}-panel{{left:180px;top:250px;width:1000px}}
.{F}-clock{{font-size:190px;font-weight:700;letter-spacing:-.02em;line-height:1}}
.{F}-due{{font-size:32px;margin-top:22px}}
.{F}-bar{{margin-top:30px;width:900px;height:16px;border-radius:8px;background:rgba(13,92,82,.15);overflow:hidden}}
.{F}-fill{{height:100%;width:100%;background:{SUN};transform-origin:0 50%}}
.{F}-still{{font-size:30px;margin-top:18px;color:{EMBER}}}
.{F}-chip{{left:1240px;width:520px;border:2px solid {INK};border-radius:16px;background:#FFFDF8;padding:22px 28px;font-size:32px;display:flex;justify-content:space-between}}
.{F}-stamp{{left:1010px;top:570px;border:8px solid {SUN};color:{SUN};border-radius:18px;padding:6px 34px;font-size:104px;font-weight:700;letter-spacing:.04em;transform:rotate(-7deg)}}
.{F}-note{{left:1020px;top:780px;font-size:50px}}
""", f"""
  <div class="{F}-abs {F}-serif {F}-h" id="{F}-h">Temporal holds the room.</div>
  <div class="{F}-abs {F}-panel" id="{F}-panel">
    <div class="{F}-mono {F}-clock" id="{F}-clock">11:59:58</div>
    <div class="{F}-mono {F}-due">advance due Rs 3,500</div>
    <div class="{F}-bar"><div class="{F}-fill" id="{F}-fill"></div></div>
    <div class="{F}-mono {F}-still" id="{F}-still">still due Rs 1,500</div>
  </div>
  <div class="{F}-abs {F}-mono {F}-chip" id="{F}-c0" style="top:280px"><span>JC-48120</span><span>Rs 2,000</span></div>
  <div class="{F}-abs {F}-mono {F}-chip" id="{F}-c1" style="top:390px"><span>JC-48177</span><span>Rs 1,500</span></div>
  <div class="{F}-abs {F}-serif {F}-stamp" id="{F}-stamp">CONFIRMED</div>
  <div class="{F}-abs {F}-hand {F}-note" id="{F}-note">a short payment never confirms a room</div>
""", f"""
  tl.fromTo($('#{F}-h'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 0.0);
  tl.fromTo($('#{F}-panel'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 0.2);
  const c = {{ s: 0 }};
  const fmt = (s) => {{ const r = 43198 - Math.floor(s); const h = Math.floor(r / 3600), m = Math.floor((r % 3600) / 60), x = r % 60;
    return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(x).padStart(2, "0"); }};
  tl.to(c, {{ s: 8, duration: 8, ease: "none", onUpdate: () => {{ $('#{F}-clock').textContent = fmt(c.s); }} }}, 0);
  tl.fromTo($('#{F}-fill'), {{ scaleX: 0 }}, {{ scaleX: 0 }}, 0);
  tl.fromTo($('#{F}-still'), {{ opacity: 0 }}, {{ opacity: 0 }}, 0);
  tl.fromTo($('#{F}-c0'), {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, 2.0);
  tl.to($('#{F}-fill'), {{ scaleX: 0.571, duration: 0.6, ease: "power2.out" }}, 2.2);
  tl.to($('#{F}-still'), {{ opacity: 1, duration: 0.3 }}, 2.5);
  tl.fromTo($('#{F}-c1'), {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, 3.8);
  tl.to($('#{F}-fill'), {{ scaleX: 1, duration: 0.6, ease: "power2.out" }}, 4.0);
  tl.to($('#{F}-still'), {{ opacity: 0, duration: 0.2 }}, 4.3);
  tl.to([$('#{F}-c0'), $('#{F}-c1')], {{ y: -40, opacity: 0.35, duration: 0.5, ease: "power2.out" }}, 5.1);
  tl.fromTo($('#{F}-stamp'), {{ scale: 2.2, opacity: 0, rotation: -14 }}, {{ scale: 1, opacity: 1, rotation: -7, duration: 0.32, ease: "power4.in" }}, 5.3);
  tl.fromTo($('#{F}-note'), {{ opacity: 0, y: 12 }}, {{ opacity: 1, y: 0, duration: 0.5 }}, 6.0);
""", ("72%", "55%", "1000px"))

# ── 8. We killed the server ───────────────────────────────────────────────────
F = "08-we-killed-the-server"
frames[F] = (7, f"""
.{F}-h{{left:0;right:0;top:330px;text-align:center;font-size:130px}}
.{F}-dark{{position:absolute;inset:0;background:{DARK}}}
.{F}-kill{{left:0;right:0;top:470px;text-align:center;font-size:40px;color:#E06A55;letter-spacing:.08em}}
.{F}-card{{left:160px;top:250px;width:1600px;border:2px solid {INK};border-radius:16px;overflow:hidden;background:#111}}
.{F}-card img{{display:block;width:100%}}
.{F}-k2{{left:160px;top:180px}}
.{F}-head{{left:160px;top:96px;font-size:66px}}
.{F}-play{{left:0;top:236px;width:4px;height:320px;background:{SUN};box-shadow:0 0 0 2px rgba(227,162,26,.25)}}
.{F}-dot{{left:-11px;top:-14px;width:26px;height:26px;border-radius:50%;background:{SUN}}}
.{F}-dead{{left:640px;top:600px;font-size:48px}}
.{F}-c{{left:160px;font-size:36px;display:flex;gap:18px;align-items:center}}
.{F}-c i{{display:inline-block;width:16px;height:16px;border-radius:50%;background:{SUN}}}
""", f"""
  <div class="{F}-abs {F}-kicker {F}-k2" id="{F}-k2">temporal web ui · the real run</div>
  <div class="{F}-abs {F}-serif {F}-head" id="{F}-head">The timer survived.</div>
  <div class="{F}-abs {F}-card" id="{F}-card"><img src="assets/temporal-drill.png" alt=""></div>
  <div class="{F}-abs {F}-play" id="{F}-play"><div class="{F}-abs {F}-dot"></div></div>
  <div class="{F}-abs {F}-hand {F}-dead" id="{F}-dead">worker + server dead here. timer still running.</div>
  <div class="{F}-abs {F}-mono {F}-c" id="{F}-c0" style="top:700px"><i></i>timer fired 0.1 s after the server came back</div>
  <div class="{F}-abs {F}-mono {F}-c" id="{F}-c1" style="top:770px"><i></i>0 steps ran twice</div>
  <div class="{F}-abs {F}-dark" id="{F}-dark"></div>
  <div class="{F}-abs {F}-serif {F}-h" id="{F}-h">We killed the server mid-hold.</div>
  <div class="{F}-abs {F}-mono {F}-kill" id="{F}-kill">SIGKILL worker · SIGKILL temporal server</div>
""", f"""
  tl.fromTo($('#{F}-dark'), {{ opacity: 0 }}, {{ opacity: 0 }}, 0);
  tl.fromTo($('#{F}-h'), {{ y: 30, opacity: 0, color: "{INK}" }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 0.05);
  tl.fromTo($('#{F}-kill'), {{ opacity: 0 }}, {{ opacity: 0 }}, 0);
  // the kill: hard flicker to dark (deterministic steps), then the headline goes out with the lights
  [[1.35, 1], [1.42, 0.2], [1.5, 1], [1.56, 0.4], [1.62, 1]].forEach(([t, o]) => tl.set($('#{F}-dark'), {{ opacity: o }}, t));
  tl.set($('#{F}-h'), {{ color: "#F4EDE0" }}, 1.35);
  tl.to($('#{F}-h'), {{ opacity: 0, duration: 0.15 }}, 1.62);
  tl.set($('#{F}-kill'), {{ opacity: 1 }}, 1.62);
  tl.to($('#{F}-dark'), {{ opacity: 0, duration: 0.35, ease: "power2.out" }}, 2.0);
  tl.to($('#{F}-kill'), {{ opacity: 0, duration: 0.2 }}, 2.0);
  // the real timeline; the playhead runs along the orange room-hold bar (x 475..1400 of 1568 in the screenshot)
  tl.fromTo($('#{F}-k2'), {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.4 }}, 2.1);
  tl.fromTo($('#{F}-head'), {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, 2.1);
  tl.fromTo($('#{F}-card'), {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 2.15);
  const sx = 160 + 475 * 1600 / 1568, ex = 160 + 1400 * 1600 / 1568;
  tl.fromTo($('#{F}-play'), {{ x: sx, opacity: 0 }}, {{ x: sx, opacity: 1, duration: 0.2 }}, 2.7);
  tl.to($('#{F}-play'), {{ x: ex, duration: 2.3, ease: "power1.inOut" }}, 2.9);
  tl.fromTo($('#{F}-dead'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 3.4);
  tl.fromTo($('#{F}-c0'), {{ x: -30, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, 5.2);
  tl.fromTo($('#{F}-c1'), {{ x: -30, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "power3.out" }}, 5.7);
""", ("55%", "50%", "1400px"))

# ── 9. The receipts ───────────────────────────────────────────────────────────
F = "09-the-receipts"
M = lambda s: f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.5em;vertical-align:.22em">{s}</span>'
cards = [(f"0% {M('→')} 75% {M('→')} 95%", "untuned · fine-tuned · + code rules"),
         ("30 / 30", "fresh test, written after the rules froze"),
         (f"82% {M('→')} 81%", "TabPFN says · actually cancelled"),
         ("70 / 70", "Gemma replies passed the number check")]
frames[F] = (6, f"""
.{F}-k{{left:180px;top:96px}}
.{F}-card{{width:760px;height:310px;border:2px solid {INK};border-radius:22px;background:#FFFDF8;padding:34px 44px;display:flex;flex-direction:column;justify-content:space-between}}
.{F}-fig{{font-size:120px;font-weight:700;line-height:1}}
.{F}-cap{{font-size:28px;opacity:.85}}
""", f"""
  <div class="{F}-abs {F}-kicker {F}-k" id="{F}-k">measured, not claimed · all numbers in the repo</div>
""" + "\n".join(f'  <div class="{F}-abs {F}-card" id="{F}-c{i}" style="left:{180 + (i % 2) * 800}px;top:{170 + (i // 2) * 350}px">'
                f'<div class="{F}-serif {F}-fig">{fig}</div><div class="{F}-mono {F}-cap">{cap}</div></div>' for i, (fig, cap) in enumerate(cards)),
f"""
  tl.fromTo($('#{F}-k'), {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.5 }}, 0.0);
  for (let i = 0; i < 4; i++) tl.fromTo($('#{F}-c' + i), {{ y: 60, opacity: 0, scale: 0.96 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.55, ease: "power3.out" }}, 0.6 + i * 0.9);
""", ("50%", "50%", "1500px"))

# ── 10. Outro ─────────────────────────────────────────────────────────────────
F = "10-outro"
frames[F] = (4, f"""
.{F}-stack{{left:0;right:0;top:250px;text-align:center;transform-origin:50% 0%}}
.{F}-l{{font-size:110px;line-height:1.15}}
.{F}-sw{{position:relative;display:inline-block;isolation:isolate}}
.{F}-swipe{{position:absolute;left:-18px;right:-18px;top:18%;bottom:6%;background:{SUN};border-radius:14px 40px 16px 36px;transform-origin:0 50%;z-index:-1}}
.{F}-word{{left:0;right:0;top:590px;text-align:center;font-size:150px;font-weight:700}}
.{F}-url{{left:0;right:0;top:780px;text-align:center;font-size:34px}}
""", f"""
  <div class="{F}-abs {F}-stack" id="{F}-stack">
    <div class="{F}-serif {F}-l" id="{F}-l0">Models read.</div>
    <div class="{F}-serif {F}-l" id="{F}-l1">Code decides.</div>
    <div class="{F}-serif {F}-l" id="{F}-l2"><span class="{F}-sw"><span class="{F}-swipe" id="{F}-swipe"></span>Temporal keeps the promise.</span></div>
  </div>
  <div class="{F}-abs {F}-serif {F}-word" id="{F}-word">Munshi</div>
  <div class="{F}-abs {F}-mono {F}-url" id="{F}-url">github.com/ArqamWaheed/munshi</div>
""", f"""
  for (let i = 0; i < 3; i++) tl.fromTo($('#{F}-l' + i), {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power3.out" }}, 0.05 + i * 0.55);
  tl.fromTo($('#{F}-swipe'), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.45, ease: "power3.inOut" }}, 1.25);
  tl.to($('#{F}-stack'), {{ scale: 0.62, y: -120, duration: 0.6, ease: "power3.inOut" }}, 1.8);
  tl.fromTo($('#{F}-word'), {{ y: 40, opacity: 0 }}, {{ y: -60, opacity: 1, duration: 0.6, ease: "power3.out" }}, 1.95);
  tl.fromTo($('#{F}-url'), {{ opacity: 0 }}, {{ opacity: 1, y: -60, duration: 0.5 }}, 2.35);
""", ("50%", "48%", "1500px"))

OUT.mkdir(parents=True, exist_ok=True)
for fid, (dur, css, body, js, *rest) in frames.items():
    bloom = rest[0] if rest else ("62%", "48%", "980px")
    # ids/classes may not start with a digit in CSS: prefix "f" to every "<fid>-..." token; the bare
    # composition id (followed by a quote) stays as is.
    html = frame(fid, dur, css, body, js, bloom).replace(fid + "-", "f" + fid + "-")
    (OUT / f"{fid}.html").write_text(html, encoding="utf-8")
    print("wrote", fid)
