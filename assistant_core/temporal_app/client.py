from __future__ import annotations

import asyncio
from uuid import uuid4

from assistant_core.config import load_assistant_config
from assistant_core.temporal_app.worker import TASK_QUEUE
from assistant_core.temporal_app.workflows import ClarificationWorkflow, OvernightExecutionWorkflow


async def _start_overnight_execution_async(work_packet_id: str) -> str:
    try:
        from temporalio.client import Client
    except Exception as exc:
        raise RuntimeError("temporalio is not installed. Run bash scripts/install_core.sh.") from exc
    cfg = load_assistant_config()
    client = await Client.connect(cfg.temporal_address)
    workflow_id = f"overnight-{work_packet_id}-{uuid4()}"
    await client.start_workflow(
        OvernightExecutionWorkflow.run,
        work_packet_id,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    return workflow_id


def start_overnight_execution(work_packet_id: str) -> str:
    return asyncio.run(_start_overnight_execution_async(work_packet_id))


async def _start_clarification_async(title: str, description: str) -> str:
    try:
        from temporalio.client import Client
    except Exception as exc:
        raise RuntimeError("temporalio is not installed. Run bash scripts/install_core.sh.") from exc
    cfg = load_assistant_config()
    client = await Client.connect(cfg.temporal_address)
    workflow_id = f"clarification-{uuid4()}"
    await client.start_workflow(
        ClarificationWorkflow.run,
        args=[title, description],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    return workflow_id


def start_clarification(title: str, description: str) -> str:
    return asyncio.run(_start_clarification_async(title, description))
