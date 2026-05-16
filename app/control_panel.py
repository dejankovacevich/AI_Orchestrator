from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from assistant_core.clarification.graph import run_deterministic_clarification
from assistant_core.config import load_assistant_config
from assistant_core.execution.graph import describe_execution_scaffold
from assistant_core.storage import StorageUnavailable, list_work_packets


st.set_page_config(page_title="Local AI Orchestrator", layout="wide")


def current_mode() -> str:
    return os.environ.get("LOCALAI_MODE", "DAY_MODE")


def main() -> None:
    cfg = load_assistant_config()
    st.title("Local AI Orchestrator")
    st.caption("Local-first, clarification-driven work orchestration. v1 scaffold.")

    mode = current_mode()
    st.metric("Current mode", mode)
    if mode == "DAY_MODE":
        st.info("Day mode: clarification only. Heavy local models and cloud are blocked by default.")
    st.warning("Claude/cloud fallback is disabled unless every policy gate is explicitly satisfied.")

    tabs = st.tabs(["Dashboard", "Create Work Packet", "Clarification", "Execution", "Artifacts"])

    with tabs[0]:
        st.subheader("Work Packets")
        try:
            packets = list_work_packets()
        except StorageUnavailable as exc:
            st.error(str(exc))
            packets = []
        if packets:
            st.dataframe(packets, use_container_width=True)
        else:
            st.write("No database-backed work packets are available yet.")

    with tabs[1]:
        title = st.text_input("Title", value="Prepare me for tomorrow")
        description = st.text_area("Initial request", value="Prepare me for tomorrow from my notes.")
        if st.button("Draft and Score", type="primary"):
            result = run_deterministic_clarification(title, description)
            st.session_state["last_clarification"] = result
        result = st.session_state.get("last_clarification")
        if result:
            st.metric("Readiness score", result.readiness.score)
            st.write("Status:", result.readiness.status)
            st.write("Blocking gaps:", result.readiness.blocking_gaps)
            st.write("Questions")
            for question in result.questions:
                st.checkbox(f"[{question.category}] {question.question}", value=question.blocking, disabled=True)

    with tabs[2]:
        st.subheader("Answer Questions")
        st.write("Markdown answer ingestion is implemented in CLI as deterministic rescore scaffolding.")
        uploaded = st.file_uploader("Answers markdown", type=["md", "txt"])
        if uploaded is not None:
            st.text_area("Preview", uploaded.read().decode("utf-8"), height=200)

    with tabs[3]:
        st.subheader("Execution Plan")
        st.json(describe_execution_scaffold())
        st.button("Pause", disabled=True)
        st.button("Resume", disabled=True)
        st.caption("Pause/resume database statuses exist; full UI action handling is scaffolded for v2.")

    with tabs[4]:
        st.subheader("Output Artifacts")
        output_root = Path(cfg.output_dir)
        if output_root.exists():
            files = sorted(str(path) for path in output_root.rglob("*") if path.is_file())
            st.write(files or "No output artifacts yet.")
        else:
            st.write("Output directory does not exist yet. Run scripts/install_core.sh.")


if __name__ == "__main__":
    main()
