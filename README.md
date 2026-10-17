# Munshi: a WhatsApp front desk for small hotels

One inquiry: WhatsApp text → **fine-tuned Qwen3.5-4B on Tinker** parses it to strict JSON → **TabPFN-3.5** scores
P(cancel/no-show) → **SerpApi Google Hotels** fetches nearby nightly rates (PKR, cached) → **Gemma 4** drafts the reply
from parsed fields only → a **Temporal** `RoomHoldWorkflow` holds the room for a time that depends on the risk score,
waits for a `deposit_received` signal, then confirms or releases. A Temporal Schedule writes the owner's morning
brief. **Sentry** traces every model and tool call.

Skeleton status: imports, the Temporal workflows (with mocked model calls), the LR/HGB risk baselines and the
UI page were run locally on 2026-10-16. Everything that needs an API key is marked `TODO` and has **not** run yet.

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
