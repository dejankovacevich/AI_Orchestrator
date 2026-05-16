from __future__ import annotations

import asyncio

from assistant_core.config import load_assistant_config
from assistant_core.temporal_app import activities
from assistant_core.temporal_app.workflows import ClarificationWorkflow, ManualResumeWorkflow, OvernightExecutionWorkflow


TASK_QUEUE = "local-ai-orchestrator"


async def main_async() -> None:
    try:
        from temporalio.client import Client
        from temporalio.worker import Worker
    except Exception as exc:
        raise RuntimeError("temporalio is not installed. Run bash scripts/install_core.sh.") from exc

    cfg = load_assistant_config()
    client = await Client.connect(cfg.temporal_address)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ClarificationWorkflow, OvernightExecutionWorkflow, ManualResumeWorkflow],
        activities=[
            activities.create_work_packet_activity,
            activities.generate_questions_activity,
            activities.score_readiness_activity,
            activities.run_langgraph_execution_activity,
            activities.write_outputs_activity,
            activities.update_status_activity,
            activities.archive_files_activity,
        ],
    )
    print(f"Temporal worker listening on task queue: {TASK_QUEUE}")
    await worker.run()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
