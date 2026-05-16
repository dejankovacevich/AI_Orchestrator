# Onboarding — Local AI Orchestrator

> A practical guide for using this system on your Mac. Written so you can come
> back to it in a month and pick up without thinking. Read this once, then
> bookmark the Quick Reference at the top.

---

## TL;DR — Quick Reference

| You want to… | Command |
|---|---|
| Check what's installed and healthy | `bash scripts/check_system.sh` |
| Start Postgres + Temporal + Open WebUI | `bash scripts/start_services.sh` |
| Start Ollama (background, survives reboots) | `brew services start ollama` |
| Start the control panel (browser UI) | `bash scripts/start_control_panel.sh` |
| Open the control panel | http://127.0.0.1:8501 |
| Create a work packet from a vague request | `bash scripts/create_work_packet.sh "Title" "Description"` |
| Provide answers to clarification questions | `bash scripts/answer_questions.sh <packet_id> examples/sample_answers.md` |
| Allow local model use during the day | `bash scripts/day_unlock.sh "reason"` |
| Re-enable strict daytime policy | `bash scripts/day_lock.sh` |
| Load / unload / test a model in the browser | Panel → **Models** tab |
| Change day/night times in the browser | Panel → **Schedule** tab |
| Verify nothing auto-runs at night | `launchctl list \| grep localai` (empty = off) |
| Run the test suite | `bash scripts/run_tests.sh` |
| See readiness-scoring demo without DB | `.venv/bin/python -m assistant_core.cli sample-readiness` |
| Stop docker services (keeps data) | `bash scripts/stop_services.sh` |

---

## 1. What this is

A private, **local-first executive work orchestrator** for your Mac. It does
not have a chat interface. It is a system that:

