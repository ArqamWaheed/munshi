| Model | N | Booking exact | Exact match | Mean field acc | Roman-Urdu booking exact | Valid JSON | p50 s | p90 s | $/1k actual | $/1k list |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base_spec (qwen3.5-4b-base) | 30 | 90.0% | 43.3% | 92.1% | 87.5% | 100.0% | 2.591 | 3.358 | 0.2716 | 0.2716 |
| tinker (tinker://25643fe9-07bf-5662-be34-ddc6fee4d576:train:0/sampler_weights/munshi-parser-v2) | 30 | 100.0% | 90.0% | 98.8% | 100.0% | 100.0% | 1.117 | 6.059 | 0.0837 | 0.0837 |
| gemma (gemma-4-26b-a4b-it) | 30 | 96.7% | 86.7% | 98.3% | 95.8% | 100.0% | 3.073 | 3.463 | 0 | 0.07495 |

Per-field accuracy:

| Field | base_spec | tinker | gemma |
|---|---:|---:|---:|
| check_in | 100.0% | 100.0% | 100.0% |
| nights | 100.0% | 100.0% | 100.0% |
| guests | 100.0% | 100.0% | 100.0% |
| rooms | 100.0% | 100.0% | 100.0% |
| room_type | 96.7% | 100.0% | 96.7% |
| budget_pkr | 93.3% | 100.0% | 100.0% |
| language | 46.7% | 90.0% | 90.0% |
| needs_clarification | 100.0% | 100.0% | 100.0% |

Booking exact match with 95% bootstrap CI:

| Model | Booking exact | 95% CI |
|---|---:|---|
| base_spec | 90.0% | 76.7% to 100.0% |
| tinker | 100.0% | 100.0% to 100.0% |
| gemma | 96.7% | 90.0% to 100.0% |

Paired exact McNemar, fine-tune vs each baseline (same rows):

| Comparison | Metric | Only fine-tune right | Only baseline right | p |
|---|---|---:|---:|---:|
| tinker vs base_spec | booking_exact | 3 | 0 | 0.25 |
| tinker vs base_spec | exact_match | 16 | 2 | 0.00131 |
| tinker vs gemma | booking_exact | 1 | 0 | 1 |
| tinker vs gemma | exact_match | 1 | 0 | 1 |
