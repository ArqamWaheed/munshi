| Model | N | Booking exact | Exact match | Mean field acc | Roman-Urdu booking exact | Valid JSON | p50 s | p90 s | $/1k actual | $/1k list |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base (None) | 80 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | n/a | n/a | 0 | 0 |
| base_spec (qwen3.5-4b-base) | 80 | 81.2% | 43.8% | 91.2% | 76.7% | 100.0% | 2.464 | 3.21 | 0.2716 | 0.2716 |
| tinker (tinker://25643fe9-07bf-5662-be34-ddc6fee4d576:train:0/sampler_weights/munshi-parser-v2) | 80 | 86.2% | 73.8% | 95.3% | 86.7% | 98.8% | 5.901 | 6.14 | 0.08399 | 0.08399 |

Per-field accuracy:

| Field | base | base_spec | tinker |
|---|---:|---:|---:|
| check_in | 0.0% | 100.0% | 97.5% |
| nights | 0.0% | 95.0% | 97.5% |
| guests | 0.0% | 97.5% | 97.5% |
| rooms | 0.0% | 93.8% | 92.5% |
| room_type | 0.0% | 100.0% | 98.8% |
| budget_pkr | 0.0% | 91.2% | 95.0% |
| language | 0.0% | 53.8% | 85.0% |
| needs_clarification | 0.0% | 98.8% | 98.8% |

Booking exact match with 95% bootstrap CI:

| Model | Booking exact | 95% CI |
|---|---:|---|
| base | 0.0% | 0.0% to 0.0% |
| base_spec | 81.2% | 72.5% to 90.0% |
| tinker | 86.2% | 78.8% to 93.8% |

Paired exact McNemar, fine-tune vs each baseline (same rows):

| Comparison | Metric | Only fine-tune right | Only baseline right | p |
|---|---|---:|---:|---:|
| tinker vs base | booking_exact | 69 | 0 | 3.39e-21 |
| tinker vs base | exact_match | 59 | 0 | 3.47e-18 |
| tinker vs base_spec | booking_exact | 7 | 3 | 0.344 |
| tinker vs base_spec | exact_match | 36 | 12 | 0.000717 |
