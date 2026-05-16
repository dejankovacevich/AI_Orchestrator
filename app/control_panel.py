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
from assistant_core.config_writer import (
    ConfigEditError,
    update_assistant_config,
)
from assistant_core.execution.graph import describe_execution_scaffold
from assistant_core.llm import ollama_admin
from assistant_core.safety import (
    DAY_UNLOCK_ENV_VAR,
    SafetyError,
    day_unlock_active,
    day_unlock_flag_path,
)
from assistant_core.scheduler_status import (
    LAUNCHD_JOB_LABEL,
    auto_execution_status,
    compute_window_status,
    litellm_up,
    ollama_up,
    postgres_up,
    temporal_up,
)
from assistant_core.storage import StorageUnavailable, list_work_packets


st.set_page_config(page_title="Local AI Orchestrator", layout="wide")


def current_mode() -> str:
    return os.environ.get("LOCALAI_MODE", "DAY_MODE")


def _status_pill(label: str, ok: bool, *, on_text: str = "up", off_text: str = "down") -> None:
    st.metric(label, on_text if ok else off_text)


def _render_header(cfg) -> tuple[str, bool]:
    mode = current_mode()
    unlocked = day_unlock_active()
    window = compute_window_status(cfg=cfg)
    auto = auto_execution_status()

    row1 = st.columns(4)
    row1[0].metric("Current mode", mode)
    row1[1].metric("Day unlock", "ACTIVE" if unlocked else "off")
    row1[2].metric(
        "Now",
        window.now.strftime("%H:%M"),
        delta=window.label,
        delta_color="off",
    )
    row1[3].metric(
        "Auto-execution",
        "SCHEDULED" if auto["loaded_in_launchctl"] else "off",
        delta=f"{cfg.night_mode_start}" if auto["loaded_in_launchctl"] else None,
        delta_color="off",
    )

    row2 = st.columns(4)
    with row2[0]:
        _status_pill("Postgres", postgres_up(cfg))
    with row2[1]:
        _status_pill("Temporal", temporal_up(cfg))
    with row2[2]:
        _status_pill("Ollama", ollama_up(cfg))
    with row2[3]:
        _status_pill("LiteLLM", litellm_up(cfg))

    if unlocked:
        details: list[str] = []
        flag_path = day_unlock_flag_path()
        if flag_path.exists():
            details.append(f"Flag file: `{flag_path}`")
            try:
                contents = flag_path.read_text(encoding="utf-8").strip()
                if contents:
                    details.append("```\n" + contents + "\n```")
            except OSError:
                details.append("Flag file exists but could not be read.")
        if os.environ.get(DAY_UNLOCK_ENV_VAR):
            details.append(
                f"Env var `{DAY_UNLOCK_ENV_VAR}` is set in the Streamlit process."
            )
        details.append(
            "Local-* model groups can run in DAY_MODE. Lock again with: "
            "`bash scripts/day_lock.sh`"
        )
        st.error(
            "Day unlock is ACTIVE — local models can load during the day.\n\n"
            + "\n\n".join(details)
        )
    elif mode == "DAY_MODE":
        st.info(
            "DAY_MODE: clarification only. All local-* model groups and cloud "
            "are blocked unless you run `bash scripts/day_unlock.sh` first."
        )

    if auto["loaded_in_launchctl"]:
        st.warning(
            f"Nightly auto-execution is SCHEDULED via launchd job "
            f"`{LAUNCHD_JOB_LABEL}` at {cfg.night_mode_start}. "
            "Disable with: `launchctl unload "
            "~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist`"
        )
    st.warning(
        "Claude / cloud fallback is disabled unless every policy gate is "
        "explicitly satisfied."
    )

    return mode, unlocked


def _render_dashboard_tab() -> None:
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


def _render_create_packet_tab() -> None:
    title = st.text_input("Title", value="Prepare me for tomorrow")
    description = st.text_area(
        "Initial request", value="Prepare me for tomorrow from my notes."
    )
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
            st.checkbox(
                f"[{question.category}] {question.question}",
                value=question.blocking,
                disabled=True,
            )


