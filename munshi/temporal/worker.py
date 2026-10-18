"""Run: python -m munshi.temporal.worker   (needs `temporal server start-dev --db-filename munshi.db`)

Kill it mid-hold (Ctrl+C) and start it again: the hold timer lives on the Temporal server, so the
workflow resumes exactly where it was. That's the Temporal screenshot.
"""
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from munshi import config as cfg
from munshi import llm, risk
from munshi.temporal.activities import ALL_ACTIVITIES
from munshi.temporal.workflows import NightlyBriefWorkflow, RoomHoldWorkflow
from munshi.tracing import init_sentry


async def connect() -> Client:
    return await Client.connect(cfg.TEMPORAL_ADDRESS, data_converter=pydantic_data_converter)


async def warm_risk_model() -> None:
    t0 = time.perf_counter()
    try:
        name = await asyncio.wait_for(asyncio.to_thread(risk.warm_up), timeout=180)
        print(f"risk model warm: {name} in {time.perf_counter() - t0:.1f}s")
    except Exception as e:  # noqa: BLE001 (inquiries still work: score_risk falls back to logreg)
        print(f"risk warm-up failed after {time.perf_counter() - t0:.1f}s ({type(e).__name__}); logreg fallback")


async def warm_tokenizer() -> None:
    # Load the Qwen chat template once, before parse_inquiry activities can race to import transformers.
    t0 = time.perf_counter()
    try:
        await asyncio.to_thread(llm.qwen_tokenizer)
        print(f"tokenizer warm in {time.perf_counter() - t0:.1f}s")
    except Exception as e:  # noqa: BLE001 (the lock in qwen_tokenizer still serialises the first load)
        print(f"tokenizer warm-up failed ({type(e).__name__}); loading on first parse")


async def main() -> None:
    init_sentry("worker")
    client = await connect()
    await warm_risk_model()
    await warm_tokenizer()
    worker = Worker(client, task_queue=cfg.TASK_QUEUE, workflows=[RoomHoldWorkflow, NightlyBriefWorkflow],
                    activities=ALL_ACTIVITIES, activity_executor=ThreadPoolExecutor(max_workers=8))
    print(f"worker up on {cfg.TEMPORAL_ADDRESS}, queue={cfg.TASK_QUEUE}. Web UI: http://localhost:8233")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
