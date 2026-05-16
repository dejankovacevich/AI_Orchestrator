from __future__ import annotations

from datetime import timedelta

try:
    from temporalio import workflow
except Exception:  # pragma: no cover - allows py_compile without temporalio installed
    workflow = None


if workflow:

    @workflow.defn
    class ClarificationWorkflow:
        @workflow.run
        async def run(self, title: str, description: str) -> dict:
            return await workflow.execute_activity(
                "create_work_packet_activity",
                args=[title, description],
                start_to_close_timeout=timedelta(minutes=5),
            )


    @workflow.defn
    class OvernightExecutionWorkflow:
        @workflow.run
        async def run(self, work_packet_id: str) -> dict:
            await workflow.execute_activity(
                "update_status_activity",
                args=[work_packet_id, "RUNNING"],
                start_to_close_timeout=timedelta(minutes=2),
            )
            result = await workflow.execute_activity(
                "run_langgraph_execution_activity",
                args=[work_packet_id],
                start_to_close_timeout=timedelta(hours=8),
            )
            await workflow.execute_activity(
                "update_status_activity",
                args=[work_packet_id, "COMPLETED"],
                start_to_close_timeout=timedelta(minutes=2),
            )
            return result


    @workflow.defn
    class ManualResumeWorkflow:
        @workflow.run
        async def run(self, work_packet_id: str) -> dict:
            return {
                "status": "scaffolded",
                "work_packet_id": work_packet_id,
                "message": "Manual resume workflow is scaffolded for v2.",
            }

else:

    class ClarificationWorkflow:  # type: ignore[no-redef]
        pass

    class OvernightExecutionWorkflow:  # type: ignore[no-redef]
        pass

    class ManualResumeWorkflow:  # type: ignore[no-redef]
        pass
