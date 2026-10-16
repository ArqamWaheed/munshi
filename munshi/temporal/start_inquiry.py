"""CLI: start a hold, send the deposit signal, or read status.

  python -m munshi.temporal.start_inquiry start --message "kal 2 log 1 room, rate?" --demo-speed 60
  python -m munshi.temporal.start_inquiry start --file whatsapp_export.txt
  python -m munshi.temporal.start_inquiry deposit --id hold-ab12cd --amount 5000 --ref JC-123
  python -m munshi.temporal.start_inquiry status --id hold-ab12cd
"""
from __future__ import annotations

import argparse
import asyncio
import uuid

import sentry_sdk

from munshi import config as cfg
from munshi.schema import DepositInfo, GuestContext, HoldInput, HoldPolicy, HoldStatus
from munshi.temporal.activities import dumps, pkt_today
from munshi.temporal.worker import connect
from munshi.temporal.workflows import RoomHoldWorkflow
from munshi.tracing import current_trace_headers, init_sentry


async def start_hold(client, message: str, demo_speed: float = cfg.DEMO_SPEED, provider: str = "tinker",
                     guest: GuestContext | None = None) -> str:
    init_sentry("starter")
    wf_id = f"hold-{uuid.uuid4().hex[:8]}"
    with sentry_sdk.start_transaction(op="munshi.inquiry", name="new WhatsApp inquiry"):
        inp = HoldInput(message=message, today=pkt_today(), guest=guest or GuestContext(),
                        policy=HoldPolicy(base_rate_pkr=cfg.BASE_RATE_PKR, floor_rate_pkr=cfg.FLOOR_RATE_PKR,
                                          demo_speed=demo_speed),
                        hotel_name=cfg.HOTEL_NAME, parser_provider=provider, trace_headers=current_trace_headers())
        await client.start_workflow(RoomHoldWorkflow.run, inp, id=wf_id, task_queue=cfg.TASK_QUEUE)
    return wf_id


async def send_deposit(client, wf_id: str, amount: int, ref: str | None = None) -> None:
    await client.get_workflow_handle(wf_id).signal(RoomHoldWorkflow.deposit_received,
                                                   DepositInfo(amount_pkr=amount, reference=ref))


async def get_status(client, wf_id: str) -> HoldStatus:
    # typed handle so the pydantic converter returns HoldStatus, not a dict
    return await client.get_workflow_handle_for(RoomHoldWorkflow.run, wf_id).query(RoomHoldWorkflow.get_status)


async def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--message")
    s.add_argument("--file")
    s.add_argument("--demo-speed", type=float, default=cfg.DEMO_SPEED)
    s.add_argument("--provider", choices=["tinker", "gemma"], default="tinker")
    d = sub.add_parser("deposit")
    d.add_argument("--id", required=True)
    d.add_argument("--amount", type=int, required=True)
    d.add_argument("--ref")
    q = sub.add_parser("status")
    q.add_argument("--id", required=True)
    a = ap.parse_args()
    client = await connect()
    if a.cmd == "start":
        msg = open(a.file, encoding="utf-8").read() if a.file else a.message
        print("started", await start_hold(client, msg, a.demo_speed, a.provider))
    elif a.cmd == "deposit":
        await send_deposit(client, a.id, a.amount, a.ref)
        print("signal sent")
    else:
        print(dumps((await get_status(client, a.id)).model_dump(mode="json")))
    sentry_sdk.flush()


if __name__ == "__main__":
    asyncio.run(main())
