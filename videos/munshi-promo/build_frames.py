"""Generates compositions/frames/NN-*.html (one <template> each) for the Munshi promo.

Brand kit from frame.md (and ../../DESIGN.md): the reception at 11:40 pm. Night ground #11162A,
chalk type #EDEFF3, one key-tag red #C4302F for whatever code decided (signal red #F06A5F when red
is text on night). Big Shoulders Display for display, Schibsted Grotesk for text, JetBrains Mono for
data only. Fonts are local files in assets/fonts (Latin subsets: arrows go in JetBrains Mono, which has U+2192).
Every number on screen comes from munshi/results (see STORYBOARD.md).
Run: python build_frames.py
"""
from pathlib import Path

OUT = Path(__file__).parent / "compositions" / "frames"
NIGHT, NIGHT2, LINE = "#11162A", "#1B2240", "#2E3760"
CHALK, MUTED = "#EDEFF3", "#9AA2C2"
RED, SIGNAL = "#C4302F", "#F06A5F"

FONTS = """
@font-face{font-family:"Big Shoulders Display";src:url(assets/fonts/big-shoulders-display-latin-600-normal.woff2) format("woff2");font-weight:600}
@font-face{font-family:"Big Shoulders Display";src:url(assets/fonts/big-shoulders-display-latin-800-normal.woff2) format("woff2");font-weight:800}
@font-face{font-family:"Schibsted Grotesk";src:url(assets/fonts/schibsted-grotesk-latin-400-normal.woff2) format("woff2");font-weight:400}
@font-face{font-family:"Schibsted Grotesk";src:url(assets/fonts/schibsted-grotesk-latin-400-italic.woff2) format("woff2");font-weight:400;font-style:italic}
@font-face{font-family:"Schibsted Grotesk";src:url(assets/fonts/schibsted-grotesk-latin-600-normal.woff2) format("woff2");font-weight:600}
@font-face{font-family:"Schibsted Grotesk";src:url(assets/fonts/schibsted-grotesk-latin-700-normal.woff2) format("woff2");font-weight:700}
@font-face{font-family:"JetBrains Mono";src:url(assets/fonts/JetBrainsMono-400.woff2) format("woff2");font-weight:400}
@font-face{font-family:"JetBrains Mono";src:url(assets/fonts/JetBrainsMono-700.woff2) format("woff2");font-weight:700}
"""


