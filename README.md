# Munshi: a WhatsApp front desk for small hotels

One inquiry: WhatsApp text → **fine-tuned Qwen3.5-4B on Tinker** parses it to strict JSON → **TabPFN-3.5** scores
P(cancel/no-show) → (optional) **SerpApi Google Hotels** nearby nightly rates set the price, otherwise your base rate → **Gemma 4** drafts the reply
from parsed fields only → a **Temporal** `RoomHoldWorkflow` holds the room for a time that depends on the risk score,
waits for a `deposit_received` signal, then confirms or releases. A Temporal Schedule writes the owner's morning
brief. **Sentry** traces every model and tool call.

Rule of the codebase: **models read and write, code decides.** Dates, counts, the advance, the hold time and every
number in a reply are computed or checked in plain Python (`munshi/dates.py`, `parser.apply_rules`, `policy.py`,
`reply.check_draft`). Demo (57 s, no narration): [docs/demo.mp4](docs/demo.mp4). Brand kit: [DESIGN.md](DESIGN.md).

## Results (every number is a file in `results/` or `evidence/`)

Parser, booking fields exactly right (all fields but `language`):

| Parser | Run 1, no rules | + dates in code | + counts in code | Fresh 30, rules frozen, run once |
|---|---:|---:|---:|---:|
| **Qwen3.5-4B + Munshi LoRA**, 68-token prompt | 75.0% | 86.2% | **95.0%** | **30 / 30** |
| Gemma 4 + 532-token rulebook (the teacher) | 87.5% | n/a | 98.8% | 29 / 30 |
| Qwen3.5-4B untuned + rulebook | 68.8% | 81.2% | 87.5% | 27 / 30 |

The counting rules were found on the 80-message set, so run 3 is tuned; `data/eval_fresh.jsonl` was committed
before any model saw it. Fine-tune vs Gemma: 0/3 discordant on the 80 (p = 0.25), 1/0 on the fresh 30 (p = 1),
a tie. Files: `parser_eval.json` (run 1), `parser_eval_r2_tinker_side.json`, `parser_eval_r3.json`, `parser_eval_fresh.json`.

- **Risk (TabPFN-3.5, 300 training bookings, 2,000 held out):** AUC 0.830 vs 0.806 / 0.789 for the baselines, ahead
  on 10 of 10 seeds; the high band predicts 82% cancels and 81% cancel. Tiered advances keep 37.7% of cancelled
  value vs 30.0% flat while asking 26.9% of guests who came. `risk_eval.md`, `risk_policy.md`.
- **Replies:** 70 Gemma quotes, 70 passed `check_draft()` with no invented or missing number. `reply_eval.md`.
- **Durability:** worker and Temporal server SIGKILLed mid-hold; the hold timer fired 0.1 s after the server came
  back and no activity ran twice. Chaos run: 5 / 5 holds completed, 11 of 25 activities retried. `temporal_drills.md`.
- **Cost:** each training run billed $0.29 on Tinker (387,659 tokens); the whole project, evals and storage included,
  $0.66.

## 1. Python env (about 0.9 GB, no torch)
Python 3.11 or newer is required (tinker needs >=3.11).
```powershell
py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install --no-cache-dir -r requirements.txt
copy .env.example .env   # then fill in the keys
```
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
cp .env.example .env
```
Do **not** `pip install tinker-cookbook`: it requires torch>=2.10 (several GB). The raw `tinker` SDK is enough here.

## 2. Temporal dev server (45 MB download, 156 MB unpacked)
Windows: download https://temporal.download/cli/archive/latest?platform=windows&arch=amd64, unzip `temporal.exe`.
Linux/WSL: `curl -sSf https://temporal.download/cli.sh | sh` or the `platform=linux&arch=amd64` archive.
```bash
temporal server start-dev --db-filename munshi.db     # gRPC :7233, Web UI http://localhost:8233
```
`--db-filename` keeps history across restarts, which the kill/resume demo needs.

## 3. Data
```bash
python -m data.fetch_hotel_bookings          # 16.9 MB public dataset (CC BY 4.0) -> data/hotels.csv
python -m data.gen_synthetic --target 900    # Gemma teacher, ~80 min at 14 RPM; resumable
# hand-label data/eval.jsonl (60-100 rows, format = data/eval_template.jsonl; real messages where possible)
```

## 4. Train and evaluate
```bash
python -m train.tinker_sft --epochs 3        # prints tinker://.../sampler_weights/munshi-parser -> .env TINKER_MODEL_PATH
python -m train.sample_check "kal 3 log 1 room 2 raat"
python -m eval.eval_parser --models gemma tinker   # results/parser_eval.{json,md}
python -m eval.eval_risk --rows 300 --seeds 10     # results/risk_eval.{json,md}
```

## 5. Run the product
```bash
python -m munshi.temporal.worker             # terminal 2
uvicorn app.server:app --port 8000           # terminal 3 -> http://localhost:8000
python -m munshi.temporal.schedules create   # nightly brief at 06:15 PKT
python -m munshi.temporal.schedules trigger  # run it now -> results/briefs/
# CLI alternative to the UI:
python -m munshi.temporal.start_inquiry start --message "3 log, family room" --demo-speed 60
python -m munshi.temporal.start_inquiry reply --id hold-xxxxxxxx --text "kal se 2 raat"   # answers the question
python -m munshi.temporal.start_inquiry deposit --id hold-xxxxxxxx --amount 5000 --ref JC-123
python -m munshi.temporal.start_inquiry list
```
The UI is the owner's desk: a list of holds, the guest conversation, a copy button for each drafted reply,
a box for the guest's answer when Munshi had to ask for a date or head count (it waits `hours_clarify`, then
re-parses the whole conversation), deposits that add up until they cover the advance (several JazzCash
transfers are normal; a short payment never confirms, and a released hold shows what to refund), and
"Run morning brief".

Demo tricks: `DEMO_SPEED=60` makes a 2 h hold expire in 2 min. Set `MUNSHI_INJECT_FAILURE_RATE=0.5` to force
visible first-attempt retries. Kill the worker (Ctrl+C) during a hold, wait, then restart it: the workflow resumes.
A missing key fails fast instead of retrying: no TabPFN token -> logreg, no Gemini key -> template reply,
no SerpApi key -> base rate. Only the parser has no fallback (raw text never goes to Gemma unless
`allow_gemma_fallback`), so without a trained Tinker model every inquiry goes to the owner by hand.

## Tests (offline, no keys)
```bash
python -m pytest -q    # rules, redaction, eval-set integrity, and RoomHoldWorkflow on a local Temporal
                       # dev server with mocked model calls (needs the `temporal` CLI on PATH)
```

## Privacy
- Raw WhatsApp text goes only to your own fine-tuned model on Tinker, after `parser.redact()` strips export
  headers (sender names), phone numbers and emails.
- Gemma (Gemini API free tier, where prompts may be used to improve Google products) sees only parsed fields:
  dates, counts and prices.
- Sentry runs with `send_default_pii=False` and receives no prompt text.

## Layout
`munshi/` config, schema, policy (pure rules), llm (clients + Sentry spans), parser, risk, comps, reply, tracing ·
`munshi/temporal/` activities, workflows, worker, start_inquiry, schedules · `data/` · `train/` · `eval/` · `app/server.py`
