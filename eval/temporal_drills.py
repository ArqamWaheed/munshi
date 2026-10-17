"""Durability drills with the real models, timelines read from Temporal's own event history.

Starts a private Temporal dev server (ports 7243 / UI 8243, fresh on-disk db under results/drills/) so it
never touches your dev server, then:
  1. worker-kill  : hold reaches "holding"; SIGKILL the worker; signal the deposit while NO worker is alive;
                    start a fresh worker; the hold confirms. Checks every activity ran to completion once.
  2. full-stack   : hold reaches "holding"; SIGKILL the worker AND the Temporal server; stay down past the
                    hold deadline; restart both; the durable timer fires late, not lost, and the hold releases.
  3. chaos        : worker with MUNSHI_INJECT_FAILURE_RATE=0.5 (first attempts only); N inquiries; counts the
                    failures Temporal absorbed.
Writes results/temporal_drills.{json,md}; the db stays in results/drills/ for the Web UI screenshots:
  temporal server start-dev --db-filename results/drills/drills.db --port 7243 --ui-port 8243

  python -m eval.temporal_drills                     # needs TINKER_MODEL_PATH (or --provider gemma)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PORT, UI_PORT = 7243, 8243
os.environ["TEMPORAL_ADDRESS"] = f"localhost:{PORT}"  # before munshi.config is imported
# Drill bookings must not land in the hotel's real register (they did, in the first runs).
os.environ["MUNSHI_BOOKINGS_LOG"] = str(Path(__file__).resolve().parent.parent / "results" / "drills" / "bookings.jsonl")

from temporalio.api.enums.v1 import EventType  # noqa: E402

from munshi.temporal.start_inquiry import get_status, send_deposit, start_hold  # noqa: E402
from munshi.temporal.worker import connect  # noqa: E402
from munshi.temporal.workflows import RoomHoldWorkflow  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DRILLS = ROOT / "results" / "drills"
MESSAGE = "AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. advance kitna?"


class Stack:
    """The private Temporal server and worker processes, with a log of when each was started or killed."""

    def __init__(self, log: list[tuple[float, str]]):
        self.server = self.worker = None
        self.log = log
        self.n_workers = 0

    def mark(self, what: str) -> None:
        self.log.append((time.time(), what))
        print(time.strftime("%H:%M:%S"), what, flush=True)

    def start_server(self) -> None:
        self.server = subprocess.Popen(
            [shutil.which("temporal"), "server", "start-dev", "--headless", "--db-filename",
             str(DRILLS / "drills.db"), "--port", str(PORT), "--ui-port", str(UI_PORT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.mark(f"Temporal server process started (pid {self.server.pid})")
        # A plain TCP probe: this also runs inside the drills' event loop, where asyncio.run() would raise (and
        # an earlier version swallowed that and waited out its whole retry budget, faking a slow restart).
        for _ in range(240):
            try:
                socket.create_connection(("localhost", PORT), timeout=1).close()
                break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("Temporal server did not start")
        self.mark("Temporal server accepting client connections")

    def start_worker(self, env: dict | None = None) -> None:
        self.n_workers += 1
        logf = open(DRILLS / f"worker-{self.n_workers}.log", "w")  # noqa: SIM115 (lives as long as the worker)
        self.worker = subprocess.Popen([sys.executable, "-m", "munshi.temporal.worker"], cwd=ROOT,
                                       env={**os.environ, "PYTHONUNBUFFERED": "1", **(env or {})}, stdout=logf, stderr=subprocess.STDOUT)
        self.mark(f"worker #{self.n_workers} started (pid {self.worker.pid})")

    def kill_worker(self) -> None:
        self.worker.kill()
        self.worker.wait()
        self.mark(f"worker #{self.n_workers} SIGKILLed")

    def kill_server(self) -> None:
        self.server.kill()
        self.server.wait()
        self.mark("Temporal server SIGKILLed")

    def stop(self) -> None:
        for p in (self.worker, self.server):
            if p and p.poll() is None:
                p.kill()
                p.wait()


async def wait_stage(client, wf_id: str, stage: str, timeout: float = 300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            st = await get_status(client, wf_id)
            if st.stage == stage:
                return st
        except Exception:  # noqa: BLE001 (worker restarting)
            pass
        await asyncio.sleep(0.5)
    raise TimeoutError(f"{wf_id} never reached {stage}")


async def timeline(client, wf_id: str, marks: list[tuple[float, str]]) -> dict:
    """Workflow history -> [(seconds since start, event)], merged with the drill's own process marks."""
    hist = await client.get_workflow_handle(wf_id).fetch_history()
    names, rows, attempts, completed, t0 = {}, [], {}, [], None
    for ev in hist.events:
        t = ev.event_time.ToDatetime().replace(tzinfo=timezone.utc).timestamp()
        t0 = t0 or t
        et = ev.event_type
        if et == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_STARTED:
            rows.append((t, "workflow started"))
        elif et == EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED:
            a = ev.activity_task_scheduled_event_attributes
            names[ev.event_id] = a.activity_type.name
            rows.append((t, f"scheduled {a.activity_type.name}"))
        elif et == EventType.EVENT_TYPE_ACTIVITY_TASK_STARTED:
            a = ev.activity_task_started_event_attributes
            attempts[names[a.scheduled_event_id]] = a.attempt
        elif et == EventType.EVENT_TYPE_ACTIVITY_TASK_COMPLETED:
            n = names[ev.activity_task_completed_event_attributes.scheduled_event_id]
            completed.append(ev.activity_task_completed_event_attributes.scheduled_event_id)
            rows.append((t, f"completed {n}" + (f" (attempt {attempts[n]})" if attempts.get(n, 1) > 1 else "")))
        elif et == EventType.EVENT_TYPE_ACTIVITY_TASK_FAILED:
            n = names[ev.activity_task_failed_event_attributes.scheduled_event_id]
            rows.append((t, f"FAILED {n} (after {attempts.get(n, 1)} attempts)"))
        elif et == EventType.EVENT_TYPE_TIMER_STARTED:
            secs = ev.timer_started_event_attributes.start_to_fire_timeout.ToTimedelta().total_seconds()
            rows.append((t, f"durable timer started ({secs:.0f} s)"))
        elif et == EventType.EVENT_TYPE_TIMER_FIRED:
            rows.append((t, "durable timer FIRED"))
        elif et == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_SIGNALED:
            rows.append((t, f"signal {ev.workflow_execution_signaled_event_attributes.signal_name} recorded"))
        elif et == EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED:
            rows.append((t, "workflow COMPLETED"))
    rows += [(t, f"[drill] {m}") for t, m in marks if t >= t0 - 1]
    rows.sort()
    return {"rows": [(round(t - t0, 1), what) for t, what in rows], "activities_scheduled": len(names),
            "activities_completed": len(completed), "completed_twice": len(completed) - len(set(completed)),
            "retried": {n: a for n, a in attempts.items() if a > 1}}


