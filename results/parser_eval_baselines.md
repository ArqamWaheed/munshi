| Model | N | Booking exact | Exact match | Mean field acc | Roman-Urdu booking exact | Valid JSON | p50 s | p90 s | $/1k actual | $/1k list |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma (gemma-4-26b-a4b-it) | 80 | 87.5% | 78.8% | 97.2% | 86.7% | 100.0% | 3.086 | 3.333 | 0 | 0.07481 |
| base (None) | 80 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | n/a | n/a | 0 | 0 |
| base_spec (qwen3.5-4b-base) | 80 | 68.8% | 38.8% | 88.9% | 70.0% | 100.0% | 2.374 | 3.247 | 0.2716 | 0.2716 |

Per-field accuracy:

| Field | gemma | base | base_spec |
|---|---:|---:|---:|
| check_in | 100.0% | 0.0% | 87.5% |
| nights | 97.5% | 0.0% | 91.2% |
| guests | 100.0% | 0.0% | 97.5% |
| rooms | 91.2% | 0.0% | 93.8% |
| room_type | 100.0% | 0.0% | 100.0% |
| budget_pkr | 98.8% | 0.0% | 91.2% |
| language | 90.0% | 0.0% | 56.2% |
| needs_clarification | 100.0% | 0.0% | 93.8% |

Booking exact match with 95% bootstrap CI:

| Model | Booking exact | 95% CI |
|---|---:|---|
| gemma | 87.5% | 80.0% to 93.8% |
| base | 0.0% | 0.0% to 0.0% |
| base_spec | 68.8% | 58.8% to 78.8% |
