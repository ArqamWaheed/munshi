# First drill run (before the fix): TabPFN cold start blew the 90 s activity timeout

Run 2026-10-17 20:43 PKT, parser = Gemma (fine-tune not trained yet). score_risk attempt 1 was
cancelled at the 90 s start-to-close timeout inside tabpfn_client predict_proba (the client's fit() is lazy;
the real work happens on the first predict). Attempt 2 reused the model the orphaned thread had finished.

Temporal drills, parser = gemma, run 2026-10-17T15:41 UTC. Times are from Temporal's event history; [drill] rows are the drill's own process actions.

### 1. Worker SIGKILLed mid-hold, deposit signalled with no worker alive

Workflow `hold-330a588a`, outcome **confirmed**; 6 activities scheduled, 6 completed, 0 completed twice; retried: {'score_risk': 2}.

| t (s) | Event |
|---:|---|
| -0.3 | [drill] Temporal server started (pid 81000) |
| -0.3 | [drill] worker #1 started (pid 81031) |
| 0.0 | workflow started |
| 0.0 | [drill] hold hold-330a588a started |
| 1.0 | scheduled parse_inquiry |
| 4.6 | completed parse_inquiry |
| 4.6 | scheduled score_risk |
| 4.6 | scheduled fetch_comps |
| 4.6 | completed fetch_comps |
| 104.4 | completed score_risk (attempt 2) |
| 104.4 | scheduled draft_reply |
| 107.1 | completed draft_reply |
| 107.1 | durable timer started (720 s) |
| 107.4 | [drill] worker #1 SIGKILLed |
| 115.4 | signal deposit_received recorded |
| 115.4 | [drill] deposit Rs 3,500 signalled while no worker is running |
| 123.4 | [drill] worker #2 started (pid 81223) |
| 125.4 | scheduled record_booking |
| 125.5 | completed record_booking |
| 125.5 | scheduled draft_reply |
| 128.2 | completed draft_reply |
| 128.3 | workflow COMPLETED |