1. **Takes vague work requests** ("prepare me for tomorrow", "summarize the
   board notes") and turns them into structured **work packets**.
2. **Asks you strong clarifying questions** until the request is concrete
   enough to execute safely. Vague in → questions out. Concrete in → ready.
3. **Scores readiness** on 9 dimensions (objective, output format, sources,
   privacy/cloud policy, quality bar, audience, assumption policy,
   escalation, success criteria) and refuses to execute until the score
   crosses a threshold.
4. **Will eventually execute** the well-scoped packet overnight using local
   Ollama models, write outputs to `~/LocalAI/output/<date>/`, and surface
   memory candidates to Obsidian for your review.

The whole point is **clarify before doing anything heavy**, and **keep
everything on your machine** unless you explicitly opt into cloud.

### What "v1 scaffold" means

Today (the codebase as of this writing):

- **Implemented and usable**: clarification flow, readiness scoring, work
  packet storage in Postgres, the safety gates, the day-unlock switch, the
  control panel UI, the test suite.
- **Scaffolded only (placeholder code)**: the execution graph that actually
  calls models, the overnight pipeline body, the pause/resume buttons, the
  semantic memory indexer, the Claude cloud-review path. These exist as
  stubs so the wiring is right, but nothing real happens when you trigger
  them yet.

The day-unlock work was just landed. The next chapter is wiring the
execution graph.

---

## 2. What this is NOT

If you remember nothing else, remember the no list.

- **Not a chatbot.** There is no conversational interface. If you want to
  chat with a local model, use Open WebUI at http://localhost:3000 — that's
  a separate tool living alongside this one.
- **Not multi-user.** Single Mac, single user. No auth, no sharing.
- **Not for sending anything externally.** Cannot send email, Slack, SMS,
  calendar invites, GitHub PRs, or any other external write. Blocked at the
  safety layer; not a config you can flip.
- **Not for editing your original files.** Outputs are written to allowed
  roots only (`~/LocalAI/output/`, `~/LocalAI/archive/`, the Obsidian vault).
  Your inbox files are never modified.
- **Not auto-using cloud.** Claude requires *six* policy gates to pass for
  any single call. Day unlock does not open the cloud path.
- **Not running models in the background all day.** Default policy in
  `DAY_MODE` blocks every local-* model group. Models only load when you
  flip the day-unlock switch or you're in NIGHT_MODE.
- **Not exposed beyond localhost.** Every port binds to `127.0.0.1`. No
  LAN, no tunnel, no remote access.
- **Not a knowledge base by itself.** It writes to your Obsidian vault and
  reads from `~/LocalAI/inbox/`; the vault and inbox are *your* knowledge.

---

## 3. First-time setup (one-time)

You only do this once per Mac. Skip this section if your system is already
bootstrapped (which yours is).

```bash
cd /Users/macbookpro/Projects/local-ai-orchestrator

# 1. Verify hardware, OS, Docker, Ollama, Homebrew, ports
bash scripts/check_system.sh

# 2. Create .venv and install Python dependencies; creates ~/LocalAI and the
#    Obsidian vault subfolders.
bash scripts/install_core.sh

# 3. Install Docker Desktop (one-time)
brew install --cask docker
open -a Docker     # wait for it to finish initializing

# 4. Install Ollama (one-time)
brew install ollama
```

That's the bootstrap. Now you're ready for the daily flow.

---

## 4. Daily start sequence

Every time you want to actually use the system, run these in order. None of
them load models or do heavy work — they just bring services online.

```bash
cd /Users/macbookpro/Projects/local-ai-orchestrator

# 1. Make sure Ollama is running (as a brew service, survives reboots)
brew services start ollama
curl http://localhost:11434/api/tags     # should return JSON

# 2. Start the docker services (Postgres, Temporal, Temporal UI, Open WebUI)
bash scripts/start_services.sh

# 3. Confirm everything is up
bash scripts/check_system.sh             # full readout

# 4. Start the control panel
bash scripts/start_control_panel.sh
```

Open http://127.0.0.1:8501 in your browser.

To stop at the end of the day:

```bash
bash scripts/stop_services.sh            # stops Docker containers (data persists)
brew services stop ollama                # optional; releases the ollama daemon
# Ctrl+C the streamlit terminal tab, or kill it from the lsof PID
```

Volumes are preserved. Nothing is destroyed. Your work packets in Postgres
survive across restarts.

---

## 5. How to use it — concrete examples

### Example A: Pull a model so model-backed work can run later

Pulling downloads bytes to disk. It does NOT keep anything in RAM.

```bash
bash scripts/pull_models.sh
```

This pulls the three default models:
- `qwen3:30b-a3b` — the workhorse (`local-main`)
- `qwen3-coder:30b` — for code tasks (`local-coder`)
- `deepseek-r1:8b` — for reasoning checks (`local-reasoner`)

The big 70B (`local-secondary`) is skipped by default. To pull it
explicitly:

```bash
LOCALAI_PULL_LLAMA70B=true bash scripts/pull_models.sh
```

You can also pull manually:

```bash
ollama pull qwen3:30b-a3b
```

### Example B: Create a vague work packet (should be REJECTED for clarification)

```bash
bash scripts/create_work_packet.sh "Tomorrow prep" "Prepare me for tomorrow from my notes."
```

Expected output (JSON):

```json
{
  "work_packet_id": "abc123…",
  "status": "UNDERDEFINED",
  "readiness_score": 0.18,
  "questions": [
    {"category": "objective", "question": "What exact outcome should this produce…"},
    {"category": "outputs",   "question": "What exact output files or formats…"},
    {"category": "sources",   "question": "Which folders or files are in scope…"},
    {"category": "privacy/cloud", "question": "Is cloud fallback allowed…"},
    …
  ]
}
```

This is the **correct behavior**. The score is below 0.65, the status is
`UNDERDEFINED`, and the system is refusing to do anything until you answer
the gating questions.

### Example C: Answer the clarification questions

Look at the sample answer file for the format:

```bash
cat examples/sample_answers.md
```

Either edit that file or write your own. Then submit:

```bash
bash scripts/answer_questions.sh abc123… examples/sample_answers.md
```

Expected output:

```json
{
  "work_packet_id": "abc123…",
  "status": "READY_FOR_OVERNIGHT",
  "readiness_score": 0.90,
  "database": "updated",
  "remaining_questions": []
}
```

Status flipped to `READY_FOR_OVERNIGHT` (or `READY_HIGH_CONFIDENCE`),
remaining questions is empty. The packet is now eligible for execution.

### Example D: Try the demo without touching Postgres

If you just want to see clarification + scoring work, with no DB writes:

```bash
.venv/bin/python -m assistant_core.cli sample-readiness
```

This runs the deterministic flow on a hardcoded vague request and prints
the same JSON shape. Useful for sanity-checking the system when Docker is
down.

### Example E: Browse work packets in the panel

1. Open http://127.0.0.1:8501
2. **Dashboard** tab → table of all work packets with status + readiness
3. **Create Work Packet** tab → draft + score one interactively
4. **Clarification** tab → upload an answer markdown to preview
5. **Execution** tab → see the 18-step scaffold list (does not execute yet)
6. **Artifacts** tab → lists files in `~/LocalAI/output/`

### Example F: Allow local model use during the day

Default policy blocks all local-* model groups in `DAY_MODE`. To override
deliberately:

```bash
bash scripts/day_unlock.sh "checking last night's output before running again"
```

The panel will show a red banner. When you're done:

```bash
bash scripts/day_lock.sh
```

Full details: [docs/day_unlock.md](docs/day_unlock.md).

### Example G: Wake up a model from the browser (Models tab)

1. Open http://127.0.0.1:8501 → **Models** tab.
2. If you're in strict DAY_MODE, run `bash scripts/day_unlock.sh "reason"`
   first — otherwise the Load buttons are disabled.
3. Under **Pulled models (on disk)**, click **Load** on the model you
   want. The header status strip shows "Ollama: up"; you'll see a
   spinner; on success a toast appears and the model moves into
   **Currently loaded**.
4. Scroll to **Quick test prompt** → pick the loaded model → type a
   short prompt → hit **Send**. The response shows in a code block.
   Single-shot, no chat history. For real conversations use Open WebUI
   at http://localhost:3000.
5. Click **Unload** under *Currently loaded* to drop the model from
   VRAM immediately.

Full details: [docs/models_panel.md](docs/models_panel.md).

### Example H: Change day/night times from the browser (Schedule tab)

1. Open http://127.0.0.1:8501 → **Schedule** tab.
2. Edit any of `day_mode_start`, `night_mode_start`, `night_mode_end`.
   Format is 24-hour `HH:MM` (e.g. `08:00`, `22:30`).
3. Click **Save to config/assistant.yaml**. Atomic write; validation
   runs first.
4. If the nightly launchd plist is *installed*, the panel shows a
   yellow warning with the exact three commands to regenerate + reload.
   Until you run them, the installed plist still uses the old time.

The mode itself (DAY/NIGHT) does NOT auto-flip based on these times.
That stays a deliberate `LOCALAI_MODE` env var gesture. The times only
drive: (a) the launchd plist when generated, and (b) the visual hint
showing whether you're currently in the day or night window.

Full details: [docs/auto_execution.md](docs/auto_execution.md).

### Example I: Run the test suite (after any change)

```bash
bash scripts/run_tests.sh
```

Should print `88 passed`, plus shell-syntax and docker-compose
validation.

---

## 6. What this is FOR (use cases)

These are the scenarios this system is built around. If your need matches
one of these, you're in the right tool.

- **Morning briefing.** "From my notes/transcripts/docs, prepare a private
  morning brief: today's priorities, decisions needed, risks, draft
  messages I might send."
- **Meeting prep.** "Pull together what I need to know going into the
  call with X tomorrow."
- **Decision capture.** "Read these transcripts, extract decisions and
  who owns each follow-up, write them to my decisions vault."
- **Risk surfacing.** "Read this week's logs / notes and flag anything
  that looks like a risk or blocker for review tomorrow morning."
- **Drafting in your voice from your sources.** "Draft a follow-up
  message to person X based on these conversation notes — but do not
  send it; leave it in `~/LocalAI/output/<date>/` for me to review."
- **Pre-night clarification.** Most of your weekly value will come from
  the *clarification* step alone — the system forcing you to be explicit
  about quality bar, audience, sources, escalation, etc. That's useful
  even if execution never runs.

The pattern: you give it ambiguous work, it interrogates you until it's
not ambiguous, *then* it goes off and does it overnight, with everything
landing in `~/LocalAI/output/<date>/` for you to read in the morning.

---

## 7. What this is NOT for (and what to use instead)

| You want… | Use instead |
|---|---|
| Chat with a local model | Open WebUI at http://localhost:3000 |
| Code review / code generation | Claude Code, Cursor, or `local-coder` via LiteLLM (not gated through this orchestrator) |
| Reading Obsidian notes from chat | Open WebUI + the obsidian MCP (separate setup) |
| Sending an email | n/a — write the draft via this system, send it manually |
| A real-time API for other apps | Wrong tool; this is batch/overnight |
| Multi-user team workflows | Wrong tool; this is single-user |
| Heavy cloud-only models | Not the design point; cloud is gated and rarely used |

---

## 8. Do / Don't

### Do

- **Do** keep your input files under `~/LocalAI/inbox/` (notes,
  transcripts, docs, csv, cloud_review subfolders). That's the only
  place this system reads from.
- **Do** be specific in clarification answers. Single-line answers like
  `Cloud: do not use cloud` and explicit paths like `~/LocalAI/inbox/notes`
  parse better than vague prose.
- **Do** mark packets as `high_stakes` (board, CEO, legal, investor) if
  they need the 0.90 readiness bar instead of 0.85. The work packet
  builder auto-detects these terms in the title/description.
- **Do** use `day_unlock` deliberately, and lock again when done. The
  banner is your reminder.
- **Do** run `bash scripts/run_tests.sh` before committing changes.
- **Do** read [AGENTS.md](AGENTS.md) — it lists rules for anyone (human
  or AI) working in this repo.
- **Do** put model pulls on the Wi-Fi, not your mobile hotspot —
  `qwen3:30b-a3b` alone is ~19 GB.

### Don't

- **Don't** put cloud API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)
  in `.env` unless you specifically want to authorize cloud fallback.
  The system already refuses to use them by default; setting them
  removes one of the gates.
- **Don't** point the system at `~/Documents`, `~/Desktop`, or any
  folder you wouldn't be comfortable having a future indexer touch.
  Use `~/LocalAI/inbox/` only.
- **Don't** delete the `temporal_data` Docker volume thinking it
  contains your work. Your work packets live in the `postgres_data`
  volume.
- **Don't** edit files in `~/LocalAI/output/` and expect them to come
  back next time — they're regenerated on each run. Save important
  outputs into your Obsidian vault.
- **Don't** leave `day_unlock` on overnight if you don't need to —
  the file persists across reboots by design. Banner is loud, but
  habits beat banners.
- **Don't** run `git add .` blindly — `.gitignore` covers the
  important stuff (`.venv/`, `config/litellm.yaml`, `launchd/*.plist`,
  `logs/*.log`), but always glance at `git status` first.
- **Don't** bypass `assert_model_allowed()` by calling the LiteLLM /
  Ollama clients directly with raw tags. That's the safety gate;
  bypassing it defeats the whole DAY_MODE policy.
- **Don't** start the Temporal worker before the docker services are
  healthy. It'll fail to connect to `localhost:7233` and exit.

---

## 9. Safety rules (one-pager)

Every rule is enforced in code, not just documented.

| Rule | Where enforced |
|---|---|
| No cloud calls without 6 policy gates passing | `assert_cloud_allowed` in `assistant_core/safety.py` |
| No local model calls in DAY_MODE by default | `assert_heavy_execution_allowed` + `LOCAL_MODEL_GROUPS` |
| Day unlock is the only way to relax that, and it's visible | `day_unlock_active` + Streamlit banner |
| No writes outside allowed roots | `assert_original_file_write_allowed` |
| No emails / external API writes in v1 | `assert_no_external_write` (always denies) |
| Cloud Claude blocked at model selection too | `assert_model_allowed("cloud-claude-opus", …)` raises |
| Services bind to 127.0.0.1 only | docker-compose port mappings |
| Original inbox files never modified | output paths constrained to `~/LocalAI/output/` |

---

## 10. Daily shutdown

Most days you don't need a formal shutdown. If you want one:

```bash
bash scripts/day_lock.sh         # if unlock was on
bash scripts/stop_services.sh    # stops Docker containers (volumes preserved)
# Ctrl+C the streamlit terminal, or:
kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t)
# Ollama can stay running — it's idle when no calls come in
```

If you really want everything down:

```bash
brew services stop ollama
```

To wipe everything (NUCLEAR; you lose all work packets):

```bash
docker compose down -v    # removes containers AND volumes
```

Don't run this unless you genuinely want a clean slate.

---

## 11. Troubleshooting

### "Safari can't connect to 127.0.0.1:8501"
Streamlit isn't running. Start it: `bash scripts/start_control_panel.sh`.
If the port is held by a dead process: `kill $(lsof -nP -iTCP:8501 -sTCP:LISTEN -t)` then start again.

### "Error: could not connect to ollama server"
Ollama isn't running. Start it: `brew services start ollama`. Verify with `curl http://localhost:11434/api/tags`.

### Docker shows Temporal "Restarting"
Look at logs: `docker logs --tail=20 localai-temporal`. If it complains about a missing dynamic config file, the path in `docker-compose.yml` is wrong (this was fixed in commit `a2d6485` to use `docker.yaml`). Force-recreate: `docker compose up -d --force-recreate temporal`.

### "Postgres unavailable at postgresql://localai:localai@localhost:5432/localai"
Docker isn't running or the postgres container is down. Run `bash scripts/start_services.sh`. Then `bash scripts/status_services.sh`.

### Day unlock banner won't go away after running day_lock.sh
1. Refresh the browser tab (Streamlit only re-reads on script run).
2. Check `echo $LOCALAI_DAY_UNLOCK` in the shell that launched Streamlit. If set, `unset LOCALAI_DAY_UNLOCK` and restart Streamlit.

### `bash scripts/install_core.sh` fails on Python 3.14
Use Python 3.13 explicitly:
```bash
brew install python@3.13
LOCALAI_PYTHON_BIN=/opt/homebrew/bin/python3.13 bash scripts/install_core.sh
```

### Model pull says "Failed to pull <tag>"
Likely a registry name change. Fall back to one of the alternatives listed at the end of `scripts/pull_models.sh` — `ollama pull qwen3:32b`, `ollama pull qwen2.5-coder:32b`, etc.

### Tests fail with "DEFAULT_STATE_DIR" or unlock-related errors
The autouse fixture in `tests/conftest.py` should isolate tests from your real `~/LocalAI/state/day_unlock.flag`. If you've manually deleted `conftest.py`, restore it.

---

## 12. Where to read more

| Topic | Doc |
|---|---|
| Project overview, install, ports, architecture | [README.md](README.md) |
| Rules for agents (human or AI) editing this repo | [AGENTS.md](AGENTS.md) |
| The day-unlock switch in depth | [docs/day_unlock.md](docs/day_unlock.md) |
| Models tab — load/unload/test from the browser | [docs/models_panel.md](docs/models_panel.md) |
| Nightly auto-execution (off by default) | [docs/auto_execution.md](docs/auto_execution.md) |
| Postgres schema | [db/migrations/001_init.sql](db/migrations/001_init.sql) |
| Default config | [config/assistant.yaml](config/assistant.yaml) |
| Model groups → Ollama tags | [config/models.yaml](config/models.yaml) |
| LiteLLM routing | [config/litellm.yaml.example](config/litellm.yaml.example) |
| Safety code | [assistant_core/safety.py](assistant_core/safety.py) |
| Ollama admin code | [assistant_core/llm/ollama_admin.py](assistant_core/llm/ollama_admin.py) |
| Scheduler + service status | [assistant_core/scheduler_status.py](assistant_core/scheduler_status.py) |
| Config writer (atomic edits) | [assistant_core/config_writer.py](assistant_core/config_writer.py) |
| Clarification logic | [assistant_core/clarification/](assistant_core/clarification/) |
| Tests | [tests/](tests/) |

---

## 13. Mental model summary

> A vague request comes in. The system refuses to act on it. Instead it
> asks you 5–7 questions sized to the gaps in the request. You answer
> them in a markdown file. The system rescores. If readiness is ≥ 0.85
> (or ≥ 0.90 for high-stakes), the packet is eligible for overnight
> execution. Overnight, in NIGHT_MODE, the execution graph reads
> sources, calls local models through a safety gate, evaluates the
> output, retries on a secondary local model if needed, writes results
> to `~/LocalAI/output/<date>/`, and adds memory candidates to the
> Obsidian review queue. Cloud is never used unless six specific
> conditions are explicitly met. You read the output in the morning.
> Nothing leaves your machine.

That's the whole system in one paragraph. Everything else is plumbing.
