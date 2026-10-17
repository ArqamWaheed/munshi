| Model | N | Booking exact | Exact match | Mean field acc | Roman-Urdu booking exact | Valid JSON | p50 s | p90 s | $/1k actual | $/1k list |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma (gemma-4-26b-a4b-it) | 80 | 87.5% | 78.8% | 97.2% | 86.7% | 100.0% | 3.086 | 3.333 | 0 | 0.07481 |
| base (None) | 80 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | n/a | n/a | 0 | 0 |
| base_spec (qwen3.5-4b-base) | 80 | 68.8% | 38.8% | 88.9% | 70.0% | 100.0% | 2.374 | 3.247 | 0.2716 | 0.2716 |
| tinker (tinker://25643fe9-07bf-5662-be34-ddc6fee4d576:train:0/sampler_weights/munshi-parser-v2) | 80 | 75.0% | 62.5% | 93.3% | 75.0% | 98.8% | 1.039 | 5.963 | 0.08399 | 0.08399 |

Per-field accuracy:

| Field | gemma | base | base_spec | tinker |
|---|---:|---:|---:|---:|
| check_in | 100.0% | 0.0% | 87.5% | 91.2% |
| nights | 97.5% | 0.0% | 91.2% | 93.8% |
| guests | 100.0% | 0.0% | 97.5% | 97.5% |
| rooms | 91.2% | 0.0% | 93.8% | 87.5% |
| room_type | 100.0% | 0.0% | 100.0% | 98.8% |
| budget_pkr | 98.8% | 0.0% | 91.2% | 95.0% |
| language | 90.0% | 0.0% | 56.2% | 85.0% |
| needs_clarification | 100.0% | 0.0% | 93.8% | 97.5% |

Booking exact match with 95% bootstrap CI:

| Model | Booking exact | 95% CI |
|---|---:|---|
| gemma | 87.5% | 80.0% to 93.8% |
| base | 0.0% | 0.0% to 0.0% |
| base_spec | 68.8% | 58.8% to 78.8% |
| tinker | 75.0% | 65.0% to 83.8% |

Paired exact McNemar, fine-tune vs each baseline (same rows):

| Comparison | Metric | Only fine-tune right | Only baseline right | p |
|---|---|---:|---:|---:|
| tinker vs gemma | booking_exact | 1 | 11 | 0.00635 |
| tinker vs gemma | exact_match | 3 | 16 | 0.00443 |
| tinker vs base | booking_exact | 60 | 0 | 1.73e-18 |
| tinker vs base | exact_match | 50 | 0 | 1.78e-15 |
| tinker vs base_spec | booking_exact | 14 | 9 | 0.405 |
| tinker vs base_spec | exact_match | 33 | 14 | 0.00794 |
