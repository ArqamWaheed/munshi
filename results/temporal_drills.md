Temporal drills, parser = tinker, run 2026-10-17T16:37 UTC. Times are from Temporal's event history; [drill] rows are the drill's own process actions.

### 1. Worker SIGKILLed mid-hold, deposit signalled with no worker alive

Workflow `hold-af1fc9a6`, outcome **confirmed**; 6 activities scheduled, 6 completed, 0 completed twice.

| t (s) | Event |
|---:|---|
| -0.3 | [drill] Temporal server accepting client connections |
| -0.3 | [drill] worker #1 started (pid 88680) |
| 0.0 | workflow started |
| 0.1 | [drill] hold hold-af1fc9a6 started |
| 9.7 | scheduled parse_inquiry |
| 19.0 | completed parse_inquiry |
| 19.0 | scheduled score_risk |
| 19.0 | scheduled fetch_comps |
| 19.0 | completed fetch_comps |
| 21.0 | completed score_risk |
| 21.3 | scheduled draft_reply |
| 24.1 | completed draft_reply |
| 24.1 | durable timer started (720 s) |
| 24.4 | [drill] worker #1 SIGKILLed |
| 32.4 | signal deposit_received recorded |
| 32.4 | [drill] deposit Rs 3,500 signalled while no worker is running |
| 40.5 | [drill] worker #2 started (pid 88796) |
| 55.2 | scheduled record_booking |
| 55.2 | completed record_booking |
| 55.3 | scheduled draft_reply |
| 57.7 | completed draft_reply |
| 57.7 | workflow COMPLETED |

### 2. Worker and Temporal server SIGKILLed across the hold deadline (timer fired 15.1 s late, not lost)

Workflow `hold-9277e22e`, outcome **released**; 5 activities scheduled, 5 completed, 0 completed twice.

| t (s) | Event |
|---:|---|
| -0.0 | [drill] worker #3 started (pid 88867) |
| 0.0 | workflow started |
| 0.0 | [drill] hold hold-9277e22e started |
| 14.5 | scheduled parse_inquiry |
| 23.4 | completed parse_inquiry |
| 23.4 | scheduled score_risk |
| 23.4 | scheduled fetch_comps |
| 23.4 | completed fetch_comps |
| 30.9 | completed score_risk |
| 31.0 | scheduled draft_reply |
| 40.3 | completed draft_reply (attempt 2) |
| 40.3 | durable timer started (72 s) |
| 40.6 | [drill] worker #3 SIGKILLed |
| 40.7 | [drill] Temporal server SIGKILLed |
| 127.3 | [drill] hold deadline passed 15 s ago with everything down |
| 127.3 | [drill] Temporal server process started (pid 89432) |
| 127.4 | durable timer FIRED |
| 127.6 | [drill] Temporal server accepting client connections |
| 127.6 | [drill] worker #4 started (pid 89451) |
| 135.0 | scheduled draft_reply |
| 137.8 | completed draft_reply |
| 137.8 | workflow COMPLETED |

### 3. Chaos: 50% of first attempts fail on purpose

5/5 holds completed; 11 of 25 activities failed their first attempt and succeeded on retry; 0 replies fell back to the template.
