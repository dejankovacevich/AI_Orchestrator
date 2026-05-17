"""Build the System Guide and Onboarding PDFs from in-script content.

Regenerate after any architecture change with:

    .venv/bin/python scripts/build_pdfs.py

Both PDFs are written to ``docs/`` and overwrite previous versions.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"


# ---------------------------------------------------------------------------
# Style sheet
# ---------------------------------------------------------------------------

def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["TitleBig"] = ParagraphStyle(
        "TitleBig",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=38,
        textColor=colors.HexColor("#111111"),
        alignment=TA_CENTER,
        spaceAfter=18,
    )
    styles["SubtitleBig"] = ParagraphStyle(
        "SubtitleBig",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#444444"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["CoverMeta"] = ParagraphStyle(
        "CoverMeta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["H1"] = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0a3d62"),
        spaceBefore=18,
        spaceAfter=10,
    )
    styles["H2"] = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0a3d62"),
        spaceBefore=12,
        spaceAfter=6,
    )
    styles["H3"] = ParagraphStyle(
        "H3",
        parent=base["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=4,
    )
    styles["Body"] = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=8,
        alignment=TA_LEFT,
    )
    styles["Bullet"] = ParagraphStyle(
        "Bullet",
        parent=styles["Body"],
        leftIndent=14,
        bulletIndent=2,
        spaceAfter=3,
    )
    styles["Code"] = ParagraphStyle(
        "Code",
        parent=base["Code"],
        fontName="Courier",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1a1a1a"),
        backColor=colors.HexColor("#f4f4f4"),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=4,
        spaceAfter=8,
        borderColor=colors.HexColor("#dddddd"),
        borderWidth=0.5,
        borderPadding=6,
    )
    styles["Caption"] = ParagraphStyle(
        "Caption",
        parent=styles["Body"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#666666"),
        spaceAfter=10,
    )
    styles["Warn"] = ParagraphStyle(
        "Warn",
        parent=styles["Body"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#7c1a1a"),
        backColor=colors.HexColor("#fdecea"),
        borderColor=colors.HexColor("#f5b7b1"),
        borderWidth=0.5,
        borderPadding=8,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=10,
    )
    styles["Hint"] = ParagraphStyle(
        "Hint",
        parent=styles["Body"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1d4f72"),
        backColor=colors.HexColor("#eaf4fb"),
        borderColor=colors.HexColor("#aed6f1"),
        borderWidth=0.5,
        borderPadding=8,
        leftIndent=4,
        rightIndent=4,
        spaceAfter=10,
    )
    return styles


# ---------------------------------------------------------------------------
# Document scaffolding
# ---------------------------------------------------------------------------

def _on_page(footer_text: str):
    def _handler(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#888888"))
        canvas_obj.drawString(0.75 * inch, 0.45 * inch, footer_text)
        canvas_obj.drawRightString(
            LETTER[0] - 0.75 * inch,
            0.45 * inch,
            f"Page {doc.page}",
        )
        canvas_obj.restoreState()

    return _handler


def build_document(out_path: Path, story: list, footer_text: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=footer_text,
        author="Local AI Orchestrator",
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    template = PageTemplate(id="default", frames=[frame], onPage=_on_page(footer_text))
    doc.addPageTemplates([template])
    doc.build(story)


# ---------------------------------------------------------------------------
# Reusable helpers
# ---------------------------------------------------------------------------

def p(styles, name, text):
    return Paragraph(text, styles[name])


def bullets(styles, items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{item}", styles["Bullet"]) for item in items]


def code_block(styles, text):
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(" ", "&nbsp;")
    )
    lines = escaped.split("\n")
    return Paragraph("<br/>".join(lines), styles["Code"])


def section_table(rows, col_widths=None, header=True):
    style_commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style_commands.append(
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3d62"))
        )
        style_commands.append(("TEXTCOLOR", (0, 0), (-1, 0), colors.white))
        style_commands.append(("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"))
    table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    table.setStyle(TableStyle(style_commands))
    return table


# ---------------------------------------------------------------------------
# System Guide content
# ---------------------------------------------------------------------------

def build_system_guide(styles) -> list:
    story = []

    # --- Cover ---------------------------------------------------------
    story += [
        Spacer(1, 2.2 * inch),
        p(styles, "TitleBig", "Local AI Orchestrator"),
        p(styles, "SubtitleBig", "System Guide and Architecture"),
        Spacer(1, 0.4 * inch),
        p(styles, "CoverMeta", "Private, local-first executive work orchestration on macOS"),
        p(styles, "CoverMeta", "v1 scaffold &mdash; clarification implemented, execution graph in progress"),
        Spacer(1, 0.6 * inch),
        p(styles, "CoverMeta", f"Generated: {date.today().isoformat()}"),
        PageBreak(),
    ]

    # --- Section 1: What this is --------------------------------------
    story += [
        p(styles, "H1", "1. What this system is"),
        p(
            styles,
            "Body",
            "A private, local-first AI work orchestrator running entirely on your Mac. "
            "It is <b>not a chatbot</b>. It is a system that takes vague work requests "
            "(\"prepare me for tomorrow,\" \"summarize the board notes\"), turns them into "
            "structured <i>work packets</i>, asks you strong clarifying questions until "
            "the request is concrete and safe to execute, scores readiness on nine "
            "dimensions, and &mdash; eventually &mdash; executes the well-scoped work "
            "overnight using local Ollama models.",
        ),
        p(
            styles,
            "Body",
            "The design intent is two-fold:",
        ),
        *bullets(
            styles,
            [
                "<b>Clarify before doing anything heavy.</b> Vague input never produces low-quality output; it produces questions.",
                "<b>Keep everything on your machine.</b> No cloud calls unless every one of six policy gates passes. No external sends in v1. No service exposure beyond localhost.",
            ],
        ),
        p(styles, "H2", "What it is NOT"),
        *bullets(
            styles,
            [
                "Not a chatbot &mdash; for conversations, use Open WebUI at http://localhost:3000.",
                "Not multi-user &mdash; single Mac, single operator.",
                "Not for sending anything externally &mdash; email, Slack, calendar invites, GitHub PRs are blocked at the safety layer in v1.",
                "Not auto-cloud &mdash; Claude requires six gates; the day-unlock switch does not open them.",
                "Not running models in the background all day &mdash; DAY_MODE blocks every local-* model group unless you deliberately unlock.",
            ],
        ),
        PageBreak(),
    ]

    # --- Section 2: Mental model --------------------------------------
    story += [
        p(styles, "H1", "2. Mental model"),
        p(
            styles,
            "Body",
            "The system is built around one loop, repeated as often as you have work:",
        ),
        section_table(
            [
                ["Stage", "What happens", "Who acts"],
                ["1. Capture", "You give it a title and a vague description.", "You"],
                ["2. Clarify", "The system builds an initial work packet, scores readiness on 9 dimensions, and generates up to 7 strong questions where gaps are.", "System"],
                ["3. Answer", "You respond in a markdown file or via the panel.", "You"],
                ["4. Re-score", "The system parses your answers, rescores, and either marks the packet READY_FOR_OVERNIGHT (≥ 0.85) or generates more questions.", "System"],
                ["5. Execute", "Overnight, in NIGHT_MODE, the execution graph reads sources, calls local models through the safety gate, evaluates output, writes artifacts.", "System (scaffolded)"],
                ["6. Review", "You read the output in ~/LocalAI/output/<date>/ and the Obsidian vault; approve memory candidates for the long-term review queue.", "You"],
            ],
            col_widths=[0.9 * inch, 4.4 * inch, 1.2 * inch],
        ),
        Spacer(1, 0.2 * inch),
        p(styles, "H2", "Readiness scoring (nine dimensions)"),
        section_table(
            [
                ["Dimension", "Weight", "What it captures"],
                ["objective", "0.18", "Is the desired outcome explicit?"],
                ["output_format", "0.14", "Is the output shape specified?"],
                ["sources", "0.14", "Which folders/files are in scope?"],
                ["privacy_cloud_policy", "0.14", "Is cloud explicitly allowed or forbidden?"],
                ["quality_threshold", "0.12", "What quality bar to optimize for?"],
                ["audience", "0.10", "Who is the output for?"],
                ["assumption_policy", "0.08", "May the system infer when uncertain?"],
                ["escalation_policy", "0.06", "When should it stop and ask?"],
                ["success_criteria", "0.04", "What makes the work done?"],
            ],
            col_widths=[1.7 * inch, 0.7 * inch, 4.1 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "Thresholds: &ge; 0.90 = READY_HIGH_CONFIDENCE; &ge; 0.85 = READY_FOR_OVERNIGHT; "
            "0.65&ndash;0.84 = NEEDS_CLARIFICATION; &lt; 0.65 = UNDERDEFINED. "
            "High-stakes packets (board, CEO, legal, investor) auto-detect and require &ge; 0.90.",
        ),
        PageBreak(),
    ]

    # --- Section 3: Architecture --------------------------------------
    story += [
        p(styles, "H1", "3. Architecture at a glance"),
        p(
            styles,
            "Body",
            "Nine components, all running locally, talking to each other on 127.0.0.1.",
        ),
        code_block(
            styles,
            """+-----------------------------------------------------------------+
