---
format: 1920x1080
duration: 56s
message: "A room hold is a promise with a deadline. Models read, code decides, Temporal keeps the promise."
arc: Hook → Problem → Product intro → Read → Price → Reply → Hold → Durability proof → Numbers → Outro
audience: developers on dev.to (Hacktoberfest judges); small-hotel owners
mode: autonomous
music: confident minimal tech underscore, light percussion, modern product launch, steady build
---

## Video direction

- palette system: canvas paper #F4EDE0 on every frame; ink #0D5C52 (teal) for all type, rules and outlines; sun #E3A21A as the single accent (highlighter swipes, the live element, check marks, the playhead); ember #A23B2A only for the pain strikes and the server-kill beat; one sun-bloom per frame behind the focal element. WhatsApp-green #D9FDD3 only inside chat bubbles, never as a design accent. Frame 8's Temporal screenshot is the one dark surface; it sits inside a paper frame, never full-bleed.
- type: display = Instrument Serif (headlines, wordmark, numerals); body = Archivo; data/code = JetBrains Mono (JSON, amounts, timers, ids).
- motion grammar: long-tail power3 eases, smooth over bouncy; text enters by short rise+fade or in-place token swap; numbers count up; one camera move per shot at most. No narration, so reveals are paced to the on-screen text cue and the music: nothing appears before its line is due; reveals spread across each shot's back half.
- rhythm: frames 1, 4, 7 and 8 carry the motion; frames 3 and 10 are held brand reads; frame 6 is a quiet breather before the hold.
- negative list: no stock icons, no bokeh, no purple/blue AI gradients, no fake logos, no invented numbers (every figure from munshi/results), no first-user or testimonial claims. Neither failure mode: no slideshow (front-load then freeze), no screensaver (everything floating).

## Frame 1 — 11:40 pm

- scene: A phone lock screen at 11:40 PM; a WhatsApp message slides in and types itself out in Roman Urdu
- voiceover: ""
- duration: 5s
- transition_in: cut
- status: animated
- src: compositions/frames/01-midnight-message.html
- type: hook
- persuasion: Pain validation
- beat: tension
- blueprint: typewriter-reveal
- asset_candidates:
- sfx: notification pop, keyboard typing

- blueprint: typewriter-reveal (Adapt)
- focal: phone card
- roles: none (typography + rebuilt chat UI)

Adapt: keep the caret typing a line as a human would; the payoff is the clock, not a brand pop (the brand lands in frame 3).
Scene 1 (0.0–1.0s): parchment; a large serif clock "11:40 PM" fades up centred-left over a faint sun-bloom; small mono kicker "a hotel owner's phone" beneath. Centered-left, 2 depth layers.
Scene 2 (1.0–1.6s): a tall phone card rises in on the right third with a WhatsApp header "Guest · +92 3•• •••••••"; notification pop.
Scene 3 (1.6–4.2s): a guest bubble types itself out word by word: "AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. rate kya hai? advance kitni?" with a blinking caret. Asymmetric 40/60.
Scene 4 (4.2–5.0s): hold; an unread badge on the phone ticks 1 → 43 in the corner.

narrativeRole: Open on the exact message every small hotel gets, at the hour it arrives, before saying a word about the product.
keyMessage: "AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. rate kya hai? advance kitni?" arrives at 11:40 PM.

## Frame 2 — Nobody holds the clock

- scene: Three short pain lines land alone on the parchment, each struck through in ember: rate from memory, advance never chased, room sits empty
- voiceover: ""
- duration: 4s
- transition_in: crossfade
- status: animated
- src: compositions/frames/02-nobody-holds-the-clock.html
- type: pain_point
- persuasion: Pain agitation
- beat: frustration
- blueprint: kinetic-type-beats
- asset_candidates:
- sfx: whoosh, pen scratch

- blueprint: kinetic-type-beats (Reproduce)
- focal: three pain lines
- roles: none