def frame(fid: str, dur: float, css: str, body: str, js: str) -> str:
    p = fid  # prefix for ids/classes
    return f"""<template>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
{FONTS}
#root{{position:absolute;inset:0;overflow:hidden;font-family:"Schibsted Grotesk",sans-serif;color:{CHALK}}}
.{p}-bg{{position:absolute;inset:0;background:{NIGHT}}}
.{p}-abs{{position:absolute}}
.{p}-disp{{font-family:"Big Shoulders Display",sans-serif;font-weight:800;letter-spacing:-.005em;line-height:1}}
.{p}-mono{{font-family:"JetBrains Mono",monospace}}
.{p}-note{{font-style:italic;font-weight:400;color:{SIGNAL}}}
.{p}-cap{{font-size:30px;font-weight:600;color:{MUTED}}}
{css}
</style>
<div id="root" data-composition-id="{fid}" data-width="1920" data-height="1080">
  <div class="clip {p}-bg" id="{p}-bg" data-start="0" data-duration="{dur}" data-track-index="0"></div>
{body}
</div>
<script>
(function(){{
  const tl = gsap.timeline({{ paused: true }});
  const $ = (s) => document.querySelector('[data-composition-id="{fid}"] ' + s);
  const $$ = (s) => Array.from(document.querySelectorAll('[data-composition-id="{fid}"] ' + s));
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
.{F}-clock{{left:180px;top:250px;font-size:280px;line-height:.9}}
.{F}-sub{{left:186px;top:520px}}
.{F}-msgnote{{left:186px;top:590px;font-size:48px}}
.{F}-phone{{left:1180px;top:70px;width:560px;height:800px;border:2px solid {LINE};border-radius:58px;background:#0A0E1C;overflow:hidden}}
.{F}-head{{height:118px;background:{NIGHT2};padding:46px 34px 0;display:flex;gap:18px;align-items:center}}
.{F}-avatar{{width:52px;height:52px;border-radius:50%;background:{RED}}}
.{F}-name{{font-size:28px;font-weight:600}} .{F}-num{{font-size:20px;color:{MUTED};font-family:"JetBrains Mono",monospace}}
.{F}-chat{{position:absolute;top:118px;left:0;right:0;bottom:0;padding:40px 30px}}
.{F}-bubble{{background:{NIGHT2};border-radius:6px 26px 26px 26px;padding:26px 30px;font-size:34px;line-height:1.38;color:{CHALK};width:430px}}
.{F}-w{{display:inline}}
.{F}-time{{font-family:"JetBrains Mono",monospace;font-size:18px;color:{MUTED};text-align:right;margin-top:10px}}
.{F}-badge{{left:1680px;top:52px;width:86px;height:86px;border-radius:50%;background:{RED};color:{CHALK};font:700 34px/86px "Schibsted Grotesk";text-align:center}}
""", f"""
  <div class="{F}-abs {F}-disp {F}-clock" id="{F}-clock">11:40 PM</div>
  <div class="{F}-abs {F}-cap {F}-sub" id="{F}-sub">A hotel owner's phone, tonight.</div>
  <div class="{F}-abs {F}-note {F}-msgnote" id="{F}-msgnote">A new booking. And 42 others.</div>
  <div class="{F}-abs {F}-phone" id="{F}-phone">
    <div class="{F}-head"><div class="{F}-avatar"></div><div><div class="{F}-name">Guest</div><div class="{F}-num">+92 3•• •••••••</div></div></div>
    <div class="{F}-chat"><div class="{F}-bubble" id="{F}-bubble">{words(msg, F + "-w")}<div class="{F}-time">11:40 PM</div></div></div>
  </div>
  <div class="{F}-abs {F}-badge" id="{F}-badge">1</div>
""", f"""
  tl.fromTo($('#{F}-clock'), {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.9, ease: "expo.out" }}, 0.05);
  tl.fromTo($('#{F}-sub'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6 }}, 0.35);
  tl.fromTo($('#{F}-phone'), {{ y: 120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 1.0);
  tl.fromTo($('#{F}-bubble'), {{ scale: 0.9, opacity: 0, transformOrigin: "0% 0%" }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, 1.45);
  const ws = $$('.{F}-w');
  ws.forEach((w, i) => tl.fromTo(w, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.05 }}, 1.6 + i * (2.5 / ws.length)));
  tl.fromTo($('#{F}-badge'), {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, 1.1);
  const n = {{ v: 1 }};
  tl.to(n, {{ v: 43, duration: 0.8, ease: "power2.in", onUpdate: () => {{ $('#{F}-badge').textContent = Math.round(n.v); }} }}, 4.2);
  tl.fromTo($('#{F}-msgnote'), {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "expo.out" }}, 4.2);
""")

# ── 2. Nobody holds the clock ─────────────────────────────────────────────────
F = "02-nobody-holds-the-clock"
lines = ["Rate quoted from memory.", "Advance never chased.", "Room sits empty."]
frames[F] = (4, f"""
.{F}-line{{left:0;right:0;text-align:center;font-size:150px}}
.{F}-txt{{position:relative;display:inline-block}}
.{F}-strike{{position:absolute;left:-18px;right:-18px;top:50%;height:12px;background:{RED};transform-origin:0 50%}}
""", "\n".join(f'  <div class="{F}-abs {F}-disp {F}-line" id="{F}-l{i}" style="top:{180 + i * 210}px"><span class="{F}-txt">{t}<span class="{F}-strike" id="{F}-s{i}"></span></span></div>'
               for i, t in enumerate(lines)), "\n".join(f"""
  tl.fromTo($('#{F}-l{i}'), {{ y: 50, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "expo.out" }}, {0.05 + i * 1.12});
  tl.fromTo($('#{F}-s{i}'), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power2.inOut" }}, {0.62 + i * 1.12});"""
  + (f"\n  tl.to($('#{F}-l{i}'), {{ opacity: 0.35, duration: 0.4 }}, {1.17 + i * 1.12});" if i < 2 else "")
  for i in range(3)))

