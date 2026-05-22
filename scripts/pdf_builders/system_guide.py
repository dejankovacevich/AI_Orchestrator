"""System Guide PDF — section builders.

This module owns the full content of the System Guide. To edit a section:
locate the corresponding ``p(styles, "H1", "N. <title>")`` and edit the
following block. The function returns a Platypus *story* list (paragraphs,
tables, spacers, page breaks) that ``build_document`` renders.
"""

from __future__ import annotations

from datetime import date

from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Spacer

from scripts.pdf_builders.helpers import bullets, code_block, p, section_table


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
            "db/migrations/001_init.sql + assistant_core/storage/",
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
            "unlocked_by: user@host\n"
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
            "...     file_path='~/LocalAI/inbox/cloud_review/brief.cloud.md',\n"
            "...     cloud_fallback_enabled=False,   # config gate -> raises\n"
            "...     work_packet_cloud_allowed=True,\n"
            "...     high_stakes=True,\n"
            "...     local_quality_gate_failed=True,\n"
            "...     anthropic_api_key='sk-...',\n"
            "...     daily_budget_remaining=True,\n"
            "...     cloud_review_dir='~/LocalAI/inbox/cloud_review',\n"
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
            "1. **Decide Q3 staffing for the Scope1 project.** Three weeks of notes\n"
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
            "- ~/LocalAI/inbox/transcripts/2026-05-15-scope1-1on1.md\n"
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
                ["Overnight execution graph (top-level steps)", "Implemented", "11-step pipeline in execution/graph.py iterated by the thin runner."],
                ["File classifier -> model routing", "Implemented", "Code suffixes -> local-coder; everything else -> local-main."],
                ["Secondary local retry chain", "Implemented", "Primary fails evaluator -> retry on local-secondary; promotes retry output when it passes."],
                ["Task-type prompts (morning_brief, code_review)", "Implemented", "Per-task extract + synthesize templates. Auto-detected from request text; CLI --task-type to override. test_generation/doc_generation/decision_capture/risk_scan exist as types and route to dedicated output filenames, falling back to morning_brief prompts until their templates are written."],
                ["Citation / grounding enforcement", "Implemented", "WorkPacket.grounding_required=True makes the evaluator require >=3 'Source:' lines per extraction. Auto-set when request mentions 'cite source', 'every claim', 'regulated', 'auditable'."],
                ["Audit export (one packet -> single JSON)", "Implemented", "scripts/export_audit.sh dumps the full Postgres audit trail for one packet, reviewer-ready."],
                ["Indie-dev one-shot code review", "Implemented", "scripts/review_code.sh: copy file -> packet with task_type=code_review -> synchronous execution -> review markdown in ~/LocalAI/output and ~/Obsidian vault."],
                ["Cloud-review gate", "Implemented", "Files where both local attempts fail are catalogued in 08_CLOUD_REVIEW_CANDIDATES.md with the gate verdict. Default-off: no cloud spend until cloud_fallback_enabled + ANTHROPIC_API_KEY are set."],
                ["Claude cloud-review caller (actual HTTP)", "Implemented", "When all six gates pass, the gate makes one LiteLLM call per flagged file, writes the response under _cloud, and records estimated cost."],
                ["Self-consistency / self-critique loops", "Scaffolded", "Extraction is single-shot today. N-of-3 voting and self-critique are the next quality lift."],
                ["Pause/resume UI", "Scaffolded", "Buttons disabled. DB statuses exist."],
                ["Semantic memory indexing", "Scaffolded", "Chroma client exists. No indexer yet."],
                ["Drafted messages", "Scaffolded", "Output template exists; nothing fills it yet."],
                ["PDF documentation builder", "Implemented", "scripts/build_pdfs.py (thin entry) + scripts/pdf_builders/ package render all three PDFs."],
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
    storage/             Postgres CRUD package (by-entity submodules)
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
                ["add a Postgres column", "db/migrations/ (add a new file) + assistant_core/storage/"],
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


