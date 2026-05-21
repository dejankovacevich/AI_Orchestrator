# Contributing

Welcome. This is a private-first AI orchestrator with intentionally
conservative defaults; the contribution rules reflect that. Read this once,
then look at [docs/Local_AI_Orchestrator_System_Guide.pdf](docs/Local_AI_Orchestrator_System_Guide.pdf)
(34 pages) and [docs/Local_AI_Orchestrator_Technical_Reference.pdf](docs/Local_AI_Orchestrator_Technical_Reference.pdf)
(40 pages) for the design and the file-by-file map.

## What this project IS / IS NOT

Read AGENTS.md before your first PR. The short version:

- **Is**: a local-first, clarification-driven, fail-closed-by-default work
  orchestrator. Patterns matter as much as code here.
- **Is not**: a chatbot, a multi-user system, a Cloud-first system, or
  something that sends external messages. PRs that change those defaults
  without explicit discussion will be closed.

## Setup

```bash
git clone https://github.com/dejankovacevich/AI_Orchestrator.git
cd AI_Orchestrator
bash scripts/check_system.sh
bash scripts/install_core.sh
```

Hardware floor: 16 GB unified memory minimum (tight); 32+ GB comfortable.
Apple Silicon recommended; Linux + NVIDIA works in principle but has not
been smoke-tested by maintainers (good first issue to fix).

## Run the test suite

```bash
bash scripts/run_tests.sh
```

You should see "153 passed" (or higher after recent additions) plus a
shell-syntax pass and a docker-compose-config pass. Every PR must keep
all tests green.

## Architecture rules of thumb

1. **No monoliths.** If you find yourself writing a 500-line function or
   a file longer than ~300 lines without a strong reason, you're probably
   conflating concerns. Split it. The recent storage and pdf_builders
   refactors are the patterns to follow.

2. **Each pipeline step is a function in `assistant_core/execution/steps.py`
   with signature `StepContext -> StepContext`.** Adding a new step is
   one function + one line in `assistant_core/execution/graph.py`.

3. **Every model call goes through `assert_model_allowed`.** No direct
   Ollama / LiteLLM calls that bypass the safety gate. Test it locally
   with `bash scripts/day_lock.sh` to confirm the gate fires.

4. **Cloud is fail-closed.** Six gates must pass. PRs that add cloud
   features must keep the default off and document how to enable them
   per-feature.

5. **Documented vs scaffolded matters.** When you add a stub or a
   placeholder, label it that way in the System Guide implementation
   table. Never claim "implemented" when the activity body returns a
   placeholder dict.

6. **Distinguish implemented from intended in user-facing strings.** If
   your PR adds a UI element for a scaffolded feature, the button should
   be disabled with a clear caption explaining what it will do.

## What makes a good PR

- **Scope**: one cohesive concept per PR. A new task type is a PR. A
  bug fix is a PR. "Refactor several things" without a unifying concept
  is too big.
- **Tests**: new behavior gets new tests in `tests/`. Look at
  `tests/test_task_types.py` and `tests/test_execution_steps.py` for the
  patterns. Tests must run hermetically — no real Ollama / Postgres /
  filesystem outside `tmp_path`.
- **Docs**: if the change is user-facing, edit
  `scripts/pdf_builders/` modules and regenerate PDFs with
  `.venv/bin/python scripts/build_pdfs.py`. Commit the regenerated
  PDFs.
- **Commit messages**: explain WHY the change exists. The body is more
  important than the subject. Look at the existing log for the house
  style (`git log --oneline`).
- **Conservative defaults**: any new capability defaults to OFF. Users
  opt in explicitly.

## What needs work right now

See [ROADMAP.md](ROADMAP.md) and the GitHub Issues tagged
`good-first-issue`. The current best entry points:

- **Prompt engineering for under-served task types** —
  `test_generation`, `doc_generation`, `decision_capture`, `risk_scan`
  fall back to `morning_brief` prompts today. Each one is ~50-100 lines
  of template work in `assistant_core/execution/prompts.py`, plus a
  test.
- **Few-shot examples** to extraction prompts. Local models benefit
  meaningfully from in-context examples. Worth ~+10% quality.
- **Self-consistency voting** in `process_sources` — run extraction
  N times, merge. Highest single-PR quality lift remaining.
- **Wire the actual Anthropic HTTP caller** so the cloud-review catalog
  can actually escalate when budget permits. Today the gate runs and
  catalogs candidates but never calls.
- **Linux + NVIDIA quick-start.** The codebase is platform-agnostic but
  install_core.sh is Mac-centric. Mirror it for Linux.

## How to propose something larger

Open a GitHub Discussion under "Ideas" before writing code. Examples:

- VS Code extension that surfaces overnight reviews inline
- Retrieval-augmented extraction (wiring Chroma)
- A 5-minute "essence" quickstart (pure Python + Ollama, no Docker)
- Self-critique loop

We'd rather align on the design than reject the PR after you've written it.

## Communication

- **Bugs / specific feature work**: GitHub Issues
- **Open questions / design discussions**: GitHub Discussions
- **Quick fixes**: just open a PR

There is no Discord, Slack, or mailing list. Asynchronous-by-default is
intentional — the system is built for people who want to focus on real
work and check status when they choose.

## License

By contributing, you agree your contributions are licensed under the same
MIT terms as the rest of the project. See [LICENSE](LICENSE).
