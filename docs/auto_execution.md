# Auto-execution (launchd nightly job) — User Manual & Design

## What it is, in one sentence

A macOS **launchd** job that runs `scripts/run_ready_overnight.sh` at the
hour configured in `config/assistant.yaml` (`night_mode_start`), so the
orchestrator can wake up overnight, find work packets in
`READY_FOR_OVERNIGHT` or `READY_HIGH_CONFIDENCE` status, and process
them with `LOCALAI_MODE=NIGHT_MODE` set.

**Default state: OFF.** Nothing auto-runs unless you explicitly install
and load the plist with two terminal commands. The system ships with the
plist *generated* but not *armed*.

---

## TL;DR

| You want to… | Command |
|---|---|
| Verify auto-execution is OFF | `launchctl list \| grep com.localai.orchestrator.nightly` (empty = off) |
| See the four-layer status from the panel | Schedule tab → top metrics |
| Change the nightly hour | Schedule tab → edit `night_mode_start` |
| Regenerate the plist after editing times | `bash scripts/create_launchd_plist.sh` |
| Install the plist into LaunchAgents | `LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh` |
| Arm auto-execution | `launchctl load ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist` |
| Disarm auto-execution | `launchctl unload ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist` |
| Remove the plist entirely | `rm ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist` |

---

## The four states

There are three independent layers, giving four meaningful states:

| Project plist generated | Installed in `~/Library/LaunchAgents` | Loaded in launchctl | State |
|---|---|---|---|
| no | no | no | **fully off, nothing installed** |
| yes | no | no | **off — plist generated locally but never installed** ← default |
| yes | yes | no | **off — installed but not loaded** |
| yes | yes | yes | **ARMED — will run nightly at `night_mode_start`** |

The Schedule tab in the panel shows all three layers as separate metrics.
A glance tells you exactly which state you're in.

---

## How to read your current state from the terminal

```bash
# Is launchctl currently running the job?
launchctl list | grep com.localai.orchestrator.nightly
# (no output = not loaded)

# Is the plist installed in LaunchAgents?
ls ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist

# Does the project-local plist file exist?
ls launchd/com.localai.orchestrator.nightly.plist

# Are any cron entries lurking?
crontab -l | grep -i localai
```

All four returning empty / "no such file" = auto-execution is OFF.

---

## How to arm it (deliberate, three steps)

```bash
# 1. Make sure config/assistant.yaml has the time you want. Edit in the
#    panel's Schedule tab or hand-edit the yaml.

# 2. Regenerate the plist so it picks up the current night_mode_start.
bash scripts/create_launchd_plist.sh
# The script prints the scheduled time it baked in. Verify it matches.

# 3. Copy the plist into LaunchAgents (the script does this if you set
#    the env var) and then load it.
LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh
launchctl load ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist
```

After step 3, `launchctl list | grep com.localai.orchestrator.nightly`
should return one line. You're armed.

The panel's status strip will flip:
- "Auto-execution" → `SCHEDULED` with the configured time underneath
- A yellow banner appears at the top of every page

---

## How to disarm it

```bash
launchctl unload ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist
# Optionally remove it entirely:
rm ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist
```

The project-local copy at `launchd/com.localai.orchestrator.nightly.plist`
is harmless to keep — it does nothing unless installed.

---

## What the job actually does when it fires

`scripts/run_ready_overnight.sh` is the entry point. Reading from the top:

1. Refuses to proceed unless `LOCALAI_MODE=NIGHT_MODE` or
   `LOCALAI_MANUAL_RESUME=true`. The launchd plist sets `LOCALAI_MODE`
   for you. (If you ran the script manually in DAY_MODE without the
   override, it exits with a clear refusal message.)
2. Runs `.venv/bin/python -m assistant_core.cli run-ready-overnight`.
3. That CLI command queries Postgres for packets in
   `READY_FOR_OVERNIGHT` or `READY_HIGH_CONFIDENCE`, then for each one
   submits a Temporal `OvernightExecutionWorkflow` against the
   `local-ai-orchestrator` task queue.
4. The Temporal worker (a long-running Python process, **separate**)
   actually executes the workflow. **If the worker isn't running, the
   job will just queue the workflows in Temporal and they'll wait.**

This means arming launchd is not enough on its own to actually process
work overnight — you also need the Temporal worker running. In v1 the
execution graph is still a scaffold (returns a placeholder), so even
with both armed, nothing material happens yet. That changes when the
execution graph is wired.

---

## Editing the nightly time

The Schedule tab exposes three editable fields:

- `day_mode_start` — the time you consider "day" to begin (e.g. 07:30).
- `night_mode_start` — the time the nightly job will fire (e.g. 01:30).
  This is the value that drives the launchd plist.
- `night_mode_end` — the time night execution should hard-stop.

After clicking Save:

1. `config/assistant.yaml` is rewritten atomically (temp file +
   `os.replace`).
2. The panel shows a success banner with a regenerate hint.
3. **If the plist is already installed in `~/Library/LaunchAgents`**, the
   panel shows a follow-up warning explaining that the *installed* plist
   is out of sync with the *config*, with the exact three commands
   needed to regenerate and reload.