async def drill_worker_kill(stack: Stack, provider: str) -> dict:
    client = await connect()
    stack.start_worker()
    wf = await start_hold(client, MESSAGE, demo_speed=60, provider=provider)
    stack.mark(f"hold {wf} started")
    st = await wait_stage(client, wf, "holding")
    stack.kill_worker()
    await asyncio.sleep(8)
    await send_deposit(client, wf, st.quote.advance_pkr, "DRILL-1")
    stack.mark(f"deposit Rs {st.quote.advance_pkr:,} signalled while no worker is running")
    await asyncio.sleep(8)
    stack.start_worker()
    result = await client.get_workflow_handle_for(RoomHoldWorkflow.run, wf).result()
    return {"workflow_id": wf, "outcome": result.outcome, **await timeline(client, wf, stack.log)}


async def drill_full_stack(stack: Stack, provider: str) -> dict:
    client = await connect()
    stack.start_worker()
    wf = await start_hold(client, MESSAGE, demo_speed=600, provider=provider)  # 12 h -> 72 s, 6 h -> 36 s
    stack.mark(f"hold {wf} started")
    st = await wait_stage(client, wf, "holding")
    deadline = st.hold_expires_at.timestamp()
    stack.kill_worker()
    stack.kill_server()
    await asyncio.sleep(max(0.0, deadline - time.time()) + 15)
    stack.mark(f"hold deadline passed {time.time() - deadline:.0f} s ago with everything down")
    stack.start_server()
    client = await connect()
    stack.start_worker()
    result = await client.get_workflow_handle_for(RoomHoldWorkflow.run, wf).result()
    tl = await timeline(client, wf, stack.log)
    fired = next(t for t, what in tl["rows"] if what == "durable timer FIRED")
    started = next(t for t, what in tl["rows"] if what.startswith("durable timer started"))
    secs = next(float(what.split("(")[1].split(" s")[0]) for t, what in tl["rows"] if what.startswith("durable timer started"))
    return {"workflow_id": wf, "outcome": result.outcome, "timer_late_s": round(fired - started - secs, 1), **tl}


