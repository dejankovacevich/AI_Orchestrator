from __future__ import annotations

from dataclasses import dataclass

from assistant_core.clarification.question_generator import generate_questions
from assistant_core.clarification.readiness import score_readiness
from assistant_core.clarification.work_packet_builder import build_initial_work_packet
from assistant_core.schemas import ClarificationQuestion, ReadinessScore, WorkPacket


@dataclass
class ClarificationResult:
    work_packet: WorkPacket
    readiness: ReadinessScore
    questions: list[ClarificationQuestion]


def run_deterministic_clarification(title: str, description: str, *, max_questions: int = 7) -> ClarificationResult:
    packet = build_initial_work_packet(title, description)
    readiness = score_readiness(packet)
    questions = generate_questions(packet, readiness, max_questions=max_questions)
    packet.status = readiness.status
    packet.readiness_score = readiness.score
    return ClarificationResult(work_packet=packet, readiness=readiness, questions=questions)


def build_langgraph_clarification_graph():
    try:
        from langgraph.graph import END, StateGraph
    except Exception as exc:  # pragma: no cover - optional scaffold
        raise RuntimeError("LangGraph is not installed. Run scripts/install_core.sh first.") from exc

    graph = StateGraph(dict)

    def build_packet(state: dict) -> dict:
        packet = build_initial_work_packet(state["title"], state["description"])
        return {**state, "packet": packet}

    def score(state: dict) -> dict:
        readiness = score_readiness(state["packet"])
        return {**state, "readiness": readiness}

    def questions(state: dict) -> dict:
        generated = generate_questions(state["packet"], state["readiness"])
        return {**state, "questions": generated}

    graph.add_node("build_packet", build_packet)
    graph.add_node("score_readiness", score)
    graph.add_node("generate_questions", questions)
    graph.set_entry_point("build_packet")
    graph.add_edge("build_packet", "score_readiness")
    graph.add_edge("score_readiness", "generate_questions")
    graph.add_edge("generate_questions", END)
    return graph.compile()