# ── 3. Munshi ─────────────────────────────────────────────────────────────────
F = "03-munshi"
frames[F] = (4, f"""
.{F}-field{{left:0;top:0;width:1920px;height:1080px;background:{RED};transform-origin:0 50%}}
.{F}-word{{left:0;right:0;top:250px;text-align:center;font-size:380px;line-height:1}}
.{F}-tag{{left:0;right:0;top:660px;text-align:center;font-size:64px;font-weight:600}}
.{F}-k{{left:0;right:0;top:770px;text-align:center;font-size:32px;font-weight:400}}
""", f"""
  <div class="{F}-abs {F}-field" id="{F}-field"></div>
  <div class="{F}-abs {F}-disp {F}-word" id="{F}-word">Munshi</div>
  <div class="{F}-abs {F}-tag" id="{F}-tag">The front desk that holds the clock.</div>
  <div class="{F}-abs {F}-k" id="{F}-k">A WhatsApp front desk for small hotels</div>
""", f"""
  tl.fromTo($('#{F}-field'), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.8, ease: "expo.inOut" }}, 0.0);
  tl.fromTo($('#{F}-word'), {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "expo.out" }}, 0.35);
  tl.fromTo($('#{F}-tag'), {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }}, 1.2);
  tl.fromTo($('#{F}-k'), {{ opacity: 0, y: 12 }}, {{ opacity: 0.9, y: 0, duration: 0.5 }}, 1.5);
""")

# ── 4. It reads Roman Urdu ────────────────────────────────────────────────────
F = "04-reads-roman-urdu"
msg4 = (f'AoA, <span class="{F}-T" id="{F}-T0">kal</span> <span class="{F}-T" id="{F}-T1">2 log</span> ke liye '
        f'<span class="{F}-T" id="{F}-T3">1 room</span> chahiye <span class="{F}-T" id="{F}-T2">2 raat</span> ke liye. rate kya hai? advance kitni?')
fields = [("check_in", '"2026-10-18"'), ("guests", "2"), ("nights", "2"), ("rooms", "1")]
frames[F] = (7, f"""
.{F}-h{{left:180px;top:100px;font-size:120px}}
.{F}-bubble{{left:180px;top:330px;width:720px;background:{NIGHT2};border-radius:6px 28px 28px 28px;padding:30px 36px;font-size:40px;line-height:1.5;color:{CHALK}}}
.{F}-T{{border-radius:6px;padding:0 6px;margin:0 -6px}}
.{F}-card{{left:1040px;top:300px;width:700px;border:2px solid {LINE};border-radius:12px;background:#0A0E1C;padding:34px 40px;font-size:36px;line-height:1.75}}
.{F}-key{{color:{MUTED}}} .{F}-val{{color:{CHALK};font-weight:700}}
.{F}-chip{{left:520px;top:450px;background:{RED};color:{CHALK};border-radius:6px;padding:4px 14px;font-size:34px;font-weight:700}}
.{F}-foot{{left:1040px;top:780px;font-size:24px;color:{MUTED}}}
.{F}-arrow{{left:930px;top:470px;font-size:64px;color:{SIGNAL}}}
""", f"""
  <div class="{F}-abs {F}-disp {F}-h" id="{F}-h">A fine-tuned 4B reads it.</div>
  <div class="{F}-abs {F}-bubble" id="{F}-bubble">{msg4}</div>
  <div class="{F}-abs {F}-mono {F}-arrow" id="{F}-arrow">→</div>
  <div class="{F}-abs {F}-mono {F}-card" id="{F}-card">{{<br>""" + "<br>".join(
      f'&nbsp;&nbsp;<span class="{F}-key">"{k}"</span>: <span class="{F}-val" id="{F}-v{i}">{v}</span>{"," if i < 3 else ""}' for i, (k, v) in enumerate(fields))
  + f"""<br>}}</div>
""" + "\n".join(f'  <div class="{F}-abs {F}-chip" id="{F}-c{i}" data-layout-allow-overlap>{t}</div>' for i, t in enumerate(["kal", "2 log", "2 raat", "1 room"])) + f"""
  <div class="{F}-abs {F}-mono {F}-foot" id="{F}-foot">Qwen3.5-4B + LoRA on Tinker. Dates resolved in code.</div>
""", f"""
  tl.fromTo($('#{F}-h'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "expo.out" }}, 0.05);
  tl.fromTo($('#{F}-bubble'), {{ x: -40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.3);
  tl.fromTo($('#{F}-card'), {{ x: 40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.8);
  tl.fromTo($('#{F}-arrow'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 1.0);
  for (let i = 0; i < 4; i++) tl.set($('#{F}-v' + i), {{ opacity: 0 }}, 0);
  const targets = [[1240, 360], [1210, 425], [1210, 488], [1200, 551]];
  const starts = [[300, 340], [400, 340], [560, 400], [210, 400]];
  for (let i = 0; i < 4; i++) {{
    const t0 = 1.6 + i * 1.0;
    tl.fromTo($('#{F}-T' + i), {{ backgroundColor: "rgba(196,48,47,0)" }}, {{ backgroundColor: "rgba(196,48,47,.9)", duration: 0.25 }}, t0);
    tl.fromTo($('#{F}-c' + i), {{ x: starts[i][0] - 520, y: starts[i][1] - 450, opacity: 0, scale: 0.8 }},
      {{ x: starts[i][0] - 520, y: starts[i][1] - 450, opacity: 1, scale: 1, duration: 0.15 }}, t0 + 0.15);
    tl.to($('#{F}-c' + i), {{ x: targets[i][0] - 520, y: targets[i][1] - 450, duration: 0.55, ease: "expo.inOut" }}, t0 + 0.3);
    tl.to($('#{F}-c' + i), {{ opacity: 0, duration: 0.12 }}, t0 + 0.85);
    tl.fromTo($('#{F}-v' + i), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15 }}, t0 + 0.8);
  }}
  tl.fromTo($('#{F}-foot'), {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.5 }}, 5.4);
""")