def _render_clarification_tab() -> None:
    st.subheader("Answer Questions")
    st.write(
        "Markdown answer ingestion is implemented in CLI as deterministic "
        "rescore scaffolding."
    )
    uploaded = st.file_uploader("Answers markdown", type=["md", "txt"])
    if uploaded is not None:
        st.text_area("Preview", uploaded.read().decode("utf-8"), height=200)


def _render_models_tab(mode: str, unlocked: bool) -> None:
    st.subheader("Local model administration")
    st.caption(
        "Load, unload, and quick-test local Ollama models. This is not a chat "
        "interface — use Open WebUI at http://localhost:3000 for conversations."
    )

    if not ollama_admin.ollama_available():
        st.error(
            "Ollama is not reachable at the configured base URL. Start it with "
            "`brew services start ollama` and refresh."
        )
        return

    gate_open = mode.upper() != "DAY_MODE" or unlocked
    if not gate_open:
        st.warning(
            "Strict DAY_MODE: load and quick-test actions are blocked. Run "
            "`bash scripts/day_unlock.sh \"reason\"` to enable them, or wait "
            "for NIGHT_MODE."
        )

    st.markdown("### Currently loaded (in VRAM)")
    try:
        loaded = ollama_admin.list_loaded_models()
    except ollama_admin.OllamaUnavailable as exc:
        st.error(f"Ollama error: {exc}")
        loaded = []
    if loaded:
        for entry in loaded:
            cols = st.columns([4, 2, 2, 2])
            cols[0].write(f"**{entry['name']}**")
            cols[1].write(entry["size_human"])
            cols[2].write(entry.get("expires_at") or "—")
            if cols[3].button("Unload", key=f"unload-{entry['name']}"):
                try:
                    ollama_admin.unload_model(entry["name"])
                    st.success(f"Unloaded {entry['name']}")
                    st.rerun()
                except ollama_admin.OllamaUnavailable as exc:
                    st.error(f"Failed to unload: {exc}")
    else:
        st.write("Nothing loaded. VRAM is idle.")

    st.markdown("### Pulled models (on disk)")
    try:
        pulled = ollama_admin.list_pulled_models()
    except ollama_admin.OllamaUnavailable as exc:
        st.error(f"Ollama error: {exc}")
        pulled = []
    if not pulled:
        st.info(
            "No models on disk. Pull from the terminal: `bash scripts/pull_models.sh`."
        )
    else:
        mapping = ollama_admin.tag_to_group_mapping()
        for entry in pulled:
            cols = st.columns([4, 2, 2, 2])
            cols[0].write(f"**{entry['name']}**")
            cols[0].caption(
                f"group: {mapping.get(entry['name'], 'local-main (fallback)')}"
            )
            cols[1].write(entry["size_human"])
            cols[2].write(str(entry.get("modified_at") or "—"))
            if cols[3].button("Load", key=f"load-{entry['name']}", disabled=not gate_open):
                try:
                    with st.spinner(f"Loading {entry['name']} into VRAM…"):
                        ollama_admin.load_model(entry["name"], mode=mode)
                    st.success(
                        f"Loaded {entry['name']} (keep-alive 30m default)"
                    )
                    st.rerun()
                except SafetyError as exc:
                    st.error(f"Blocked by safety gate: {exc}")
                except ollama_admin.OllamaUnavailable as exc:
                    st.error(f"Ollama error: {exc}")

    st.markdown("### Quick test prompt")
    test_options = [entry["name"] for entry in loaded] or [
        entry["name"] for entry in pulled
    ]
    if not test_options:
        st.write("No models available to test.")
        return

    selected = st.selectbox("Model", options=test_options, key="test-model-select")
    prompt = st.text_area(
        "Prompt", value="Say hi in one short sentence.", key="test-model-prompt"
    )
    if st.button(
        "Send",
        type="primary",
        key="test-model-send",
        disabled=not gate_open or not prompt.strip(),
    ):
        try:
            with st.spinner("Running…"):
                response = ollama_admin.quick_prompt(selected, prompt, mode=mode)
            st.markdown("**Response**")
            st.code(response or "(empty response)")
        except SafetyError as exc:
            st.error(f"Blocked by safety gate: {exc}")
        except ollama_admin.OllamaUnavailable as exc:
            st.error(f"Ollama error: {exc}")


