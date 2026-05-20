# Roadmap

What's named but not yet built, roughly in order of value-per-PR.
Pick anything in here as a starter; open a Discussion first only for
items marked **larger**.

The implementation status table in
[docs/Local_AI_Orchestrator_System_Guide.pdf](docs/Local_AI_Orchestrator_System_Guide.pdf)
section 8 is the source of truth; this file is the human-readable view.

## Quality lifts (local-only, free overnight)

- [ ] **Few-shot examples in extraction prompts.** Add 1-2 worked examples
      to `MORNING_BRIEF_EXTRACT_TEMPLATE` and `CODE_REVIEW_EXTRACT_TEMPLATE`
      in `assistant_core/execution/prompts.py`. Measure quality on a
      small held-out set. Typically +5-15% completeness.
- [ ] **Self-consistency voting** in `assistant_core/execution/steps.py`.
      Run extraction N times (config-driven, default 3), merge by
      majority. Largest single quality bump for mid-tier local models.
- [ ] **Self-critique loop.** After extraction, ask a local model to
      critique its own output against the source. Revise on failure.
      Catches hallucinations the deterministic evaluator misses.

## Task type completeness

Today only `morning_brief` and `code_review` have specialized prompts.
The others fall back. Each is ~50-100 lines + a test:

- [ ] **`test_generation`** extract + synthesize prompts. Output:
      structured "missing test cases" list with given/when/then outlines.
- [ ] **`doc_generation`** extract + synthesize prompts. Output:
      docstrings + README section per module.
- [ ] **`decision_capture`** extract + synthesize prompts. Reads
      transcripts; output: decisions + action items by owner + ambiguous
      ownership list.
- [ ] **`risk_scan`** extract + synthesize prompts. Output: risks +
      blockers sorted by severity, with recommended action.

## Cloud-review caller (small, focused)

- [ ] **Wire the actual Anthropic HTTP call** in
      `assistant_core/execution/steps.py::cloud_review_gate`. The gate
      runs and catalogs candidates today; flipping `escalated=True`
      requires the actual call. Use LiteLLM's `/v1/chat/completions` so
      future OpenAI/other-provider routing is one config line. Add a
      per-call cost estimate (token counts * pricing constants in
      `config/assistant.yaml`) and a hard stop when
      `daily_cloud_budget_usd` is exceeded.

## Platform / packaging

- [ ] **Linux + NVIDIA quick-start.** Mirror `scripts/install_core.sh`
      and `scripts/check_system.sh` for Linux. Ollama works there; the
      only Mac-specific bits are `brew`, `launchd`, and the M-series VRAM
      assumptions in the docs.
- [ ] **One-command quickstart.** `bash scripts/quickstart.sh` that
      handles brew + docker + ollama + model pulls + service start. The
      current 7-step setup is the biggest barrier to adoption.
- [ ] **"Essence" variant.** A stripped-down branch (no Postgres, no
      Temporal) that takes 5 minutes to install and demonstrates the
      core clarification + safety patterns. Useful as a teaching artifact.

## UX / integrations

- [ ] **VS Code extension.** Right-click → "queue for overnight review".
      Surfaces the resulting markdown inline next morning. Largest
      single move for the indie-dev persona.
- [ ] **A demo GIF / screencast in the README.** 30 seconds of
      `review_code.sh` running. Adoption depends on people seeing what
      it produces before they install.
- [ ] **Status badges in README** (build, license, latest release).

## Retrieval-augmented context (**larger**)

- [ ] **Index the vault + inbox into Chroma.** The vector store is
      scaffolded in `assistant_core/memory/vector_store.py` but no
      indexer writes to it.
- [ ] **Retrieve relevant chunks per extraction** instead of stuffing
      the whole source in. Improves grounding for long documents.
- [ ] **Cross-document reasoning.** Synthesis that pulls citations from
      multiple sources via retrieval.

## Tool use / agentic moves (**larger**)

- [ ] **Calculator tool** for the model. Local execution; structured
      input/output.
- [ ] **File-search tool** scoped to `~/LocalAI/inbox/`.
- [ ] **Inline test-execution + repair loop** for code tasks: model
      proposes code → runner executes in a sandbox → on failure, model
      sees output and revises. The closed loop is what makes cloud
      coding agents useful; doable locally.

## Operational

- [ ] **Pause/resume UI** actually wired (today the buttons are
      disabled, the DB statuses exist).
- [ ] **Streamlit panel auto-refresh** of status pills (today static
      until you reload).
- [ ] **Better launchd diagnostics** when the nightly job fails (parse
      `~/LocalAI/logs/launchd.err.log` and surface the last error in
      the panel).

## Security / hardening

- [ ] **Cryptographic grounding** in addition to today's "Source:"
      marker counting. Verify quoted snippets actually appear in the
      cited source files; surface mismatches in the audit log.
- [ ] **Reproducibility hash** per run: hash of (model tag, prompt
      versions, input bytes) so a re-run can prove it was the same
      inputs.
- [ ] **Hardware attestation** export (optional, for regulated work):
      include the Mac's hardware-keyed identity in the audit JSON so a
      reviewer can confirm a specific machine produced the output.

---

If you want to tackle something, open an issue first (or pick one from
the existing list) so the work isn't accidentally duplicated. PRs that
match an existing issue + reference it in the description merge faster.
