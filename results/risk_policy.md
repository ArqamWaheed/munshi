Test set 2000 bookings (cancel rate 35.2%); each model trained on 300 rows, mean over 5 seeds.

**Calibration by hold band**

| Model | Band | Share of bookings | Mean predicted | Actually cancelled | Share of all cancels |
|---|---|---:|---:|---:|---:|
| tabpfn | low | 40% | 13% | 12% | 14% |
| tabpfn | medium | 36% | 36% | 30% | 31% |
| tabpfn | high | 24% | 82% | 81% | 55% |
| logreg | low | 40% | 14% | 15% | 17% |
| logreg | medium | 35% | 36% | 29% | 29% |
| logreg | high | 25% | 80% | 78% | 54% |

| Model | Brier (lower better) | ECE (lower better) |
|---|---:|---:|
| tabpfn | 0.1477 | 0.051 |
| logreg | 0.1569 | 0.050 |

**Advance policy** (advance kept when a guest cancels; % of booking value)

| Policy | Kept from cancelled bookings | Asked of guests who came | Guests asked 50% |
|---|---:|---:|---:|
| flat_20 | 20.0% | 20.0% | 0% |
| flat_30 | 30.0% | 30.0% | 0% |
| flat_50 | 50.0% | 50.0% | 100% |
| tiered by tabpfn | 37.7% | 26.9% | 24% |
| tiered by logreg | 37.8% | 27.3% | 25% |