Scene 1 (0.0–1.1s): "Rate quoted from memory." rises in alone, centred, display serif; an ember strike draws through it.
Scene 2 (1.1–2.2s): line 1 slides up and dims; "Advance never chased." rises in; ember strike.
Scene 3 (2.2–3.4s): line 2 slides up and dims; "Room sits empty." rises in; ember strike; the three lines read as a stack.
Scene 4 (3.4–4.0s): hold the stack.

narrativeRole: Name what goes wrong after the message: a quote with no deadline and an advance nobody chases.
keyMessage: The problem is the promise with no deadline.

## Frame 3 — Munshi

- scene: The wordmark "Munshi" writes on in serif with a saffron highlighter swipe; the line "the front desk that holds the clock" settles beneath
- voiceover: ""
- duration: 4s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/03-munshi.html
- type: product_intro
- persuasion: Negative contrast
- beat: relief
- blueprint: logo-assemble-lockup
- asset_candidates:
- sfx: swoosh, soft impact

- blueprint: logo-assemble-lockup (Adapt)
- focal: wordmark
- roles: none

Adapt: the mark comes to exist by a saffron highlighter swipe drawing left to right behind the serif wordmark.
Scene 1 (0.0–1.2s): saffron swipe draws across centre; "Munshi" in display serif rises onto it. Centered, ~45% width, sun-bloom behind.
Scene 2 (1.2–2.4s): mono kicker above: "MUNSHI · منشی"; line beneath fades up: "the front desk that holds the clock."
Scene 3 (2.4–4.0s): held read.

narrativeRole: Resolve the pain with the product name and its one-line promise.
keyMessage: Munshi holds the clock.

## Frame 4 — It reads Roman Urdu

- scene: The guest message sits left; its words light up one by one and fly into a JSON card on the right: kal → 2026-10-18, 2 log → guests 2, 2 raat → nights 2, 1 room → rooms 1
- voiceover: ""
- duration: 7s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/04-reads-roman-urdu.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: clarity
- blueprint: prompt-type-submit-generate
- asset_candidates: assets/app-quote.jpg — real owner screen whose parsed JSON panel is the target state
- sfx: tick, tick, tick, confirm

- blueprint: prompt-type-submit-generate (Adapt)
- focal: JSON card
- roles: app-quote.jpg = supporting (only the JSON values are taken from it; the card is rebuilt crisp)

Adapt: the "prompt" is the guest message, the "generated artifact" is the parsed JSON; keep the round trip as the signature.
Scene 1 (0.0–1.2s): headline top-left: "A fine-tuned 4B reads it." (display); the guest bubble sits left-centre. Asymmetric 45/55.
Scene 2 (1.2–5.2s): four tokens highlight in sun one at a time and fly into a mono JSON card on the right, each landing as a field: "kal" → "check_in": "2026-10-18"; "2 log" → "guests": 2; "2 raat" → "nights": 2; "1 room" → "rooms": 1. One tick per field.
Scene 3 (5.2–6.2s): a small rule under the card: "Qwen3.5-4B + LoRA on Tinker · dates resolved in code".
Scene 4 (6.2–7.0s): hold.

narrativeRole: Prove the first job: a 4B model fine-tuned on Tinker turns messy Roman Urdu into exact fields.
keyMessage: "kal" becomes a date. A fine-tuned 4B reads it; code does the calendar.

## Frame 5 — It prices the risk

- scene: Push into the real owner screen; the risk card isolates: "5% cancel risk" counts up, then the advance tiers 20 / 30 / 50% appear and the low tier lights: advance Rs 3,500, hold 12 h
- voiceover: ""
- duration: 7s
- transition_in: crossfade
- status: animated
- src: compositions/frames/05-prices-the-risk.html
- type: feature_showcase
- persuasion: Feature-to-benefit translation
- beat: control
- blueprint: dataviz-countup
- asset_candidates: assets/app-quote.jpg — real owner screen with the 5% risk card, Rs 16,000 total, Rs 3,500 advance, 12 h hold
- sfx: counter, click

