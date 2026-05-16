from __future__ import annotations

from assistant_core.clarification.graph import run_deterministic_clarification
from assistant_core.execution.graph import describe_execution_scaffold
from assistant_core.storage import StorageUnavailable, create_work_packet, save_questions

try:
    from temporalio import activity
except Exception:  # pragma: no cover
    activity = None


def _activity_defn(name: str):
    if activity is None:
        return lambda fn: fn
    return activity.defn(name=name)


@_activity_defn("create_work_packet_activity")
async def create_work_packet_activity(title: str, description: str) -> dict:
    result = run_deterministic_clarification(title, description)
    try:
        create_work_packet(result.work_packet)
        save_questions(result.questions)
    except StorageUnavailable as exc:
        return {"status": "failed", "error": str(exc)}
    return {
        "work_packet_id": str(result.work_packet.id),
        "status": result.readiness.status,
        "readiness_score": result.readiness.score,
    }


@_activity_defn("generate_questions_activity")
async def generate_questions_activity(title: str, description: str) -> dict:
    result = run_deterministic_clarification(title, description)
    return {"questions": [question.model_dump(mode="json") for question in result.questions]}


@_activity_defn("score_readiness_activity")
async def score_readiness_activity(title: str, description: str) -> dict:
    result = run_deterministic_clarification(title, description)
    return result.readiness.model_dump(mode="json")


@_activity_defn("run_langgraph_execution_activity")
async def run_langgraph_execution_activity(work_packet_id: str) -> dict:
    scaffold = describe_execution_scaffold()
    return {"work_packet_id": work_packet_id, **scaffold}


@_activity_defn("write_outputs_activity")
async def write_outputs_activity(work_packet_id: str) -> dict:
    return {"work_packet_id": work_packet_id, "status": "scaffolded"}


@_activity_defn("update_status_activity")
async def update_status_activity(work_packet_id: str, status: str) -> dict:
    return {"work_packet_id": work_packet_id, "status": status, "note": "DB status update scaffolded for v1."}


@_activity_defn("archive_files_activity")
async def archive_files_activity(work_packet_id: str) -> dict:
    return {"work_packet_id": work_packet_id, "status": "scaffolded", "note": "No files archived by scaffold."}
