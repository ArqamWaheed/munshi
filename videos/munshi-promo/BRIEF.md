---
workflow: product-launch-video
flow: automation
storyboard: no
message: "A room hold is a promise with a deadline. Models read, code decides, Temporal keeps the promise."
destination: youtube
aspect: 1920x1080
language: en
audience: "dev.to readers and Hacktoberfest judges (developers); secondarily small-hotel owners"
length: 55s
angle: problem-moment hook -> real product demo -> durability proof -> numbers -> outro
---

## Intent

Demo video for Munshi, a WhatsApp front desk for small Pakistani hotels, embedded in the Hacktoberfest Week 2
(Side Hustle) dev.to post. The user asked for motion design, music from HeyGen, sound effects, and to study
existing viral product demos rather than go in blind. Research (Linear, Cursor, Notion launch breakdowns):
no narration, music + kinetic on-screen text + SFX; problem-moment hook in the first 3 s; real UI held long
enough to read, with zooms; numbers as anchors; 45-60 s; short outro after the product has been shown.

## Assets

- ../../docs/images/app-quote.jpg — real owner screen: parsed JSON, 5% TabPFN risk, quote, hold countdown.
- ../../docs/images/app-clarify.png — real clarification round (no date -> question -> "parso se 2 raat" -> quote).
- ../../docs/images/app-partial-deposit.png — hold panel with Rs 2,000 of 3,500 paid.
- ../../docs/images/app-confirmed.png — confirmed conversation with Gemma's confirmation message.
- ../../docs/images/temporal-drill.png — Temporal Web UI timeline: the room-hold timer spans a full worker+server kill.

## Customizations

- Ledger palette shared with the post's images: parchment #F4EDE0, teal ink #0D5C52, saffron #E3A21A, brick #A23B2A; serif display type.
- Music: HeyGen music library bed; SFX on message pops, counters, the confirmation stamp, the server kill.

## Notes

- Every number on screen must come from the repo's results/ files (75% -> 95% -> 30/30; 82% vs 81%; 70/70; timer 0.1 s after restart; Rs 3,500).
- No invented first user, no claims of hotels pitched. No narration.
