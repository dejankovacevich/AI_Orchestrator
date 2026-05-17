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
    styles["TocItem"] = ParagraphStyle(
        "TocItem",
        parent=styles["Body"],
        fontSize=10.5,
        leading=16,
        spaceAfter=2,
    )
    styles["RecipeTitle"] = ParagraphStyle(
        "RecipeTitle",
        parent=styles["H2"],
        fontSize=15,
        textColor=colors.HexColor("#7c2d12"),
        spaceBefore=14,
        spaceAfter=6,
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


def toc_entry(styles, num, title):
    return Paragraph(
        f'<font face="Helvetica-Bold">{num}.</font>&nbsp;&nbsp;{title}',
        styles["TocItem"],
    )


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

    # --- Table of contents -------------------------------------------
    toc_items = [
        "1. What this system is",
        "2. What this system is NOT",
        "3. Mental model and the clarify-then-execute loop",
        "4. Readiness scoring in depth",
        "5. Architecture at a glance",
        "6. Components: what each does and why",
        "7. The safety system in depth",
        "8. The day-unlock switch",
        "9. Auto-execution (launchd nightly job)",
        "10. End-to-end data flow",
        "11. Worked example: a clarification round",
        "12. Worked example: walking the safety gates",
        "13. Worked example: loading and unloading a model",
        "14. Worked example: editing day/night times",
        "15. Sample artifacts (what a morning brief looks like)",
        "16. Configuration recipes",
        "17. Model selection by hardware",
        "18. What's implemented vs scaffolded",
        "19. File system layout",
        "20. Database schema",
        "21. Code roadmap (file-by-file)",
        "22. Anti-patterns and pitfalls",
        "23. Glossary",
    ]
    story += [p(styles, "H1", "Table of contents")]
    story += [Paragraph(item, styles["TocItem"]) for item in toc_items]
    story += [PageBreak()]

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
        p(styles, "Body", "The design intent is two-fold:"),
        *bullets(
            styles,
            [
                "<b>Clarify before doing anything heavy.</b> Vague input never produces low-quality output; it produces questions.",
                "<b>Keep everything on your machine.</b> No cloud calls unless every one of six policy gates passes. No external sends in v1. No service exposure beyond localhost.",
            ],
        ),
        p(styles, "H2", "The everyday claim"),
        p(
            styles,
            "Body",
            "<i>If you give it a vague request during the day, it gives you back a list of "
            "questions. If you answer those questions, it scores you ready. Overnight it "
            "produces a morning brief that respects what you said. Nothing leaves your "
            "machine.</i>",
        ),
    ]

    # --- Section 2: What it's NOT ------------------------------------
    story += [
        p(styles, "H1", "2. What this system is NOT"),
        p(
            styles,
            "Body",
            "The negative space matters as much as the positive space. The orchestrator "
            "deliberately doesn't try to be these things:",
        ),
        *bullets(
            styles,
            [
                "Not a chatbot &mdash; for conversations with a local model, use Open WebUI at http://localhost:3000.",
                "Not multi-user &mdash; single Mac, single operator, no auth.",
                "Not for sending anything externally &mdash; email, Slack, calendar invites, GitHub PRs, production API writes are blocked at the safety layer in v1.",
                "Not auto-cloud &mdash; Claude requires six gates; the day-unlock switch does not open them.",
                "Not running models in the background all day &mdash; DAY_MODE blocks every local-* model group unless you deliberately unlock.",
                "Not exposed beyond localhost &mdash; every port binds to 127.0.0.1.",
                "Not a knowledge base by itself &mdash; it writes to your Obsidian vault and reads from ~/LocalAI/inbox/; both are yours.",
                "Not auto-armed at install &mdash; the nightly launchd job is generated but never loaded without your explicit terminal command.",
            ],
        ),
        PageBreak(),
    ]

    # --- Section 3: Mental model -------------------------------------
    story += [
        p(styles, "H1", "3. Mental model and the clarify-then-execute loop"),
        p(
            styles,
            "Body",
            "The system is built around one loop, repeated as often as you have work. Read "
            "this table once and the rest of the architecture will follow:",
        ),
        section_table(
            [
                ["Stage", "What happens", "Who acts"],
                ["1. Capture", "You give it a title and a vague description.", "You"],
                ["2. Clarify", "The system builds an initial work packet, scores readiness on 9 dimensions, and generates up to 7 strong questions where gaps are.", "System"],
                ["3. Answer", "You respond in a markdown file or via the panel.", "You"],
                ["4. Re-score", "The system parses your answers, rescores, and either marks the packet READY_FOR_OVERNIGHT (>= 0.85) or generates more questions.", "System"],
                ["5. Execute", "Overnight, in NIGHT_MODE, the execution graph reads sources, calls local models through the safety gate, evaluates output, writes artifacts.", "System (scaffolded)"],
                ["6. Review", "You read the output in ~/LocalAI/output/<date>/ and the Obsidian vault; approve memory candidates for the long-term review queue.", "You"],
            ],
            col_widths=[0.9 * inch, 4.4 * inch, 1.2 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "Two key properties of the loop:",
        ),
        *bullets(
            styles,
            [
                "<b>The system never executes without your consent.</b> Readiness threshold is the gate; below 0.85 (or 0.90 for high-stakes) the work refuses to start.",
                "<b>The clarification step is valuable by itself.</b> Most weekly value comes from being forced to be explicit about quality, audience, sources, and escalation &mdash; even when overnight execution never runs.",
            ],
        ),
        PageBreak(),
    ]

    # --- Section 4: Readiness scoring --------------------------------
    story += [
        p(styles, "H1", "4. Readiness scoring in depth"),
        p(
            styles,
            "Body",
            "Readiness is a deterministic weighted sum over nine binary dimensions. Each "
            "dimension is 1 if present in the packet, 0 if missing. The score lands in [0, 1].",
        ),
        section_table(
            [
                ["Dimension", "Weight", "What it captures", "Blocking?"],
                ["objective", "0.18", "Is the desired outcome explicit?", "yes"],
                ["output_format", "0.14", "Is the output shape specified?", "yes"],
                ["sources", "0.14", "Which folders/files are in scope?", "yes"],
                ["privacy_cloud_policy", "0.14", "Is cloud explicitly allowed or forbidden?", "yes"],
                ["quality_threshold", "0.12", "What quality bar to optimize for?", "no"],
                ["audience", "0.10", "Who is the output for?", "no"],
                ["assumption_policy", "0.08", "May the system infer when uncertain?", "no"],
                ["escalation_policy", "0.06", "When should it stop and ask?", "no"],
                ["success_criteria", "0.04", "What makes the work done?", "no"],
            ],
            col_widths=[1.7 * inch, 0.7 * inch, 3.3 * inch, 0.8 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Thresholds and status mapping"),
        section_table(
            [
                ["Score range", "Status", "Eligible for overnight?"],
                ["&ge; 0.90", "READY_HIGH_CONFIDENCE", "Yes (required for high-stakes)"],
                ["0.85 to 0.89", "READY_FOR_OVERNIGHT", "Yes for normal packets; no for high-stakes"],
                ["0.65 to 0.84", "NEEDS_CLARIFICATION", "No; another question round"],
                ["&lt; 0.65", "UNDERDEFINED", "No; major gaps remain"],
            ],
            col_widths=[1.5 * inch, 2.4 * inch, 2.5 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "<b>High-stakes auto-detection</b>: the work packet builder scans title and "
            "description for any of: board, CEO, legal, investor, high-stakes. If found, "
            "<code>high_stakes=True</code> is set and the threshold becomes 0.90.",
        ),
        p(
            styles,
            "Body",
            "<b>Blocking vs non-blocking gaps</b>: the four blocking dimensions (objective, "
            "output_format, sources, privacy_cloud_policy) are weighted heavily and must all "
            "be 1 to even reach 0.85. The other five contribute to fine-tuning but cannot "
            "individually keep a packet from going ready.",
        ),
        PageBreak(),
    ]

    # --- Section 5: Architecture --------------------------------------
    story += [
        p(styles, "H1", "5. Architecture at a glance"),
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
        p(styles, "Caption", "Solid lines: required. LiteLLM and Open WebUI are optional in v1 &mdash; the panel talks to Ollama directly through assistant_core.llm.ollama_admin."),
        p(styles, "H2", "What runs where"),
        section_table(
            [
                ["Component", "Lifecycle", "Started by"],
                ["Streamlit panel", "Host Python process", "bash scripts/start_control_panel.sh"],
                ["assistant_core CLI", "Host Python process (one-shot)", "bash scripts/*.sh"],
                ["Postgres", "Docker container", "bash scripts/start_services.sh"],
                ["Temporal + Temporal UI", "Docker containers", "bash scripts/start_services.sh"],
                ["Open WebUI", "Docker container", "bash scripts/start_services.sh"],
                ["Ollama", "Host service (brew)", "brew services start ollama"],
                ["LiteLLM", "Host Python process", "bash scripts/start_litellm.sh"],
                ["Temporal worker", "Host Python process (long-running)", "bash scripts/start_temporal_worker.sh"],
            ],
            col_widths=[1.7 * inch, 1.9 * inch, 2.9 * inch],
        ),
        Spacer(1, 0.1 * inch),
        p(
            styles,
            "Body",
            "<b>Important consequence</b>: <code>bash scripts/stop_services.sh</code> only "
            "stops the Docker containers (Postgres, Temporal, Temporal UI, Open WebUI). It "
            "does not touch Streamlit, Ollama, or LiteLLM &mdash; those are host processes "
            "and must be stopped separately (Ctrl+C their terminals, or "
            "<code>kill $(lsof -nP -iTCP:&lt;port&gt; -sTCP:LISTEN -t)</code>).",
        ),
        PageBreak(),
    ]

    # --- Section 6: Component-by-component ----------------------------
    story += [
        p(styles, "H1", "6. Components: what each does and why"),
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
                "config. psycopg for direct Postgres I/O without an ORM layer that hides intent."
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

    # --- Section 7: Safety system ------------------------------------
    story += [
        p(styles, "H1", "7. The safety system in depth"),
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
        p(styles, "H2", "Modes"),
        section_table(
            [
                ["LOCALAI_MODE value", "Meaning", "Local model calls allowed?"],
                ["DAY_MODE (default)", "Workday: clarification + deterministic logic only.", "No, unless day_unlock active"],
                ["NIGHT_MODE", "Overnight: heavy execution permitted.", "Yes"],
                ["MANUAL_RESUME", "User-driven re-run of paused work.", "Yes"],
            ],
            col_widths=[1.7 * inch, 3.0 * inch, 1.8 * inch],
        ),
        Spacer(1, 0.1 * inch),
        p(
            styles,
            "Body",
            "Mode is a single env var. The default is DAY_MODE. The overnight runner refuses "
            "to start unless NIGHT_MODE is set; the launchd plist sets it automatically when "
            "it fires.",
        ),
        PageBreak(),
    ]

    # --- Section 8: Day-unlock --------------------------------------
    story += [
        p(styles, "H1", "8. The day-unlock switch"),
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
                "<b>Sentinel file</b> &mdash; <code>~/LocalAI/state/day_unlock.flag</code>. Created by <code>scripts/day_unlock.sh</code> with a timestamp, hostname, and reason. Persists across terminal closes and reboots.",
                "<b>Environment variable</b> &mdash; <code>LOCALAI_DAY_UNLOCK=true</code>. Per-shell, ephemeral.",
            ],
        ),
        p(
            styles,
            "Body",
            "Either being on opens the gate. Cloud and external-write gates are <b>not</b> "
            "affected. The Streamlit panel renders a red banner with the flag contents while "
            "unlock is ACTIVE so the state is impossible to miss.",
        ),
        p(styles, "H2", "Sentinel file format"),
        code_block(
            styles,
            "$ cat ~/LocalAI/state/day_unlock.flag\n"
            "unlocked_at: 2026-05-17T03:48:22Z\n"
            "unlocked_by: macbookpro@Mac\n"
            "reason: spot-checking the morning brief",
        ),
        p(
            styles,
            "Body",
            "Contents are informational only &mdash; the safety layer never parses them. An "
            "empty <code>touch ~/LocalAI/state/day_unlock.flag</code> also unlocks. The "
            "structure is for you (or for a future you reviewing why the flag was left on).",
        ),
        p(styles, "Hint",
          "Full design rationale: docs/day_unlock.md. Locking again: bash scripts/day_lock.sh."),
        PageBreak(),
    ]

    # --- Section 9: Auto-execution -----------------------------------
    story += [
        p(styles, "H1", "9. Auto-execution (launchd nightly job)"),
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
            "# Optionally also delete the installed copy:\n"
            "rm ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist",
        ),
        p(styles, "H2", "How to verify the state from anywhere"),
        code_block(
            styles,
            "launchctl list | grep com.localai.orchestrator.nightly\n"
            "ls ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist\n"
            "ls launchd/com.localai.orchestrator.nightly.plist\n"
            "crontab -l | grep -i localai",
        ),
        p(styles, "Hint", "Full design rationale: docs/auto_execution.md."),
        PageBreak(),
    ]

    # --- Section 10: Data flow ---------------------------------------
    story += [
        p(styles, "H1", "10. End-to-end data flow"),
        p(
            styles,
            "Body",
            "From a vague request to overnight output, in nine steps. The next section walks "
            "the same flow with concrete JSON.",
        ),
        section_table(
            [
                ["Step", "What happens", "Storage"],
                ["1", "You: bash scripts/create_work_packet.sh \"Title\" \"Description\"", "&mdash;"],
                ["2", "build_initial_work_packet builds a WorkPacket pydantic model.", "in memory"],
                ["3", "score_readiness assigns 0/1 per dimension, computes weighted score.", "in memory"],
                ["4", "generate_questions emits up to 7 ranked clarification questions.", "in memory"],
                ["5", "create_work_packet + save_questions write the row and questions to Postgres.", "Postgres: work_packets, clarification_questions"],
                ["6", "You answer in a markdown file. bash scripts/answer_questions.sh parses.", "&mdash;"],
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

    # --- Section 11: Worked example, clarification round -------------
    story += [
        p(styles, "H1", "11. Worked example: a clarification round"),
        p(
            styles,
            "Body",
            "A complete walk through a real clarification. The same call you would make "
            "from the CLI, with the exact JSON the system returns at each step.",
        ),
        p(styles, "H2", "Step 1: vague request"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh \\\n'
            '   "Morning prep" \\\n'
            '   "Prepare me for tomorrow from my notes."',
        ),
        p(styles, "H2", "Step 2: response &mdash; rejected for clarification"),
        code_block(
            styles,
            "{\n"
            '  "work_packet_id": "f37b8a92-...-4c11",\n'
            '  "status": "UNDERDEFINED",\n'
            '  "readiness_score": 0.18,\n'
            '  "questions": [\n'
            '    {\n'
            '      "category": "objective",\n'
            '      "question": "What exact outcome should this work produce, and what '
            "should be considered out of scope?\",\n"
            '      "priority": 100, "blocking": true\n'
            '    },\n'
            '    {\n'
            '      "category": "outputs",\n'
            '      "question": "What exact output files or formats do you want at the end?",\n'
            '      "priority": 95, "blocking": true\n'
            '    },\n'
            '    {\n'
            '      "category": "sources",\n'
            '      "question": "Which folders or files are in scope, and are any sources '
            "explicitly off-limits?\",\n"
            '      "priority": 90, "blocking": true\n'
            '    },\n'
            '    {\n'
            '      "category": "privacy/cloud",\n'
            '      "question": "Is cloud fallback explicitly allowed for this packet, or '
            "must it stay fully local?\",\n"
            '      "priority": 88, "blocking": true\n'
            '    },\n'
            '    ...\n'
            '  ]\n'
            "}",
        ),
        p(
            styles,
            "Body",
            "Score 0.18 is below 0.65, so status is UNDERDEFINED. Four blocking dimensions "
            "are missing (objective is too generic to satisfy the check; the rest have "
            "nothing). The system refuses to proceed.",
        ),
        p(styles, "H2", "Step 3: answer markdown"),
        code_block(
            styles,
            "# examples/sample_answers.md\n"
            "\n"
            "Outputs: morning brief, today's priorities, risks and blockers, meeting prep.\n"
            "Sources: only ~/LocalAI/inbox/notes and ~/LocalAI/inbox/docs.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: private user only.\n"
            "Assumptions: infer low-risk priorities but label every assumption.\n"
            "Quality: optimize for factuality, criticality, and actionability.\n"
            "Stop conditions: stop for missing sources, unclear ownership, or anything\n"
            "  requiring external action.\n"
            "Success: I can read it in the morning and know what matters first.",
        ),
        p(styles, "H2", "Step 4: submit answers"),
        code_block(
            styles,
            'bash scripts/answer_questions.sh \\\n'
            '   f37b8a92-...-4c11 \\\n'
            '   examples/sample_answers.md',
        ),
        p(styles, "H2", "Step 5: response &mdash; ready"),
        code_block(
            styles,
            "{\n"
            '  "work_packet_id": "f37b8a92-...-4c11",\n'
            '  "status": "READY_FOR_OVERNIGHT",\n'
            '  "readiness_score": 0.9,\n'
            '  "database": "updated",\n'
            '  "remaining_questions": []\n'
            "}",
        ),
        p(
            styles,
            "Body",
            "All four blocking dimensions are filled (objective is the request itself, "
            "outputs and sources extracted from the markdown, cloud policy explicit). The "
            "five non-blocking dimensions add up to 0.40 / 0.40 (audience, quality, "
            "assumptions, escalation, success all answered). Score lands at 0.90 = "
            "READY_HIGH_CONFIDENCE.",
        ),
        p(styles, "H2", "What the packet looks like in Postgres now"),
        code_block(
            styles,
            "SELECT id, status, readiness_score, high_stakes\n"
            "FROM work_packets\n"
            "WHERE id = 'f37b8a92-...-4c11';\n"
            "\n"
            "             id              |        status         | readiness_score | high_stakes\n"
            "-----------------------------+-----------------------+-----------------+------------\n"
            " f37b8a92-...-4c11           | READY_FOR_OVERNIGHT   | 0.90            | false",
        ),
        PageBreak(),
    ]

    # --- Section 12: Worked example, gates ---------------------------
    story += [
        p(styles, "H1", "12. Worked example: walking the safety gates"),
        p(
            styles,
            "Body",
            "A Python REPL session showing each gate in turn. Useful for understanding what "
            "the gate functions actually do without reading the code.",
        ),
        p(styles, "H2", "DAY_MODE blocks local-main by default"),
        code_block(
            styles,
            "$ .venv/bin/python\n"
            ">>> from assistant_core.safety import assert_model_allowed, SafetyError\n"
            ">>> try:\n"
            "...     assert_model_allowed('local-main', 'DAY_MODE', manual_override=False)\n"
            "... except SafetyError as e:\n"
            "...     print('blocked:', e)\n"
            "blocked: Local model execution is blocked in DAY_MODE without explicit\n"
            "manual override.",
        ),
        p(styles, "H2", "Manual override unblocks it"),
        code_block(
            styles,
            ">>> assert_model_allowed('local-main', 'DAY_MODE', manual_override=True)\n"
            ">>># returns None silently &mdash; call would proceed",
        ),
        p(styles, "H2", "Day-unlock flag does the same thing without per-call override"),
        code_block(
            styles,
            "$ bash scripts/day_unlock.sh \"REPL demo\"\n"
            ">>> assert_model_allowed('local-main', 'DAY_MODE', manual_override=False)\n"
            ">>># returns None silently\n"
            "$ bash scripts/day_lock.sh\n"
            ">>> assert_model_allowed('local-main', 'DAY_MODE', manual_override=False)\n"
            "SafetyError: Local model execution is blocked in DAY_MODE without explicit\n"
            "manual override.",
        ),
        p(styles, "H2", "Cloud Claude is always blocked here"),
        code_block(
            styles,
            ">>> assert_model_allowed('cloud-claude-opus', 'NIGHT_MODE', manual_override=True)\n"
            "SafetyError: Claude must be authorized through cloud policy checks, not\n"
            "model selection alone.",
        ),
        p(
            styles,
            "Body",
            "Cloud Claude has its own dedicated gate. Even with NIGHT_MODE + manual_override "
            "+ day unlock all set, you cannot reach Claude through this function. The "
            "right path is <code>assert_cloud_allowed(...)</code> which checks six "
            "independent conditions.",
        ),
        p(styles, "H2", "Cloud Claude with the proper gate (still mostly fails)"),
        code_block(
            styles,
            ">>> from assistant_core.safety import assert_cloud_allowed\n"
            ">>> assert_cloud_allowed(\n"
            "...     file_path='/Users/me/LocalAI/inbox/cloud_review/brief.cloud.md',\n"
            "...     cloud_fallback_enabled=False,   # config gate -> raises\n"
            "...     work_packet_cloud_allowed=True,\n"
            "...     high_stakes=True,\n"
            "...     local_quality_gate_failed=True,\n"
            "...     anthropic_api_key='sk-...',\n"
            "...     daily_budget_remaining=True,\n"
            "...     cloud_review_dir='/Users/me/LocalAI/inbox/cloud_review',\n"
            "... )\n"
            "SafetyError: Cloud fallback is disabled by configuration.",
        ),
        p(
            styles,
            "Body",
            "Six different gate conditions; flipping any one false raises. To actually reach "
            "Claude you need to satisfy all six simultaneously. That's deliberate.",
        ),
        PageBreak(),
    ]

    # --- Section 13: Worked example, model load ----------------------
    story += [
        p(styles, "H1", "13. Worked example: loading and unloading a model"),
        p(
            styles,
            "Body",
            "The Models tab and the underlying API calls. Same effect from either entry point.",
        ),
        p(styles, "H2", "From the panel"),
        *bullets(
            styles,
            [
                "Browse to <code>http://127.0.0.1:8501</code> -> <b>Models</b> tab.",
                "Day unlock must be ACTIVE if you're in DAY_MODE &mdash; run <code>bash scripts/day_unlock.sh \"reason\"</code> first if needed.",
                "Click <b>Load</b> next to <code>deepseek-r1:8b</code>. Spinner. Success toast.",
                "Model now appears in <i>Currently loaded</i> with size, expires_at, and Unload button.",
                "Scroll to <b>Quick test prompt</b>, pick the model, type a prompt, click Send.",
                "Click <b>Unload</b>. Model disappears from <i>Currently loaded</i>.",
            ],
        ),
        p(styles, "H2", "What the panel does behind the scenes (curl equivalents)"),
        code_block(
            styles,
            "# Load with 30-minute keep-alive\n"
            'curl -X POST http://localhost:11434/api/generate \\\n'
            '   -d \'{"model":"deepseek-r1:8b","prompt":"","keep_alive":"30m"}\'\n'
            "\n"
            "# What is currently in VRAM\n"
            "curl http://localhost:11434/api/ps\n"
            "\n"
            "# Send a prompt\n"
            'curl -X POST http://localhost:11434/api/generate \\\n'
            '   -d \'{"model":"deepseek-r1:8b","prompt":"Say hi.","stream":false}\'\n'
            "\n"
            "# Unload (note the string '0s', not int 0 &mdash; some Ollama versions parse\n"
            "# int 0 as \"use default 5m\" and silently re-pin the model)\n"
            'curl -X POST http://localhost:11434/api/generate \\\n'
            '   -d \'{"model":"deepseek-r1:8b","prompt":"","keep_alive":"0s"}\'',
        ),
        p(styles, "H2", "Equivalent CLI"),
        code_block(
            styles,
            "ollama list                     # what's on disk\n"
            "ollama ps                       # what's in VRAM\n"
            "ollama run deepseek-r1:8b       # interactive chat (not what the orchestrator uses)\n"
            "ollama stop deepseek-r1:8b      # immediate unload (sends keep_alive=0s)",
        ),
        p(styles, "H2", "What the gate sees"),
        code_block(
            styles,
            "# Inside ollama_admin.load_model('deepseek-r1:8b', mode='DAY_MODE'):\n"
            "1. resolve_group_for_tag('deepseek-r1:8b') -> 'local-reasoner'\n"
            "2. assert_model_group_allowed('local-reasoner', 'DAY_MODE')\n"
            "     -> calls assert_model_allowed\n"
            "       -> not cloud-claude-opus, so skip first check\n"
            "       -> 'local-reasoner' in LOCAL_MODEL_GROUPS, delegate\n"
            "         -> assert_heavy_execution_allowed('DAY_MODE')\n"
            "           -> day_unlock_active() reads ~/LocalAI/state/day_unlock.flag\n"
            "           -> if ACTIVE: pass; if not: raise SafetyError\n"
            "3. If gate passes: POST /api/generate with keep_alive='30m'",
        ),
        PageBreak(),
    ]

    # --- Section 14: Worked example, schedule edit -------------------
    story += [
        p(styles, "H1", "14. Worked example: editing day/night times"),
        p(
            styles,
            "Body",
            "Say you want the nightly job to start at 02:00 instead of 01:30, and treat 06:30 "
            "as the end of night. Two ways: edit the config file directly, or use the panel.",
        ),
        p(styles, "H2", "Via the panel"),
        *bullets(
            styles,
            [
                "Browse to the panel -> <b>Schedule</b> tab.",
                "Edit <code>night_mode_start</code> to <code>02:00</code> and <code>night_mode_end</code> to <code>06:30</code>.",
                "Click <b>Save to config/assistant.yaml</b>. Atomic write; validation runs first.",
                "If the plist is already installed in LaunchAgents, a yellow warning appears with the regenerate+reload commands.",
            ],
        ),
        p(styles, "H2", "Via the terminal"),
        code_block(
            styles,
            "# Edit config/assistant.yaml by hand or with sed; the panel and the safety\n"
            "# layer pick it up automatically on next read.\n"
            "\n"
            "# Then if the plist is installed:\n"
            "LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh\n"
            "launchctl unload ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist\n"
            "launchctl load ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist\n"
            "\n"
            "# Verify the new time is baked into the installed plist:\n"
            "grep -A3 StartCalendarInterval \\\n"
            "  ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist",
        ),
        p(styles, "H2", "What does NOT change automatically"),
        *bullets(
            styles,
            [
                "<code>LOCALAI_MODE</code> stays at whatever the shell sets it to. Editing the times does not auto-flip mode.",
                "The launchd plist installed in <code>~/Library/LaunchAgents</code> is not regenerated until you run the script with <code>LOCALAI_WRITE_LAUNCHD=true</code>.",
                "Already-running services don't restart.",
                "Already-running Temporal workflows continue with whatever mode they were started in.",
            ],
        ),
        PageBreak(),
    ]

    # --- Section 15: Sample artifacts --------------------------------
    story += [
        p(styles, "H1", "15. Sample artifacts (what a morning brief looks like)"),
        p(
            styles,
            "Body",
            "When the overnight pipeline is fully wired, each run produces a dated directory "
            "under <code>~/LocalAI/output/YYYY-MM-DD/</code> containing the following nine "
            "files. The shapes are committed; only the placeholder content rendered today "
            "will change once the LangGraph executor is implemented.",
        ),
        p(styles, "H2", "Directory contents"),
        section_table(
            [
                ["File", "Purpose"],
                ["00_STATUS.json", "Machine-readable summary of the run (packet id, status, timestamps)."],
                ["01_MORNING_BRIEF.md", "Top-line synthesis: what matters today, in priority order."],
                ["02_TODAY_PRIORITIES.md", "Ordered list of priorities with rationale and source citations."],
                ["03_ACTIONS_BY_PERSON.md", "Grouped by stakeholder: what each owns and what you owe each."],
                ["04_DECISIONS_NEEDED.md", "Items requiring your call before they can move."],
                ["05_RISKS_AND_BLOCKERS.md", "Flagged risks, with criticality and recommended next action."],
                ["06_DRAFT_MESSAGES.md", "Drafts of messages you might want to send. Never sent automatically."],
                ["07_MEETING_PREP.md", "Per-meeting prep notes: who, agenda, what to push, what to listen for."],
                ["08_CLOUD_REVIEW_CANDIDATES.md", "Items the local model flagged as candidates for cloud review (only used if cloud policy permits)."],
                ["09_AUDIT_LOG.md", "What ran, what models were called, what the evaluator said."],
            ],
            col_widths=[2.2 * inch, 4.3 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Sample 01_MORNING_BRIEF.md (mock content)"),
        code_block(
            styles,
            "# Morning Brief &mdash; 2026-05-17\n"
            "\n"
            "## Today's three things\n"
            "\n"
            "1. **Decide Q3 staffing for the Tania project.** Three weeks of notes\n"
            "   point at a hire vs reallocate question. Source: 04_DECISIONS_NEEDED.md.\n"
            "2. **Reply to the legal followup on the data sharing agreement.** Draft\n"
            "   in 06_DRAFT_MESSAGES.md ready for your review.\n"
            "3. **30-min prep for the board sync at 14:00.** Agenda + likely Qs in\n"
            "   07_MEETING_PREP.md.\n"
            "\n"
            "## Risks surfaced\n"
            "\n"
            "- Vendor X has not confirmed renewal terms (deadline Friday).\n"
            "- The migration runbook from 2026-05-10 still has two unowned steps.\n"
            "\n"
            "## Sources used\n"
            "\n"
            "- ~/LocalAI/inbox/notes/2026-W20-recap.md\n"
            "- ~/LocalAI/inbox/transcripts/2026-05-15-tania-1on1.md\n"
            "- ~/LocalAI/inbox/docs/2026-Q3-staffing-draft.md\n"
            "\n"
            "## Confidence\n"
            "\n"
            "Medium-high. Six assumptions labeled in 02_TODAY_PRIORITIES.md.",
        ),
        p(
            styles,
            "Body",
            "Memory candidates extracted from this run land in "
            "<code>~/Obsidian/LocalAI-ChiefOfStaff/00_Inbox/Memory_Review/</code> for your "
            "approval before they enter long-term memory.",
        ),
        PageBreak(),
    ]

    # --- Section 16: Configuration recipes ---------------------------
    story += [
        p(styles, "H1", "16. Configuration recipes"),
        p(styles, "Body", "Three schedule profiles you might pick from."),
        p(styles, "H2", "Recipe: \"strict night worker\" (default)"),
        code_block(
            styles,
            "day_mode_start:   '07:30'\n"
            "night_mode_start: '01:30'\n"
            "night_mode_end:   '07:00'",
        ),
        p(
            styles,
            "Body",
            "Day window is long (07:30 - 01:30 next day). Night execution starts late and "
            "ends well before you wake up. Good for the typical knowledge-worker schedule. "
            "Heavy models run with the laptop on charger overnight; you wake up to the brief.",
        ),
        p(styles, "H2", "Recipe: \"early bird\""),
        code_block(
            styles,
            "day_mode_start:   '05:30'\n"
            "night_mode_start: '23:00'\n"
            "night_mode_end:   '05:00'",
        ),
        p(
            styles,
            "Body",
            "Night starts at 23:00, leaving six hours of model time before the day window "
            "opens at 05:30. Suits someone who's at their desk by 06:00 reading briefs.",
        ),
        p(styles, "H2", "Recipe: \"weekday office, weekend lab\""),
        code_block(
            styles,
            "day_mode_start:   '08:00'\n"
            "night_mode_start: '20:00'\n"
            "night_mode_end:   '07:30'",
        ),
        p(
            styles,
            "Body",
            "Longer night window (11.5 hours) for someone who runs experiments or larger "
            "batch work overnight. The day window is shorter, so models stay safely "
            "untouched during working hours unless you explicitly day-unlock.",
        ),
        p(styles, "H2", "Threshold tuning"),
        code_block(
            styles,
            "# Stricter: require near-perfect packets to go ready\n"
            "minimum_readiness_for_overnight:   0.92\n"
            "minimum_readiness_for_high_stakes: 0.95\n"
            "\n"
            "# Looser: accept more borderline packets (NOT recommended)\n"
            "minimum_readiness_for_overnight:   0.75\n"
            "minimum_readiness_for_high_stakes: 0.85",
        ),
        p(
            styles,
            "Warn",
            "Lowering thresholds is rarely the right answer. Below 0.85, blocking gaps are "
            "almost guaranteed and the system produces lower-quality output that you'll "
            "have to redo. Stricter is fine; looser is a tax on tomorrow's you.",
        ),
        PageBreak(),
    ]

    # --- Section 17: Model selection ---------------------------------
    story += [
        p(styles, "H1", "17. Model selection by hardware"),
        p(
            styles,
            "Body",
            "Pick tags appropriate for your VRAM. The default config assumes a beefy M2 Max "
            "with 77+ GiB Metal VRAM. Smaller machines need smaller tags.",
        ),
        section_table(
            [
                ["Hardware", "local-main", "local-secondary", "local-coder", "local-reasoner"],
                ["96 GB unified (M2/M3 Max)", "qwen3:30b-a3b", "llama3.3:70b", "qwen3-coder:30b", "deepseek-r1:8b"],
                ["64 GB unified", "qwen3:30b-a3b", "(skip 70B)", "qwen3-coder:30b", "deepseek-r1:8b"],
                ["32 GB unified", "qwen3:14b", "qwen3:32b", "qwen2.5-coder:14b", "deepseek-r1:8b"],
                ["16 GB unified", "qwen3:8b", "qwen3:14b", "qwen2.5-coder:7b", "deepseek-r1:8b"],
                ["Linux NVIDIA 24GB", "qwen3:30b-a3b", "qwen3:32b", "qwen3-coder:30b", "deepseek-r1:8b"],
            ],
            col_widths=[2.0 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.2 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "When you change tags"),
        p(
            styles,
            "Body",
            "Both <code>config/models.yaml</code> and <code>config/litellm.yaml</code> must "
            "reflect the same tag for each group. The Models tab in the panel will pull the "
            "name from <code>models.yaml</code> for the gate; LiteLLM will use the "
            "<code>litellm.yaml</code> entry for routing.",
        ),
        code_block(
            styles,
            "# config/models.yaml\n"
            "local-main: qwen3:30b-a3b      # change this\n"
            "\n"
            "# config/litellm.yaml\n"
            "- model_name: local-main\n"
            "  litellm_params:\n"
            "    model: ollama/qwen3:30b-a3b  # and this, in lock-step\n"
            "    api_base: http://localhost:11434",
        ),
        p(styles, "H2", "Why MoE 30B-a3b is the workhorse default"),
        p(
            styles,
            "Body",
            "Qwen3's 30B Mixture-of-Experts model with 3B active parameters gives 30B-class "
            "quality at roughly 8B-class inference speed. Excellent fit for batch overnight "
            "work on Apple Silicon: weights load quickly, per-token latency is low, "
            "instruction following is strong for clarification-style tasks.",
        ),
        PageBreak(),
    ]

    # --- Section 18: Implemented vs scaffolded ------------------------
    story += [
        p(styles, "H1", "18. What's implemented vs scaffolded"),
        section_table(
            [
                ["Capability", "State", "Notes"],
                ["Deterministic clarification flow", "Implemented", "Builder, 9-dim readiness, question gen. 100% test-covered."],
                ["Postgres storage layer", "Implemented", "7 tables, schema migrated, CRUD for packets/questions/runs."],
                ["Safety gates (5 functions)", "Implemented", "Parameterized tests over every local-* group and mode."],
                ["Day-unlock switch", "Implemented", "File + env channels, visible banner, fail-closed."],
                ["Streamlit control panel", "Implemented", "Header strip, 7 tabs, gate-aware UI."],
                ["Models tab (load/unload/test)", "Implemented", "CLI workflow surfaced: Load -> Quick test -> Unload."],
                ["Schedule tab (time editing)", "Implemented", "Atomic config writes, validation, launchd-status mirror."],
                ["Ollama integration", "Implemented", "Pull, list, load, unload, generate."],
                ["Temporal worker + workflow defs", "Skeleton", "Workflows + activities defined; bodies return placeholders."],
                ["LiteLLM routing", "Config only", "Started via start_litellm.sh. Used by future call sites."],
                ["Launchd plist generation", "Implemented", "Reads night_mode_start; arming stays manual."],
                ["Overnight execution graph (18 steps)", "Scaffolded", "EXECUTION_STEPS list exists; activity body is stub. Next chunk."],
                ["Quality-gated local retry loop", "Scaffolded", "Deterministic evaluator fallback. Retry orchestration TBD."],
                ["Pause/resume UI", "Scaffolded", "Buttons disabled. DB statuses exist."],
                ["Semantic memory indexing", "Scaffolded", "Chroma client exists. No indexer yet."],
                ["Claude cloud-review path", "Scaffolded", "Gates implemented; no caller wired."],
                ["Drafted messages", "Scaffolded", "Output template exists; nothing fills it yet."],
                ["PDF documentation builder", "Implemented", "scripts/build_pdfs.py renders this PDF and the Onboarding one."],
            ],
            col_widths=[2.5 * inch, 1.2 * inch, 2.8 * inch],
        ),
        PageBreak(),
    ]

    # --- Section 19: File system layout -------------------------------
    story += [
        p(styles, "H1", "19. File system layout"),
        p(styles, "H2", "Project repository"),
        code_block(
            styles,
            """local-ai-orchestrator/
  AGENTS.md              rules for human/AI editors
  ONBOARDING.md          practical usage guide
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
    litellm.yaml         LiteLLM router config (gitignored)
  db/migrations/         SQL applied on Postgres first boot
  docs/                  this PDF and friends, plus design docs
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
  00_Inbox/Memory_Review/   memory candidates awaiting approval
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

    # --- Section 20: Database schema ---------------------------------
    story += [
        p(styles, "H1", "20. Database schema"),
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
        p(styles, "H2", "Looking at the data directly"),
        code_block(
            styles,
            "# Open a psql shell against the local Postgres container\n"
            "docker exec -it localai-postgres psql -U localai -d localai\n"
            "\n"
            "# In psql:\n"
            "\\dt                                  -- list tables\n"
            "SELECT id, title, status, readiness_score, created_at\n"
            "  FROM work_packets ORDER BY created_at DESC LIMIT 5;\n"
            "\n"
            "SELECT round_number, category, question, answered\n"
            "  FROM clarification_questions\n"
            "  WHERE work_packet_id = 'YOUR-UUID'\n"
            "  ORDER BY round_number, priority DESC;",
        ),
        p(styles, "Hint",
          "All tables use UUID primary keys. JSONB columns on work_packets allow policy "
          "evolution without migrations. Foreign keys enforce relational integrity."),
        PageBreak(),
    ]

    # --- Section 21: Code roadmap ------------------------------------
    story += [
        p(styles, "H1", "21. Code roadmap (file-by-file)"),
        p(styles, "Body", "Where to look when you want to change something."),
        section_table(
            [
                ["When you want to&hellip;", "Look here"],
                ["change clarification question wording", "assistant_core/clarification/question_generator.py"],
                ["change readiness weights or thresholds", "assistant_core/clarification/readiness.py + config/assistant.yaml"],
                ["change which fields the work packet has", "assistant_core/schemas.py"],
                ["change what \"high stakes\" detects", "assistant_core/clarification/work_packet_builder.py"],
                ["add a safety gate or tighten an existing one", "assistant_core/safety.py"],
                ["add a new model group", "assistant_core/safety.py (LOCAL_MODEL_GROUPS) + config/models.yaml + config/litellm.yaml"],
                ["change the day-unlock UI behavior", "app/control_panel.py (_render_header) + scripts/day_unlock.sh"],
                ["wire the actual overnight execution pipeline", "assistant_core/execution/graph.py + assistant_core/temporal_app/activities.py"],
                ["add a Postgres column", "db/migrations/ (add a new file) + assistant_core/storage.py"],
                ["change LiteLLM routing", "config/litellm.yaml + assistant_core/llm/litellm_client.py"],
                ["add a new tab to the panel", "app/control_panel.py (new _render_xxx_tab function + register)"],
                ["add a new background service status", "assistant_core/scheduler_status.py"],
                ["change what files Ollama admin lists", "assistant_core/llm/ollama_admin.py"],
                ["add a new editable config field", "assistant_core/config_writer.py (EDITABLE_FIELDS) + config/assistant.yaml"],
                ["change the launchd schedule template", "scripts/create_launchd_plist.sh"],
                ["regenerate these PDFs", "scripts/build_pdfs.py"],
            ],
            col_widths=[2.7 * inch, 3.8 * inch],
        ),
        PageBreak(),
    ]

    # --- Section 22: Anti-patterns -----------------------------------
    story += [
        p(styles, "H1", "22. Anti-patterns and pitfalls"),
        p(
            styles,
            "Body",
            "Mistakes that are easy to make. Each one is real (some are things I, your "
            "co-author, almost made you do at some point):",
        ),
        p(styles, "H2", "Loading both 30B models simultaneously to \"test things\""),
        p(
            styles,
            "Body",
            "Two 30B-class models in VRAM is 60+ GB on M2 Max. The OS starts shuffling, "
            "the first inference takes 30+ seconds, and you'll blame the orchestrator. "
            "Unload one before testing the other.",
        ),
        p(styles, "H2", "Lowering readiness thresholds to \"get things moving\""),
        p(
            styles,
            "Body",
            "Tempting when a packet just won't pass. Almost always wrong: the blocking gaps "
            "are blocking <i>because</i> the system can't safely produce useful output "
            "without them. Lower the bar and you get a confidently wrong morning brief.",
        ),
        p(styles, "H2", "Leaving day_unlock on overnight"),
        p(
            styles,
            "Body",
            "The flag persists across reboots. The Streamlit banner makes it visible, but "
            "the banner is only loud if you're <i>looking</i> at the panel. Make "
            "<code>day_lock.sh</code> part of your end-of-day habit.",
        ),
        p(styles, "H2", "Pointing the orchestrator at ~/Documents"),
        p(
            styles,
            "Body",
            "<code>~/LocalAI/inbox/</code> is the source directory by convention. Pointing "
            "the system at broader user data invites accidents: a tag indexer might pick up "
            "personal docs, an evaluator might leak content into outputs you share. Stay in "
            "the sandbox.",
        ),
        p(styles, "H2", "Setting ANTHROPIC_API_KEY \"just in case\""),
        p(
            styles,
            "Body",
            "Setting the key satisfies one of the six cloud gates. If you also set "
            "<code>cloud_fallback_enabled: true</code> in config and one of your packets "
            "happens to mark cloud allowed, a high-stakes failure path could escalate. "
            "Don't pre-arm a gun you don't plan to fire.",
        ),
        p(styles, "H2", "Skipping Temporal because it's \"just clarification\""),
        p(
            styles,
            "Body",
            "True today &mdash; clarification is synchronous Python and doesn't touch "
            "Temporal. But the moment execution is wired, the worker needs to be running "
            "or workflows queue and never run. Bring up the worker as part of the start "
            "sequence so you don't get surprised at 06:00.",
        ),
        p(styles, "H2", "Editing files in ~/LocalAI/output/<date>/ expecting them to persist"),
        p(
            styles,
            "Body",
            "Outputs are regenerated on each run; the dated directory is overwritten. "
            "Anything you want to keep, copy to your Obsidian vault. The vault is the "
            "durable layer.",
        ),
        p(styles, "H2", "Running `stop_services.sh` and assuming everything is off"),
        p(
            styles,
            "Body",
            "That script only stops Docker containers. Streamlit, Ollama, LiteLLM, and the "
            "Temporal worker are host processes. They survive. If you want everything down: "
            "stop_services.sh + Ctrl+C the Streamlit tab + "
            "<code>brew services stop ollama</code> + Ctrl+C the worker.",
        ),
        PageBreak(),
    ]

    # --- Section 23: Glossary ----------------------------------------
    story += [
        p(styles, "H1", "23. Glossary"),
        section_table(
            [
                ["Term", "Definition"],
                ["Work packet", "The orchestrator's unit of work. A structured representation of a request with objective, sources, outputs, policies, success criteria."],
                ["Readiness score", "Weighted sum of nine binary dimension checks, in [0, 1]. Threshold 0.85 to be eligible for overnight execution; 0.90 for high-stakes."],
                ["Clarification round", "One pass of: build packet -> score -> generate questions -> wait for answers."],
                ["DAY_MODE", "Mode in which all local-* model groups are blocked at the safety gate unless day_unlock is active."],
                ["NIGHT_MODE", "Mode in which local model calls are allowed. Required by the overnight runner."],
                ["MANUAL_RESUME", "Third mode value. Allows the overnight runner to proceed when you're explicitly re-running paused work."],
                ["Day unlock", "An explicit, visible override that lets local models load in DAY_MODE. Implemented as a flag file plus env-var fallback."],
                ["Model group", "A logical role (local-main, local-coder, etc.) that maps to a specific Ollama tag in config/models.yaml. The safety gate operates on groups."],
                ["Keep-alive", "Ollama's per-model VRAM retention timer. Our Load uses 30m; Quick test uses 5m; Unload sends '0s'."],
                ["Cloud-review path", "The Claude Opus route, gated by six policy checks. Files must be in ~/LocalAI/inbox/cloud_review/ or have .cloud. in the name."],
                ["Auto-execution", "The launchd job that runs run_ready_overnight.sh at night_mode_start. Off by default; arming is a deliberate three-step terminal gesture."],
                ["Manual override", "A per-call boolean (manual_override=True) that bypasses the day gate. Used in tests and direct CLI invocations."],
                ["Sentinel file", "A small file whose existence (not contents) signals a state. day_unlock.flag is one; the launchd plist is another."],
                ["Fail-closed", "Default-to-block when input is ambiguous, missing, or unknown. Opposite of fail-open. The right default for safety code."],
                ["Memory candidate", "A statement extracted from a run that might be worth keeping long-term. Lands in the Obsidian memory-review queue for your approval."],
                ["MoE", "Mixture of Experts. Models like qwen3:30b-a3b have 30B parameters but only ~3B active per token, giving small-model speed with bigger-model quality."],
            ],
            col_widths=[1.8 * inch, 4.7 * inch],
        ),
        Spacer(1, 0.25 * inch),
        p(styles, "Caption",
          "End of System Guide. For practical usage recipes and day-to-day operation, see "
          "the companion Onboarding PDF."),
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

    # --- TOC ---------------------------------------------------------
    toc_items = [
        "1. Quick reference",
        "2. Daily start sequence",
        "3. Daily shutdown sequence",
        "4. A complete worked example (vague -> ready)",
        "5. Using the Models tab",
        "6. Using the Schedule tab",
        "7. The day-unlock switch",
        "8. Recipe: morning brief",
        "9. Recipe: meeting prep",
        "10. Recipe: decision capture from transcripts",
        "11. Recipe: risk and blocker surfacing",
        "12. Recipe: code task using qwen3-coder",
        "13. Sample answer files for every recipe",
        "14. Do / Don't",
        "15. Memory budgeting (what to load when)",
        "16. Troubleshooting",
        "17. Recovery scenarios",
        "18. Weekly maintenance checklist",
        "19. Safety rules at a glance",
        "20. Tips and tricks",
        "21. One paragraph to remember",
    ]
    story += [p(styles, "H1", "Table of contents")]
    story += [Paragraph(item, styles["TocItem"]) for item in toc_items]
    story += [PageBreak()]

    # --- Quick reference ---------------------------------------------
    story += [
        p(styles, "H1", "1. Quick reference"),
        p(styles, "Body",
          "Every common operation, one row. Run all commands from the project root: "
          "<font face=\"Courier\">cd /Users/macbookpro/Projects/local-ai-orchestrator</font>."),
        section_table(
            [
                ["Goal", "Command"],
                ["See system health (Docker, Ollama, ports)", "bash scripts/check_system.sh"],
                ["Start Docker services", "bash scripts/start_services.sh"],
                ["Stop Docker services (keep data)", "bash scripts/stop_services.sh"],
                ["Start Ollama (persistent service)", "brew services start ollama"],
                ["Stop Ollama", "brew services stop ollama"],
                ["Start the control panel", "bash scripts/start_control_panel.sh"],
                ["Stop the control panel", "kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t)"],
                ["Start LiteLLM (router)", "bash scripts/start_litellm.sh"],
                ["Start Temporal worker", "bash scripts/start_temporal_worker.sh"],
                ["Open the panel in browser", "http://127.0.0.1:8501"],
                ["Open WebUI for chat with local models", "http://localhost:3000"],
                ["Open Temporal UI", "http://localhost:8233"],
                ["Create a work packet from CLI", 'bash scripts/create_work_packet.sh "Title" "Description"'],
                ["Submit answers to clarification", "bash scripts/answer_questions.sh <id> path/to/answers.md"],
                ["Allow local models in the day", 'bash scripts/day_unlock.sh "reason"'],
                ["Lock the day-unlock again", "bash scripts/day_lock.sh"],
                ["Load/unload/test a model in browser", "Panel -> Models tab"],
                ["Edit day/night times in browser", "Panel -> Schedule tab"],
                ["Verify nothing runs automatically", "launchctl list | grep localai (empty = off)"],
                ["List currently-pulled models", "ollama list"],
                ["See what is in VRAM right now", "ollama ps"],
                ["Pull all configured models (~41 GB)", "bash scripts/pull_models.sh"],
                ["Force-unload a model right now", "ollama stop <tag>"],
                ["Run the full test suite", "bash scripts/run_tests.sh"],
                ["Regenerate these PDFs", ".venv/bin/python scripts/build_pdfs.py"],
            ],
            col_widths=[3.0 * inch, 3.5 * inch],
        ),
        PageBreak(),
    ]

    # --- Daily start sequence ----------------------------------------
    story += [
        p(styles, "H1", "2. Daily start sequence"),
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
    ]

    # --- Daily shutdown ----------------------------------------------
    story += [
        p(styles, "H1", "3. Daily shutdown sequence"),
        p(styles, "Body", "End of day, in order. Each step is independent."),
        code_block(
            styles,
            "# 1. Lock the day-unlock if it was on\n"
            "bash scripts/day_lock.sh\n"
            "\n"
            "# 2. Stop the Docker services (keeps volumes, your packets persist)\n"
            "bash scripts/stop_services.sh\n"
            "\n"
            "# 3. Stop the control panel\n"
            "kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t) 2>/dev/null\n"
            "\n"
            "# 4. Optional: stop Ollama (lets the M-series unified memory page out)\n"
            "brew services stop ollama\n"
            "\n"
            "# 5. Optional: stop LiteLLM and the Temporal worker if running\n"
            "kill $(lsof -nP -iTCP:4000 -sTCP:LISTEN -t) 2>/dev/null   # LiteLLM\n"
            "pkill -f temporal_app.worker                                # worker",
        ),
        p(styles, "Warn",
          "<code>stop_services.sh</code> stops Docker containers ONLY. Streamlit, Ollama, "
          "LiteLLM, and the Temporal worker run as host processes and are NOT affected. "
          "That is why you can still see the Streamlit panel at :8501 after stopping "
          "services &mdash; the panel just shows database errors because Postgres is down."),
        PageBreak(),
    ]

    # --- Worked example ----------------------------------------------
    story += [
        p(styles, "H1", "4. A complete worked example (vague to ready)"),
        p(styles, "Body",
          "End-to-end use of the system today, from a vague request to a ready packet. "
          "Execution is still scaffolded; this stops before the night step."),
        p(styles, "H2", "Step 1: create a vague packet (expect rejection)"),
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
        p(styles, "H2", "Step 2: look at the sample answer format"),
        code_block(styles, "cat examples/sample_answers.md"),
        p(styles, "H2", "Step 3: edit your own answers or reuse the sample"),
        p(styles, "Body",
          "Write a markdown file with answers. Specific paths under ~/LocalAI/inbox/, "
          "explicit cloud policy, clear quality bar, named audience."),
        p(styles, "H2", "Step 4: submit the answers"),
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
        p(styles, "H1", "5. Using the Models tab"),
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
          "the day, run <code>bash scripts/day_unlock.sh \"reason\"</code> first."),
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
        p(styles, "H1", "6. Using the Schedule tab"),
        p(styles, "Body",
          "From the panel, click <b>Schedule</b>. Two sections:"),
        p(styles, "H2", "Status metrics"),
        p(styles, "Body",
          "Three independent checks of the launchd job: is the project plist present, is "
          "the plist installed in ~/Library/LaunchAgents, is it loaded in launchctl. "
          "All three off = auto-execution is OFF."),
        p(styles, "H2", "Edit times"),
        p(styles, "Body",
          "Three editable fields: <code>day_mode_start</code>, <code>night_mode_start</code>, "
          "<code>night_mode_end</code>. Format 24-hour HH:MM. Click Save to rewrite "
          "config/assistant.yaml atomically. Validation runs first; bad values are rejected "
          "with a clear error."),
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
        p(styles, "H1", "7. Day-unlock switch"),
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

    # --- Recipes -----------------------------------------------------
    story += [
        p(styles, "H1", "8. Recipe: morning brief"),
        p(styles, "Body",
          "The flagship use case. Goal: tomorrow morning, you read one markdown file and "
          "know what matters."),
        p(styles, "H2", "1. Drop your inputs"),
        code_block(
            styles,
            "# Drop yesterday's working materials into the inbox\n"
            "cp ~/Downloads/2026-W20-recap.md       ~/LocalAI/inbox/notes/\n"
            "cp ~/Downloads/2026-05-15-1on1.md      ~/LocalAI/inbox/transcripts/\n"
            "cp ~/Downloads/q3-staffing-draft.md    ~/LocalAI/inbox/docs/",
        ),
        p(styles, "H2", "2. Create the packet"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh \\\n'
            '   "Morning prep 2026-05-18" \\\n'
            '   "Prepare a private morning brief from this week\'s notes, '
            "transcripts, and docs. Surface priorities, decisions needed, risks, "
            "and meeting prep.\"",
        ),
        p(styles, "H2", "3. Answer the questions"),
        p(styles, "Body",
          "Edit a copy of <code>examples/sample_answers.md</code>; see section 13 for the "
          "exact text I'd suggest. Then:"),
        code_block(
            styles,
            "bash scripts/answer_questions.sh <packet_id> ~/answers/morning-2026-05-18.md",
        ),
        p(styles, "H2", "4. Verify ready"),
        p(styles, "Body",
          "Open the panel -> Dashboard. The packet should show "
          "<code>READY_FOR_OVERNIGHT</code> or <code>READY_HIGH_CONFIDENCE</code>."),
        p(styles, "H2", "5. Wait for night"),
        p(styles, "Body",
          "If launchd auto-execution is armed: nothing to do. If not, the brief generates "
          "when you run "
          "<code>LOCALAI_MODE=NIGHT_MODE bash scripts/run_ready_overnight.sh</code>."),
        p(styles, "Hint",
          "Once the execution graph is wired (next chunk of feature work), the output lands "
          "in ~/LocalAI/output/<date>/01_MORNING_BRIEF.md and a copy in "
          "~/Obsidian/LocalAI-ChiefOfStaff/01_Daily_Briefs/."),
        PageBreak(),
    ]

    story += [
        p(styles, "H1", "9. Recipe: meeting prep"),
        p(
            styles,
            "Body",
            "Goal: a single page for each upcoming meeting with the right context, agenda, "
            "stakeholder notes, and \"things to push for / things to listen for.\"",
        ),
        p(styles, "H2", "Setup"),
        code_block(
            styles,
            "# Stage the inputs\n"
            "cp ~/Downloads/2026-05-16-board-deck-draft.md  ~/LocalAI/inbox/docs/\n"
            "cp ~/Downloads/prior-board-notes.md             ~/LocalAI/inbox/notes/\n"
            "cp ~/Downloads/q2-financials-narrative.md      ~/LocalAI/inbox/docs/",
        ),
        p(styles, "H2", "Create packet"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh \\\n'
            '   "Board prep 2026-05-20" \\\n'
            '   "Prepare for the board meeting. Cover the Q2 narrative, '
            "any open decisions, and likely tough questions. High-stakes.\"",
        ),
        p(
            styles,
            "Body",
            "Note: the words \"board\" and \"high-stakes\" trigger "
            "<code>high_stakes=True</code> on the packet. The threshold becomes 0.90 "
            "(not 0.85) before execution.",
        ),
        p(styles, "H2", "Answers worth giving"),
        code_block(
            styles,
            "Outputs: meeting prep markdown file, decisions needed list,\n"
            "  one-page narrative summary.\n"
            "Sources: only ~/LocalAI/inbox/docs and ~/LocalAI/inbox/notes.\n"
            "  Treat Q2 financial narrative as authoritative.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me, then I share with the board.\n"
            "Assumptions: do not infer financial figures; surface ambiguity\n"
            "  rather than guess.\n"
            "Quality: optimize for factuality and defensibility. No hedging.\n"
            "Stop conditions: stop if any figure is unsourced, or if a decision\n"
            "  conflicts with a prior board minute.\n"
            "Success: I can walk in and answer every question without notes.",
        ),
        PageBreak(),
    ]

    story += [
        p(styles, "H1", "10. Recipe: decision capture from transcripts"),
        p(
            styles,
            "Body",
            "Goal: read meeting transcripts, extract the decisions, who owns each follow-up, "
            "and write them to the decisions vault.",
        ),
        p(styles, "H2", "Setup"),
        code_block(
            styles,
            "# Drop the transcripts (use OpenAI Whisper or similar to transcribe)\n"
            "cp ~/Downloads/2026-05-week-transcripts/*.md \\\n"
            "    ~/LocalAI/inbox/transcripts/",
        ),
        p(styles, "H2", "Create packet"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh \\\n'
            '   "Decision capture 2026-W20" \\\n'
            '   "Read this week\'s call transcripts. Extract every decision made, '
            "every action item with owner, and any items where ownership was left "
            "ambiguous. Write to my decisions vault.\"",
        ),
        p(styles, "H2", "Answers worth giving"),
        code_block(
            styles,
            "Outputs: decisions markdown, action items grouped by owner,\n"
            "  separate file flagging ambiguous ownership.\n"
            "Sources: only ~/LocalAI/inbox/transcripts.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me, then propagated to Obsidian 05_Decisions/.\n"
            "Assumptions: do NOT infer ownership when not stated. Flag instead.\n"
            "Quality: optimize for grounding. Every decision must cite a transcript\n"
            "  line range.\n"
            "Stop conditions: stop if a decision references a person not present\n"
            "  in the call.\n"
            "Success: every decision is traceable to its transcript moment.",
        ),
        PageBreak(),
    ]

    story += [
        p(styles, "H1", "11. Recipe: risk and blocker surfacing"),
        p(
            styles,
            "Body",
            "Goal: read recent notes/logs, flag anything that looks like a risk or blocker "
            "for review tomorrow morning.",
        ),
        p(styles, "H2", "Setup"),
        code_block(
            styles,
            "# A week's worth of notes\n"
            "cp ~/Downloads/2026-W20-*.md ~/LocalAI/inbox/notes/",
        ),
        p(styles, "H2", "Create packet"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh \\\n'
            '   "Risk scan 2026-W20" \\\n'
            '   "Read this week\'s notes and flag risks, blockers, and anything '
            "that looks like it could break next week. Sort by severity.\"",
        ),
        p(styles, "H2", "Answers worth giving"),
        code_block(
            styles,
            "Outputs: 05_RISKS_AND_BLOCKERS.md with severity + recommended action\n"
            "  for each item.\n"
            "Sources: only ~/LocalAI/inbox/notes from this week.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me only.\n"
            "Assumptions: rate severity using a low/medium/high scale. Label\n"
            "  assumptions about external context (e.g., vendor timelines).\n"
            "Quality: optimize for completeness over polish. Better to over-flag.\n"
            "Stop conditions: never stop &mdash; flag everything, even uncertain.\n"
            "Success: nothing important slipped through this week.",
        ),
        PageBreak(),
    ]

    story += [
        p(styles, "H1", "12. Recipe: code task using qwen3-coder"),
        p(
            styles,
            "Body",
            "Goal: feed a code task to <code>local-coder</code> (qwen3-coder:30b) for "
            "structured review, refactor proposal, or test generation.",
        ),
        p(styles, "H2", "Setup"),
        code_block(
            styles,
            "# Copy the file or directory into the inbox\n"
            "cp ~/Projects/some-repo/src/payments.py  ~/LocalAI/inbox/docs/\n"
            "cp ~/Projects/some-repo/tests/payments_test.py  ~/LocalAI/inbox/docs/",
        ),
        p(styles, "H2", "Create packet"),
        code_block(
            styles,
            'bash scripts/create_work_packet.sh \\\n'
            '   "Payments refactor review" \\\n'
            '   "Review payments.py for clarity issues, suggest a refactor that '
            "improves testability, and propose three additional test cases that the "
            "current tests miss.\"",
        ),
        p(styles, "H2", "Answers worth giving"),
        code_block(
            styles,
            "Outputs: review markdown with three sections: clarity issues,\n"
            "  refactor proposal (with code), additional tests (with code).\n"
            "Sources: ~/LocalAI/inbox/docs/payments.py and payments_test.py.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me, then I share with a teammate.\n"
            "Assumptions: stay within the existing dependency set. Do not propose\n"
            "  introducing new libraries.\n"
            "Quality: optimize for actionability. Each suggestion must be applyable\n"
            "  in under 10 minutes.\n"
            "Stop conditions: stop if the file references a config file not provided.\n"
            "Success: I can apply the suggestions today and ship.",
        ),
        p(
            styles,
            "Hint",
            "Today, the orchestrator routes code-classified tasks to <code>local-coder</code> "
            "automatically. The classification is part of the (scaffolded) execution graph. "
            "Until that's wired, you can manually load <code>qwen3-coder:30b</code> in the "
            "Models tab and quick-test prompt the review."
        ),
        PageBreak(),
    ]

    # --- Sample answer files ----------------------------------------
    story += [
        p(styles, "H1", "13. Sample answer files for every recipe"),
        p(
            styles,
            "Body",
            "Copy these as starting points; adapt them to your specific work. The parser is "
            "forgiving about wording but cares about explicit cloud policy, explicit paths "
            "under ~/LocalAI/inbox/, and recognizable key labels (Outputs, Sources, Cloud, "
            "Audience, Quality, Assumptions, Stop conditions, Success).",
        ),
        p(styles, "H2", "Morning brief template"),
        code_block(
            styles,
            "Outputs: 01_MORNING_BRIEF.md, 02_TODAY_PRIORITIES.md,\n"
            "  04_DECISIONS_NEEDED.md, 05_RISKS_AND_BLOCKERS.md,\n"
            "  07_MEETING_PREP.md.\n"
            "Sources: only ~/LocalAI/inbox/notes and ~/LocalAI/inbox/transcripts\n"
            "  and ~/LocalAI/inbox/docs. Skip anything older than one week.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me only.\n"
            "Assumptions: infer low-risk priorities but label every assumption.\n"
            "Quality: factuality > completeness > polish.\n"
            "Stop conditions: stop for missing sources or unclear ownership.\n"
            "Success: I read it in five minutes and know what to do first.",
        ),
        p(styles, "H2", "High-stakes meeting prep template"),
        code_block(
            styles,
            "Outputs: 07_MEETING_PREP.md (one section per meeting), plus a\n"
            "  separate one-page narrative summary for sharing.\n"
            "Sources: only ~/LocalAI/inbox/docs and ~/LocalAI/inbox/notes.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me, then I share with named participants.\n"
            "Assumptions: do not infer financial or commitment figures.\n"
            "Quality: defensibility > brevity.\n"
            "Stop conditions: stop if any figure is unsourced.\n"
            "Success: I can answer any question without notes.",
        ),
        p(styles, "H2", "Decision capture template"),
        code_block(
            styles,
            "Outputs: decisions.md, action_items_by_owner.md,\n"
            "  ambiguous_ownership.md.\n"
            "Sources: only ~/LocalAI/inbox/transcripts.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me, propagated to Obsidian 05_Decisions/.\n"
            "Assumptions: do NOT infer ownership. Flag instead.\n"
            "Quality: every decision cites a transcript line range.\n"
            "Stop conditions: stop if a decision references a person not in the call.\n"
            "Success: every decision is traceable to its transcript moment.",
        ),
        p(styles, "H2", "Risk scan template"),
        code_block(
            styles,
            "Outputs: 05_RISKS_AND_BLOCKERS.md sorted by severity, with\n"
            "  recommended action per item.\n"
            "Sources: only ~/LocalAI/inbox/notes from this week.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me only.\n"
            "Assumptions: rate severity low/medium/high. Label assumptions.\n"
            "Quality: completeness > polish. Over-flag.\n"
            "Stop conditions: never stop; flag everything, even uncertain.\n"
            "Success: nothing important slipped through.",
        ),
        p(styles, "H2", "Code task template"),
        code_block(
            styles,
            "Outputs: review.md with three sections: clarity, refactor proposal,\n"
            "  additional test cases.\n"
            "Sources: ~/LocalAI/inbox/docs/<file>.py and any provided tests.\n"
            "Cloud: do not use cloud fallback.\n"
            "Audience: me, then a named teammate.\n"
            "Assumptions: stay within existing dependency set.\n"
            "Quality: actionability > thoroughness. Each suggestion applyable\n"
            "  in under ten minutes.\n"
            "Stop conditions: stop if the file references missing context.\n"
            "Success: I can apply today.",
        ),
        PageBreak(),
    ]

    # --- Do / Don't --------------------------------------------------
    story += [
        p(styles, "H1", "14. Do / Don't"),
        p(styles, "H2", "Do"),
        *bullets(
            styles,
            [
                "Keep input files under ~/LocalAI/inbox/. That's the only place this system reads from.",
                "Be specific in clarification answers. Explicit paths, single-line key:value lines parse better than prose.",
                "Mark packets as high_stakes (board, CEO, legal, investor) when they need the 0.90 readiness bar.",
                "Use day_unlock deliberately, lock again when done. The red banner is your reminder.",
                "Run <code>bash scripts/run_tests.sh</code> before committing changes.",
                "Read AGENTS.md if you're going to modify this repo.",
                "Pull models on stable Wi-Fi; qwen3:30b-a3b is ~18 GB.",
                "Unload models when you're done; 30 GB of idle VRAM is wasted budget.",
                "Keep your Obsidian vault open while reviewing memory candidates.",
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
                "Don't load two 30B models simultaneously and expect snappy inference.",
                "Don't assume <code>stop_services.sh</code> stops everything &mdash; it stops Docker only.",
            ],
        ),
        PageBreak(),
    ]

    # --- Memory budgeting --------------------------------------------
    story += [
        p(styles, "H1", "15. Memory budgeting (what to load when)"),
        p(
            styles,
            "Body",
            "Your M2 Max has 77.8 GB Metal VRAM. Comfortable budgets:",
        ),
        section_table(
            [
                ["Scenario", "Loaded models", "VRAM", "Why"],
                ["Spot-check quality", "local-reasoner only", "~5 GB", "Fast first inference. Good for one-off checks."],
                ["Drafting work", "local-main only", "~17 GB", "30B MoE for general drafting. Comfortable margin."],
                ["Code review", "local-coder only", "~17 GB", "Swap to coder when working on code tasks."],
                ["Overnight pipeline", "local-main + local-reasoner", "~22 GB", "Primary model + evaluator. Default night profile."],
                ["Quality-gated retry", "local-main, local-reasoner, local-secondary on-demand", "~22-60 GB", "70B loads when local-main output fails the evaluator."],
                ["Trying everything at once", "all four loaded", "~60+ GB", "Don't. You'll feel it."],
            ],
            col_widths=[1.5 * inch, 1.7 * inch, 0.8 * inch, 2.5 * inch],
        ),
        Spacer(1, 0.2 * inch),
        p(styles, "Hint",
          "Keep-alive defaults: Load button = 30 minutes; Quick test = 5 minutes. Ollama "
          "auto-unloads idle models after the timer expires, so even if you forget to "
          "unload, VRAM frees up on its own within half an hour."),
        PageBreak(),
    ]

    # --- Troubleshooting --------------------------------------------
    story += [
        p(styles, "H1", "16. Troubleshooting"),
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
                ["Quick test prompt takes 30+ seconds", "First inference after a load is cold. Subsequent calls 5-10x faster. Also: are two 30B models loaded? Unload one."],
                ["Open WebUI won't open at :3000", "Container is part of the Docker stack. Run bash scripts/start_services.sh."],
                ["Brew says ollama started but curl fails", "Race condition. Wait 3-5 seconds and retry. If still failing after 10s: brew services list | grep ollama (should say started)."],
                ["I see two ollama serve processes", "Probably one from brew + one from your earlier foreground run. brew services stop ollama then start again."],
            ],
            col_widths=[2.3 * inch, 4.2 * inch],
        ),
        PageBreak(),
    ]

    # --- Recovery scenarios -----------------------------------------
    story += [
        p(styles, "H1", "17. Recovery scenarios"),
        p(styles, "H2", "Streamlit crashed mid-session"),
        code_block(
            styles,
            "# Diagnose: nothing on the port? probably dead.\n"
            "lsof -nP -iTCP:8501 -sTCP:LISTEN\n"
            "\n"
            "# Restart\n"
            "bash scripts/start_control_panel.sh\n"
            "\n"
            "# Your work packets are in Postgres &mdash; nothing lost.",
        ),
        p(styles, "H2", "Ollama daemon died, models you had loaded are gone"),
        code_block(
            styles,
            "brew services restart ollama\n"
            "# Re-load the model you were testing\n"
            "ollama list                          # confirm tag still on disk\n"
            "# In the panel, click Load again, OR:\n"
            "ollama run <tag> 'hello'              # forces load + responds",
        ),
        p(styles, "H2", "Temporal container is restarting"),
        code_block(
            styles,
            "docker logs --tail=30 localai-temporal\n"
            "# If 'dynamic config' error, the path in compose was wrong; should be\n"
            "# config/dynamicconfig/docker.yaml (fixed in commit a2d6485).\n"
            "docker compose up -d --force-recreate temporal",
        ),
        p(styles, "H2", "I think launchd is running my packets but I didn't arm it"),
        code_block(
            styles,
            "launchctl list | grep com.localai.orchestrator.nightly\n"
            "# Empty output = not loaded. You're not armed.\n"
            "# If something is in the output:\n"
            "launchctl unload \\\n"
            "  ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist",
        ),
        p(styles, "H2", "I accidentally pulled a 70B model on slow Wi-Fi"),
        code_block(
            styles,
            "# Cancel the pull\n"
            "pkill -f 'ollama pull llama3.3'\n"
            "\n"
            "# Optional: remove the partial layers from disk\n"
            "ollama rm llama3.3:70b",
        ),
        p(styles, "H2", "I want to start completely fresh"),
        code_block(
            styles,
            "# Stop everything\n"
            "bash scripts/stop_services.sh\n"
            "brew services stop ollama\n"
            "kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t) 2>/dev/null\n"
            "\n"
            "# NUCLEAR: also wipe all volumes (you lose your work packets!)\n"
            "docker compose down -v\n"
            "\n"
            "# Then bring it all back up from scratch\n"
            "bash scripts/start_services.sh\n"
            "brew services start ollama",
        ),
        PageBreak(),
    ]

    # --- Weekly maintenance -----------------------------------------
    story += [
        p(styles, "H1", "18. Weekly maintenance checklist"),
        p(styles, "Body", "Five-minute weekly upkeep to keep the system healthy:"),
        *bullets(
            styles,
            [
                "<b>Empty the inbox</b>: archive consumed inputs from <code>~/LocalAI/inbox/</code> to <code>~/LocalAI/archive/</code> so next week's pulls are clean.",
                "<b>Review memory candidates</b>: open <code>~/Obsidian/LocalAI-ChiefOfStaff/00_Inbox/Memory_Review/</code> and approve or trash each candidate.",
                "<b>Prune old output directories</b>: <code>~/LocalAI/output/YYYY-MM-DD/</code> older than four weeks can be deleted. Anything important should already be in your vault.",
                "<b>Check disk usage</b>: <code>du -sh ~/.ollama/models</code> &mdash; if you have unused tags, <code>ollama rm &lt;tag&gt;</code> them.",
                "<b>Test suite</b>: <code>bash scripts/run_tests.sh</code> after any code change, even small ones.",
                "<b>Update if needed</b>: <code>brew upgrade ollama</code> &mdash; the keep-alive payload behavior changed across versions; we send '0s' string to be compatible.",
                "<b>Lock day-unlock</b>: <code>bash scripts/day_lock.sh</code> as a hygiene reset, even if you don't think it's on.",
                "<b>Backup your vault</b>: rsync, Time Machine, whatever you use. The orchestrator does not back up the vault for you.",
            ],
        ),
        PageBreak(),
    ]

    # --- Safety rules summary ---------------------------------------
    story += [
        p(styles, "H1", "19. Safety rules at a glance"),
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
                ["Unknown model tags fall back to local-main", "ollama_admin.resolve_group_for_tag (fail-closed)"],
            ],
            col_widths=[3.4 * inch, 3.1 * inch],
        ),
        PageBreak(),
    ]

    # --- Tips and tricks --------------------------------------------
    story += [
        p(styles, "H1", "20. Tips and tricks"),
        *bullets(
            styles,
            [
                "<b>Long pulls survive a closed terminal.</b> Wrap any <code>ollama pull</code> in <code>nohup ... > ~/LocalAI/logs/pull-&lt;tag&gt;.log 2>&amp;1 &amp;</code>. Close the window, come back later, check <code>ollama list</code>.",
                "<b>Parallel pulls share bandwidth.</b> Three pulls in parallel = each gets a third the speed. Total wall-clock the same. Serializing (one at a time) gets you the smallest model in front of you fastest.",
                "<b>Keep your laptop awake.</b> Use Amphetamine or <code>nohup caffeinate -i &amp;</code> for unattended overnight pulls. Closed lids suspend network on Wi-Fi-only Macs.",
                "<b>The day-unlock flag is just a file.</b> If <code>day_lock.sh</code> can't reach you (you're SSH'd in, weird shell), <code>rm ~/LocalAI/state/day_unlock.flag</code> does the same thing.",
                "<b>Read the audit log first when debugging</b>: <code>09_AUDIT_LOG.md</code> shows which models ran, what the evaluator said, and where each output came from.",
                "<b>Your Obsidian vault is the real long-term memory.</b> Don't be precious about ~/LocalAI/output/ &mdash; treat that as scratch.",
                "<b>The panel updates on rerun, not on a timer.</b> After flipping any external state (unlock, services up/down), Cmd+R the browser tab.",
                "<b>SQL is your friend.</b> Postgres has your whole history. <code>docker exec -it localai-postgres psql -U localai -d localai</code> and run <code>SELECT</code>s freely.",
                "<b>Save your packet ids.</b> <code>create_work_packet.sh</code> prints the UUID once. Copy it. You'll need it for <code>answer_questions.sh</code>.",
                "<b>Two terminals open is the minimum.</b> One for services + scripts, one for tail-following logs. Three is better.",
            ],
        ),
        PageBreak(),
    ]

    # --- Mental model ------------------------------------------------
    story += [
        p(styles, "H1", "21. One paragraph to remember"),
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