# ── 5. It prices the risk ─────────────────────────────────────────────────────
F = "05-prices-the-risk"
frames[F] = (7, f"""
.{F}-shot{{left:200px;top:90px;width:1520px;border:2px solid {LINE};border-radius:12px;overflow:hidden;background:#fff;transform-origin:83% 52%}}
.{F}-shot img{{display:block;width:100%}}
.{F}-dim{{position:absolute;inset:0;background:{NIGHT}}}
.{F}-pct{{left:220px;top:110px;font-size:400px;line-height:.9}}
.{F}-pl{{left:236px;top:500px}}
.{F}-tiers{{left:960px;top:150px;display:flex;flex-direction:column;gap:26px}}
.{F}-tier{{width:700px;border:2px solid {LINE};border-radius:12px;padding:22px 30px;font-size:34px;display:flex;justify-content:space-between;background:{NIGHT2};color:{CHALK}}}
.{F}-res{{left:960px;top:640px;font-size:84px;white-space:nowrap}}
.{F}-src{{left:236px;top:560px;font-size:22px;color:{MUTED}}}
""", f"""
  <div class="{F}-abs {F}-shot" id="{F}-shot" data-layout-allow-overflow><img src="assets/app-quote.jpg" alt=""></div>
  <div class="{F}-abs {F}-dim" id="{F}-dim"></div>
  <div class="{F}-abs {F}-disp {F}-pct" id="{F}-pct">0%</div>
  <div class="{F}-abs {F}-cap {F}-pl" id="{F}-pl">Cancel risk, TabPFN-3.5</div>
  <div class="{F}-abs {F}-mono {F}-src" id="{F}-src">from a 300-booking register</div>
  <div class="{F}-abs {F}-tiers" id="{F}-tiers">
    <div class="{F}-tier {F}-mono" id="{F}-t0"><span>low risk</span><span>20% · 12 h</span></div>
    <div class="{F}-tier {F}-mono" id="{F}-t1"><span>medium</span><span>30% · 6 h</span></div>
    <div class="{F}-tier {F}-mono" id="{F}-t2"><span>high risk</span><span>50% · 2 h</span></div>
  </div>
  <div class="{F}-abs {F}-disp {F}-res" id="{F}-res">Advance Rs 3,500. Hold 12 h.</div>
""", f"""
  tl.fromTo($('#{F}-shot'), {{ opacity: 0, y: 30, scale: 1 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }}, 0.0);
  tl.to($('#{F}-shot'), {{ scale: 1.55, duration: 1.6, ease: "power2.inOut" }}, 0.35);
  tl.fromTo($('#{F}-dim'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, 1.8);
  tl.fromTo($('#{F}-pct'), {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "expo.out" }}, 1.9);
  const p = {{ v: 0 }};
  tl.to(p, {{ v: 5, duration: 1.4, ease: "power2.out", onUpdate: () => {{ $('#{F}-pct').textContent = Math.round(p.v) + "%"; }} }}, 2.0);
  tl.fromTo($('#{F}-pl'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, 2.4);
  tl.fromTo($('#{F}-src'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, 2.8);
  for (let i = 0; i < 3; i++) tl.fromTo($('#{F}-t' + i), {{ x: 60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, 3.6 + i * 0.45);
  tl.fromTo($('#{F}-t0'), {{ backgroundColor: "{NIGHT2}", borderColor: "{LINE}" }}, {{ backgroundColor: "{RED}", borderColor: "{RED}", duration: 0.3 }}, 5.2);
  tl.fromTo($('#{F}-res'), {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }}, 5.45);
""")

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
                          f'<svg class="{F}-ck" id="{F}-k{i}" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="{RED}"/>'
                          f'<path d="M6.5 12.5l3.6 3.6 7.4-8" fill="none" stroke="{CHALK}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>')
    else:
        html_words.append(f'<span class="{F}-w">{w}</span>')
