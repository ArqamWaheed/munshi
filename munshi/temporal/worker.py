"""Run: python -m munshi.temporal.worker   (needs `temporal server start-dev --db-filename munshi.db`)

Kill it mid-hold (Ctrl+C) and start it again: the hold timer lives on the Temporal server, so the
workflow resumes exactly where it was. That's the Temporal screenshot.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from munshi import config as cfg
from munshi.temporal.activities import ALL_ACTIVITIES
from munshi.temporal.workflows import NightlyBriefWorkflow, RoomHoldWorkflow
from munshi.tracing import init_sentry


async def connect() -> Client:
    return await Client.connect(cfg.TEMPORAL_ADDRESS, data_converter=pydantic_data_converter)


async def main() -> None:
    init_sentry("worker")
    client = await connect()
    worker = Worker(client, task_queue=cfg.TASK_QUEUE, workflows=[RoomHoldWorkflow, NightlyBriefWorkflow],
                    activities=ALL_ACTIVITIES, activity_executor=ThreadPoolExecutor(max_workers=8))
    print(f"worker up on {cfg.TEMPORAL_ADDRESS}, queue={cfg.TASK_QUEUE}. Web UI: http://localhost:8233")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