|                      You (browser + terminal)                   |
+-----------------------------------------------------------------+
                |                              |
                v                              v
+---------------------------+    +-----------------------------+
|  Streamlit control panel  |    |   CLI (assistant_core.cli)  |
|  http://127.0.0.1:8501    |    |   bash scripts/*.sh         |
+---------------------------+    +-----------------------------+
                |                              |
                +--------------+---------------+
                               v
                +-----------------------------+
                |   assistant_core (Python)   |
                |  clarification + safety +   |
                |  storage + execution graph  |
                +-----------------------------+
                  |        |       |       |
                  v        v       v       v
        +--------+ +-------+ +----------+ +----------------+
        |Postgres| |Temporal| |  Ollama  | | Obsidian vault |
        | :5432  | | :7233  | |  :11434  | | filesystem     |
        +--------+ +-------+ +----------+ +----------------+
                                |
                                v
                        +----------------+
                        |    LiteLLM     |
                        |    :4000       |
                        +----------------+
                                |
                                v
                         +------------+
                         | Open WebUI |
                         |   :3000    |
                         +------------+
""",
        ),
        p(styles, "Caption", "Solid lines: required. LiteLLM and Open WebUI are optional in v1 &mdash; the panel can talk to Ollama directly through assistant_core.llm.ollama_admin."),
        PageBreak(),
    ]

    # --- Section 4: Component-by-component ----------------------------
    story += [
        p(styles, "H1", "4. Components: what each does and why"),
    ]

    components = [
        (
            "Python orchestrator (assistant_core)",
            "The brain. Pure Python, no framework.",
            (
                "Holds the deterministic clarification logic, the safety gates, the work-packet "
                "schema, the storage layer, and the (scaffolded) execution graph. Has no opinion "
                "about UI &mdash; both the Streamlit panel and the CLI call into it. Tested "
                "in isolation via pytest."
            ),
            (
                "Pure Python keeps the core auditable, easy to reason about, easy to test. "
                "Pydantic for schemas (validation at type boundaries). YAML for human-editable "
                "config. PsycoPG for direct Postgres I/O without an ORM layer that hides intent."
            ),
            "assistant_core/{clarification,llm,memory,execution,temporal_app}/",
        ),
        (
            "Streamlit control panel",
            "Local web UI on :8501.",
            (
                "Renders the status strip (mode, day unlock, services up/down), seven tabs "
                "(Dashboard, Create Work Packet, Clarification, Models, Schedule, Execution, "
                "Artifacts), and is the only UI surface for safe model load/unload."
            ),
            (
                "Streamlit lets us iterate in pure Python without writing a frontend. Tabs are "
                "stateless re-renders &mdash; safe by construction. Editing config or invoking "
                "Ollama always goes through assistant_core, never bypasses the gate."
            ),
            "app/control_panel.py",
        ),
        (
            "PostgreSQL",
            "Operational state store.",
            (
                "Holds work_packets, clarification_questions, execution_runs, model_calls, "
                "evaluations, artifacts, memory_candidates. Migrated automatically on first "
                "container start (db/migrations/001_init.sql is mounted into Postgres' init dir)."
            ),
            (
                "Postgres because we want durable, queryable state with relational integrity "
                "across the seven tables &mdash; work packets relate to questions, runs, model "
                "calls, and evaluations. JSON columns for cloud/source/output policy let us "
                "evolve without migrations."
            ),
            "db/migrations/001_init.sql + assistant_core/storage.py",
        ),
        (
            "Temporal",
            "Durable workflow engine on :7233 (UI on :8233).",
            (
                "Manages overnight workflows: clarification, execution, manual resume. Survives "
                "process crashes; can pause and resume long-running work. The worker process "
                "(scripts/start_temporal_worker.sh) executes activities defined in "
                "assistant_core/temporal_app/."
            ),
            (
                "Overnight work runs for hours, may hit transient model failures, and needs "
                "to be resumable. Temporal handles retries, timeouts, idempotency, and audit "
                "trail out of the box. Cron + bash would be fragile at this scale."
            ),
            "assistant_core/temporal_app/{workflows,activities,worker,client}.py",
        ),
        (
            "Ollama",
            "Local model runtime on :11434.",
            (
                "Pulls models to ~/.ollama/models on disk, loads them into Metal VRAM on demand, "
                "serves inference via HTTP. The orchestrator never bypasses Ollama for local "
                "model calls &mdash; it always goes through this daemon."
            ),
            (
                "Ollama is the de facto local-model runtime on macOS Metal. Native Apple Silicon "
                "support, good keep-alive semantics, simple HTTP API, library of pre-quantized "
                "models. Lighter and easier to operate than running llama.cpp directly."
            ),
            "config/models.yaml maps groups -> Ollama tags",
        ),
        (
            "LiteLLM",
            "Model router and gateway on :4000.",
            (
                "Translates a model-group name (local-main, local-coder, etc.) into the right "
                "Ollama tag or cloud endpoint. Configured with local-only fallbacks; cloud "
                "is intentionally not chained behind local."
            ),
            (
                "LiteLLM gives us a single OpenAI-style API for code that wants to swap models "
                "later, with fallback rules expressed declaratively. We keep the cloud route in "
                "the config but disable cloud at the safety layer so no blind escalation can "
                "happen."
            ),
            "config/litellm.yaml.example + assistant_core/llm/litellm_client.py",
        ),
        (
            "Open WebUI",
            "ChatGPT-style chat against local models, on :3000.",
            (
                "A separate tool that lives next to the orchestrator. Talks directly to Ollama. "
                "Provides conversational access when you want it; the orchestrator deliberately "
                "does not offer chat."
            ),
            (
                "Sometimes you want to chat with a model. Open WebUI is a polished, mature tool "
                "for that. Co-installing it via docker-compose lets you have both surfaces."
            ),
            "docker-compose.yml &mdash; service: open-webui",
        ),
        (
            "Obsidian vault",
            "Human-readable long-term notes.",
            (
                "The system writes outputs and memory candidates into ~/Obsidian/LocalAI-ChiefOfStaff/. "
                "Daily briefs, work packets, decisions, meeting notes, memory review queue. "
                "You read and curate these directly in Obsidian."
            ),
            (
                "Obsidian's plaintext markdown vault is durable, indexable, and yours. No "
                "lock-in. The orchestrator writes; you review. The vault becomes your "
                "long-term knowledge layer."
            ),
            "~/Obsidian/LocalAI-ChiefOfStaff/{01_Daily_Briefs, 02_Work_Packets, ...}",
        ),
        (
            "Chroma (vector store)",
            "Local semantic retrieval target.",
            (
                "Scaffolded but not yet wired. Will hold embeddings of selected outputs and "
                "vault content for retrieval-augmented work."
            ),
            (
                "Chroma is simple, file-backed, no separate daemon. Right tradeoff for a "
                "single-user local system. Persistent client at ~/LocalAI/state/chroma."
            ),
            "assistant_core/memory/vector_store.py",
        ),
        (
            "Docker Compose",
            "Service orchestration for Postgres / Temporal / Open WebUI.",
            (
                "One file, four services. Containers expose ports only on 127.0.0.1. Named "
                "volumes persist data across container recreates. The migration SQL is "
                "mounted into Postgres' init directory so the schema is created on first run."
            ),
            (
                "Docker keeps these three services consistent across machines without "
                "ceremony. They're stateful, multi-process, and have non-trivial init &mdash; "
                "containers handle that cleanly."
            ),
            "docker-compose.yml",
        ),
    ]

    for name, tagline, what, why, where in components:
        story += [
            KeepTogether(
                [
                    p(styles, "H2", name),
                    p(styles, "Caption", tagline),
                    p(styles, "H3", "What it does"),
                    p(styles, "Body", what),
                    p(styles, "H3", "Why this tool"),
                    p(styles, "Body", why),
                    p(styles, "H3", "Where to look"),
                    p(styles, "Code", where.replace("<", "&lt;").replace(">", "&gt;")),
                ]
            ),
        ]

    story += [PageBreak()]

    # --- Section 5: Safety system ------------------------------------
    story += [
        p(styles, "H1", "5. The safety system in depth"),
        p(
            styles,
            "Body",
            "The orchestrator is built around the assumption that you do not want the system "
            "to make decisions you wouldn't make yourself. Every model call, every cloud "
            "fallback, every external write passes through a deterministic gate in "
            "assistant_core/safety.py. Gates are written as <i>fail-closed</i> &mdash; an "
            "unknown tag, an empty env var, or a missing flag all default to <b>blocked</b>.",
        ),
        p(styles, "H2", "The five gate functions"),
        section_table(
            [
                ["Function", "What it gates"],
                ["assert_cloud_allowed", "Six checks before any Claude call: cloud_fallback_enabled, work_packet_cloud_allowed, file inside cloud_review or marked .cloud., ANTHROPIC_API_KEY present, high-stakes or local-quality-gate-failed, daily budget remaining."],
                ["assert_no_external_write", "Always blocks in v1. Used at any future email/Slack/API boundary."],
                ["assert_original_file_write_allowed", "Refuses writes outside the configured roots (output, archive, logs, work_packets, vault)."],
                ["assert_heavy_execution_allowed", "Refuses model execution in DAY_MODE unless day unlock is active or manual_override=True."],
                ["assert_model_allowed", "Top-level entry point. Rejects cloud-claude-opus outright; then delegates local groups to assert_heavy_execution_allowed."],
            ],
            col_widths=[2.2 * inch, 4.3 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "DAY_MODE / NIGHT_MODE / MANUAL_RESUME"),
        p(
            styles,
            "Body",
            "Mode is a single env var, LOCALAI_MODE. The default is DAY_MODE. The overnight "
            "runner refuses to start unless NIGHT_MODE is set; the launchd plist sets it "
            "automatically when it fires. The third value, MANUAL_RESUME, is reserved for "
            "user-driven re-runs of previously paused workflows.",
        ),
        p(styles, "H2", "The day-unlock switch"),
        p(
            styles,
            "Body",
            "DAY_MODE blocks all four local-* model groups (local-main, local-secondary, "
            "local-coder, local-reasoner). To deliberately work with models during the day, "
            "the day-unlock switch flips a single boolean. Two channels:",
        ),
        *bullets(
            styles,
            [
                "<b>Sentinel file</b> &mdash; ~/LocalAI/state/day_unlock.flag. Created by scripts/day_unlock.sh with a timestamp, hostname, and reason. Persists across terminal closes and reboots.",
                "<b>Environment variable</b> &mdash; LOCALAI_DAY_UNLOCK=true. Per-shell, ephemeral.",
            ],
        ),
        Paragraph(
            "Either being on opens the gate. Cloud and external-write gates are <b>not</b> "
            "affected. The Streamlit panel renders a red banner with the flag contents while "
            "unlock is ACTIVE so the state is impossible to miss.",
            styles["Body"],
        ),
        p(styles, "Hint",
          "Full design rationale: docs/day_unlock.md. Locking again: bash scripts/day_lock.sh."),
        PageBreak(),
    ]

    # --- Section 6: Auto-execution -----------------------------------
    story += [
        p(styles, "H1", "6. Auto-execution (launchd nightly job)"),
        p(
            styles,
            "Body",
            "Default state: <b>OFF</b>. The orchestrator can be scheduled to run "
            "overnight via macOS launchd, but the plist is never armed automatically. "
            "Arming requires three deliberate steps in the terminal.",
        ),
        p(styles, "H2", "The four states"),
        section_table(
            [
                ["Project plist", "Installed in LaunchAgents", "Loaded in launchctl", "State"],
                ["no", "no", "no", "fully off, nothing installed"],
                ["yes", "no", "no", "off (default after install_core)"],
                ["yes", "yes", "no", "off, installed but not loaded"],
                ["yes", "yes", "yes", "ARMED, will run nightly at night_mode_start"],
            ],
            col_widths=[0.95 * inch, 1.5 * inch, 1.3 * inch, 2.4 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Arming (three deliberate steps)"),
        code_block(
            styles,
            "# 1. Verify the configured time is what you want.\n"
            "#    Edit it in the panel's Schedule tab or in config/assistant.yaml.\n"
            "\n"
            "# 2. Regenerate the plist with that time:\n"
            "bash scripts/create_launchd_plist.sh\n"
            "\n"
            "# 3. Install into LaunchAgents and load:\n"
            "LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh\n"
            "launchctl load ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist",
        ),
        p(styles, "H2", "Disarming"),
        code_block(
            styles,
            "launchctl unload ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist\n"
            "# Optionally:\n"
            "rm ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist",
        ),
        p(styles, "Hint", "Full design rationale: docs/auto_execution.md."),
        PageBreak(),
    ]

    # --- Section 7: Data flow -----------------------------------------
    story += [
        p(styles, "H1", "7. End-to-end data flow"),
        p(
            styles,
            "Body",
            "From a vague request to overnight output, in nine steps:",
        ),
        section_table(
            [
                ["Step", "What happens", "Storage"],
                ["1", "You: bash scripts/create_work_packet.sh \"Title\" \"Description\"", "&mdash;"],
                ["2", "build_initial_work_packet builds a WorkPacket pydantic model.", "in memory"],
                ["3", "score_readiness assigns 0/1 per dimension, computes weighted score.", "in memory"],
                ["4", "generate_questions emits up to 7 ranked clarification questions.", "in memory"],
                ["5", "create_work_packet + save_questions write the row and questions to Postgres.", "Postgres: work_packets, clarification_questions"],
                ["6", "You answer in a markdown file. bash scripts/answer_questions.sh PARSES.", "&mdash;"],
                ["7", "update_packet_from_answers extracts fields. Rescore. If READY, mark status.", "Postgres: update work_packets"],
                ["8", "Overnight runner (manual or via launchd at NIGHT_MODE) finds READY packets, submits Temporal workflows.", "Postgres: execution_runs"],
                ["9", "Workflow body (scaffolded) reads sources, calls models, evaluates, writes outputs to ~/LocalAI/output/<date>/ and Obsidian vault.", "Filesystem + Postgres: artifacts, model_calls, evaluations"],
            ],
            col_widths=[0.45 * inch, 3.8 * inch, 2.25 * inch],
        ),
        Spacer(1, 0.2 * inch),
        p(styles, "Warn",
          "Step 9 is still scaffolded as of this writing. The workflow is wired and the "
          "Temporal worker accepts the submission, but the activity body returns a "
          "placeholder dict instead of running the 18-step pipeline. That is the next "
          "feature-work chunk."),
        PageBreak(),
    ]

    # --- Section 8: Implemented vs scaffolded ------------------------
    story += [
        p(styles, "H1", "8. What's implemented vs scaffolded"),
        section_table(
            [
                ["Capability", "State", "Notes"],
                ["Deterministic clarification flow", "Implemented", "Work packet builder, 9-dim readiness, question generator. 100% test-covered."],
                ["Postgres storage layer", "Implemented", "7 tables, schema migration applied, CRUD for packets/questions/runs/calls."],
                ["Safety gates (5 functions)", "Implemented", "Tests parameterized over every local-* group and DAY/NIGHT/override case."],
                ["Day-unlock switch", "Implemented", "File + env channel, visible banner, fail-closed. docs/day_unlock.md."],
                ["Streamlit control panel", "Implemented", "Header strip, 7 tabs, Models tab, Schedule tab, config editor."],
                ["Models tab (load/unload/test)", "Implemented", "Gate-checked. CLI workflow: Load -> Quick test -> Unload."],
                ["Schedule tab (time editing)", "Implemented", "Atomic config writes, validation, launchd-status mirror."],
                ["Ollama integration", "Implemented", "Pull, list, load, unload, generate. ollama_admin.py."],
                ["Temporal worker + workflow definitions", "Implemented (skeleton)", "Workflows defined, activities defined, but bodies return placeholder dicts for execution."],
                ["LiteLLM routing", "Implemented (config only)", "Started via scripts/start_litellm.sh. Used by future model-call code paths."],
                ["Launchd plist generation", "Implemented", "Reads night_mode_start from config; arming stays a manual step."],
                ["Overnight execution graph (18 steps)", "Scaffolded", "EXECUTION_STEPS list exists. Activity body returns a stub. Next major chunk of work."],
                ["Quality-gated local retry loop", "Scaffolded", "evaluators.py exists with deterministic fallback. Retry orchestration not wired."],
                ["Pause/resume UI", "Scaffolded", "Buttons disabled in panel. DB statuses (PAUSED, RESUME_REQUESTED) exist."],
                ["Semantic memory indexing", "Scaffolded", "Chroma client exists. No indexing workflow yet."],
                ["Claude cloud-review path", "Scaffolded", "Gates implemented; no caller wired."],
                ["Drafted messages", "Scaffolded", "Output template exists; nothing fills it yet."],
            ],
            col_widths=[2.5 * inch, 1.4 * inch, 2.6 * inch],
        ),
        PageBreak(),
    ]

    # --- Section 9: File system layout -------------------------------
    story += [
        p(styles, "H1", "9. File system layout"),
        p(styles, "H2", "Project repository"),
        code_block(
            styles,
            """local-ai-orchestrator/
  AGENTS.md              rules for human/AI editors
  ONBOARDING.md          practical usage guide (separate PDF)
  README.md              setup + ports + safety summary
  app/control_panel.py   Streamlit UI
  assistant_core/        Python package
    clarification/       work packet builder, readiness, questions
    execution/           18-step pipeline (scaffolded)
    llm/                 ollama_admin, litellm_client, model_policy
    memory/              Obsidian + Chroma writers
    temporal_app/        worker, workflows, activities
    safety.py            5 gate functions
    schemas.py           pydantic models for the whole system
    storage.py           Postgres CRUD
    config.py            yaml config loader
    config_writer.py     atomic config edits
    scheduler_status.py  launchd + service health
  config/
    assistant.yaml       day/night times, thresholds, paths
    models.yaml          group -> Ollama tag mapping
    memory.yaml          vector store settings
    litellm.yaml         LiteLLM router config (gitignored copy)
  db/migrations/         SQL applied on Postgres first boot
  docs/                  deep-dive design docs
  examples/              sample answers, sample packet
  launchd/               generated plist (gitignored)
  scripts/               bash entrypoints for every operation
  tests/                 pytest, isolated from real state
  docker-compose.yml     postgres + temporal + temporal-ui + open-webui""",
        ),
        p(styles, "H2", "Data directories (outside the repo)"),
        code_block(
            styles,
            """~/LocalAI/
  inbox/
    notes/         your input notes
    transcripts/   call/meeting transcripts
    docs/          documents
    csv/           tabular sources
    cloud_review/  files marked for cloud review (Claude gate path)
  output/<date>/   generated artifacts (briefs, priorities, etc.)
  archive/         processed inputs
  logs/            runtime logs (incl. launchd stdout/stderr)
  state/           operational state (incl. day_unlock.flag)
  work_packets/    packet-specific files

