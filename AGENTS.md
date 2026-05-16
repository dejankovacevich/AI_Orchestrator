# AGENTS

Rules for future agents working in this repository:

- Be conservative. This is a private local-first executive work orchestrator, not a chatbot.
- Do not use cloud by default. Claude requires explicit task policy authorization and every safety gate.
- Do not delete user data, Docker volumes, Obsidian notes, or original files.
- Do not hardcode secrets. Keep API keys in environment variables only.
- Do not modify original user files. Write outputs to configured output, work packet, archive, log, or allowed Obsidian folders.
- Do not send emails, calendar invites, Slack messages, external API writes, or production actions in v1.
- Do not expose services beyond localhost unless explicitly requested.
- Do not run uncontrolled heavy local execution during daytime. DAY_MODE is clarification only by default.
- Prefer explicit policies and deterministic checks over model judgment.
- Keep the system local-first and clarification-driven.
- Distinguish implemented behavior from scaffolded behavior in user-facing reports.
- Update README.md when changing behavior, scripts, ports, service topology, or safety policy.
- Run validation before claiming success: `bash scripts/run_tests.sh` plus any task-specific checks.
- Never overclaim installation success. If Docker, Ollama, Temporal, Postgres, models, or cloud keys are missing, say so clearly.