def _render_schedule_tab(cfg) -> None:
    st.subheader("Day / night schedule")
    st.caption(
        "These times define the day and night windows. They drive the launchd "
        "plist generated by `scripts/create_launchd_plist.sh`. Editing them "
        "does NOT auto-flip `LOCALAI_MODE` — that remains an explicit gesture."
    )

    auto = auto_execution_status()
    cols = st.columns(3)
    cols[0].metric(
        "Project plist",
        "present" if auto["project_plist_present"] else "missing",
    )
    cols[1].metric(
        "Installed in LaunchAgents",
        "yes" if auto["installed_in_launch_agents"] else "no",
    )
    cols[2].metric(
        "Loaded in launchctl",
        "yes (auto-run armed)" if auto["loaded_in_launchctl"] else "no (off)",
    )

    with st.form("schedule-form"):
        day_start = st.text_input("day_mode_start (HH:MM)", value=cfg.day_mode_start)
        night_start = st.text_input(
            "night_mode_start (HH:MM)", value=cfg.night_mode_start
        )
        night_end = st.text_input("night_mode_end (HH:MM)", value=cfg.night_mode_end)
        submitted = st.form_submit_button("Save to config/assistant.yaml")
        if submitted:
            try:
                update_assistant_config(
                    {
                        "day_mode_start": day_start.strip(),
                        "night_mode_start": night_start.strip(),
                        "night_mode_end": night_end.strip(),
                    }
                )
                st.success(
                    "Updated. If the nightly plist is installed, regenerate "
                    "it so the schedule takes effect: "
                    "`bash scripts/create_launchd_plist.sh` (then reload it "
                    "via launchctl if you've installed it)."
                )
                st.rerun()
            except ConfigEditError as exc:
                st.error(str(exc))

    if auto["installed_in_launch_agents"]:
        st.warning(
            "The plist installed in `~/Library/LaunchAgents` may be out of "
            "date relative to these times. Regenerate and reload:\n\n"
            "1. `LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh`\n"
            "2. `launchctl unload ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist`\n"
            "3. `launchctl load ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist`"
        )
    else:
        st.info(
            "No launchd job installed. Auto-execution is OFF. To arm it, see "
            "[docs/auto_execution.md](docs/auto_execution.md)."
        )


def _render_execution_tab() -> None:
    st.subheader("Execution plan")
    st.json(describe_execution_scaffold())
    st.button("Pause", disabled=True)
    st.button("Resume", disabled=True)
    st.caption(
        "Pause/resume database statuses exist; full UI action handling is "
        "scaffolded for v2."
    )


def _render_artifacts_tab(cfg) -> None:
    st.subheader("Output artifacts")
    output_root = Path(cfg.output_dir)
    if output_root.exists():
        files = sorted(
            str(path) for path in output_root.rglob("*") if path.is_file()
        )
        st.write(files or "No output artifacts yet.")
    else:
        st.write("Output directory does not exist yet. Run scripts/install_core.sh.")


def main() -> None:
    cfg = load_assistant_config()
    st.title("Local AI Orchestrator")
    st.caption("Local-first, clarification-driven work orchestration. v1 scaffold.")

    mode, unlocked = _render_header(cfg)

    tab_labels = [
        "Dashboard",
        "Create Work Packet",
        "Clarification",
        "Models",
        "Schedule",
        "Execution",
        "Artifacts",
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_dashboard_tab()
    with tabs[1]:
        _render_create_packet_tab()
    with tabs[2]:
        _render_clarification_tab()
    with tabs[3]:
        _render_models_tab(mode, unlocked)
    with tabs[4]:
        _render_schedule_tab(cfg)
    with tabs[5]:
        _render_execution_tab()
    with tabs[6]:
        _render_artifacts_tab(cfg)


if __name__ == "__main__":
    main()
