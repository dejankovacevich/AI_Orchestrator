# Local AI Orchestrator

Private, local-first AI work orchestration for a Mac. The system is designed to clarify vague work before doing anything heavy: it builds a work packet, asks strong questions, scores readiness, and only prepares overnight execution when enough context exists.

This is not a chatbot. V1 is a usable clarification and control scaffold. Full overnight execution is still scaffolded.

## Fast Setup

Run every command from the project root:

```bash
cd /Users/macbookpro/Projects/local-ai-orchestrator
```

### 1. Check The Mac

```bash
bash scripts/check_system.sh
```

This prints macOS, chip/RAM, disk, Python, Homebrew, Docker, Ollama, ports, Postgres, and Temporal status. It does not change anything.

### 2. Install The Python Environment

```bash
bash scripts/install_core.sh
```

This creates `.venv`, installs Python dependencies, and creates:

- `~/LocalAI`
- `~/Obsidian/LocalAI-ChiefOfStaff`

It does not install Docker Desktop, Ollama, launchd jobs, cloud keys, or large models.

If Python package installation fails on Python 3.14, use Python 3.13:

```bash
brew install python@3.13
LOCALAI_PYTHON_BIN=/opt/homebrew/bin/python3.13 bash scripts/install_core.sh
```

### 3. Install And Start Docker Desktop

Docker Desktop is required for Postgres, Temporal, Temporal UI, and Open WebUI.

```bash
brew install --cask docker
open -a Docker
```

Wait until Docker Desktop says it is running. Then verify Compose:

```bash
docker compose version
```

If `docker compose version` fails, Docker Desktop has not finished setup. Open Docker Desktop again and wait.

### 4. Start Local Services

```bash
bash scripts/start_services.sh
```

Expected local URLs:

- Open WebUI: <http://localhost:3000>
- Temporal UI: <http://localhost:8233>
- Postgres: `localhost:5432`
- Temporal: `localhost:7233`

Check service status:

```bash
bash scripts/status_services.sh
```

Stop services without deleting volumes:

```bash
bash scripts/stop_services.sh
```

### 5. Install And Start Ollama

Ollama is the local model runtime.

```bash
brew install ollama
```

Run it in a terminal tab:

```bash
OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /opt/homebrew/opt/ollama/bin/ollama serve
```

Or start it as a Homebrew service if you explicitly want it running in the background:

```bash
brew services start ollama
```

Confirm it responds:

```bash
curl http://localhost:11434/api/tags
```

### 6. Pull Models Manually

Model pulls are explicit because they can be large.

```bash
bash scripts/pull_models.sh
```

This tries the preferred local models and continues if a tag is unavailable. It skips `llama3.3:70b` by default.

To pull the large 70B model explicitly:

```bash
LOCALAI_PULL_LLAMA70B=true bash scripts/pull_models.sh
```

### 7. Start LiteLLM

Use a separate terminal tab:

```bash
cd /Users/macbookpro/Projects/local-ai-orchestrator
bash scripts/start_litellm.sh
```

LiteLLM runs on <http://localhost:4000>. Local model fallback is allowed. Blind fallback from local models to Claude is not configured.

### 8. Start The Temporal Worker

Use another terminal tab:

```bash
cd /Users/macbookpro/Projects/local-ai-orchestrator
bash scripts/start_temporal_worker.sh
```

The worker listens on task queue `local-ai-orchestrator`.

### 9. Start The Control Panel

Use another terminal tab:

```bash
cd /Users/macbookpro/Projects/local-ai-orchestrator
bash scripts/start_control_panel.sh
```

Open:

<http://localhost:8501>

## First Use

### Create A Work Packet

Postgres must be running first.

```bash
bash scripts/create_work_packet.sh "Morning prep" "Prepare me for tomorrow from my notes."
```

The expected behavior is clarification, not execution. A vague request should return a low readiness score and questions.

### Answer The Questions

Edit or reuse:

```bash
examples/sample_answers.md
```

Then run:

```bash
bash scripts/answer_questions.sh <work_packet_id> examples/sample_answers.md
```

This updates the stored packet, marks open questions answered, rescales readiness, and creates another question round if gaps remain.

### Run A Readiness Demo Without Postgres

```bash
.venv/bin/python -m assistant_core.cli sample-readiness
```

This is useful for confirming clarification logic even when Docker services are not running.

## Overnight Execution

V1 only starts workflows for packets marked `READY_FOR_OVERNIGHT` or `READY_HIGH_CONFIDENCE`. The full heavy execution graph is still scaffolded.

Manual overnight start:

```bash
LOCALAI_MODE=NIGHT_MODE bash scripts/run_ready_overnight.sh
```

This refuses to run from `DAY_MODE` unless you explicitly use the night/manual mode flags.

## Optional Nightly launchd Job

Generate the plist safely inside the project:

```bash
bash scripts/create_launchd_plist.sh
```

This writes:

```text
launchd/com.localai.orchestrator.nightly.plist
```

It does not write to `~/Library/LaunchAgents` by default.

To copy it into LaunchAgents explicitly:

```bash
LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh
```

Then review and load manually:

```bash
launchctl load "$HOME/Library/LaunchAgents/com.localai.orchestrator.nightly.plist"
```

## Validation

Run:

```bash
bash scripts/run_tests.sh
```

This checks:

- shell syntax
- Python compilation
- pytest
- Docker Compose config when Compose is available

If Docker Compose is missing, the script skips only that check and prints the manual Docker Desktop instruction.

## Safety Rules

- No cloud by default.
- No Claude unless every cloud policy gate passes.
- No external writes in v1.
- No emails, calendar invites, Slack messages, production API writes, or production actions in v1.
- No original user file modification.
- No service exposure beyond localhost.
- No local model calls in `DAY_MODE` by default. All local-* model groups (`local-main`, `local-secondary`, `local-coder`, `local-reasoner`) require `NIGHT_MODE` or an explicit manual override. Day mode is clarification and deterministic logic only. To deliberately allow local models during the day, use the day-unlock switch — see [docs/day_unlock.md](docs/day_unlock.md).
- No model pulls unless explicitly invoked.
- No launchd loading unless manually approved.

## Cloud Policy

Claude Opus is never automatic. Every condition must be true:

1. `cloud_fallback_enabled = true`
2. File is inside `~/LocalAI/inbox/cloud_review` or filename contains `.cloud.`
3. `ANTHROPIC_API_KEY` exists
4. Task is high-stakes or local quality gates failed
5. Daily cloud budget remains
6. Work packet explicitly allows cloud fallback

Do not put Claude into blind LiteLLM fallback chains.

## Local Folders

The install script creates:

```text
~/LocalAI/
  inbox/
    notes/
    transcripts/
    docs/
    csv/
    cloud_review/
  output/
  archive/
  logs/
  state/
  work_packets/
```

And:

```text
~/Obsidian/LocalAI-ChiefOfStaff/
  00_Inbox/Memory_Review/
  01_Daily_Briefs/
  02_Work_Packets/
  03_Projects/
  04_Meetings/
  05_Decisions/
  06_Stakeholders/
  07_Playbooks/
  08_Prompts/
  09_System_Logs_Summaries/
  99_Archive/
```

## Service Ports

| Service | URL |
| --- | --- |
| Ollama | `http://localhost:11434` |
| Open WebUI | `http://localhost:3000` |
| LiteLLM | `http://localhost:4000` |
| Temporal | `localhost:7233` |
| Temporal UI | `http://localhost:8233` |
| Postgres | `localhost:5432` |
| Control Panel | `http://localhost:8501` |

## Architecture

- Ollama: local model runtime.
- Open WebUI: manual local assistant GUI.
- LiteLLM: local/cloud model gateway and local fallback layer.
- LangGraph: clarification and future execution graph structure.
- Temporal: durable workflow engine for retries, resumability, and future pause/resume.
- Postgres: operational state, work packets, audit trail, model calls, evaluations, artifacts, and memory candidates.
- Obsidian: human-readable long-term notes and review queues.
- Chroma: local semantic retrieval target.

## Readiness Scoring

Dimensions:

- objective clarity: 0.18
- output format clarity: 0.14
- source clarity: 0.14
- privacy/cloud policy clarity: 0.14
- quality threshold clarity: 0.12
- audience clarity: 0.10
- assumption policy clarity: 0.08
- escalation policy clarity: 0.06
- success criteria clarity: 0.04

Thresholds:

- `>= 0.90`: `READY_HIGH_CONFIDENCE`
- `>= 0.85`: `READY_FOR_OVERNIGHT`
- `0.65` to `0.84`: `NEEDS_CLARIFICATION`
- `< 0.65`: `UNDERDEFINED`

High-stakes packets require `>= 0.90`.

## Troubleshooting

### Docker CLI exists but daemon is not reachable

Open Docker Desktop:

```bash
open -a Docker
```

Wait, then run:

```bash
docker info
docker compose version
```

### `docker compose` is missing

Install/use Docker Desktop, not only the standalone Docker CLI:

```bash
brew install --cask docker
open -a Docker
```

### Ollama is missing

```bash
brew install ollama
OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /opt/homebrew/opt/ollama/bin/ollama serve
```

### Postgres is unavailable

Start Docker Desktop, then:

```bash
bash scripts/start_services.sh
```

### Temporal worker will not start

Make sure services are running first:

```bash
bash scripts/status_services.sh
bash scripts/start_temporal_worker.sh
```

### LiteLLM warns about `ANTHROPIC_API_KEY`

That is expected for local-only use. Do not set cloud keys unless you intend to enable explicit cloud fallback.

## Current V1 Limits

Implemented:

- project structure
- safe install scripts
- configs
- database schema
- deterministic clarification
- work packet creation/update
- readiness scoring
- basic memory scaffolding
- basic control panel
- tests and validation scripts

Scaffolded:

- full LangGraph execution
- heavy overnight file-processing pipeline
- quality-gated local retry loop
- real pause/resume UI
- semantic memory indexing workflow
- Claude review path after policy gates