~/Obsidian/LocalAI-ChiefOfStaff/
  00_Inbox/Memory_Review/   memory candidates awaiting your approval
  01_Daily_Briefs/          morning briefs
  02_Work_Packets/          packet notes
  03_Projects/              project pages
  04_Meetings/              meeting notes
  05_Decisions/             logged decisions
  06_Stakeholders/          people pages
  07_Playbooks/             reusable procedures
  08_Prompts/               curated prompts
  09_System_Logs_Summaries/ run summaries
  99_Archive/               historical""",
        ),
        PageBreak(),
    ]

    # --- Section 10: Database schema ---------------------------------
    story += [
        p(styles, "H1", "10. Database schema"),
        p(styles, "Body", "Seven tables in the localai database, all created from db/migrations/001_init.sql:"),
        section_table(
            [
                ["Table", "Purpose"],
                ["work_packets", "One row per packet: title, objective, status, readiness, policies (jsonb), raw and structured request."],
                ["clarification_questions", "Per-packet questions across rounds; each can be answered or unanswered."],
                ["execution_runs", "One row per overnight invocation, with Temporal workflow id, mode, start/end timestamps."],
                ["model_calls", "Audit row per local-model or cloud call: task type, group, actual tag, sizes, success/error."],
                ["evaluations", "Quality / grounding / completeness / contradiction scores from the evaluator, with recommended next step."],
                ["artifacts", "File-level pointers to generated outputs and their Obsidian copies."],
                ["memory_candidates", "Items extracted from outputs as candidates for long-term memory; require user approval."],
            ],
            col_widths=[1.8 * inch, 4.7 * inch],
        ),
        Spacer(1, 0.2 * inch),
        p(styles, "Hint",
          "All tables use UUID primary keys. JSONB columns on work_packets allow policy "
          "evolution without migrations. Foreign keys enforce relational integrity. "
          "Indexes cover status, work_packet_id joins, and timestamp ranges."),
        PageBreak(),
    ]

    # --- Section 11: Configuration -----------------------------------
    story += [
        p(styles, "H1", "11. Configuration"),
        p(styles, "Body", "Three YAML files in config/, plus a small set of env vars."),
        p(styles, "H2", "config/assistant.yaml &mdash; main tunables"),
        section_table(
            [
                ["Key", "Default", "Meaning"],
                ["day_mode_start", "07:30", "When the day window begins (editable in Schedule tab)."],
                ["night_mode_start", "01:30", "When night begins; drives the launchd plist."],
                ["night_mode_end", "07:00", "Cutoff for night work."],
                ["clarification_required", "true", "Skip clarification only with explicit override."],
                ["minimum_readiness_for_overnight", "0.85", "Threshold for READY_FOR_OVERNIGHT."],
                ["minimum_readiness_for_high_stakes", "0.90", "Threshold when packet.high_stakes is true."],
                ["cloud_fallback_enabled", "false", "Master switch for cloud. Even with true, six more gates apply."],
                ["daily_cloud_budget_usd", "5.00", "Hard cap on Anthropic spend per day."],
                ["max_local_attempts", "2", "Retry budget through local-main -> local-secondary."],
                ["max_chars_per_chunk", "12000", "Source-file chunking for long inputs."],
                ["temperature, top_p", "0.2 / 0.9", "Conservative sampling defaults for execution."],
            ],
            col_widths=[2.3 * inch, 0.9 * inch, 3.3 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "config/models.yaml &mdash; group to tag"),
        code_block(
            styles,
            "local-main:        qwen3:30b-a3b\n"
            "local-secondary:   llama3.3:70b\n"
            "local-coder:       qwen3-coder:30b\n"
            "local-reasoner:    deepseek-r1:8b\n"
            "cloud-claude-opus: claude-opus-4-7",
        ),
        p(styles, "H2", "Environment variables"),
        section_table(
            [
                ["Variable", "Effect"],
                ["LOCALAI_MODE", "DAY_MODE (default), NIGHT_MODE, or MANUAL_RESUME"],
                ["LOCALAI_DAY_UNLOCK", "Truthy value opens the day gate for this shell only"],
                ["LOCALAI_MANUAL_RESUME", "Lets run_ready_overnight.sh proceed outside NIGHT_MODE"],
                ["LOCALAI_WRITE_LAUNCHD", "Truthy = create_launchd_plist.sh installs into LaunchAgents"],
                ["LOCALAI_POSTGRES_URL", "Override DB connection (defaults to local Docker)"],
                ["ANTHROPIC_API_KEY", "Required for cloud-claude-opus calls (plus 5 other gates)"],
            ],
            col_widths=[2.2 * inch, 4.3 * inch],
        ),
        PageBreak(),
    ]

    # --- Section 12: Glossary ----------------------------------------
    story += [
        p(styles, "H1", "12. Glossary"),
        section_table(
            [
                ["Term", "Definition"],
                ["Work packet", "The orchestrator's unit of work. A structured representation of a request with objective, sources, outputs, policies, success criteria."],
                ["Readiness score", "Weighted sum of nine binary dimension checks, in [0, 1]. Threshold 0.85 to be eligible for overnight execution; 0.90 for high-stakes."],
                ["Clarification round", "One pass of: build packet -> score -> generate questions -> wait for answers."],
                ["DAY_MODE", "Mode in which all local-* model groups are blocked at the safety gate unless day_unlock is active."],
                ["NIGHT_MODE", "Mode in which local model calls are allowed. Required by the overnight runner."],
                ["Day unlock", "An explicit, visible override that lets local models load in DAY_MODE. Implemented as a flag file plus env-var fallback."],
                ["Model group", "A logical role (local-main, local-coder, etc.) that maps to a specific Ollama tag in config/models.yaml. The safety gate operates on groups."],
                ["Keep-alive", "Ollama's per-model VRAM retention timer. Our Load button uses 30m; Quick test uses 5m; Unload sends \"0s\"."],
                ["Cloud-review path", "The Claude Opus route, gated by six policy checks. Files must be in ~/LocalAI/inbox/cloud_review/ or have .cloud. in the name."],
                ["Auto-execution", "The launchd job that runs run_ready_overnight.sh at night_mode_start. Off by default; arming is a deliberate three-step terminal gesture."],
                ["Manual override", "A per-call boolean (manual_override=True) that bypasses the day gate. Used in tests and direct CLI invocations."],
            ],
            col_widths=[1.8 * inch, 4.7 * inch],
        ),
        Spacer(1, 0.25 * inch),
        p(styles, "Caption",
          "End of System Guide. For the practical usage walkthrough, see the companion "
          "Onboarding PDF."),
    ]

    return story


# ---------------------------------------------------------------------------
# Onboarding content
# ---------------------------------------------------------------------------

def build_onboarding(styles) -> list:
    story = []

    # --- Cover ---------------------------------------------------------
    story += [
        Spacer(1, 2.2 * inch),
        p(styles, "TitleBig", "Local AI Orchestrator"),
        p(styles, "SubtitleBig", "Onboarding &mdash; how to use it"),
        Spacer(1, 0.4 * inch),
        p(styles, "CoverMeta",
          "Practical, command-by-command guide. Pair with the System Guide for the why and how."),
        Spacer(1, 0.6 * inch),
        p(styles, "CoverMeta", f"Generated: {date.today().isoformat()}"),
        PageBreak(),
    ]

    # --- Quick reference ---------------------------------------------
    story += [
        p(styles, "H1", "Quick reference"),
        p(styles, "Body",
          "Every common operation, one row. Run all commands from the project root: "
          "<font face=\"Courier\">cd /Users/macbookpro/Projects/local-ai-orchestrator</font>."),
        section_table(
            [
                ["Goal", "Command"],
                ["See system health (Docker, Ollama, ports)", "bash scripts/check_system.sh"],
                ["Start Docker services", "bash scripts/start_services.sh"],
                ["Start Ollama (persistent service)", "brew services start ollama"],
                ["Start the control panel", "bash scripts/start_control_panel.sh"],
                ["Open the panel in browser", "http://127.0.0.1:8501"],
                ["Create a work packet from CLI", 'bash scripts/create_work_packet.sh "Title" "Description"'],
                ["Submit answers to clarification", "bash scripts/answer_questions.sh <id> examples/sample_answers.md"],
                ["Allow local models in the day", 'bash scripts/day_unlock.sh "reason"'],
                ["Lock the day-unlock again", "bash scripts/day_lock.sh"],
                ["Load/unload/test a model in browser", "Panel → Models tab"],
                ["Edit day/night times in browser", "Panel → Schedule tab"],
                ["Verify nothing runs automatically", "launchctl list | grep localai (empty = off)"],
                ["Pull all configured models (~41 GB)", "bash scripts/pull_models.sh"],
                ["Stop Docker services (keep data)", "bash scripts/stop_services.sh"],
                ["Run the full test suite", "bash scripts/run_tests.sh"],
            ],
            col_widths=[3.0 * inch, 3.5 * inch],
        ),
        PageBreak(),
    ]

    # --- Daily start sequence ----------------------------------------
    story += [
        p(styles, "H1", "Daily start sequence"),
        p(styles, "Body",
          "Every time you want to use the system, run these four steps in order. None "
          "of them load models or do heavy work; they just bring services online."),
        code_block(
            styles,
            "cd /Users/macbookpro/Projects/local-ai-orchestrator\n"
            "\n"
            "# 1. Make sure Ollama is running (persistent service)\n"
            "brew services start ollama\n"
            "curl http://localhost:11434/api/tags     # should return JSON\n"
            "\n"
            "# 2. Start Docker services (Postgres, Temporal, Open WebUI)\n"
            "bash scripts/start_services.sh\n"
            "\n"
            "# 3. Confirm everything is up\n"
            "bash scripts/check_system.sh\n"
            "\n"
            "# 4. Start the control panel\n"
            "bash scripts/start_control_panel.sh\n"
            "# then browse to http://127.0.0.1:8501",
        ),
        p(styles, "Hint",
          "All four are safe to re-run. start_services.sh skips already-running containers; "
          "brew services start ollama is a no-op if it's already loaded; start_control_panel.sh "
          "will fail if port 8501 is held by a previous Streamlit (kill it first with "
          "kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t))."),
        PageBreak(),
    ]

    # --- Worked example ----------------------------------------------
    story += [
        p(styles, "H1", "A complete worked example"),
        p(styles, "Body",
          "End-to-end use of the system today, from a vague request to a ready packet. "
          "Execution is still scaffolded; this stops before the night step."),
        p(styles, "H2", "1. Create a vague packet (expect rejection)"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh "Tomorrow prep" \\\n'
            '   "Prepare me for tomorrow from my notes."',
        ),
        p(styles, "Body", "Expected output:"),
        code_block(
            styles,
            "{\n"
            '  "work_packet_id": "abc123...",\n'
            '  "status": "UNDERDEFINED",\n'
            '  "readiness_score": 0.18,\n'
            '  "questions": [\n'
            '    {"category": "objective",     "question": "What exact outcome..."},\n'
            '    {"category": "outputs",       "question": "What output files..."},\n'
            '    {"category": "sources",       "question": "Which folders are..."},\n'
            '    {"category": "privacy/cloud", "question": "Is cloud allowed..."},\n'
            "    ...\n"
            "  ]\n"
            "}",
        ),
        p(styles, "Body",
          "The score is below 0.65 and status is UNDERDEFINED. <b>This is correct.</b> "
          "The system refuses to act until you answer the gating questions."),
        p(styles, "H2", "2. Look at the sample answer format"),
        code_block(styles, "cat examples/sample_answers.md"),
        p(styles, "H2", "3. Edit your own answers or reuse the sample"),
        p(styles, "Body",
          "Write a markdown file with answers. Specific paths under ~/LocalAI/inbox/, "
          "explicit cloud policy, clear quality bar, named audience."),
        p(styles, "H2", "4. Submit the answers"),
        code_block(
            styles,
            "bash scripts/answer_questions.sh abc123... examples/sample_answers.md",
        ),
        p(styles, "Body", "Expected output:"),
        code_block(
            styles,
            "{\n"
            '  "work_packet_id": "abc123...",\n'
            '  "status": "READY_FOR_OVERNIGHT",\n'
            '  "readiness_score": 0.90,\n'
            '  "database": "updated",\n'
            '  "remaining_questions": []\n'
            "}",
        ),
        p(styles, "Body",
          "Status flipped, no remaining questions. The packet is eligible for overnight execution."),
        p(styles, "Warn",
          "Today, the actual overnight execution is scaffolded. Submitting overnight runs "
          "creates an execution_runs row and queues a Temporal workflow that returns a "
          "placeholder. Wiring the real pipeline is the next major chunk of feature work."),
        PageBreak(),
    ]

    # --- Models tab walkthrough -------------------------------------
    story += [
        p(styles, "H1", "Using the Models tab"),
        p(styles, "Body", "From http://127.0.0.1:8501, click <b>Models</b>. You'll see three sections:"),
        p(styles, "H2", "Currently loaded (in VRAM)"),
        p(styles, "Body",
          "What Ollama has resident right now. Each row shows the tag, VRAM size, and an "
          "expires_at timestamp (when Ollama's keep-alive timer will auto-unload). An "
          "<b>Unload</b> button frees VRAM immediately."),
        p(styles, "H2", "Pulled models (on disk)"),
        p(styles, "Body",
          "What's available to load. Each row shows the tag, the model group it maps to, "
          "size, and modification time. <b>Load</b> pulls weights into VRAM with a 30-minute "
          "keep-alive. Buttons are disabled in strict DAY_MODE; if you need to load during "
          "the day, run bash scripts/day_unlock.sh \"reason\" first."),
        p(styles, "H2", "Quick test prompt"),
        p(styles, "Body",
          "Single-shot verification. Pick a loaded model, type a prompt, hit Send. The "
          "response renders in a code block. Not a chat &mdash; no history. For "
          "conversations, use Open WebUI at http://localhost:3000."),
        p(styles, "Hint",
          "First inference after a fresh Load is always the slowest (KV cache cold). "
          "Subsequent prompts are 5-10x faster. With two 30B models loaded at once "
          "(61.6 GB VRAM), expect noticeable slowdown from memory pressure on a 96 GB "
          "M2 Max."),
        PageBreak(),
    ]

    # --- Schedule tab walkthrough ----------------------------------
    story += [
        p(styles, "H1", "Using the Schedule tab"),
        p(styles, "Body",
          "From the panel, click <b>Schedule</b>. Two sections:"),
        p(styles, "H2", "Status metrics"),
        p(styles, "Body",
          "Three independent checks of the launchd job: is the project plist present, is "
          "the plist installed in ~/Library/LaunchAgents, is it loaded in launchctl. "
          "All three off = auto-execution is OFF."),
        p(styles, "H2", "Edit times"),
        p(styles, "Body",
          "Three editable fields: day_mode_start, night_mode_start, night_mode_end. "
          "Format 24-hour HH:MM. Click Save to rewrite config/assistant.yaml atomically. "
          "Validation runs first; bad values are rejected with a clear error."),
        p(styles, "Warn",
          "Editing the times does NOT auto-flip LOCALAI_MODE. That stays an explicit env-var "
          "gesture. The times drive (a) the launchd plist when you regenerate it, and "
          "(b) the visual hint in the header showing whether you're in DAY or NIGHT "
          "window right now."),
        p(styles, "H2", "If the plist is already installed"),
        p(styles, "Body",
          "The panel shows a yellow warning with the three commands needed to regenerate "
          "and reload the plist so the new times take effect. The panel never touches "
          "launchd directly &mdash; arming and disarming are deliberate terminal commands."),
        PageBreak(),
    ]

    # --- Day unlock --------------------------------------------------
    story += [
        p(styles, "H1", "Day-unlock switch"),
        p(styles, "Body",
          "DAY_MODE blocks every local-* model group. To deliberately allow local "
          "models during the day, the day-unlock switch flips a single, visible boolean."),
        p(styles, "H2", "Turn it on"),
        code_block(styles, 'bash scripts/day_unlock.sh "checking last night\'s output"'),
        p(styles, "Body",
          "Creates ~/LocalAI/state/day_unlock.flag with a timestamp, hostname, and reason. "
          "The Streamlit header flips Day unlock from off to ACTIVE and a red banner "
          "appears with the flag contents."),
        p(styles, "H2", "Turn it off"),
        code_block(styles, "bash scripts/day_lock.sh"),
        p(styles, "Body",
          "Deletes the flag. Warns if LOCALAI_DAY_UNLOCK is also set in the shell so you "
          "know to unset it."),
        p(styles, "H2", "One-shot env-var variant"),
        code_block(styles, "LOCALAI_DAY_UNLOCK=true .venv/bin/python -m assistant_core.cli sample-readiness"),
        p(styles, "Body",
          "Per-shell, ephemeral. Useful for one-off commands without touching the flag file."),
        p(styles, "Hint",
          "Day unlock does NOT open the cloud path. cloud-claude-opus still raises a "
          "SafetyError regardless. Full design rationale: docs/day_unlock.md."),
        PageBreak(),
    ]

    # --- Do / Don't --------------------------------------------------
    story += [
        p(styles, "H1", "Do / Don't"),
        p(styles, "H2", "Do"),
        *bullets(
            styles,
            [
                "Keep input files under ~/LocalAI/inbox/. That's the only place this system reads from.",
                "Be specific in clarification answers. Explicit paths, single-line key:value lines parse better than prose.",
                "Mark packets as high_stakes (board, CEO, legal, investor) when they need the 0.90 readiness bar.",
                "Use day_unlock deliberately, lock again when done. The red banner is your reminder.",
                "Run bash scripts/run_tests.sh before committing changes.",
                "Read AGENTS.md if you're going to modify this repo.",
                "Pull models on stable Wi-Fi; qwen3:30b-a3b is ~18 GB.",
            ],
        ),
        p(styles, "H2", "Don't"),
        *bullets(
            styles,
            [
                "Don't put ANTHROPIC_API_KEY in .env unless you actually want cloud fallback. Default policy refuses it; setting the key removes one of six gates.",
                "Don't point the system at ~/Documents, ~/Desktop, or anywhere outside ~/LocalAI/inbox/.",
                "Don't delete the temporal_data Docker volume thinking it holds your work. Your packets live in postgres_data.",
                "Don't edit files in ~/LocalAI/output/ and expect them to come back next run. Save important outputs into your Obsidian vault.",
                "Don't leave day_unlock on overnight if you don't need to. It persists across reboots by design.",
                "Don't bypass assert_model_allowed() by hitting Ollama/LiteLLM directly with raw tags. That defeats the safety policy.",
                "Don't start the Temporal worker before docker services are healthy.",
            ],
        ),
        PageBreak(),
    ]

    # --- Troubleshooting --------------------------------------------
    story += [
        p(styles, "H1", "Troubleshooting"),
        section_table(
            [
                ["Symptom", "Fix"],
                ["Safari can't connect to 127.0.0.1:8501", "Streamlit isn't running. bash scripts/start_control_panel.sh. If port is held: kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t)"],
                ["Error: could not connect to ollama server", "Ollama isn't running. brew services start ollama. Verify with curl http://localhost:11434/api/tags"],
                ["Docker shows Temporal Restarting", "docker logs --tail=20 localai-temporal. If dynamic-config error, force-recreate: docker compose up -d --force-recreate temporal"],
                ["Postgres unavailable", "Docker isn't running or postgres container is down. bash scripts/start_services.sh"],
                ["Day unlock banner won't go away", "Refresh the browser. Check echo $LOCALAI_DAY_UNLOCK in the shell that started Streamlit. unset if set, then restart panel."],
                ["bash scripts/install_core.sh fails on Python 3.14", "Use Python 3.13: brew install python@3.13 then LOCALAI_PYTHON_BIN=/opt/homebrew/bin/python3.13 bash scripts/install_core.sh"],
                ["Model pull says \"file does not exist\"", "Tag name wrong. Try alternatives listed at the end of scripts/pull_models.sh, or qwen2.5-coder:32b / qwen3:14b / deepseek-r1:14b."],
                ["Panel Unload doesn't unload", "Refresh page. If still loaded, run ollama stop <tag> from terminal as a workaround."],
                ["Tests fail with state-dir errors", "tests/conftest.py should isolate. If you've deleted it, restore it."],
            ],
            col_widths=[2.3 * inch, 4.2 * inch],
        ),
        PageBreak(),
    ]

    # --- Safety rules summary ---------------------------------------
    story += [
        p(styles, "H1", "Safety rules at a glance"),
        p(styles, "Body", "All enforced in code, not just documented."),
        section_table(
            [
                ["Rule", "Where enforced"],
                ["No cloud calls without 6 policy gates passing", "assert_cloud_allowed"],
                ["No local model calls in DAY_MODE by default", "assert_heavy_execution_allowed + LOCAL_MODEL_GROUPS"],
                ["Day unlock is the only relax mechanism, and it's visible", "day_unlock_active + Streamlit banner"],
                ["No writes outside allowed roots", "assert_original_file_write_allowed"],
                ["No emails / external API writes in v1", "assert_no_external_write (always denies)"],
                ["Cloud Claude blocked at model selection too", "assert_model_allowed('cloud-claude-opus', ...) raises"],
                ["Services bind to 127.0.0.1 only", "docker-compose.yml port mappings"],
                ["Original inbox files never modified", "Output paths constrained to ~/LocalAI/output/"],
                ["Nightly auto-execution OFF by default", "launchd plist generated but not installed; arming is a 3-step manual gesture"],
            ],
            col_widths=[3.4 * inch, 3.1 * inch],
        ),
        PageBreak(),
    ]

    # --- Mental model ------------------------------------------------
    story += [
        p(styles, "H1", "One paragraph to remember"),
        p(styles, "Body",
          "A vague request comes in. The system refuses to act on it. Instead it asks "
          "you five to seven questions sized to the gaps in the request. You answer "
          "them in a markdown file. The system rescores. If readiness is &ge; 0.85 "
          "(or &ge; 0.90 for high-stakes), the packet is eligible for overnight "
          "execution. Overnight, in NIGHT_MODE, the execution graph reads sources, "
          "calls local models through a safety gate, evaluates the output, retries on "
          "a secondary local model if needed, writes results to ~/LocalAI/output/&lt;date&gt;/, "
          "and adds memory candidates to the Obsidian review queue. Cloud is never used "
          "unless six specific conditions are explicitly met. You read the output in "
          "the morning. Nothing leaves your machine."),
        Spacer(1, 0.3 * inch),
        p(styles, "Caption",
          "End of Onboarding. For the deeper architecture, see the companion System Guide PDF."),
    ]

    return story


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    styles = make_styles()

    guide_path = DOCS_DIR / "Local_AI_Orchestrator_System_Guide.pdf"
    build_document(
        guide_path,
        build_system_guide(styles),
        footer_text="Local AI Orchestrator — System Guide",
    )
    print(f"Wrote {guide_path}")

    onb_path = DOCS_DIR / "Local_AI_Orchestrator_Onboarding.pdf"
    build_document(
        onb_path,
        build_onboarding(styles),
        footer_text="Local AI Orchestrator — Onboarding",
    )
    print(f"Wrote {onb_path}")


if __name__ == "__main__":
    main()
