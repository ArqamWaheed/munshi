# Munshi brand kit

The world is the reception desk of a twelve-room hotel at 11:40 pm: the owner, one tube light, a phone
that is the brightest thing in the room, and a board of room keys on red tags. Munshi is the clerk who
holds the clock. The look follows from that scene, so it is dark by default.

One rule carries the brand: **red marks what code decided.** Models read and write in chalk on night.
Anything Python computed, checked or enforced (the advance, the hold, the struck-through failure, the
confirmed stamp, the 30 / 30) wears key-tag red. If something is red and a model produced it, it is wrong.

## Colour

Strategy: committed. Night owns the ground, red owns whole regions when code takes over (the brand frame,
the kill alarm, the confirmed stamp), and nothing else competes.

| Token | Hex | Role |
|---|---|---|
| night | `#11162A` | ground on every surface |
| night-2 | `#1B2240` | raised surfaces: chat bubbles, cards, tiers |
| line | `#2E3760` | 2px borders and tracks |
| chalk | `#EDEFF3` | all primary type; the outgoing reply bubble |
| muted | `#9AA2C2` | captions, JSON keys, secondary data (7:1 on night) |
| red | `#C4302F` | fields, fills, strikes, stamps, check marks (chalk on red is 4.8:1) |
| signal | `#F06A5F` | red used as text on night (5.5:1) |

No cream, no gradients, no glow. Screenshots of the real app keep their own colours inside a `line` frame.

## Type

| Face | Use |
|---|---|
| Big Shoulders Display 800 | headlines, the wordmark, big numerals. Condensed signage, set tight, sentence case. |
| Schibsted Grotesk 400/600/700 (+ 400 italic) | body, captions, chat text. Italic in signal red is the annotation voice. |
| JetBrains Mono 400/700 | data only: JSON, amounts, timers, ids, measured results. |

Files are self-hosted from `@fontsource` (Latin subsets) in `videos/munshi-promo/assets/fonts/`.
Big Shoulders has no arrow glyph, so arrows are set in JetBrains Mono.

## Shape and depth

12px radius on cards and tiers, 6px on chips, chat bubbles keep their tail corner. Fields, strikes,
stamps and the progress bar are square. Depth comes from night vs night-2 and the 2px line, never from
shadows or blur.

## Motion

Exponential ease-out (`expo.out`) for entrances from an already-visible layout; `expo.inOut` for wipes
and moves; one slam (`power4.in`) for the confirmed stamp. Numbers count up, words type in, red wipes in
from the left. One camera move per shot at most.

## Copy

No eyebrow labels above headlines, no section numbers, no em dashes. Captions sit under what they
describe. Every figure on screen traces to a file in `results/` or `evidence/`.