frames[F] = (5, f"""
.{F}-lab{{left:240px;top:90px;font-size:96px}}
.{F}-lab2{{left:240px;top:90px;font-size:96px;color:{SIGNAL}}}
.{F}-bubble{{left:240px;top:250px;width:1360px;background:{CHALK};border-radius:28px 6px 28px 28px;padding:44px 54px;font-size:52px;line-height:1.5;color:{NIGHT}}}
.{F}-num{{position:relative;display:inline-block;font-weight:700;isolation:isolate}}
.{F}-ul{{position:absolute;left:-4px;right:-4px;bottom:4px;height:10px;background:{RED};opacity:.85;transform-origin:0 50%;z-index:-1}}
.{F}-ck{{position:absolute;right:-12px;top:-30px;width:30px;height:30px}}
""", f"""
  <div class="{F}-abs {F}-disp {F}-lab" id="{F}-lab">Gemma 4 writes the reply.</div>
  <div class="{F}-abs {F}-disp {F}-lab2" id="{F}-lab2">Code checks every number.</div>
  <div class="{F}-abs {F}-bubble" id="{F}-bubble">{" ".join(html_words)}</div>
""", f"""
  tl.fromTo($('#{F}-lab'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 0.0);
  tl.fromTo($('#{F}-bubble'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, 0.05);
  const ws = $$('.{F}-w');
  ws.forEach((w, i) => tl.fromTo(w, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.04 }}, 0.2 + i * (2.3 / ws.length)));
  tl.to($('#{F}-lab'), {{ opacity: 0, duration: 0.15 }}, 2.55);
  tl.fromTo($('#{F}-lab2'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, 2.62);
  for (let i = 0; i < 3; i++) {{
    tl.fromTo($('#{F}-u' + i), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power2.out" }}, 2.8 + i * 0.5);
    tl.fromTo($('#{F}-k' + i), {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, 2.85 + i * 0.5);
  }}
""")