- blueprint: dataviz-countup (Adapt)
- focal: assets/app-quote.jpg
- roles: app-quote.jpg = background-then-cutout (the real screen, pushed into the risk card)

Adapt: one hero metric (5%) instead of a chart; the push-THROUGH goes into the real risk card.
Scene 1 (0.0–1.8s): the real owner screen sits framed in a paper card at ~80% width; slow push toward the right-hand risk card.
Scene 2 (1.8–3.6s): the screen dims; a rebuilt risk card scales up from the screenshot's card position: "5%" counts 0 → 5 in jumbo serif, "cancel risk · TabPFN-3.5" beneath.
Scene 3 (3.6–6.2s): three tier chips appear left to right: "low · 20% · 12 h", "medium · 30% · 6 h", "high · 50% · 2 h"; the low chip lights saffron and resolves into "Advance Rs 3,500 · hold 12 h".
Scene 4 (6.2–7.0s): hold.

narrativeRole: TabPFN scores the cancel risk and the risk sets the advance and the hold length.
keyMessage: Low risk pays 20% and is held 12 h; high risk pays 50% and is held 2 h.

## Frame 6 — Gemma writes, code checks

- scene: Gemma's real Roman-Urdu quote types into a green reply bubble; each number in it gets a saffron check mark as code verifies it against the facts
- voiceover: ""
- duration: 5s
- transition_in: crossfade
- status: animated
- src: compositions/frames/06-gemma-writes-code-checks.html
- type: feature_showcase
- persuasion: Risk reversal
- beat: trust
- blueprint: kinetic-type-beats
- asset_candidates:
- sfx: typing, tick, tick, tick

- blueprint: kinetic-type-beats (Adapt)
- focal: reply bubble
- roles: none

Adapt: the token swap becomes number checks: each figure in the typed reply gets a saffron check as code verifies it.
Scene 1 (0.0–2.6s): small label top-left "Gemma 4 writes the reply"; a green reply bubble types: "Aapki 18 October ki booking ke liye 1 room… total 16,000 Rs… 3,500 Rs advance… 12 ghanto ke liye hold".
Scene 2 (2.6–4.2s): "16,000", "3,500", "12" each underline in saffron with a check tick; label swaps to "code checks every number".
Scene 3 (4.2–5.0s): hold.

narrativeRole: The reply is written by Gemma 4 but every number in it is checked by code before the owner sees it.
keyMessage: Gemma writes. Code checks every number.

## Frame 7 — The hold

- scene: A big countdown ticks down from 11:59:58; deposit chips arrive: JC-48120 Rs 2,000 (still due Rs 1,500), then JC-48177 Rs 1,500; a CONFIRMED stamp lands
- voiceover: ""
- duration: 8s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/07-the-hold.html
- type: feature_showcase
- persuasion: Show-don't-tell proof
- beat: tension + relief
- blueprint: video-text-pivot
- asset_candidates:
- sfx: clock ticking, coin, coin, stamp

- blueprint: video-text-pivot (Adapt)
- focal: countdown
- roles: none (rebuilt hold panel with the real values)

Adapt: the "video" is the live hold panel; it slides aside to hand weight to the CONFIRMED stamp.
Scene 1 (0.0–2.0s): headline "Temporal holds the room."; a jumbo mono countdown "11:59:58" ticks down second by second, centred; "advance due Rs 3,500" beneath.
Scene 2 (2.0–3.8s): a deposit chip slides in from the right: "JC-48120 · Rs 2,000"; a progress bar fills to 57%; "still due Rs 1,500" in ember.
Scene 3 (3.8–5.4s): a second chip: "JC-48177 · Rs 1,500"; bar fills to 100%.
Scene 4 (5.4–8.0s): the panel slides left; a saffron "CONFIRMED" stamp slams in at a slight angle; small line "a short payment never confirms a room". Hold.

narrativeRole: The heart of the product: a Temporal workflow holds the room until the advance adds up, or releases it.
keyMessage: A short payment never confirms a room.

## Frame 8 — We killed the server

