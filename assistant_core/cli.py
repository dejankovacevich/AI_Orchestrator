from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from assistant_core.clarification.graph import run_deterministic_clarification
from assistant_core.clarification.question_generator import generate_questions
from assistant_core.clarification.readiness import score_readiness
from assistant_core.clarification.work_packet_builder import build_initial_work_packet, update_packet_from_answers
from assistant_core.paths import ensure_local_folders
from assistant_core.storage import (
    StorageUnavailable,
    create_work_packet,
    get_work_packet,
    mark_open_questions_answered,
    ready_work_packet_ids,
    run_migration,
    save_questions,
    update_work_packet,
)
from assistant_core.temporal_app.client import start_overnight_execution


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, default=str))


def cmd_ensure_folders(_: argparse.Namespace) -> int:
    created = ensure_local_folders()
    for path in created:
        print(path)
    return 0


def cmd_sample_readiness(_: argparse.Namespace) -> int:
    result = run_deterministic_clarification("Sample", "Prepare me for tomorrow from my notes.")
    _print_json(
        {
            "work_packet_id": result.work_packet.id,
            "status": result.readiness.status,
            "score": result.readiness.score,
            "questions": [question.model_dump() for question in result.questions],
        }
    )
    return 0


def cmd_migrate(_: argparse.Namespace) -> int:
    try:
        run_migration()
    except StorageUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("Database migration applied.")
    return 0


def cmd_create_work_packet(args: argparse.Namespace) -> int:
    result = run_deterministic_clarification(args.title, args.description)
    try:
        create_work_packet(result.work_packet)
        save_questions(result.questions)
    except StorageUnavailable as exc:
        print(str(exc), file=sys.stderr)
        print("No filesystem fallback was used because Postgres is the configured machine state store.", file=sys.stderr)
        return 2
    _print_json(
        {
            "work_packet_id": result.work_packet.id,
            "status": result.readiness.status,
            "readiness_score": result.readiness.score,
            "questions": [question.model_dump() for question in result.questions],
        }
    )
    return 0


def cmd_run_clarification(args: argparse.Namespace) -> int:
    try:
        packet = get_work_packet(args.work_packet_id)
        readiness = score_readiness(packet)
        questions = generate_questions(packet, readiness)
        packet.status = readiness.status
        packet.readiness_score = readiness.score
        update_work_packet(packet)
        save_questions(questions)
    except StorageUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    _print_json(
        {
            "work_packet_id": packet.id,
            "status": readiness.status,
            "readiness_score": readiness.score,
            "questions": [question.model_dump() for question in questions],
        }
    )
    return 0


def cmd_answer_questions(args: argparse.Namespace) -> int:
    answers = Path(args.answers_file).expanduser().read_text(encoding="utf-8")
    try:
        packet = get_work_packet(args.work_packet_id)
    except StorageUnavailable as exc:
        print(str(exc), file=sys.stderr)
        print("Falling back to deterministic rescore without database update.", file=sys.stderr)
        packet = build_initial_work_packet(args.work_packet_id, answers)
    packet = update_packet_from_answers(packet, answers)
    readiness = score_readiness(packet)
    questions = generate_questions(packet, readiness)
    packet.status = readiness.status
    packet.readiness_score = readiness.score
    try:
        update_work_packet(packet)
        mark_open_questions_answered(str(packet.id), answers)
        save_questions(questions)
        db_status = "updated"
    except StorageUnavailable:
        db_status = "not_updated"
    _print_json(
        {
            "work_packet_id": args.work_packet_id,
            "status": readiness.status,
            "readiness_score": readiness.score,
            "database": db_status,
            "remaining_questions": [question.model_dump() for question in questions],
        }
    )
    return 0


def cmd_run_ready_overnight(_: argparse.Namespace) -> int:
    try:
        ids = ready_work_packet_ids()
    except StorageUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not ids:
        print("No READY_FOR_OVERNIGHT work packets found.")
        return 0
    for packet_id in ids:
        print(start_overnight_execution(packet_id))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="local-ai-orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure-folders").set_defaults(func=cmd_ensure_folders)
    sub.add_parser("sample-readiness").set_defaults(func=cmd_sample_readiness)
    sub.add_parser("migrate").set_defaults(func=cmd_migrate)

    create = sub.add_parser("create-work-packet")
    create.add_argument("title")
    create.add_argument("description")
    create.set_defaults(func=cmd_create_work_packet)

    clarify = sub.add_parser("run-clarification")
    clarify.add_argument("work_packet_id")
    clarify.set_defaults(func=cmd_run_clarification)

    answer = sub.add_parser("answer-questions")
    answer.add_argument("work_packet_id")
    answer.add_argument("answers_file")
    answer.set_defaults(func=cmd_answer_questions)

    sub.add_parser("run-ready-overnight").set_defaults(func=cmd_run_ready_overnight)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