# ── 7. The hold ───────────────────────────────────────────────────────────────
F = "07-the-hold"
frames[F] = (8, f"""
.{F}-h{{left:180px;top:90px;font-size:120px}}
.{F}-panel{{left:180px;top:260px;width:1000px}}
.{F}-clock{{font-size:190px;font-weight:700;letter-spacing:-.02em;line-height:1}}
.{F}-due{{font-size:32px;margin-top:22px;color:{MUTED}}}
.{F}-bar{{margin-top:30px;width:900px;height:16px;background:{LINE};overflow:hidden}}
.{F}-fill{{height:100%;width:100%;background:{RED};transform-origin:0 50%}}
.{F}-still{{font-size:30px;margin-top:18px;color:{SIGNAL}}}
.{F}-chip{{left:1240px;width:520px;border:2px solid {LINE};border-radius:12px;background:{NIGHT2};padding:22px 28px;font-size:32px;display:flex;justify-content:space-between}}
.{F}-stamp{{left:1010px;top:570px;background:{RED};color:{CHALK};padding:14px 44px 6px;font-size:132px;letter-spacing:.03em;transform:rotate(-7deg)}}
.{F}-msgnote{{left:1020px;top:800px;font-size:48px}}
""", f"""
  <div class="{F}-abs {F}-disp {F}-h" id="{F}-h">Temporal holds the room.</div>
  <div class="{F}-abs {F}-panel" id="{F}-panel">
    <div class="{F}-mono {F}-clock" id="{F}-clock">11:59:58</div>
    <div class="{F}-mono {F}-due">advance due Rs 3,500</div>
    <div class="{F}-bar"><div class="{F}-fill" id="{F}-fill"></div></div>
    <div class="{F}-mono {F}-still" id="{F}-still">still due Rs 1,500</div>
  </div>
  <div class="{F}-abs {F}-mono {F}-chip" id="{F}-c0" style="top:280px"><span>JC-48120</span><span>Rs 2,000</span></div>
  <div class="{F}-abs {F}-mono {F}-chip" id="{F}-c1" style="top:390px"><span>JC-48177</span><span>Rs 1,500</span></div>
  <div class="{F}-abs {F}-disp {F}-stamp" id="{F}-stamp">CONFIRMED</div>
  <div class="{F}-abs {F}-note {F}-msgnote" id="{F}-msgnote">A short payment never confirms a room.</div>
""", f"""
  tl.fromTo($('#{F}-h'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.0);
  tl.fromTo($('#{F}-panel'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.2);
  const c = {{ s: 0 }};
  const fmt = (s) => {{ const r = 43198 - Math.floor(s); const h = Math.floor(r / 3600), m = Math.floor((r % 3600) / 60), x = r % 60;
    return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(x).padStart(2, "0"); }};
  tl.to(c, {{ s: 8, duration: 8, ease: "none", onUpdate: () => {{ $('#{F}-clock').textContent = fmt(c.s); }} }}, 0);
  tl.fromTo($('#{F}-fill'), {{ scaleX: 0 }}, {{ scaleX: 0 }}, 0);
  tl.fromTo($('#{F}-still'), {{ opacity: 0 }}, {{ opacity: 0 }}, 0);
  tl.fromTo($('#{F}-c0'), {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, 2.0);
  tl.to($('#{F}-fill'), {{ scaleX: 0.571, duration: 0.6, ease: "power2.out" }}, 2.2);
  tl.to($('#{F}-still'), {{ opacity: 1, duration: 0.3 }}, 2.5);
  tl.fromTo($('#{F}-c1'), {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, 3.8);
  tl.to($('#{F}-fill'), {{ scaleX: 1, duration: 0.6, ease: "power2.out" }}, 4.0);
  tl.to($('#{F}-still'), {{ opacity: 0, duration: 0.2 }}, 4.3);
  tl.to([$('#{F}-c0'), $('#{F}-c1')], {{ y: -40, opacity: 0.35, duration: 0.5, ease: "power2.out" }}, 5.1);
  tl.fromTo($('#{F}-stamp'), {{ scale: 2.2, opacity: 0, rotation: -14 }}, {{ scale: 1, opacity: 1, rotation: -7, duration: 0.32, ease: "power4.in" }}, 5.3);
  tl.fromTo($('#{F}-msgnote'), {{ opacity: 0, y: 12 }}, {{ opacity: 1, y: 0, duration: 0.5 }}, 6.0);
""")

