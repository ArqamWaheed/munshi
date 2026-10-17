| Model | N | Booking exact | Exact match | Mean field acc | Roman-Urdu booking exact | Valid JSON | p50 s | p90 s | $/1k actual | $/1k list |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma (gemma-4-26b-a4b-it) | 80 | 87.5% | 78.8% | 97.2% | 86.7% | 100.0% | 3.086 | 3.333 | 0 | 0.07481 |
| base (None) | 80 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | n/a | n/a | 0 | 0 |
| base_spec (qwen3.5-4b-base) | 80 | 68.8% | 38.8% | 88.9% | 70.0% | 100.0% | 2.374 | 3.247 | 0.2716 | 0.2716 |
| tinker (tinker://7962983b-a1b6-507c-8466-20ec4f800a9b:train:0/sampler_weights/munshi-parser) | 80 | 73.8% | 62.5% | 93.3% | 78.3% | 98.8% | 1.106 | 5.914 | 0.08386 | 0.08386 |

Per-field accuracy:

| Field | gemma | base | base_spec | tinker |
|---|---:|---:|---:|---:|
| check_in | 100.0% | 0.0% | 87.5% | 91.2% |
| nights | 97.5% | 0.0% | 91.2% | 90.0% |
| guests | 100.0% | 0.0% | 97.5% | 97.5% |
| rooms | 91.2% | 0.0% | 93.8% | 85.0% |
| room_type | 100.0% | 0.0% | 100.0% | 98.8% |
| budget_pkr | 98.8% | 0.0% | 91.2% | 98.8% |
| language | 90.0% | 0.0% | 56.2% | 86.2% |
| needs_clarification | 100.0% | 0.0% | 93.8% | 98.8% |

Booking exact match with 95% bootstrap CI:

| Model | Booking exact | 95% CI |
|---|---:|---|
| gemma | 87.5% | 80.0% to 93.8% |
| base | 0.0% | 0.0% to 0.0% |
| base_spec | 68.8% | 58.8% to 78.8% |
| tinker | 73.8% | 63.7% to 82.5% |

Paired exact McNemar, fine-tune vs each baseline (same rows):

| Comparison | Metric | Only fine-tune right | Only baseline right | p |
|---|---|---:|---:|---:|
| tinker vs gemma | booking_exact | 1 | 12 | 0.00342 |
| tinker vs gemma | exact_match | 3 | 16 | 0.00443 |
| tinker vs base | booking_exact | 59 | 0 | 3.47e-18 |
| tinker vs base | exact_match | 50 | 0 | 1.78e-15 |
| tinker vs base_spec | booking_exact | 15 | 11 | 0.557 |
| tinker vs base_spec | exact_match | 34 | 15 | 0.0094 |
