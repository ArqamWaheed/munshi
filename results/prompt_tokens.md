Prompt size per parse call over the 80 rows of data/eval.jsonl, counted with the Qwen3.5-4B tokenizer
(chat template rendered with enable_thinking=False). Measured 2026-10-17, offline.

| Prompt | Used by | Median tokens | Mean |
|---|---|---:|---:|
| SPEC_PROMPT (long rules) | Gemma 4 zero-shot baseline + teacher | 532 | 531.6 |
| SHORT_PROMPT (one line) | Tinker fine-tune | 68 | 67.6 |

Caveat: Gemma uses its own tokenizer, so its billed count will differ somewhat; the real per-call counts
come from the API `usage` fields in eval/eval_parser.py.