- scene: "We killed the server mid-hold." The screen glitches to black; then the real Temporal timeline slides in and a saffron playhead runs along the orange room-hold bar through the outage; "Timer fired 0.1 s after it came back. 0 steps ran twice."
- voiceover: ""
- duration: 7s
- transition_in: cut
- status: animated
- src: compositions/frames/08-we-killed-the-server.html
- type: benefit_highlight
- persuasion: Statistical proof
- beat: tension + awe
- blueprint: camera-journey
- asset_candidates: assets/temporal-drill.png — real Temporal Web UI timeline whose orange room-hold bar spans the full worker+server kill
- sfx: power down, glitch, power up

- blueprint: camera-journey (Adapt)
- focal: assets/temporal-drill.png
- roles: temporal-drill.png = cutout (real Temporal timeline inside a paper frame)

Adapt: the journey runs along the timeline's orange room-hold bar with a saffron playhead; the beat that fires is the kill.
Scene 1 (0.0–1.4s): "We killed the server mid-hold." centred in display serif.
Scene 2 (1.4–2.0s): the frame flickers and cuts to ink-dark for a beat (ember "SIGKILL worker · SIGKILL server" in mono).
Scene 3 (2.0–5.2s): the real Temporal timeline slides up in a paper frame; a saffron playhead travels along the orange room-hold bar from its start to its end.
Scene 4 (5.2–7.0s): two mono callouts land: "timer fired 0.1 s after the server came back" and "0 steps ran twice". Hold.

narrativeRole: Durability shown, not claimed: the hold survives a full worker and server kill.
keyMessage: The promise kept its deadline with nothing running.

## Frame 9 — The receipts

- scene: Four stat cards assemble: "0% → 75% → 95%" (fine-tune, then code rules); "30 / 30" on a test written after the rules froze; "Says 82%. 81% cancel." (TabPFN); "70 / 70" replies passed the checker
- voiceover: ""
- duration: 6s
- transition_in: crossfade
- status: animated
- src: compositions/frames/09-the-receipts.html
- type: social_proof
- persuasion: Statistical proof
- beat: confidence
- blueprint: grid-card-assemble
- asset_candidates:
- sfx: tick, tick, tick, tick

- blueprint: grid-card-assemble (Reproduce)
- focal: stat grid
- roles: none

Scene 1 (0.0–0.6s): kicker "measured, not claimed".
Scene 2 (0.6–4.4s): four cards self-assemble in a 2×2 cascade, each with a jumbo serif figure and a one-line mono caption: "0% → 75% → 95%" / "untuned → fine-tuned → + code rules"; "30 / 30" / "fresh test, written after the rules froze"; "82% → 81%" / "TabPFN says · actually cancelled"; "70 / 70" / "Gemma replies passed the number check".
Scene 3 (4.4–6.0s): hold.

narrativeRole: Back the claims with the measured numbers from the repo.
keyMessage: Measured, not claimed.

## Frame 10 — Models read. Code decides.

- scene: Three lines stack: "Models read." "Code decides." "Temporal keeps the promise." then the Munshi wordmark and github.com/ArqamWaheed/munshi
- voiceover: ""
- duration: 4s
- transition_in: blur-crossfade
- status: animated
- src: compositions/frames/10-outro.html
- type: brand_outro
- persuasion: Rule of three
- beat: triumph
- blueprint: kinetic-type-beats
- asset_candidates:
- sfx: impact

- blueprint: kinetic-type-beats (Adapt)
- focal: thesis stack
- roles: none

Scene 1 (0.0–1.8s): "Models read." / "Code decides." / "Temporal keeps the promise." rise in one by one, the last with a saffron swipe.
Scene 2 (1.8–3.0s): the stack shrinks up; "Munshi" wordmark and "github.com/ArqamWaheed/munshi" (mono) land beneath.
Scene 3 (3.0–4.0s): held end card.

narrativeRole: Land the thesis and the brand.
keyMessage: Models read. Code decides. Temporal keeps the promise.