Editing the times does NOT touch launchd directly. Mutating launchd
state remains a deliberate terminal gesture, by design. The panel only
edits config.

---

## Why this design

### Design goals

1. **OFF by default.** Bootstrapping should never silently arm a daily
   recurring job.
2. **Four states, transparent.** The user can always tell exactly where
   they are by looking at three independent checks.
3. **Config is the source of truth for time.** The launchd schedule
   reads from `config/assistant.yaml`. If you change the config, you
   regenerate the plist; you don't edit XML.
4. **Panel edits config, terminal edits launchd.** The panel can change
   *when* the job would run; only an explicit terminal command actually
   installs or loads it. This keeps the high-impact action (arming) in
   the user's hands.

### Alternatives considered and rejected

| Approach | Verdict | Why |
|---|---|---|
| **Auto-arm during install_core** | rejected | Violates "OFF by default." Bootstrapping should be inert. |
| **Panel button "Enable nightly schedule"** | rejected | Adds a one-click arm. Too easy to flip by accident. |
| **Watch config and auto-regenerate plist on change** | rejected | More magic, more invisible state. A file-watcher daemon is overkill. |
| **Use cron instead of launchd** | rejected | launchd is the macOS-native scheduler. cron is deprecated for new use. |
| **Embed the time directly in the plist (no config link)** | rejected | Two sources of truth. User edits the config, plist gets stale, surprise at 1:30 AM. |
| **Make `night_mode_end` enforced by Temporal cancellation** | future v2 | Useful but requires Temporal-side scheduling work. Today it's documentation only. |

### What can still go wrong (and what protects you)

- **You edit the time in the panel but don't regenerate the plist.** The
  installed plist still fires at the old time. Panel warning surfaces
  this explicitly.
- **You arm the job but Ollama is down at 01:30.** The job runs, fails
  trying to call models, exits with errors. Logs go to
  `~/LocalAI/logs/launchd.{out,err}.log`.
- **You arm the job but the Temporal worker isn't running.** Workflows
  queue in Temporal but don't execute. They wait for the worker.
- **You arm the job while a `~/LocalAI/state/day_unlock.flag` is
  present.** The job runs in NIGHT_MODE (set by the plist's env var), so
  unlock state doesn't matter — it's already in night.
- **macOS Battery / Low Power mode is on.** launchd will defer the job
  until the system is awake. You may see the job run at 07:00 instead
  of 01:30.

---

## Tools and code involved

| Layer | File | Role |
|---|---|---|
| Plist generator | [`scripts/create_launchd_plist.sh`](../scripts/create_launchd_plist.sh) | reads `night_mode_start`, writes plist; copies into LaunchAgents only when `LOCALAI_WRITE_LAUNCHD=true` |
| Overnight runner | [`scripts/run_ready_overnight.sh`](../scripts/run_ready_overnight.sh) | refuses unless NIGHT_MODE / MANUAL_RESUME; calls CLI |
| CLI hook | [`assistant_core/cli.py`](../assistant_core/cli.py) | `run-ready-overnight` command |
| Status inspection | [`assistant_core/scheduler_status.py`](../assistant_core/scheduler_status.py) | `launchd_job_loaded`, `launchd_plist_installed`, `project_plist_exists`, `auto_execution_status` |
| Config editing | [`assistant_core/config_writer.py`](../assistant_core/config_writer.py) | atomic, validated edits to time fields |
| Panel UI | [`app/control_panel.py`](../app/control_panel.py) | Schedule tab + status banner |
| Tests | [`tests/test_scheduler_status.py`](../tests/test_scheduler_status.py), [`tests/test_config_writer.py`](../tests/test_config_writer.py) | window math, launchd detection, atomic write |

---

## Troubleshooting

**Panel says "Auto-execution: SCHEDULED" but I don't remember enabling it.**
Run `launchctl list | grep com.localai.orchestrator.nightly`. If it
returns a line, someone (you, an earlier session, an install script you
ran) loaded it. Disarm with the unload command above.

**I edited the time but the job still fires at the old time.**
The installed plist is stale. Run:
```bash
LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh
launchctl unload ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist
launchctl load ~/Library/LaunchAgents/com.localai.orchestrator.nightly.plist
```

**`launchctl load` says the plist is already loaded.**
Unload first: `launchctl unload <path>`, then load again.

**I want a daily run but at multiple times.**
Edit the generated plist directly — `StartCalendarInterval` can be an
array. Or write a second plist with a different Label. The shipped
script only does one fire-time.

**I want to test the script without waiting until 01:30.**
`LOCALAI_MODE=NIGHT_MODE bash scripts/run_ready_overnight.sh`. This is
the same command launchd will run, and it'll proceed if there are any
`READY_*` packets in the database (and exit with "no work" if there
aren't).

---

## Mental model summary

> The panel can change *when* the nightly job is configured to run. It
> cannot arm or disarm it. Arming is a deliberate three-step terminal
> gesture: regenerate plist → install in LaunchAgents → load via
> launchctl. The status strip always shows you which of the four states
> you're in. Default is fully off and the panel's banner makes that
> visible.
