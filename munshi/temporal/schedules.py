"""Create the nightly brief Schedule (06:15 PKT daily), or fire it now for the demo.

  python -m munshi.temporal.schedules create
  python -m munshi.temporal.schedules trigger     # run once now -> results/briefs/brief-<tomorrow>.md
  python -m munshi.temporal.schedules delete
"""
from __future__ import annotations

import argparse
import asyncio

from temporalio.client import (Schedule, ScheduleActionStartWorkflow, ScheduleCalendarSpec,
                               ScheduleOverlapPolicy, SchedulePolicy, ScheduleRange, ScheduleSpec)
from temporalio.service import RPCError

from munshi import config as cfg
from munshi.schema import BriefInput, HoldPolicy
from munshi.temporal.worker import connect
from munshi.temporal.workflows import NightlyBriefWorkflow

SCHEDULE_ID = "munshi-nightly-brief"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "trigger", "delete"])
    a = ap.parse_args()
    client = await connect()
    handle = client.get_schedule_handle(SCHEDULE_ID)
    if a.cmd == "create":
        try:
            await client.create_schedule(SCHEDULE_ID, Schedule(
                action=ScheduleActionStartWorkflow(
                    NightlyBriefWorkflow.run,
                    BriefInput(policy=HoldPolicy(base_rate_pkr=cfg.BASE_RATE_PKR), hotel_name=cfg.HOTEL_NAME),
                    id="nightly-brief", task_queue=cfg.TASK_QUEUE),
                spec=ScheduleSpec(calendars=[ScheduleCalendarSpec(hour=[ScheduleRange(6)], minute=[ScheduleRange(15)])],
                                  time_zone_name="Asia/Karachi"),
                policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP)))
            print("schedule created:", SCHEDULE_ID)
        except RPCError as e:
            print("not created (already exists?):", e)
    elif a.cmd == "trigger":
        await handle.trigger()
        print("triggered; see Web UI -> Schedules, and results/briefs/")
    else:
        await handle.delete()
        print("deleted")


if __name__ == "__main__":
    asyncio.run(main())