# ── 8. We killed the server ───────────────────────────────────────────────────
F = "08-we-killed-the-server"
frames[F] = (7, f"""
.{F}-h{{left:0;right:0;top:330px;text-align:center;font-size:160px}}
.{F}-alarm{{position:absolute;inset:0;background:{RED}}}
.{F}-kill{{left:0;right:0;top:520px;text-align:center;font-size:40px;letter-spacing:.06em}}
.{F}-card{{left:160px;top:250px;width:1600px;border:2px solid {LINE};border-radius:12px;overflow:hidden;background:{NIGHT2}}}
.{F}-card img{{display:block;width:100%}}
.{F}-k2{{left:160px;top:184px}}
.{F}-head{{left:160px;top:80px;font-size:100px}}
.{F}-play{{left:0;top:236px;width:4px;height:320px;background:{RED}}}
.{F}-dot{{left:-11px;top:-14px;width:26px;height:26px;border-radius:50%;background:{RED}}}
.{F}-dead{{left:640px;top:600px;font-size:48px}}
.{F}-c{{left:160px;font-size:36px;display:flex;gap:22px;align-items:center}}
.{F}-c i{{display:inline-block;width:22px;height:6px;background:{RED}}}
""", f"""
  <div class="{F}-abs {F}-disp {F}-head" id="{F}-head">The timer survived.</div>
  <div class="{F}-abs {F}-cap {F}-k2" id="{F}-k2">Temporal Web UI, from the real run</div>
  <div class="{F}-abs {F}-card" id="{F}-card"><img src="assets/temporal-drill.png" alt=""></div>
  <div class="{F}-abs {F}-play" id="{F}-play"><div class="{F}-abs {F}-dot"></div></div>
  <div class="{F}-abs {F}-note {F}-dead" id="{F}-dead">Worker and server dead here. Timer still running.</div>
  <div class="{F}-abs {F}-mono {F}-c" id="{F}-c0" style="top:700px"><i></i>timer fired 0.1 s after the server came back</div>
  <div class="{F}-abs {F}-mono {F}-c" id="{F}-c1" style="top:770px"><i></i>0 steps ran twice</div>
  <div class="{F}-abs {F}-alarm" id="{F}-alarm"></div>
  <div class="{F}-abs {F}-disp {F}-h" id="{F}-h">We killed the server mid-hold.</div>
  <div class="{F}-abs {F}-mono {F}-kill" id="{F}-kill">SIGKILL worker. SIGKILL temporal server.</div>
""", f"""
  tl.fromTo($('#{F}-alarm'), {{ opacity: 0 }}, {{ opacity: 0 }}, 0);
  tl.fromTo($('#{F}-h'), {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.05);
  tl.fromTo($('#{F}-kill'), {{ opacity: 0 }}, {{ opacity: 0 }}, 0);
  // the kill: hard flicker to the alarm red (deterministic steps), then the headline goes out with the lights
  [[1.35, 1], [1.42, 0.2], [1.5, 1], [1.56, 0.4], [1.62, 1]].forEach(([t, o]) => tl.set($('#{F}-alarm'), {{ opacity: o }}, t));
  tl.to($('#{F}-h'), {{ opacity: 0, duration: 0.15 }}, 1.62);
  tl.set($('#{F}-kill'), {{ opacity: 1 }}, 1.62);
  tl.to($('#{F}-alarm'), {{ opacity: 0, duration: 0.35, ease: "power2.out" }}, 2.0);
  tl.to($('#{F}-kill'), {{ opacity: 0, duration: 0.2 }}, 2.0);
  // the real timeline; the playhead runs along the orange room-hold bar (x 475..1400 of 1568 in the screenshot)
  tl.fromTo($('#{F}-head'), {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }}, 2.1);
  tl.fromTo($('#{F}-k2'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 2.3);
  tl.fromTo($('#{F}-card'), {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "expo.out" }}, 2.15);
  const sx = 160 + 475 * 1600 / 1568, ex = 160 + 1400 * 1600 / 1568;
  tl.fromTo($('#{F}-play'), {{ x: sx, opacity: 0 }}, {{ x: sx, opacity: 1, duration: 0.2 }}, 2.7);
  tl.to($('#{F}-play'), {{ x: ex, duration: 2.3, ease: "power1.inOut" }}, 2.9);
  tl.fromTo($('#{F}-dead'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, 3.4);
  tl.fromTo($('#{F}-c0'), {{ x: -30, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, 5.2);
  tl.fromTo($('#{F}-c1'), {{ x: -30, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, 5.7);
""")

# ── 9. The receipts ───────────────────────────────────────────────────────────
F = "09-the-receipts"
M = lambda s: f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.45em;vertical-align:.3em">{s}</span>'
cards = [(f"0% {M('→')} 75% {M('→')} 95%", "untuned, fine-tuned, + code rules"),
         ("30 / 30", "fresh test, written after the rules froze"),
         (f"82% {M('→')} 81%", "TabPFN said, actually cancelled"),
         ("70 / 70", "Gemma replies passed the number check")]
