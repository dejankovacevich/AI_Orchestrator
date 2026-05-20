"""Onboarding PDF — section builders.

Practical, command-by-command guide. Pair with the System Guide. Edit
sections by locating their ``p(styles, "H1", "N. <title>")`` block.
"""

from __future__ import annotations

from datetime import date

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer

from scripts.pdf_builders.helpers import bullets, code_block, p, section_table


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
        "12a. Recipe: one-shot code review (indie hacker fast path)",
        "12b. Recipe: audit export for a single packet (researcher / regulated)",
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
          "<font face=\"Courier\">cd ~/Projects/local-ai-orchestrator</font>."),
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
            "cd ~/Projects/local-ai-orchestrator\n"
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

    # --- Recipe: one-shot code review (indie hacker fast path) ----------
    story += [
        p(styles, "H1", "12a. Recipe: one-shot code review (indie hacker fast path)"),
        p(
            styles,
            "Body",
            "When you want a code review without manually creating a packet + "
            "answer file, the wrapper script does it in one command. It auto-sets "
            "<code>task_type=code_review</code>, fills sensible default answers, "
            "and runs the executor synchronously with <code>--manual-override</code> "
            "so it works during the day even with strict policy.",
        ),
        p(styles, "H2", "Command"),
        code_block(
            styles,
            "bash scripts/review_code.sh path/to/file.py\n"
            "# or with explicit title + ask:\n"
            'bash scripts/review_code.sh path/to/file.py \\\n'
            '   "Payments module review" \\\n'
            '   "Focus on testability and error paths."',
        ),
        p(styles, "H2", "What lands where"),
        *bullets(
            styles,
            [
                "<code>~/LocalAI/output/&lt;date&gt;/01_CODE_REVIEW.md</code> &mdash; the review",
                "<code>~/Obsidian/LocalAI-ChiefOfStaff/02_Work_Packets/&lt;date&gt;-code_review-&lt;id&gt;.md</code> &mdash; vault copy",
                "<code>09_AUDIT_LOG.md</code>, <code>08_CLOUD_REVIEW_CANDIDATES.md</code>, per-file extractions next to the review",
            ],
        ),
        p(styles, "H2", "Routing"),
        p(
            styles,
            "Body",
            "Code files automatically route to <code>local-coder</code> (qwen3-coder:30b) "
            "when it's pulled. If the evaluator says the primary output is weak the "
            "secondary retry kicks in (llama3.3:70b). Anything still failing after that "
            "is logged in <code>08_CLOUD_REVIEW_CANDIDATES.md</code> with the safety gate "
            "verdict &mdash; cloud calls stay default-off.",
        ),
        PageBreak(),
    ]

    # --- Recipe: audit export (researcher / regulated / IP) -------------
    story += [
        p(styles, "H1", "12b. Recipe: audit export for a single packet"),
        p(
            styles,
            "Body",
            "Researcher / regulated / proprietary-IP workflow. After a run "
            "completes, dump everything Postgres recorded about that packet into "
            "one self-contained JSON file you can hand to a reviewer.",
        ),
        p(styles, "H2", "Command"),
        code_block(
            styles,
            "bash scripts/export_audit.sh &lt;packet-id&gt;\n"
            "# or specify an output path:\n"
            "bash scripts/export_audit.sh &lt;packet-id&gt; ~/audits/2026-Q2-packet.json",
        ),
        p(styles, "H2", "What's in the file"),
        *bullets(
            styles,
            [
                "the <code>work_packets</code> row (title, status, readiness, policies, structured YAML)",
                "every <code>clarification_questions</code> row across rounds",
                "every <code>execution_runs</code> row with timing + Temporal workflow id",
                "every <code>model_calls</code> row (model_group, actual tag, sizes, success)",
                "every <code>evaluations</code> row (quality, grounding, completeness, recommended next step)",
                "every <code>artifacts</code> row (file paths + Obsidian copies)",
                "every <code>memory_candidates</code> row linked to those artifacts",
            ],
        ),
        p(styles, "H2", "Why this matters"),
        p(
            styles,
            "Body",
            "A reviewer can answer \"which model produced which output, "
            "evaluated by what, with which inputs, when?\" from one file. "
            "Combined with the <code>grounding_required=True</code> flag (set "
            "from the request text or via <code>--grounding-required</code> at "
            "packet creation), the system enforces \"Source:\" citations in every "
            "extraction and refuses the run when the evaluator can't find them, "
            "so the audit trail also includes the model's own provenance claims.",
        ),
        p(styles, "Hint",
          "Combine with <code>cloud_fallback_enabled=false</code> "
          "(the default) for a guarantee: every byte the model saw, every byte "
          "it produced, every score the evaluator returned, all stayed on this "
          "machine. The JSON proves it."),
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


