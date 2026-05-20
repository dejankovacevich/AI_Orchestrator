"""Technical Reference PDF — section builders.

By-entity walkthrough of every meaningful file, service, table, and state
location. Use this as a reference; do not read end-to-end. Add sections by
appending to the TOC list and writing the corresponding ``p(styles, "H1",
"N. <title>")`` block below.
"""

from __future__ import annotations

from datetime import date

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer

from scripts.pdf_builders.helpers import bullets, code_block, p, section_table


def build_technical_reference(styles) -> list:
    """A by-entity walkthrough of every meaningful file, service, table, and
    state location in the system. The goal is: by the end, you can answer
    \"what does X do and why is it here\" for every X in the project."""

    story = []

    # --- Cover ---
    story += [
        Spacer(1, 2.0 * inch),
        p(styles, "TitleBig", "Local AI Orchestrator"),
        p(styles, "SubtitleBig", "Technical Reference"),
        Spacer(1, 0.3 * inch),
        p(styles, "CoverMeta",
          "Every file. Every service. Every table. Every state location."),
        p(styles, "CoverMeta",
          "Use as a reference; do not read end-to-end. Jump to whatever you want to understand."),
        Spacer(1, 0.5 * inch),
        p(styles, "CoverMeta", f"Generated: {date.today().isoformat()}"),
        PageBreak(),
    ]

    # --- TOC ---
    toc_items = [
        "1. How to read this document",
        "2. Service: Docker Compose",
        "3. Service: PostgreSQL",
        "4. Service: Temporal",
        "5. Service: Ollama",
        "6. Service: LiteLLM",
        "7. Service: Open WebUI",
        "8. Service: Streamlit control panel",
        "9. Service: Temporal worker (Python long-running)",
        "10. Repository: root-level files",
        "11. Repository: assistant_core/__init__.py and top-level modules",
        "12. Repository: assistant_core/clarification/",
        "13. Repository: assistant_core/execution/",
        "14. Repository: assistant_core/llm/",
        "15. Repository: assistant_core/memory/",
        "16. Repository: assistant_core/temporal_app/",
        "17. Repository: app/control_panel.py",
        "18. Repository: scripts/ (every shell script)",
        "19. Repository: config/ (every YAML)",
        "20. Repository: db/migrations/",
        "21. Repository: tests/ (every test file)",
        "22. Repository: docs/",
        "23. External state: ~/LocalAI/",
        "24. External state: ~/Obsidian/LocalAI-ChiefOfStaff/",
        "25. State files: day_unlock.flag and others",
        "26. Environment variables in depth",
        "27. The complete port map",
        "28. Logging: where logs go, what they contain",
        "29. Inspection cheatsheet: SQL + docker + ollama",
    ]
    story += [p(styles, "H1", "Table of contents")]
    story += [Paragraph(item, styles["TocItem"]) for item in toc_items]
    story += [PageBreak()]

    # --- 1. How to read --------------------------------------------
    story += [
        p(styles, "H1", "1. How to read this document"),
        p(
            styles,
            "Body",
            "This is a reference, not a tutorial. The System Guide explains the "
            "<i>shape</i> of the system and the Onboarding shows you <i>how to use</i> it; "
            "this document tells you <i>what every individual piece does</i> and why it is "
            "there. It is structured by entity, not by use case. Jump to whatever section "
            "answers the question you have right now.",
        ),
        p(styles, "H2", "Three levels of detail in three documents"),
        section_table(
            [
                ["Document", "Audience question it answers", "Reading mode"],
                ["System Guide", "\"What is this system? How does it think?\"", "Read once, cover to cover."],
                ["Onboarding", "\"How do I use this thing today?\"", "Skim once, then return for recipes."],
                ["Technical Reference (this doc)", "\"What exactly does THIS file/service/table do?\"", "Reference. Search. Never read end-to-end."],
            ],
            col_widths=[1.8 * inch, 3.0 * inch, 1.7 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Conventions used below"),
        *bullets(
            styles,
            [
                "<b>Path</b>: the file path relative to project root, or absolute for things outside the repo.",
                "<b>What it does</b>: literal description, present tense, what the entity is responsible for.",
                "<b>Why it exists</b>: design rationale; what would break or be missing without it.",
                "<b>How to inspect</b>: a command, query, or path to read what's currently true.",
            ],
        ),
        PageBreak(),
    ]

    # --- 2. Docker Compose -----------------------------------------
    story += [
        p(styles, "H1", "2. Service: Docker Compose"),
        p(styles, "H2", "What Docker is doing for us"),
        p(
            styles,
            "Body",
            "Docker is the container runtime; <b>Docker Compose</b> is the multi-service "
            "orchestrator. In this project we use Compose to start, stop, and configure "
            "four stateful services as containers running side-by-side on your Mac: "
            "<b>Postgres</b>, <b>Temporal</b>, <b>Temporal UI</b>, and <b>Open WebUI</b>. "
            "Each container is an isolated process tree with its own filesystem, but "
            "they share a private Docker network so they can reach each other by name."
        ),
        p(styles, "H2", "Why containers (rather than brew install)"),
        p(
            styles,
            "Body",
            "Postgres and Temporal have non-trivial initialization (schema setup, dynamic "
            "config, startup ordering). Containers package the init logic, environment, and "
            "the right version. Running them via Compose means: same versions across "
            "machines, no host pollution, one command up, one command down, named volumes "
            "to persist data even when the container is destroyed.",
        ),
        p(styles, "H2", "The compose file in detail"),
        p(styles, "Body", "<code>docker-compose.yml</code> at the repo root defines four services. Highlights:"),
        section_table(
            [
                ["Service", "Image", "Host port (127.0.0.1)", "Container port", "Purpose"],
                ["postgres", "postgres:16", "5432", "5432", "Operational state DB"],
                ["temporal", "temporalio/auto-setup:1.26", "7233", "7233", "Workflow engine gRPC"],
                ["temporal-ui", "temporalio/ui:2.31.2", "8233", "8080", "Web UI for Temporal"],
                ["open-webui", "ghcr.io/open-webui/open-webui:main", "3000", "8080", "Chat UI against Ollama"],
            ],
            col_widths=[1.1 * inch, 2.0 * inch, 1.2 * inch, 1.0 * inch, 1.3 * inch],
        ),
        Spacer(1, 0.1 * inch),
        p(styles, "H2", "Networks"),
        p(
            styles,
            "Body",
            "Compose auto-creates a private bridge network named "
            "<code>local-ai-orchestrator_default</code>. Containers reach each other by "
            "service name: Temporal connects to <code>postgres:5432</code> internally, "
            "Temporal UI to <code>temporal:7233</code>, Open WebUI to "
            "<code>host.docker.internal:11434</code> (the host's Ollama). Host ports are "
            "all bound to <code>127.0.0.1</code> only &mdash; nothing exposed to the LAN.",
        ),
        p(styles, "H2", "Volumes"),
        section_table(
            [
                ["Volume", "Container path", "What it holds"],
                ["postgres_data", "/var/lib/postgresql/data", "Your work packets, runs, audit data. Survives container recreates."],
                ["temporal_data", "/etc/temporal", "Temporal config (mostly bundled in image)."],
                ["open_webui_data", "/app/backend/data", "Open WebUI's chat history and user settings."],
                ["./db/migrations (bind mount)", "/docker-entrypoint-initdb.d", "Read-only. SQL files run by Postgres on first boot."],
            ],
            col_widths=[1.7 * inch, 2.0 * inch, 2.8 * inch],
        ),
        Spacer(1, 0.1 * inch),
        p(styles, "H2", "Important behaviors"),
        *bullets(
            styles,
            [
                "<b>First boot</b>: Postgres sees <code>db/migrations/001_init.sql</code> mounted in its init dir, runs it, creates the seven tables.",
                "<b>Subsequent boots</b>: Postgres ignores init scripts (data dir already initialized). Schema changes require new migration files (or DROP + re-mount).",
                "<b>Healthchecks</b>: <code>postgres</code> has a healthcheck via <code>pg_isready</code>. <code>temporal</code> depends_on postgres with <code>condition: service_healthy</code> so it waits for the DB.",
                "<b>The Temporal dynamic-config bug</b>: the compose was originally pointing at <code>config/dynamicconfig/development-sql.yaml</code> (doesn't exist in image 1.26). Fixed to <code>docker.yaml</code> in commit a2d6485.",
                "<b>stop_services.sh stops these four containers ONLY</b>. Streamlit, Ollama, and host Python processes are not affected.",
            ],
        ),
        p(styles, "H2", "How to inspect"),
        code_block(
            styles,
            "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'\n"
            "docker logs --tail=50 localai-postgres\n"
            "docker logs --tail=50 localai-temporal\n"
            "docker compose config       # print the resolved compose file\n"
            "docker volume ls            # list named volumes\n"
            "docker network inspect local-ai-orchestrator_default",
        ),
        PageBreak(),
    ]

    # --- 3. PostgreSQL ----------------------------------------------
    story += [
        p(styles, "H1", "3. Service: PostgreSQL"),
        p(styles, "H2", "What Postgres is doing for us"),
        p(
            styles,
            "Body",
            "PostgreSQL is the orchestrator's <b>operational state store</b>. It holds "
            "every work packet you create, every clarification question generated, every "
            "overnight run, every model call, every evaluation, every artifact pointer, "
            "and every memory candidate. It does <i>not</i> hold your input notes (those "
            "stay in <code>~/LocalAI/inbox/</code>) or the long-term knowledge layer "
            "(that's Obsidian). It holds the orchestrator's view of its own work.",
        ),
        p(styles, "H2", "Why Postgres (rather than SQLite or files)"),
        p(
            styles,
            "Body",
            "Three reasons: durable relational integrity (work packets, questions, runs, "
            "and model calls all reference each other and we want foreign keys enforced); "
            "JSON columns (policies are stored as JSONB so we can evolve schema without "
            "migrations); and Temporal needs Postgres anyway for its own state, so "
            "running one DB serves both.",
        ),
        p(styles, "H2", "Connection details"),
        section_table(
            [
                ["Property", "Value"],
                ["Connection string", "postgresql://localai:localai@localhost:5432/localai"],
                ["User", "localai"],
                ["Password", "localai (local-only; don't expose this DB)"],
                ["Database name", "localai"],
                ["Postgres version", "16 (postgres:16 image)"],
                ["Container name", "localai-postgres"],
            ],
            col_widths=[1.8 * inch, 4.7 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Schema overview (7 tables)"),
        section_table(
            [
                ["Table", "Rows = ", "Relations"],
                ["work_packets", "one per request you create", "parent to everything else"],
                ["clarification_questions", "one per question generated", "FK -> work_packets"],
                ["execution_runs", "one per overnight invocation", "FK -> work_packets"],
                ["model_calls", "one per model API call", "FK -> work_packets, execution_runs"],
                ["evaluations", "one per evaluator pass", "FK -> work_packets, execution_runs"],
                ["artifacts", "one per generated file", "FK -> work_packets, execution_runs"],
                ["memory_candidates", "one per candidate from outputs", "FK -> artifacts"],
            ],
            col_widths=[1.9 * inch, 2.1 * inch, 2.5 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Table: work_packets &mdash; the central record"),
        code_block(
            styles,
            "CREATE TABLE work_packets (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    title TEXT NOT NULL,             -- your title at creation\n"
            "    objective TEXT,                  -- the description / objective\n"
            "    status TEXT NOT NULL,            -- DRAFT, UNDERDEFINED,\n"
            "                                     -- NEEDS_CLARIFICATION,\n"
            "                                     -- READY_FOR_OVERNIGHT,\n"
            "                                     -- READY_HIGH_CONFIDENCE,\n"
            "                                     -- PAUSED, RESUME_REQUESTED,\n"
            "                                     -- RUNNING, COMPLETED, FAILED\n"
            "    readiness_score NUMERIC,         -- 0.0 - 1.0\n"
            "    high_stakes BOOLEAN DEFAULT FALSE,\n"
            "    cloud_policy JSONB,              -- e.g. {allowed: false, explicit: true}\n"
            "    source_policy JSONB,             -- e.g. {scope: '~/LocalAI/inbox/notes'}\n"
            "    output_policy JSONB,             -- e.g. {format: 'markdown brief'}\n"
            "    created_at TIMESTAMPTZ DEFAULT now(),\n"
            "    updated_at TIMESTAMPTZ DEFAULT now(),\n"
            "    raw_user_request TEXT,           -- the description you typed\n"
            "    structured_yaml TEXT             -- yaml-serialized full pydantic model\n"
            ");",
        ),
        p(styles, "H2", "Table: clarification_questions"),
        code_block(
            styles,
            "CREATE TABLE clarification_questions (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    work_packet_id UUID REFERENCES work_packets(id),\n"
            "    round_number INTEGER,    -- 1 = first question round; can grow if rescored\n"
            "    category TEXT,           -- 'objective', 'outputs', 'sources', 'privacy/cloud',\n"
            "                             -- 'quality', 'audience', 'assumptions',\n"
            "                             -- 'escalation', 'stop conditions'\n"
            "    question TEXT,           -- the strong-question text\n"
            "    priority INTEGER,        -- 50 - 100\n"
            "    blocking BOOLEAN,        -- true for the 4 hard dimensions\n"
            "    answered BOOLEAN DEFAULT FALSE,\n"
            "    answer TEXT,             -- the raw markdown answer block\n"
            "    created_at TIMESTAMPTZ DEFAULT now(),\n"
            "    answered_at TIMESTAMPTZ\n"
            ");",
        ),
        p(styles, "H2", "Table: execution_runs"),
        code_block(
            styles,
            "CREATE TABLE execution_runs (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    work_packet_id UUID REFERENCES work_packets(id),\n"
            "    temporal_workflow_id TEXT,  -- the workflow id submitted to Temporal\n"
            "    status TEXT,                -- RUNNING, COMPLETED, FAILED, CANCELLED\n"
            "    mode TEXT,                  -- DAY_MODE, NIGHT_MODE, MANUAL_RESUME\n"
            "    started_at TIMESTAMPTZ,\n"
            "    completed_at TIMESTAMPTZ,\n"
            "    error_summary TEXT          -- last error message, if any\n"
            ");",
        ),
        p(styles, "H2", "Table: model_calls (audit)"),
        code_block(
            styles,
            "CREATE TABLE model_calls (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    execution_run_id UUID REFERENCES execution_runs(id),\n"
            "    work_packet_id UUID REFERENCES work_packets(id),\n"
            "    file_path TEXT,           -- the source file this call is about\n"
            "    task_type TEXT,           -- 'general', 'coding', 'reasoning_check', ...\n"
            "    model_group TEXT,         -- 'local-main', 'local-coder', ...\n"
            "    actual_model TEXT,        -- e.g. 'qwen3:30b-a3b'\n"
            "    local_or_cloud TEXT,      -- 'local' or 'cloud'\n"
            "    prompt_chars INTEGER,\n"
            "    response_chars INTEGER,\n"
            "    success BOOLEAN,\n"
            "    error TEXT,\n"
            "    created_at TIMESTAMPTZ DEFAULT now()\n"
            ");",
        ),
        p(styles, "H2", "Table: evaluations"),
        code_block(
            styles,
            "CREATE TABLE evaluations (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    execution_run_id UUID REFERENCES execution_runs(id),\n"
            "    work_packet_id UUID REFERENCES work_packets(id),\n"
            "    file_path TEXT,\n"
            "    quality_score NUMERIC,        -- 0.0 - 1.0\n"
            "    grounding_score NUMERIC,\n"
            "    completeness_score NUMERIC,\n"
            "    actionability_score NUMERIC,\n"
            "    contradiction_score NUMERIC,\n"
            "    hallucination_risk TEXT,      -- 'low', 'medium', 'high'\n"
            "    needs_retry BOOLEAN,\n"
            "    recommended_next_step TEXT,   -- 'pass', 'retry_local_secondary',\n"
            "                                  -- 'reasoning_check', 'cloud_review',\n"
            "                                  -- 'human_review'\n"
            "    reason TEXT,\n"
            "    created_at TIMESTAMPTZ DEFAULT now()\n"
            ");",
        ),
        p(styles, "H2", "Table: artifacts"),
        code_block(
            styles,
            "CREATE TABLE artifacts (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    execution_run_id UUID REFERENCES execution_runs(id),\n"
            "    work_packet_id UUID REFERENCES work_packets(id),\n"
            "    artifact_type TEXT,        -- 'morning_brief', 'priorities', etc.\n"
            "    file_path TEXT,            -- absolute path under ~/LocalAI/output/\n"
            "    obsidian_path TEXT,        -- absolute path inside vault\n"
            "    created_at TIMESTAMPTZ DEFAULT now()\n"
            ");",
        ),
        p(styles, "H2", "Table: memory_candidates"),
        code_block(
            styles,
            "CREATE TABLE memory_candidates (\n"
            "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    source_artifact_id UUID REFERENCES artifacts(id),\n"
            "    candidate_text TEXT,\n"
            "    destination_suggestion TEXT,    -- where in the vault it should land\n"
            "    confidence TEXT,                -- 'low', 'medium', 'high'\n"
            "    memory_type TEXT,               -- 'confirmed', 'derived', 'inferred'\n"
            "    approved BOOLEAN DEFAULT FALSE,\n"
            "    created_at TIMESTAMPTZ DEFAULT now()\n"
            ");",
        ),
        p(styles, "H2", "Indexes"),
        section_table(
            [
                ["Index", "Speeds up"],
                ["idx_work_packets_status", "filtering by status (READY, RUNNING, etc.)"],
                ["idx_questions_work_packet", "loading all questions for one packet"],
                ["idx_execution_runs_work_packet", "loading all runs for one packet"],
                ["idx_artifacts_work_packet", "listing artifacts of one packet"],
            ],
            col_widths=[3.0 * inch, 3.5 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "How to inspect"),
        code_block(
            styles,
            "docker exec -it localai-postgres psql -U localai -d localai\n"
            "\n"
            "-- inside psql:\n"
            "\\dt                            -- list tables\n"
            "\\d work_packets                -- describe a table\n"
            "SELECT id, title, status, readiness_score\n"
            "  FROM work_packets ORDER BY created_at DESC LIMIT 10;\n"
            "SELECT count(*) FROM clarification_questions WHERE answered = false;",
        ),
        PageBreak(),
    ]

    # --- 4. Temporal -----------------------------------------------
    story += [
        p(styles, "H1", "4. Service: Temporal"),
        p(styles, "H2", "What Temporal is doing for us"),
        p(
            styles,
            "Body",
            "Temporal is a <b>durable workflow engine</b>. Where a regular Python script "
            "would lose its place if the process crashed mid-execution, a Temporal "
            "workflow records every state change to its database and can resume exactly "
            "where it left off. In this project Temporal is the runtime for overnight "
            "execution: it accepts workflow submissions, runs them across long-running "
            "Python <i>activities</i>, retries on failure, and provides a UI to observe "
            "everything that ever ran.",
        ),
        p(styles, "H2", "Why Temporal (not cron + bash)"),
        p(
            styles,
            "Body",
            "Overnight runs may take hours, talk to flaky local services (Ollama can stall, "
            "models can fail), and need clean restart semantics if your Mac sleeps mid-job. "
            "Cron + bash gives you none of that. Temporal gives you: per-activity retries, "
            "timeouts, idempotency, full audit history, pause and resume, and a web UI "
            "showing every workflow execution.",
        ),
        p(styles, "H2", "Two pieces"),
        section_table(
            [
                ["Piece", "Lives in", "Started by"],
                ["Temporal server (gRPC + UI)", "Docker container (auto-setup image)", "bash scripts/start_services.sh"],
                ["Temporal worker (Python)", "Host Python process", "bash scripts/start_temporal_worker.sh"],
            ],
            col_widths=[2.5 * inch, 2.7 * inch, 1.3 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "The <b>server</b> stores workflow state in Postgres (separate tables, "
            "different namespace from our own seven tables). The <b>worker</b> is a "
            "long-running Python process that polls the server for work to do; the work "
            "items are calls to activity functions like "
            "<code>create_work_packet_activity</code>.",
        ),
        p(styles, "H2", "Workflows (defined in code)"),
        section_table(
            [
                ["Workflow", "Where", "What it does"],
                ["ClarificationWorkflow", "assistant_core/temporal_app/workflows.py", "One activity: create_work_packet_activity. Used when clarification is moved off-thread."],
                ["OvernightExecutionWorkflow", "same file", "Three activities: update status to RUNNING, run langgraph execution, update status to COMPLETED."],
                ["ManualResumeWorkflow", "same file", "Reserved for v2 user-driven re-runs of paused work."],
            ],
            col_widths=[2.0 * inch, 2.7 * inch, 1.8 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Activities (the Python functions Temporal calls)"),
        section_table(
            [
                ["Activity name", "What it does"],
                ["create_work_packet_activity", "Builds a packet via deterministic clarification, writes to Postgres."],
                ["generate_questions_activity", "Generates questions for a description (returns JSON)."],
                ["score_readiness_activity", "Scores readiness, returns the structure."],
                ["run_langgraph_execution_activity", "(scaffolded) Runs the 18-step execution graph for a ready packet."],
                ["write_outputs_activity", "(scaffolded) Writes generated artifacts to ~/LocalAI/output/."],
                ["update_status_activity", "(scaffolded) Updates work_packet status in Postgres."],
                ["archive_files_activity", "(scaffolded) Moves processed inputs to ~/LocalAI/archive/."],
            ],
            col_widths=[2.5 * inch, 4.0 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Task queue"),
        p(
            styles,
            "Body",
            "All workflows are submitted against the single task queue named "
            "<code>local-ai-orchestrator</code>. The worker polls this queue and "
            "dispatches activities. If no worker is running, workflows queue but never "
            "execute &mdash; you can see them in the Temporal UI marked as scheduled.",
        ),
        p(styles, "H2", "Temporal UI"),
        p(
            styles,
            "Body",
            "Browse to <code>http://localhost:8233</code>. You'll see the "
            "<code>default</code> namespace, a list of workflows, and per-workflow event "
            "history with timing, retries, and inputs/outputs. Great for debugging.",
        ),
        p(styles, "H2", "How to inspect from the terminal"),
        code_block(
            styles,
            "# Server health\n"
            "docker logs --tail=30 localai-temporal\n"
            "\n"
            "# Is the worker running on the host?\n"
            "ps -ef | grep '[t]emporal_app.worker'\n"
            "\n"
            "# Submit a manual clarification workflow from Python:\n"
            ".venv/bin/python -c \"\n"
            "from assistant_core.temporal_app.client import start_clarification\n"
            "print(start_clarification('Test', 'A vague description'))\n"
            "\"",
        ),
        PageBreak(),
    ]

    # --- 5. Ollama ---------------------------------------------------
    story += [
        p(styles, "H1", "5. Service: Ollama"),
        p(styles, "H2", "What Ollama is doing for us"),
        p(
            styles,
            "Body",
            "Ollama is the <b>local model runtime</b>. It downloads quantized weights to "
            "<code>~/.ollama/models/</code>, loads them into Metal VRAM on demand, and "
            "exposes an HTTP API on <code>:11434</code> for inference, listing, and "
            "load/unload control. The orchestrator never bypasses Ollama for local model "
            "calls; every local inference goes through this daemon.",
        ),
        p(styles, "H2", "Why Ollama (not raw llama.cpp)"),
        p(
            styles,
            "Body",
            "llama.cpp is the underlying inference engine, but operating it directly "
            "means tracking weights, format conversions, quantization options, GPU "
            "settings, and writing your own HTTP server. Ollama wraps all of that, ships "
            "a registry of pre-quantized models, and gives you a simple HTTP API. It's "
            "the right level of abstraction for a single-user Mac.",
        ),
        p(styles, "H2", "Where things live"),
        section_table(
            [
                ["Path", "Contents"],
                ["~/.ollama/models/blobs/", "Raw quantized weight blobs, content-addressable."],
                ["~/.ollama/models/manifests/", "Manifests linking tags (e.g. qwen3:30b-a3b) to blob digests."],
                ["~/.ollama/logs/server.log", "Daemon logs (also visible via brew services log ollama)."],
                ["~/Library/LaunchAgents/homebrew.mxcl.ollama.plist", "macOS launchd config when running as brew service."],
            ],
            col_widths=[3.2 * inch, 3.3 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Key API endpoints"),
        section_table(
            [
                ["Endpoint", "What it does", "Used by"],
                ["GET /api/tags", "Lists tags on disk", "ollama_admin.list_pulled_models"],
                ["GET /api/ps", "Lists tags currently in VRAM", "ollama_admin.list_loaded_models"],
                ["POST /api/generate", "Run inference (also used for load/unload)", "ollama_admin.load_model, unload_model, quick_prompt"],
                ["POST /api/pull", "Pull a tag from registry", "ollama pull CLI"],
                ["POST /api/delete", "Remove a tag from disk", "ollama rm CLI"],
            ],
            col_widths=[1.5 * inch, 2.5 * inch, 2.5 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "keep_alive semantics (the subtle one)"),
        p(
            styles,
            "Body",
            "When you POST <code>/api/generate</code> you can include a <code>keep_alive</code> "
            "field telling Ollama how long to keep the model in VRAM after the call:",
        ),
        section_table(
            [
                ["Value", "Meaning", "Used here as"],
                ["\"5m\", \"30m\", \"2h\"", "Go duration: stay loaded that long after the last call", "Load button (30m), quick_prompt (5m)"],
                ["\"0s\" (string)", "Unload immediately after this call", "Unload button (CORRECT form)"],
                ["0 (integer)", "Quirky: some versions treat as \"use default 5m\"", "Avoided &mdash; was a bug we fixed in 4480d5a"],
                ["-1 (negative)", "Stay loaded indefinitely", "Not used here"],
                ["omitted", "Use server default (5m)", "Default Ollama behavior"],
            ],
            col_widths=[1.4 * inch, 2.9 * inch, 2.2 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Model-tag conventions in this project"),
        section_table(
            [
                ["Logical name (group)", "Ollama tag", "Approx size on disk", "VRAM when loaded"],
                ["local-main", "qwen3:30b-a3b", "~18 GB", "~30 GB"],
                ["local-secondary", "llama3.3:70b", "~40 GB", "~42 GB"],
                ["local-coder", "qwen3-coder:30b", "~17 GB", "~30 GB"],
                ["local-reasoner", "deepseek-r1:8b", "~5 GB", "~5 GB"],
            ],
            col_widths=[1.7 * inch, 1.5 * inch, 1.6 * inch, 1.7 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "How to inspect"),
        code_block(
            styles,
            "ollama list                                  # tags on disk\n"
            "ollama ps                                    # tags currently in VRAM\n"
            "curl http://localhost:11434/api/tags         # same, JSON\n"
            "curl http://localhost:11434/api/ps           # same, JSON\n"
            "ollama show qwen3:30b-a3b                    # detailed model metadata\n"
            "brew services list | grep ollama             # is it running as a service?\n"
            "du -sh ~/.ollama/models                      # how much disk are tags using?",
        ),
        PageBreak(),
    ]

    # --- 6. LiteLLM --------------------------------------------------
    story += [
        p(styles, "H1", "6. Service: LiteLLM"),
        p(styles, "H2", "What LiteLLM is doing for us"),
        p(
            styles,
            "Body",
            "LiteLLM is a <b>model router</b>. It speaks the OpenAI chat-completion API "
            "and dispatches each call to the right backend &mdash; in our case mostly "
            "Ollama, but it can also route to Anthropic, OpenAI, or other providers. It "
            "centralizes routing rules, fallback chains, and translates a single "
            "<code>model_group</code> name into the actual backend call.",
        ),
        p(styles, "H2", "Why LiteLLM (when we already have ollama_admin?)"),
        p(
            styles,
            "Body",
            "Two reasons: First, when the execution graph is fully wired, code calling "
            "<code>local-main</code> shouldn't have to know whether that's an Ollama tag "
            "or a cloud endpoint &mdash; LiteLLM hides that. Second, fallback chains "
            "(e.g., if local-coder fails, try local-main) are easier to express in "
            "LiteLLM's declarative config than in custom Python. The "
            "<code>ollama_admin</code> module is a direct path for admin operations "
            "(load/unload/test from the panel); LiteLLM is for the production execution "
            "path that calls models repeatedly.",
        ),
        p(styles, "H2", "Configuration: config/litellm.yaml"),
        p(
            styles,
            "Body",
            "Gitignored; copied from <code>config/litellm.yaml.example</code> on first "
            "run. Contains the model list and the fallback rules:",
        ),
        code_block(
            styles,
            "model_list:\n"
            "  - model_name: local-main\n"
            "    litellm_params:\n"
            "      model: ollama/qwen3:30b-a3b\n"
            "      api_base: http://localhost:11434\n"
            "  - model_name: local-secondary\n"
            "    litellm_params:\n"
            "      model: ollama/llama3.3:70b\n"
            "      api_base: http://localhost:11434\n"
            "  - model_name: local-coder\n"
            "    litellm_params:\n"
            "      model: ollama/qwen3-coder:30b\n"
            "      api_base: http://localhost:11434\n"
            "  - model_name: local-reasoner\n"
            "    litellm_params:\n"
            "      model: ollama/deepseek-r1:8b\n"
            "      api_base: http://localhost:11434\n"
            "  - model_name: cloud-claude-opus\n"
            "    litellm_params:\n"
            "      model: anthropic/claude-opus-4-7\n"
            "      api_key: os.environ/ANTHROPIC_API_KEY\n"
            "\n"
            "router_settings:\n"
            "  fallbacks:\n"
            "    - local-main:\n"
            "        - local-secondary\n"
            "    - local-coder:\n"
            "        - local-main\n"
            "    - local-reasoner:\n"
            "        - local-main\n"
            "\n"
            "litellm_settings:\n"
            "  request_timeout: 180\n"
            "  set_verbose: false",
        ),
        p(styles, "H2", "Important design choices"),
        *bullets(
            styles,
            [
                "<b>Cloud is in the model_list but not in any fallback chain.</b> cloud-claude-opus is declared so it can be called if every safety gate passes, but it is intentionally not chained behind local. No blind escalation.",
                "<b>Local fallbacks are layered to avoid loops.</b> local-coder -> local-main is fine; we don't chain back to local-coder.",
                "<b>request_timeout: 180s</b> matches the longest expected single-call duration on a beefy local model.",
            ],
        ),
        p(styles, "H2", "How to inspect"),
        code_block(
            styles,
            "lsof -nP -iTCP:4000 -sTCP:LISTEN     # is LiteLLM running?\n"
            "curl http://localhost:4000/v1/models  # what models does it advertise?\n"
            "tail -f logs/litellm.log              # if you redirect when starting",
        ),
        PageBreak(),
    ]

    # --- 7. Open WebUI ---------------------------------------------
    story += [
        p(styles, "H1", "7. Service: Open WebUI"),
        p(styles, "H2", "What Open WebUI is doing for us"),
        p(
            styles,
            "Body",
            "Open WebUI is a polished, ChatGPT-style web UI for chatting with local "
            "models. It speaks directly to Ollama via "
            "<code>http://host.docker.internal:11434</code>. It is <b>not part of the "
            "orchestrator's pipeline</b>; it lives next to it as a convenience.",
        ),
        p(styles, "H2", "Why include it"),
        p(
            styles,
            "Body",
            "The orchestrator deliberately does not offer chat. Sometimes you want chat "
            "anyway &mdash; for spot-checks, exploration, or interactive sessions. Open "
            "WebUI is the right tool for that and co-installing it via docker-compose "
            "means both surfaces start with one command.",
        ),
        p(styles, "H2", "Configuration"),
        section_table(
            [
                ["Environment variable", "Value", "Meaning"],
                ["OLLAMA_BASE_URL", "http://host.docker.internal:11434", "How the container reaches the host's Ollama"],
                ["WEBUI_AUTH", "\"false\"", "No login required (single-user local box)"],
            ],
            col_widths=[2.0 * inch, 2.8 * inch, 1.7 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "What is stored"),
        p(
            styles,
            "Body",
            "Chat history, user settings, and any custom prompts you save live inside the "
            "<code>open_webui_data</code> Docker volume mounted at "
            "<code>/app/backend/data</code>. Survives container recreates. To wipe: "
            "<code>docker compose down -v</code> (also nukes your work packets &mdash; "
            "be careful).",
        ),
        p(styles, "H2", "Relationship to the orchestrator"),
        p(
            styles,
            "Body",
            "They share Ollama and that's it. Open WebUI does not read or write the "
            "orchestrator's Postgres, does not see work packets, does not respect "
            "DAY_MODE / day_unlock. If you load a model in Open WebUI for a chat, the "
            "orchestrator's Models tab will show it as loaded too (both call the same "
            "Ollama).",
        ),
        PageBreak(),
    ]

    # --- 8. Streamlit panel ----------------------------------------
    story += [
        p(styles, "H1", "8. Service: Streamlit control panel"),
        p(styles, "H2", "What the panel is doing for us"),
        p(
            styles,
            "Body",
            "The Streamlit control panel is the orchestrator's <b>graphical UI</b>. It is "
            "the only browser surface for safe model load/unload, schedule editing, and "
            "work-packet status. It is a Python process running on the host (not in "
            "Docker), serving an interactive web app on <code>:8501</code>.",
        ),
        p(styles, "H2", "Why Streamlit"),
        p(
            styles,
            "Body",
            "Streamlit lets us write a UI in pure Python without managing a separate "
            "frontend. Every interaction is a server-side re-render; we can call into "
            "<code>assistant_core</code> directly with no API layer. Tabs and forms "
            "are stateless across re-renders, which fits the orchestrator's design "
            "(read state from disk or DB on every render).",
        ),
        p(styles, "H2", "Tab-by-tab"),
        section_table(
            [
                ["Tab", "Calls into", "Purpose"],
                ["Dashboard", "storage.list_work_packets", "Table of all packets and their status"],
                ["Create Work Packet", "clarification.graph.run_deterministic_clarification", "Draft + score a packet interactively"],
                ["Clarification", "(file upload only)", "Preview an answers file (parse from CLI today)"],
                ["Models", "llm.ollama_admin", "Load / Unload / Quick test, gate-checked"],
                ["Schedule", "config_writer.update_assistant_config + scheduler_status", "Edit times, view launchd state"],
                ["Execution", "execution.graph.describe_execution_scaffold", "Show the scaffold list of 18 steps"],
                ["Artifacts", "filesystem walk of cfg.output_dir", "List files in ~/LocalAI/output/"],
            ],
            col_widths=[1.6 * inch, 2.8 * inch, 2.1 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(styles, "H2", "Header status strip (rendered on every page)"),
        *bullets(
            styles,
            [
                "<b>Row 1</b>: Current mode, Day unlock, Now (clock time + DAY/NIGHT window label), Auto-execution.",
                "<b>Row 2</b>: Postgres up/down, Temporal up/down, Ollama up/down, LiteLLM up/down.",
                "<b>Day-unlock banner</b>: red error block with flag-file contents when unlock is ACTIVE.",
                "<b>Launchd banner</b>: yellow warning when the nightly job is loaded in launchctl.",
                "<b>Cloud warning</b>: always-on green block reminding you cloud is locked behind six gates.",
            ],
        ),
        p(styles, "H2", "How to inspect"),
        code_block(
            styles,
            "lsof -nP -iTCP:8501 -sTCP:LISTEN              # is Streamlit running?\n"
            "tail -f /tmp/streamlit.log                     # if launched with nohup ... > /tmp/...\n"
            "ps -ef | grep '[s]treamlit'                    # PID and command line",
        ),
        PageBreak(),
    ]

    # --- 9. Temporal worker -----------------------------------------
    story += [
        p(styles, "H1", "9. Service: Temporal worker (long-running Python)"),
        p(
            styles,
            "Body",
            "The Temporal worker is a Python process that polls the Temporal server's "
            "<code>local-ai-orchestrator</code> task queue and executes activities. "
            "Without it, workflows submitted to Temporal queue forever. It is a "
            "<b>separate process</b> from the Streamlit panel and the CLI.",
        ),
        p(styles, "H2", "Started by"),
        code_block(
            styles,
            "bash scripts/start_temporal_worker.sh\n"
            "# Equivalent:\n"
            ".venv/bin/python -m assistant_core.temporal_app.worker",
        ),
        p(styles, "H2", "What it imports and registers"),
        *bullets(
            styles,
            [
                "Workflows: ClarificationWorkflow, OvernightExecutionWorkflow, ManualResumeWorkflow.",
                "Activities: create_work_packet_activity, generate_questions_activity, score_readiness_activity, run_langgraph_execution_activity, write_outputs_activity, update_status_activity, archive_files_activity.",
                "All registered against the queue <code>local-ai-orchestrator</code> on the Temporal client connected to <code>localhost:7233</code>.",
            ],
        ),
        p(styles, "H2", "What it doesn't do today"),
        p(
            styles,
            "Body",
            "The activity bodies for execution (the actual model-calling, evaluator-running, "
            "file-writing work) are stubs returning placeholder dicts. Submitting an "
            "overnight workflow today works: the worker receives it, runs the stubs, "
            "marks them complete. No real outputs are produced yet. Wiring the real "
            "bodies is the next major feature chunk.",
        ),
        p(styles, "H2", "Running and observing"),
        code_block(
            styles,
            "# In a dedicated terminal so its logs are visible:\n"
            "bash scripts/start_temporal_worker.sh\n"
            "# It prints \"Temporal worker listening on task queue: local-ai-orchestrator\"\n"
            "# and stays running. Ctrl+C to stop.\n"
            "\n"
            "# To run it in background:\n"
            "nohup bash scripts/start_temporal_worker.sh > ~/LocalAI/logs/worker.log 2>&1 &\n"
            "\n"
            "# Verify it's running:\n"
            "ps -ef | grep '[t]emporal_app.worker'",
        ),
        PageBreak(),
    ]

    # --- 10. Root-level files --------------------------------------
    story += [
        p(styles, "H1", "10. Repository: root-level files"),
        section_table(
            [
                ["File", "Purpose"],
                ["README.md", "First impression / install / ports / safety summary. Read by humans landing on the repo."],
                ["AGENTS.md", "Rules for any future agent (human or AI) modifying this repo. Conservative defaults, no destructive ops, distinguish implemented vs scaffolded."],
                ["ONBOARDING.md", "Practical day-to-day operator guide. Companion to the Onboarding PDF."],
                [".env.example", "Template of environment variables. Copy to .env and customize. Real .env is gitignored."],
                [".gitignore", "Lists: .venv, __pycache__, config/litellm.yaml, logs/*.log, launchd/*.plist, etc."],
                ["pyproject.toml", "Python project metadata + dependency list. Used by install_core.sh."],
                ["docker-compose.yml", "The four-service stack: postgres, temporal, temporal-ui, open-webui."],
                [".streamlit/config.toml", "Streamlit defaults (disables usage stats gathering)."],
                [".pytest_cache/", "pytest's cache (gitignored)."],
                [".venv/", "The Python virtual env install_core.sh creates (gitignored)."],
            ],
            col_widths=[2.1 * inch, 4.4 * inch],
        ),
        PageBreak(),
    ]

    # --- 11. assistant_core top-level modules ----------------------
    story += [
        p(styles, "H1", "11. Repository: assistant_core top-level modules"),
        p(
            styles,
            "Body",
            "The Python package that holds the orchestrator's logic. Top-level modules "
            "(not subpackages) below:",
        ),
        section_table(
            [
                ["Module", "Responsibility"],
                ["__init__.py", "Marks assistant_core as a Python package. Empty."],
                ["cli.py", "argparse-based CLI: ensure-folders, sample-readiness, migrate, create-work-packet, run-clarification, answer-questions, run-ready-overnight. Used by every scripts/*.sh entry point."],
                ["config.py", "Loads config/assistant.yaml + config/memory.yaml into pydantic models (AssistantConfig, MemoryConfig). Loads config/models.yaml as a plain dict."],
                ["config_writer.py", "Safely writes back to config/assistant.yaml. Enforces an allow-list (only day/night time fields editable). Atomic temp-file + os.replace. Regex-validates HH:MM input."],
                ["logging_utils.py", "(stub) Future home for structured logging helpers."],
                ["paths.py", "LOCALAI_SUBDIRS, OBSIDIAN_SUBDIRS, ensure_local_folders(), path-safety helpers (is_relative_to, assert_within_roots, resolve_user_path)."],
                ["safety.py", "The five gate functions: assert_cloud_allowed, assert_no_external_write, assert_original_file_write_allowed, assert_heavy_execution_allowed, assert_model_allowed. Plus day_unlock_active() and the LOCAL_MODEL_GROUPS frozenset."],
                ["schemas.py", "All pydantic models: WorkPacket, ClarificationQuestion, ReadinessScore, EvaluationResult, ModelCallLog, Artifact, MemoryCandidate, ExecutionPlan, WorkPacketStatus literal."],
                ["scheduler_status.py", "Service health probes (postgres_up, temporal_up, ollama_up, litellm_up). launchd inspection (launchd_job_loaded, launchd_plist_installed). Window math (compute_window_status)."],
                ["storage/ (package)", "Postgres CRUD, split by entity. connection.py (StorageUnavailable, _connect, _json), serialization.py (YAML round-trip), migration.py, work_packets.py, clarification.py, execution_runs.py, audit.py (model_calls/evaluations/artifacts/memory_candidates). Public API is re-exported from storage/__init__.py so callers still use `from assistant_core.storage import ...`."],
            ],
            col_widths=[1.8 * inch, 4.7 * inch],
        ),
        PageBreak(),
    ]

    # --- 12. clarification subpackage ------------------------------
    story += [
        p(styles, "H1", "12. Repository: assistant_core/clarification/"),
        p(
            styles,
            "Body",
            "The implemented heart of the orchestrator. Everything in this subpackage is "
            "deterministic; no model calls.",
        ),
        section_table(
            [
                ["File", "Responsibility"],
                ["__init__.py", "Marker file."],
                ["work_packet_builder.py", "build_initial_work_packet(title, description) creates the first WorkPacket. update_packet_from_answers(packet, answers_text) parses the markdown answer file using regex helpers (_extract_localai_paths, _extract_line_value, _infer_outputs) and fills missing fields."],
                ["readiness.py", "READINESS_WEIGHTS dict (the 9 dimensions). _dimension_scores walks each dimension. score_readiness() returns a ReadinessScore with score, status, dimension_scores, reasons, blocking_gaps, non_blocking_gaps. readiness_status() maps a score to a status string."],
                ["question_generator.py", "QUESTION_BANK: dict of category -> (category_name, question_text, priority, blocking). generate_questions(packet, readiness, round_number, max_questions) returns the top-N missing dimensions as ClarificationQuestion models."],
                ["graph.py", "run_deterministic_clarification(title, description) ties together build + score + generate in one call. ClarificationResult dataclass. build_langgraph_clarification_graph() is the LangGraph wiring (scaffold for future use)."],
                ["prompts.py", "Prompt templates (stub today, will hold prompts the execution graph uses for LLM-side clarification)."],
            ],
            col_widths=[1.9 * inch, 4.6 * inch],
        ),
        PageBreak(),
    ]

    # --- 13. execution subpackage ---------------------------------
    story += [
        p(styles, "H1", "13. Repository: assistant_core/execution/"),
        p(
            styles,
            "Body",
            "Scaffolded today. When wired, this becomes the overnight pipeline that "
            "actually calls models and produces artifacts.",
        ),
        section_table(
            [
                ["File", "Responsibility"],
                ["__init__.py", "Marker."],
                ["graph.py", "EXECUTION_STEPS list (the 18 named steps from load_ready_work_packets through finish_run). describe_execution_scaffold() returns a status dict. This is where the LangGraph wiring will live."],
                ["file_utils.py", "load_supported_file(path) for .txt, .md, .csv, .json, .log. profile_csv() returns row count, columns, preview, missing counts. chunk_text(content, max_chars) chunks long inputs."],
                ["evaluators.py", "EvaluationResult parser. INVALID_EVALUATION fallback when an LLM evaluator returns malformed JSON. deterministic_completeness_evaluator(output, required_terms) as a model-free fallback."],
                ["output_writer.py", "dated_output_dir(cfg, day) -> ~/LocalAI/output/YYYY-MM-DD/. write_status(dir, status) writes 00_STATUS.json. write_standard_output_files(packet) writes the nine templated markdown files. write_obsidian_work_packet(packet) drops a packet summary into the vault."],
                ["prompts.py", "Prompt templates for execution-time LLM calls (currently small)."],
            ],
            col_widths=[1.7 * inch, 4.8 * inch],
        ),
        PageBreak(),
    ]

    # --- 14. llm subpackage ----------------------------------------
    story += [
        p(styles, "H1", "14. Repository: assistant_core/llm/"),
        section_table(
            [
                ["File", "Responsibility"],
                ["__init__.py", "Marker."],
                ["ollama_client.py", "Low-level wrapper around Ollama's /api/generate and /api/tags. Used by code paths that bypass LiteLLM."],
                ["ollama_admin.py", "Higher-level admin API used by the Streamlit Models tab: ollama_available, list_pulled_models, list_loaded_models, tag_to_group_mapping, resolve_group_for_tag (fail-closed -> local-main), load_model (gate-checked, 30m keep-alive), unload_model (sends '0s' string), quick_prompt (gate-checked, single-shot)."],
                ["litellm_client.py", "chat_completion(messages, model_group, mode) wrapper that pre-checks the safety gate (assert_model_group_allowed) and posts to LiteLLM's /v1/chat/completions."],
                ["model_policy.py", "LOCAL_ESCALATION chains (general, coding, reasoning_check). local_model_chain(task_type) returns the right fallback order. assert_model_group_allowed (delegates to safety.assert_model_allowed). authorize_cloud_claude(... lots of args ...) calls assert_cloud_allowed."],
            ],
            col_widths=[1.7 * inch, 4.8 * inch],
        ),
        PageBreak(),
    ]

    # --- 15. memory subpackage -------------------------------------
    story += [
        p(styles, "H1", "15. Repository: assistant_core/memory/"),
        section_table(
            [
                ["File", "Responsibility"],
                ["__init__.py", "Marker."],
                ["obsidian.py", "ensure_obsidian_vault() creates the 10 standard subfolders. write_daily_brief(content, day) -> ~/Obsidian/.../01_Daily_Briefs/YYYY-MM-DD.md. write_work_packet_note(packet) -> 02_Work_Packets/. write_memory_candidate(candidate) -> 00_Inbox/Memory_Review/. All writes are path-safety-checked."],
                ["memory_extractor.py", "extract_memory_candidates(output_text, source_path) scans markdown for lines containing 'decision:', 'confirmed:', 'preference:' and emits MemoryCandidate models."],
                ["memory_reviewer.py", "(stub today) Will gate which candidates make it into long-term memory based on your approval state."],
                ["vector_store.py", "ChromaMemoryStore wrapper. connect() creates a PersistentClient at the configured persist_dir. add_text(doc_id, text, metadata) and retrieve(query, limit) work after connect. Fails gracefully when chromadb isn't installed."],
            ],
            col_widths=[1.8 * inch, 4.7 * inch],
        ),
        PageBreak(),
    ]

    # --- 16. temporal_app subpackage -------------------------------
    story += [
        p(styles, "H1", "16. Repository: assistant_core/temporal_app/"),
        section_table(
            [
                ["File", "Responsibility"],
                ["__init__.py", "Marker."],
                ["workflows.py", "ClarificationWorkflow, OvernightExecutionWorkflow, ManualResumeWorkflow. Each is decorated with @workflow.defn from temporalio. Workflow bodies are short orchestrators that call activities by name."],
                ["activities.py", "The seven activity functions, each decorated with @activity.defn. create_work_packet_activity is fully implemented; the others are scaffolded (return placeholder dicts)."],
                ["worker.py", "main_async() connects to Temporal at the configured address, creates a Worker registered for all workflows and activities, polls the local-ai-orchestrator task queue. TASK_QUEUE constant defined here."],
                ["client.py", "start_overnight_execution(work_packet_id) and start_clarification(title, description) submit workflows to Temporal. Used by CLI's run-ready-overnight command."],
            ],
            col_widths=[1.5 * inch, 5.0 * inch],
        ),
        PageBreak(),
    ]

    # --- 17. app/control_panel.py ---------------------------------
    story += [
        p(styles, "H1", "17. Repository: app/control_panel.py"),
        p(
            styles,
            "Body",
            "The Streamlit UI. ~360 lines of declarative-ish Python; renders the 7 tabs "
            "described in section 8. Key structural elements:",
        ),
        section_table(
            [
                ["Function", "Responsibility"],
                ["main()", "Entry point. Sets page config, calls _render_header, builds tabs, dispatches to each _render_*_tab."],
                ["_render_header(cfg)", "The two-row status strip + day-unlock banner + launchd banner + cloud warning."],
                ["_render_dashboard_tab()", "Lists work packets from Postgres."],
                ["_render_create_packet_tab()", "Form for drafting and scoring a packet without DB writes."],
                ["_render_clarification_tab()", "File-upload preview for answers markdown."],
                ["_render_models_tab(mode, unlocked)", "Currently loaded list, pulled models list, Load/Unload buttons, Quick test prompt."],
                ["_render_schedule_tab(cfg)", "launchd status metrics, editable time form, regenerate-and-reload hint."],
                ["_render_execution_tab()", "Shows the scaffold step list, disabled pause/resume buttons."],
                ["_render_artifacts_tab(cfg)", "Walks ~/LocalAI/output/ and lists files."],
                ["current_mode()", "Reads LOCALAI_MODE env var with DAY_MODE default."],
                ["_status_pill(label, ok)", "Helper for the up/down metrics."],
            ],
            col_widths=[2.4 * inch, 4.1 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "Important sys.path manipulation at the top: PROJECT_ROOT is computed and "
            "inserted at index 0 of sys.path so that <code>from assistant_core...</code> "
            "imports work even when Streamlit is launched from a different working "
            "directory.",
        ),
        PageBreak(),
    ]

    # --- 18. scripts -----------------------------------------------
    story += [
        p(styles, "H1", "18. Repository: scripts/ (every shell script)"),
        section_table(
            [
                ["Script", "What it does"],
                ["check_system.sh", "Read-only health check: macOS, hardware, disk, Python, Homebrew, Docker, Ollama, ports, container status."],
                ["install_core.sh", "Creates .venv, pip installs dependencies, runs `assistant_core.cli ensure-folders` to materialize ~/LocalAI and the vault subfolders."],
                ["start_services.sh", "docker compose up -d for the four containers. Verifies Docker daemon + compose plugin first."],
                ["stop_services.sh", "docker compose stop. Does NOT touch host processes (Streamlit, Ollama, LiteLLM, worker)."],
                ["status_services.sh", "Inspection summary: what's running, what's listening."],
                ["start_litellm.sh", "Copies config/litellm.yaml from .example if missing; runs litellm proxy bound to 127.0.0.1:4000."],
                ["start_temporal_worker.sh", "Launches .venv/bin/python -m assistant_core.temporal_app.worker."],
                ["start_control_panel.sh", "Exports PYTHONPATH and launches Streamlit on 127.0.0.1:8501."],
                ["create_work_packet.sh", "Wrapper: .venv/bin/python -m assistant_core.cli create-work-packet \"$1\" \"$2\"."],
                ["answer_questions.sh", "Wrapper: .venv/bin/python -m assistant_core.cli answer-questions \"$1\" \"$2\"."],
                ["run_clarification.sh", "Wrapper for the run-clarification CLI command (rescore + regenerate questions for an existing packet id)."],
                ["run_ready_overnight.sh", "Refuses unless LOCALAI_MODE=NIGHT_MODE or LOCALAI_MANUAL_RESUME=true; then submits Temporal workflows for all READY packets."],
                ["pull_models.sh", "Sequentially pulls the three default tags from Ollama; lists alternative tags at the end."],
                ["create_launchd_plist.sh", "Reads night_mode_start from config/assistant.yaml; emits launchd/com.localai.orchestrator.nightly.plist. With LOCALAI_WRITE_LAUNCHD=true, also installs to ~/Library/LaunchAgents/."],
                ["day_unlock.sh", "Writes ~/LocalAI/state/day_unlock.flag with timestamp + reason."],
                ["day_lock.sh", "Removes the flag. Warns if LOCALAI_DAY_UNLOCK is also set in the shell."],
                ["run_tests.sh", "shellcheck-equivalent (bash -n), py_compile sweep, pytest run, docker compose config validation. The thing CI would run."],
                ["build_pdfs.py", "Thin entry point. Imports the pdf_builders/ package and renders each document. To add a PDF, write a builder module under scripts/pdf_builders/ and register it in PDFS_TO_BUILD."],
                ["pdf_builders/ (package)", "One file per PDF document: styles.py, helpers.py, document.py shared; system_guide.py, onboarding.py, technical_reference.py for content. Splitting prevents the old 4000-line monolith."],
            ],
            col_widths=[2.2 * inch, 4.3 * inch],
        ),
        PageBreak(),
    ]

    # --- 19. config files ------------------------------------------
    story += [
        p(styles, "H1", "19. Repository: config/ (every YAML)"),
        p(styles, "H2", "config/assistant.yaml"),
        p(
            styles,
            "Body",
            "The main config. Sets paths, ports, thresholds, policies, and the editable "
            "day/night times. Read via <code>config.load_assistant_config()</code>. "
            "Editable through the Schedule tab (allow-listed to the time fields only).",
        ),
        section_table(
            [
                ["Key", "Default", "Used by"],
                ["local_ai_root", "~/LocalAI", "paths.ensure_local_folders"],
                ["inbox_dir, output_dir, archive_dir, ...", "subdirs of local_ai_root", "various writers"],
                ["obsidian_vault_dir", "~/Obsidian/LocalAI-ChiefOfStaff", "memory.obsidian"],
                ["ollama_base_url", "http://localhost:11434", "ollama_admin, scheduler_status"],
                ["litellm_base_url", "http://localhost:4000", "litellm_client"],
                ["temporal_address", "localhost:7233", "temporal_app.worker, client"],
                ["postgres_url", "postgresql://localai:localai@localhost:5432/localai", "storage._connect"],
                ["day_mode_start, night_mode_start, night_mode_end", "07:30, 01:30, 07:00", "scheduler_status.compute_window_status + create_launchd_plist.sh"],
                ["minimum_readiness_for_overnight, _for_high_stakes", "0.85, 0.90", "readiness.readiness_status"],
                ["cloud_fallback_enabled", "false", "safety.assert_cloud_allowed"],
                ["daily_cloud_budget_usd", "5.00", "(future) cloud budget enforcement"],
                ["temperature, top_p", "0.2, 0.9", "(future) model call defaults"],
                ["max_chars_per_chunk", "12000", "execution.file_utils.chunk_text"],
            ],
            col_widths=[2.5 * inch, 2.2 * inch, 1.8 * inch],
        ),
        Spacer(1, 0.1 * inch),
        p(styles, "H2", "config/models.yaml"),
        p(
            styles,
            "Body",
            "The mapping of model group -> actual Ollama tag. Used by "
            "<code>ollama_admin.tag_to_group_mapping</code> (reverse-lookup) and "
            "implicitly by LiteLLM's config (which mirrors these values).",
        ),
        p(styles, "H2", "config/memory.yaml"),
        p(
            styles,
            "Body",
            "Memory layer settings: whether Obsidian writes are enabled, the vector "
            "store choice (chroma), the vector store persist directory, and the per-policy "
            "knobs that the memory reviewer will use when wired up.",
        ),
        p(styles, "H2", "config/litellm.yaml (and .example)"),
        p(
            styles,
            "Body",
            "LiteLLM's router config. .example is committed; .yaml is gitignored. "
            "<code>scripts/start_litellm.sh</code> copies .example to .yaml on first run "
            "if .yaml is missing.",
        ),
        PageBreak(),
    ]

    # --- 20. db/migrations ---------------------------------------
    story += [
        p(styles, "H1", "20. Repository: db/migrations/"),
        p(
            styles,
            "Body",
            "Postgres SQL applied automatically on first container boot via the "
            "<code>docker-entrypoint-initdb.d</code> bind mount. There is one file today:",
        ),
        section_table(
            [
                ["File", "Contents"],
                ["001_init.sql", "Creates the seven tables (work_packets, clarification_questions, execution_runs, model_calls, evaluations, artifacts, memory_candidates), four indexes, and enables the pgcrypto extension for gen_random_uuid()."],
            ],
            col_widths=[1.4 * inch, 5.1 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "Adding a new migration: drop a numbered file like "
            "<code>002_add_foo.sql</code>. Postgres only runs init scripts on first boot "
            "(when the data directory is empty). For an existing DB you would either run "
            "the file manually via psql or destroy the postgres_data volume and let init "
            "re-run.",
        ),
        PageBreak(),
    ]

    # --- 21. tests ------------------------------------------------
    story += [
        p(styles, "H1", "21. Repository: tests/ (every test file)"),
        section_table(
            [
                ["File", "What it covers"],
                ["conftest.py", "Autouse fixture isolate_day_unlock that redirects safety.DEFAULT_STATE_DIR to a per-test tmp dir and clears LOCALAI_DAY_UNLOCK so the test suite is hermetic from any real flag file."],
                ["test_clarification_flow.py", "End-to-end deterministic flow: vague request -> questions -> answers parsed -> rescored -> READY."],
                ["test_readiness.py", "Readiness scoring edge cases including UNDERDEFINED, READY_FOR_OVERNIGHT, and high-stakes threshold."],
                ["test_safety.py", "Every gate function. Parameterized over all four local-* groups for DAY_MODE block + NIGHT_MODE allow + manual_override + day-unlock channels."],
                ["test_storage_serialization.py", "Round-trip a WorkPacket through yaml serialize/deserialize."],
                ["test_file_utils.py", "load_supported_file across .txt/.md/.log/.json, profile_csv shape and missing-value behavior."],
                ["test_control_panel_import.py", "Streamlit app imports cleanly when the cwd is not the project root (regression for the sys.path injection)."],
                ["test_scripts_static.py", "Shell scripts contain expected gates (LOCALAI_WRITE_LAUNCHD check, docker compose existence check)."],
                ["test_ollama_admin.py", "tag-to-group resolution (incl. fail-closed fallback), gate enforcement, quick prompt trimming, unload payload is the string '0s'."],
                ["test_scheduler_status.py", "Window math including overnight wrap, between-window gaps, launchd job detection, port_open probes."],
                ["test_config_writer.py", "Allow-list rejection, HH:MM regex validation, atomic write leaves no .tmp leftovers, missing-file handling."],
            ],
            col_widths=[2.4 * inch, 4.1 * inch],
        ),
        PageBreak(),
    ]

    # --- 22. docs/ ------------------------------------------------
    story += [
        p(styles, "H1", "22. Repository: docs/"),
        section_table(
            [
                ["File", "Purpose"],
                ["day_unlock.md", "Full design rationale + manual for the day-unlock switch. Two channels, four-state ladder, design alternatives considered and rejected."],
                ["models_panel.md", "Models tab design and code-level walkthrough. Tag-to-group resolution, fail-closed fallback, safety wrap, future enhancements."],
                ["auto_execution.md", "Launchd job lifecycle: four states, arming via three deliberate terminal steps, disarming, verification commands."],
                ["Local_AI_Orchestrator_System_Guide.pdf", "High-level architecture guide. 34 pages, 23 sections, TOC."],
                ["Local_AI_Orchestrator_Onboarding.pdf", "Practical operator manual. 25 pages, 21 sections, 5 use-case recipes."],
                ["Local_AI_Orchestrator_Technical_Reference.pdf", "This document. Every entity explained."],
            ],
            col_widths=[3.0 * inch, 3.5 * inch],
        ),
        PageBreak(),
    ]

    # --- 23. ~/LocalAI ---------------------------------------------
    story += [
        p(styles, "H1", "23. External state: ~/LocalAI/"),
        p(
            styles,
            "Body",
            "The orchestrator's working directory outside the repo. Created by "
            "<code>install_core.sh -> ensure_local_folders()</code>. Owned by you; the "
            "orchestrator reads from inbox/ and writes to output/, archive/, logs/, "
            "state/, work_packets/.",
        ),
        section_table(
            [
                ["Path", "What goes there"],
                ["~/LocalAI/inbox/notes/", "Your free-form notes (markdown). The system reads these but never modifies them."],
                ["~/LocalAI/inbox/transcripts/", "Meeting / call transcripts (markdown). Same read-only contract."],
                ["~/LocalAI/inbox/docs/", "Documents (markdown). Source material for briefs."],
                ["~/LocalAI/inbox/csv/", "Tabular data (.csv). file_utils.profile_csv reads these."],
                ["~/LocalAI/inbox/cloud_review/", "Files explicitly flagged for cloud review. Required path for the Claude gate to even consider a call."],
                ["~/LocalAI/output/YYYY-MM-DD/", "Generated artifacts for that day's run. Regenerated each run; not durable."],
                ["~/LocalAI/archive/", "Inputs that were processed are moved here after a run (will be, when execution graph is wired)."],
                ["~/LocalAI/logs/", "Runtime logs. Includes launchd stdout/stderr when armed."],
                ["~/LocalAI/state/", "Operational state files. Currently: day_unlock.flag (if active). Future: chroma vector store, run-state caches."],
                ["~/LocalAI/work_packets/", "(reserved) Per-packet files associated with longer-running work."],
            ],
            col_widths=[2.4 * inch, 4.1 * inch],
        ),
        PageBreak(),
    ]

    # --- 24. Obsidian ---------------------------------------------
    story += [
        p(styles, "H1", "24. External state: ~/Obsidian/LocalAI-ChiefOfStaff/"),
        p(
            styles,
            "Body",
            "Your long-term knowledge layer. Plain markdown, owned by you, indexed by "
            "Obsidian. The orchestrator writes selected outputs here as a parallel copy "
            "(briefs, packet summaries, memory candidates) so they survive even if you "
            "delete <code>~/LocalAI/output/</code>.",
        ),
        section_table(
            [
                ["Folder", "What lands there"],
                ["00_Inbox/Memory_Review/", "Memory candidates awaiting your approval before joining long-term memory."],
                ["01_Daily_Briefs/", "One markdown per day, written by the morning-brief pipeline."],
                ["02_Work_Packets/", "Per-packet summary notes."],
                ["03_Projects/", "Long-running project pages you maintain; orchestrator may append related links."],
                ["04_Meetings/", "Meeting notes (yours + post-meeting outputs)."],
                ["05_Decisions/", "Logged decisions extracted from transcripts."],
                ["06_Stakeholders/", "Per-person pages."],
                ["07_Playbooks/", "Procedures and templates."],
                ["08_Prompts/", "Curated prompts (yours or system-suggested)."],
                ["09_System_Logs_Summaries/", "Run summaries written after big overnight executions."],
                ["99_Archive/", "Historical content."],
            ],
            col_widths=[2.4 * inch, 4.1 * inch],
        ),
        PageBreak(),
    ]

    # --- 25. State files ------------------------------------------
    story += [
        p(styles, "H1", "25. State files: day_unlock.flag and others"),
        section_table(
            [
                ["File", "Purpose", "Owned by"],
                ["~/LocalAI/state/day_unlock.flag", "Sentinel for the day-unlock switch. Existence opens the gate; contents are informational.", "day_unlock.sh"],
                ["~/LocalAI/state/chroma/", "(future) Chroma vector store persist directory.", "memory.vector_store"],
                ["launchd/com.localai.orchestrator.nightly.plist", "Generated plist (gitignored). Not loaded until you install + load it manually.", "create_launchd_plist.sh"],
                ["~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist", "Installed plist (only if you ran with LOCALAI_WRITE_LAUNCHD=true). Loaded only after `launchctl load`.", "you, deliberately"],
            ],
            col_widths=[2.8 * inch, 3.2 * inch, 0.5 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "<b>Inspection cheatsheet</b>:",
        ),
        code_block(
            styles,
            "# Is day unlock on?\n"
            "ls ~/LocalAI/state/day_unlock.flag 2>&1\n"
            "cat ~/LocalAI/state/day_unlock.flag 2>&1\n"
            "\n"
            "# Is the nightly job armed?\n"
            "launchctl list | grep com.localai.orchestrator.nightly\n"
            "ls ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist 2>&1\n"
            "ls launchd/com.localai.orchestrator.nightly.plist",
        ),
        PageBreak(),
    ]

    # --- 26. Env vars in depth ------------------------------------
    story += [
        p(styles, "H1", "26. Environment variables in depth"),
        section_table(
            [
                ["Variable", "Read by", "Effect"],
                ["LOCALAI_MODE", "scripts/run_ready_overnight.sh, app/control_panel.py (current_mode)", "DAY_MODE (default) / NIGHT_MODE / MANUAL_RESUME. Drives safety gate + overnight runner."],
                ["LOCALAI_DAY_UNLOCK", "safety.day_unlock_active", "Truthy (1/true/yes/on, case-insensitive) opens the day gate for this shell only."],
                ["LOCALAI_MANUAL_RESUME", "scripts/run_ready_overnight.sh", "Truthy lets run_ready_overnight.sh proceed outside NIGHT_MODE."],
                ["LOCALAI_WRITE_LAUNCHD", "scripts/create_launchd_plist.sh", "Truthy = install plist into ~/Library/LaunchAgents."],
                ["LOCALAI_POSTGRES_URL", "(future) override the assistant.yaml postgres_url", "Convenience for testing."],
                ["LOCALAI_STATE_DIR", "scripts/day_unlock.sh and day_lock.sh", "Override the state directory (defaults to ~/LocalAI/state)."],
                ["LOCALAI_PYTHON_BIN", "scripts/install_core.sh", "Force a specific Python interpreter (e.g. 3.13 instead of 3.14)."],
                ["LOCALAI_PULL_LLAMA70B", "scripts/pull_models.sh", "Truthy = include the 70B model in the default pull."],
                ["LOCALAI_TEST_PYTHON", "scripts/run_tests.sh", "Override the Python used to run pytest."],
                ["ANTHROPIC_API_KEY", "safety.assert_cloud_allowed (+ litellm.yaml)", "Required (one of six gates) for cloud-claude-opus calls."],
                ["OPENAI_API_KEY", ".env.example placeholder", "Currently unused. Reserved if non-Anthropic cloud routing is added."],
                ["OLLAMA_FLASH_ATTENTION, OLLAMA_KV_CACHE_TYPE", "ollama serve (when started manually)", "Performance knobs for Ollama; not set when running as brew service unless you edit the plist."],
            ],
            col_widths=[2.0 * inch, 2.4 * inch, 2.1 * inch],
        ),
        PageBreak(),
    ]

    # --- 27. Port map ---------------------------------------------
    story += [
        p(styles, "H1", "27. The complete port map"),
        section_table(
            [
                ["Port", "Service", "Process", "Bound to"],
                ["3000", "Open WebUI", "Docker container localai-open-webui", "127.0.0.1"],
                ["4000", "LiteLLM", "Host Python (litellm proxy)", "127.0.0.1"],
                ["5432", "PostgreSQL", "Docker container localai-postgres", "127.0.0.1"],
                ["7233", "Temporal gRPC", "Docker container localai-temporal", "127.0.0.1"],
                ["8233", "Temporal UI", "Docker container localai-temporal-ui", "127.0.0.1"],
                ["8501", "Streamlit control panel", "Host Python (streamlit run)", "127.0.0.1"],
                ["11434", "Ollama", "Host service (brew or foreground)", "127.0.0.1"],
            ],
            col_widths=[0.7 * inch, 1.8 * inch, 2.9 * inch, 1.1 * inch],
        ),
        Spacer(1, 0.15 * inch),
        p(
            styles,
            "Body",
            "Every port binds to <b>127.0.0.1</b> only. Nothing exposed to the LAN. If you "
            "want LAN access you'd have to deliberately rebind &mdash; not recommended; "
            "the system was not designed to be accessed by anyone but you on your own "
            "machine.",
        ),
        p(styles, "H2", "Quick port check"),
        code_block(
            styles,
            "for port in 3000 4000 5432 7233 8233 8501 11434; do\n"
            "  if lsof -nP -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then\n"
            "    printf '%-5s in use\\n' \"$port\"\n"
            "  else\n"
            "    printf '%-5s free\\n' \"$port\"\n"
            "  fi\n"
            "done",
        ),
        PageBreak(),
    ]

    # --- 28. Logging ----------------------------------------------
    story += [
        p(styles, "H1", "28. Logging: where logs go, what they contain"),
        section_table(
            [
                ["Source", "Log destination", "Notes"],
                ["Docker containers", "docker logs <container>", "Volatile; rotated by Docker."],
                ["Postgres (inside container)", "docker logs localai-postgres", "Includes init-script output on first boot."],
                ["Temporal server", "docker logs localai-temporal", "Verbose by default. Look for ERROR/WARN."],
                ["Ollama daemon", "$(brew --prefix)/var/log/ollama.log or stdout when foreground", "When running as brew service, brew handles it."],
                ["LiteLLM", "stdout of the litellm process (depends on how launched)", "Redirect to a file if you want persistence."],
                ["Streamlit", "stdout of the streamlit process", "Redirect when launching with nohup."],
                ["Temporal worker", "stdout", "Redirect when launching with nohup."],
                ["launchd nightly job", "~/LocalAI/logs/launchd.out.log and launchd.err.log", "Hard-coded in the plist's StandardOutPath/StandardErrorPath."],
                ["Ollama pull (when run via the user)", "wherever you redirect", "We use ~/LocalAI/logs/pull-<tag>.log convention."],
                ["assistant_core's own logging", "(currently minimal)", "Future: structured logs into ~/LocalAI/logs/."],
            ],
            col_widths=[1.7 * inch, 2.9 * inch, 1.9 * inch],
        ),
        PageBreak(),
    ]

    # --- 29. Inspection cheatsheet --------------------------------
    story += [
        p(styles, "H1", "29. Inspection cheatsheet"),
        p(styles, "H2", "Postgres"),
        code_block(
            styles,
            "# Open psql against the container\n"
            "docker exec -it localai-postgres psql -U localai -d localai\n"
            "\n"
            "# Last 10 work packets\n"
            "SELECT id, title, status, readiness_score, created_at\n"
            "  FROM work_packets ORDER BY created_at DESC LIMIT 10;\n"
            "\n"
            "# Unanswered questions for one packet\n"
            "SELECT round_number, category, priority, question\n"
            "  FROM clarification_questions\n"
            "  WHERE work_packet_id = '<uuid>' AND answered = false\n"
            "  ORDER BY priority DESC;\n"
            "\n"
            "# Recent overnight runs and their outcomes\n"
            "SELECT id, work_packet_id, status, mode, started_at, completed_at\n"
            "  FROM execution_runs ORDER BY started_at DESC LIMIT 20;\n"
            "\n"
            "# All model calls for a run (audit trail)\n"
            "SELECT model_group, actual_model, success, prompt_chars, response_chars\n"
            "  FROM model_calls WHERE execution_run_id = '<uuid>';",
        ),
        p(styles, "H2", "Docker"),
        code_block(
            styles,
            "docker ps                                         # running containers\n"
            "docker compose ps                                  # same, from compose perspective\n"
            "docker compose config                              # resolved compose yaml\n"
            "docker volume ls                                   # named volumes\n"
            "docker volume inspect local-ai-orchestrator_postgres_data\n"
            "docker exec -it localai-postgres bash              # shell inside Postgres container",
        ),
        p(styles, "H2", "Ollama"),
        code_block(
            styles,
            "ollama list                              # tags on disk\n"
            "ollama ps                                # tags in VRAM\n"
            "ollama show qwen3:30b-a3b                # detailed metadata\n"
            "ollama stop <tag>                        # force unload\n"
            "ollama rm <tag>                          # delete from disk\n"
            "curl http://localhost:11434/api/tags     # JSON list\n"
            "curl http://localhost:11434/api/ps       # JSON in-VRAM\n"
            "brew services list | grep ollama\n"
            "tail -f \"$(brew --prefix)/var/log/ollama.log\"",
        ),
        p(styles, "H2", "Temporal"),
        code_block(
            styles,
            "open http://localhost:8233                # UI in browser\n"
            "docker logs --tail=50 localai-temporal\n"
            "ps -ef | grep '[t]emporal_app.worker'     # is host worker running?",
        ),
        p(styles, "H2", "The orchestrator from Python"),
        code_block(
            styles,
            ".venv/bin/python -m assistant_core.cli sample-readiness\n"
            ".venv/bin/python -c \"from assistant_core.safety import day_unlock_active; print(day_unlock_active())\"\n"
            ".venv/bin/python -c \"from assistant_core.scheduler_status import compute_window_status; print(compute_window_status())\"\n"
            ".venv/bin/python -c \"from assistant_core.llm.ollama_admin import list_loaded_models; print(list_loaded_models())\"",
        ),
        Spacer(1, 0.2 * inch),
        p(styles, "Caption",
          "End of Technical Reference. For high-level architecture, see System Guide; for "
          "operator recipes, see Onboarding."),
    ]

    return story


