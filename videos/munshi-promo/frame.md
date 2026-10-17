---
version: beta
name: Munshi Night Desk (video / frame layer)
description: >
  The frame-scale companion to ../../DESIGN.md. Night ground, chalk type, key-tag red for whatever code
  decided. Big Shoulders Display for display, Schibsted Grotesk for text, JetBrains Mono for data only.
  Replaces the earlier biennale-yellow remix.
unit: the frame, 1920x1080
principle: red marks what code decided; numbers come from munshi/results

colors:
  night: "#11162A"
  night-2: "#1B2240"
  line: "#2E3760"
  chalk: "#EDEFF3"
  muted: "#9AA2C2"
  red: "#C4302F"
  signal: "#F06A5F"

typography:
  display:  { fontFamily: "Big Shoulders Display", weight: 800, lineHeight: 1.0, tracking: "-0.005em", px: "96-400" }
  wordmark: { fontFamily: "Big Shoulders Display", weight: 800, px: "200-380" }
  body:     { fontFamily: "Schibsted Grotesk", weight: 400, px: "34-52" }
  caption:  { fontFamily: "Schibsted Grotesk", weight: 600, px: 30, color: "muted" }
  note:     { fontFamily: "Schibsted Grotesk", weight: 400, italic: true, px: 48, color: "signal" }
  data:     { fontFamily: "JetBrains Mono", weight: "400/700", px: "22-190" }

components:
  red-field:   "full-bleed or full-height red region; chalk type on top (brand frame, kill alarm)"
  strike:      "12px square red bar through a failed line"
  stamp:       "red block, chalk Big Shoulders, rotated -7deg, slammed in"
  chip:        "red, 6px radius, chalk 700 text: a token the parser lifted"
  card / tier: "night-2 fill, 2px line border, 12px radius; the chosen one fills red"
  bubble-in:   "night-2, chalk text, tail top-left (guest)"
  bubble-out:  "chalk, night text, tail top-right (Munshi's reply)"
---

# Munshi Night Desk, frame layer

`build_frames.py` holds these tokens as constants and is the source of truth for the ten frames.

## Frame rules

- Ground is always `night`. Red appears where code takes over, and on the brand frame (3), the kill
  alarm (8), the stamp (7) and the headline receipt (9) it owns a whole region.
- One display moment per frame in Big Shoulders. Captions go under what they describe, never above a
  headline.
- Mono only for data: JSON, rupees, timers, JazzCash ids, measured results.
- Square fields and bars; 12px radius on cards; no shadows, glows or gradients.
- Real screenshots (frames 5 and 8) sit in a 2px `line` frame and keep their own colours.
- Every figure traces to munshi/results or evidence; the storyboard lists the source per frame.