async def drill_chaos(stack: Stack, provider: str, n: int) -> dict:
    client = await connect()
    stack.start_worker({"MUNSHI_INJECT_FAILURE_RATE": "0.5"})
    ids = [await start_hold(client, MESSAGE, demo_speed=3600, provider=provider) for _ in range(n)]
    stack.mark(f"{n} holds started with 50% injected first-attempt failures")
    results = [await client.get_workflow_handle_for(RoomHoldWorkflow.run, w).result() for w in ids]
    tls = [await timeline(client, w, []) for w in ids]
    return {"n": n, "completed": sum(r.stage == "done" for r in results),
            "outcomes": [r.outcome for r in results], "activities": sum(t["activities_scheduled"] for t in tls),
            "retried_activities": sum(len(t["retried"]) for t in tls),
            "template_fallbacks": sum(len(r.template_fallbacks) for r in results)}


def md_timeline(title: str, d: dict) -> list[str]:
    out = [f"### {title}", "", f"Workflow `{d['workflow_id']}`, outcome **{d['outcome']}**; "
           f"{d['activities_scheduled']} activities scheduled, {d['activities_completed']} completed, "
           f"{d['completed_twice']} completed twice"
           + (f"; retried: {d['retried']}" if d["retried"] else "") + ".", "", "| t (s) | Event |", "|---:|---|"]
    return out + [f"| {t:.1f} | {what} |" for t, what in d["rows"]] + [""]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["tinker", "gemma"], default="tinker")
    ap.add_argument("--chaos-n", type=int, default=5)
    ap.add_argument("--only", nargs="+", choices=["worker-kill", "full-stack", "chaos"])
    a = ap.parse_args()
    if DRILLS.exists():
        shutil.rmtree(DRILLS)
    DRILLS.mkdir(parents=True)
    log: list[tuple[float, str]] = []
    stack = Stack(log)
    out = {"provider": a.provider, "run_at": datetime.now(timezone.utc).isoformat()}
    todo = a.only or ["worker-kill", "full-stack", "chaos"]
    try:
        stack.start_server()
        if "worker-kill" in todo:
            out["worker_kill"] = asyncio.run(drill_worker_kill(stack, a.provider))
            stack.kill_worker()
        if "full-stack" in todo:
            log.clear()
            out["full_stack"] = asyncio.run(drill_full_stack(stack, a.provider))
            stack.kill_worker()
        if "chaos" in todo:
            out["chaos"] = asyncio.run(drill_chaos(stack, a.provider, a.chaos_n))
    finally:
        stack.stop()
    (ROOT / "results" / "temporal_drills.json").write_text(json.dumps(out, indent=2, default=str))
    md = [f"Temporal drills, parser = {a.provider}, run {out['run_at'][:16]} UTC. Times are from Temporal's event "
          "history; [drill] rows are the drill's own process actions.", ""]
    if "worker_kill" in out:
        md += md_timeline("1. Worker SIGKILLed mid-hold, deposit signalled with no worker alive", out["worker_kill"])
    if "full_stack" in out:
        fs = out["full_stack"]
        md += md_timeline(f"2. Worker and Temporal server SIGKILLed across the hold deadline "
                          f"(timer fired {fs['timer_late_s']} s late, not lost)", fs)
    if "chaos" in out:
        c = out["chaos"]
        md += ["### 3. Chaos: 50% of first attempts fail on purpose", "",
               f"{c['completed']}/{c['n']} holds completed; {c['retried_activities']} of {c['activities']} activities "
               f"failed their first attempt and succeeded on retry; {c['template_fallbacks']} replies fell back "
               "to the template.", ""]
    (ROOT / "results" / "temporal_drills.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