frames[F] = (6, f"""
.{F}-h{{left:180px;top:70px;font-size:100px}}
.{F}-k{{left:180px;top:930px}}
.{F}-card{{width:760px;height:300px;border:2px solid {LINE};border-radius:12px;background:{NIGHT2};padding:34px 44px;display:flex;flex-direction:column;justify-content:space-between}}
.{F}-card.on{{background:{RED};border-color:{RED}}}
.{F}-fig{{font-size:124px;white-space:nowrap}}
.{F}-cap{{font-size:24px;color:{MUTED}}}
.{F}-card.on .{F}-cap{{color:{CHALK}}}
""", f"""
  <div class="{F}-abs {F}-disp {F}-h" id="{F}-h">Measured, not claimed.</div>
  <div class="{F}-abs {F}-cap {F}-k" id="{F}-k">Every number here is in the repo.</div>
""" + "\n".join(f'  <div class="{F}-abs {F}-card{" on" if i == 1 else ""}" id="{F}-c{i}" style="left:{180 + (i % 2) * 800}px;top:{200 + (i // 2) * 340}px">'
                f'<div class="{F}-disp {F}-fig">{fig}</div><div class="{F}-mono {F}-cap">{cap}</div></div>' for i, (fig, cap) in enumerate(cards)),
f"""
  tl.fromTo($('#{F}-h'), {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }}, 0.0);
  for (let i = 0; i < 4; i++) tl.fromTo($('#{F}-c' + i), {{ y: 60, opacity: 0, scale: 0.96 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.55, ease: "expo.out" }}, 0.6 + i * 0.9);
  tl.fromTo($('#{F}-k'), {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, 4.3);
""")

# ── 10. Outro ─────────────────────────────────────────────────────────────────
F = "10-outro"
frames[F] = (4, f"""
.{F}-stack{{left:0;right:0;top:230px;text-align:center;transform-origin:50% 0%}}
.{F}-l{{font-size:140px;line-height:1.1}}
.{F}-sw{{position:relative;display:inline-block;isolation:isolate;padding:0 10px}}
.{F}-swipe{{position:absolute;left:-14px;right:-14px;top:4%;bottom:-2%;background:{RED};transform-origin:0 50%;z-index:-1}}
.{F}-word{{left:0;right:0;top:590px;text-align:center;font-size:200px}}
.{F}-url{{left:0;right:0;top:800px;text-align:center;font-size:34px;color:{MUTED}}}
""", f"""
  <div class="{F}-abs {F}-stack" id="{F}-stack">
    <div class="{F}-disp {F}-l" id="{F}-l0">Models read.</div>
    <div class="{F}-disp {F}-l" id="{F}-l1">Code decides.</div>
    <div class="{F}-disp {F}-l" id="{F}-l2"><span class="{F}-sw"><span class="{F}-swipe" id="{F}-swipe"></span>Temporal keeps the promise.</span></div>
  </div>
  <div class="{F}-abs {F}-disp {F}-word" id="{F}-word">Munshi</div>
  <div class="{F}-abs {F}-mono {F}-url" id="{F}-url">github.com/ArqamWaheed/munshi</div>
""", f"""
  for (let i = 0; i < 3; i++) tl.fromTo($('#{F}-l' + i), {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "expo.out" }}, 0.05 + i * 0.55);
  tl.fromTo($('#{F}-swipe'), {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.45, ease: "expo.inOut" }}, 1.25);
  tl.to($('#{F}-stack'), {{ scale: 0.62, y: -120, duration: 0.6, ease: "expo.inOut" }}, 1.8);
  tl.fromTo($('#{F}-word'), {{ y: 40, opacity: 0 }}, {{ y: -60, opacity: 1, duration: 0.6, ease: "expo.out" }}, 1.95);
  tl.fromTo($('#{F}-url'), {{ opacity: 0 }}, {{ opacity: 1, y: -60, duration: 0.5 }}, 2.35);
""")

OUT.mkdir(parents=True, exist_ok=True)
for fid, (dur, css, body, js) in frames.items():
    # ids/classes may not start with a digit in CSS: prefix "f" to every "<fid>-..." token; the bare
    # composition id (followed by a quote) stays as is.
    html = frame(fid, dur, css, body, js).replace(fid + "-", "f" + fid + "-")
    (OUT / f"{fid}.html").write_text(html, encoding="utf-8")
    print("wrote", fid)
