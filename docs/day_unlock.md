# Day Unlock — User Manual & Design

## What this is, in one sentence

A deliberate, visible switch that lets you run local Ollama models during the
day. By default the orchestrator's safety layer blocks every local-* model
group in `DAY_MODE`; flipping the switch tells it "I know what I'm doing right
now, let local models load." When you're done, you flip it back.

The goal is *intentionality*: nothing model-heavy ever loads silently into RAM
or VRAM during your work day. If something is loaded, you flipped a switch and
the control panel is showing you a red banner that says so.

---

## TL;DR — Quick reference

| Action | Command |
|---|---|
| Allow local models in DAY_MODE (persistent, survives terminal) | `bash scripts/day_unlock.sh` |
| Same, but with a reason captured in the flag file | `bash scripts/day_unlock.sh "investigating overnight output"` |
| Allow for one shell only (does not persist) | `export LOCALAI_DAY_UNLOCK=true` |
| Lock again (delete the flag) | `bash scripts/day_lock.sh` |
| Check current state from the CLI | `ls ~/LocalAI/state/day_unlock.flag` |
| Check current state from Python | `from assistant_core.safety import day_unlock_active; day_unlock_active()` |
| Check current state visually | Open the Streamlit control panel — a red banner appears when unlocked |

---

## How to use it

### From the terminal

```bash
# Open the gate. Optionally pass a reason that gets written into the flag.
bash scripts/day_unlock.sh "spot-checking a packet during the workday"

# … run whatever you need to run that calls local models …
# e.g. once execution graph is wired:
#   LOCALAI_MODE=DAY_MODE bash scripts/some_future_run_script.sh

# Close the gate when you're done.
bash scripts/day_lock.sh
```

`day_unlock.sh` writes a small file at `~/LocalAI/state/day_unlock.flag` that
contains an ISO-8601 timestamp, who ran it (`$USER@$(hostname)`), and your
reason. That file's existence is what the safety layer checks. Removing the
file re-locks.

### From the Streamlit control panel

`bash scripts/start_control_panel.sh` and open `http://127.0.0.1:8501`. At the
top of the page you'll see two metrics:

- **Current mode** — `DAY_MODE` or `NIGHT_MODE` (`LOCALAI_MODE` env var)
- **Day unlock** — `ACTIVE` or `off`

When unlock is ACTIVE the panel shows a red error-style banner with the flag
file path and its contents. There is no toggle button — you toggle it from the
shell, and the panel reflects the truth. This is deliberate: the file is the
source of truth, the panel is a read-only mirror.

Refresh the browser after running `day_unlock.sh` or `day_lock.sh` to see the
state change.

### From your own Python code

If you ever write code that calls a local model:

```python
from assistant_core.safety import assert_model_allowed

# This raises SafetyError unless we're in NIGHT_MODE, unlocked, or you pass
# manual_override=True at the call site.
assert_model_allowed("local-main", mode="DAY_MODE")
```

The `assert_model_allowed` call is your gate. Always go through it before you
hit Ollama / LiteLLM with a local model. Don't bypass it by calling the LLM
client directly with a raw Ollama tag.

---

## How it works underneath

### The check (one function, two channels)

[`assistant_core/safety.py`](../assistant_core/safety.py) defines:

```python
def day_unlock_active(state_dir=None) -> bool:
    if os.environ.get("LOCALAI_DAY_UNLOCK", "").strip().lower() in {"1","true","yes","on"}:
        return True
    base = Path(state_dir).expanduser() if state_dir else DEFAULT_STATE_DIR
    return (base / "day_unlock.flag").exists()
```

That's the whole logic. Two channels:

1. **Env var `LOCALAI_DAY_UNLOCK`** — quick, per-shell. Truthy values are
   `1`, `true`, `yes`, `on` (case-insensitive). Anything else, including the
   empty string, counts as off.
2. **Sentinel file `~/LocalAI/state/day_unlock.flag`** — persistent. The mere
   existence of the file at that path opens the gate; the contents are
   informational (timestamp, reason, hostname) and never parsed.

If either channel is on, `day_unlock_active()` returns `True`.

### Where it plugs in

The gate function is consumed in two places:

- `assert_heavy_execution_allowed(mode, manual_override=False)` — the core
  check. It computes `effective_override = manual_override or day_unlock_active()`
  and raises `SafetyError` if `DAY_MODE` and not `effective_override`.
- `assert_model_allowed(model_group, mode, manual_override=False)` — the
  caller-facing function. It first short-circuits `cloud-claude-opus`
  (always blocked here; cloud goes through `assert_cloud_allowed`), then for
  any `local-*` group it defers to `assert_heavy_execution_allowed`.

### What is gated

Today, the gate covers these model groups (defined in
[`safety.py`](../assistant_core/safety.py)):

```python
LOCAL_MODEL_GROUPS = frozenset({
    "local-main",       # → qwen3:30b-a3b
    "local-secondary",  # → llama3.3:70b
    "local-coder",      # → qwen3-coder:30b
    "local-reasoner",   # → deepseek-r1:8b
})
```

The mapping from group names to actual Ollama tags lives in
[`config/models.yaml`](../config/models.yaml) and
[`config/litellm.yaml`](../config/litellm.yaml). The gate works on group
names; if you add a new local group, add it to `LOCAL_MODEL_GROUPS` in the
same change.

### What is NOT gated by this

This is a deliberate scope. Day unlock only covers local model execution.
It does **not** affect:

- **Cloud Claude.** Still blocked. `cloud-claude-opus` is rejected by
  `assert_model_allowed` before the local-group check, and the separate
  `assert_cloud_allowed` function has its own six policy gates (see README's
  *Cloud Policy* section). Day unlock does nothing to those gates.
- **External writes** (email, Slack, calendar invites). `assert_no_external_write`
  is unaffected. V1 blocks these regardless.
- **Original-file modification.** `assert_original_file_write_allowed` is
  unaffected.
- **Heavy execution mode logic.** Mode names (`DAY_MODE`, `NIGHT_MODE`,
  `MANUAL_RESUME`) are unchanged. You're still in `DAY_MODE`. Unlock is a
  per-action policy override, not a mode change.
- **Anything Ollama itself decides to do.** Ollama only loads a model when
  asked. The gate sits *above* Ollama: it decides whether a call is made at
  all. Without unlock + a real caller, nothing reaches Ollama.

---

## Tools involved

| Layer | File | Role |
|---|---|---|
| Core gate | [`assistant_core/safety.py`](../assistant_core/safety.py) | `day_unlock_active()`, `assert_model_allowed()`, `assert_heavy_execution_allowed()` |
| State directory convention | [`assistant_core/paths.py`](../assistant_core/paths.py) | `~/LocalAI/state/` is created by `ensure_local_folders()` |
| CLI unlock | [`scripts/day_unlock.sh`](../scripts/day_unlock.sh) | Creates `day_unlock.flag` with timestamp + reason |
| CLI lock | [`scripts/day_lock.sh`](../scripts/day_lock.sh) | Removes the flag; warns if env var is also set |
| Visible status | [`app/control_panel.py`](../app/control_panel.py) | Reads `day_unlock_active()` + flag contents; renders the red banner |
| Tests | [`tests/test_safety.py`](../tests/test_safety.py) + [`tests/conftest.py`](../tests/conftest.py) | Isolated per-test state dir; covers locked, unlocked-by-file, unlocked-by-env, cloud-still-blocked, lock-restores-strict |
| Storage | filesystem | The flag *file* is the source of truth. No database row, no in-memory state, no shared lock |

---

## Why this design (and what we considered)

### Design goals

1. **Visible.** You should be able to ask "is the gate open right now?" and
   get an answer in under a second from anywhere — terminal, Python REPL,
   GUI.
2. **Cross-process.** The CLI, Temporal worker, LiteLLM proxy, and Streamlit
   panel all need to see the same answer. They run as separate processes,
   often started from different terminals.
3. **Persistent by default, ephemeral when you want.** Daily work usually
   means "unlock for the afternoon, lock before stepping away." That needs to
   survive terminal restarts. But sometimes you want a one-shot unlock for a
   single command.
4. **One source of truth.** No mismatch between "what Streamlit thinks" and
   "what the worker thinks." Both read the same thing.
5. **Reversible in one command.** No multi-step undo. No deploy. Just
   `day_lock.sh`.

### Alternatives considered and rejected

| Approach | Verdict | Why |
|---|---|---|
| **Only an env var** | rejected as sole mechanism | Doesn't survive terminal restarts. Each new shell starts locked unless you put the export in `.zshrc`, which is then *invisible* — you'd forget it's on. Kept as a secondary channel for one-off use. |
| **Just set `LOCALAI_MODE=NIGHT_MODE`** | rejected | Semantically wrong. You're not "running overnight"; you're working in the day with the gate open. Conflates two concepts. Also doesn't model-gate distinct from mode (e.g., NIGHT_MODE has its own future semantics around scheduling, archiving, etc.). |
| **Per-call `manual_override=True`** | kept but not sufficient on its own | Already exists at the function level; useful for one-off explicit gestures in code. But unusable as a daily workflow — you'd thread it through every script invocation. |
| **DB row in Postgres** | rejected | Adds a hard dependency on Postgres being up just to check a flag. Doesn't help when DB is down. Filesystem flag works always. |
| **In-memory toggle in the panel** | rejected | Only the panel process would know. CLI and worker would be blind. |
| **Sentinel file** | **chosen** | Visible (`ls`), cross-process (any reader), persistent (file system), one-command lock/unlock (`rm`/`touch`), zero deps. |

### Why I added the env-var channel too

The env var is a complement, not a substitute. Two cases:

- You want to unlock for exactly one command and not touch any state on disk:
  `LOCALAI_DAY_UNLOCK=true bash scripts/run_clarification.sh ...`
- You're inside an automated test or CI step where filesystem persistence
  would leak between runs.

In both cases the env var is scoped to the process tree of that one shell
invocation. Open a new terminal, you're locked again.

The file channel is for the daily workflow. The env channel is for sharp
one-off use.

### Why the flag holds a timestamp and reason

So later (or for someone reviewing your machine) you can answer "why is this
on?" by reading the file:

```text
$ cat ~/LocalAI/state/day_unlock.flag
unlocked_at: 2026-05-16T14:47:01Z
unlocked_by: user@host
reason: spot-checking a packet during the workday
```

The contents are informational only — the safety layer never parses them.
That means even an empty `touch ~/LocalAI/state/day_unlock.flag` will unlock.
The contents exist for the human, not the machine.

### What this does NOT try to be

- **Time-limited.** No auto-expiry. You unlock, it stays unlocked until you
  lock. If you want auto-expiry, that's an optional future enhancement —
  see below.
- **Per-model-group.** It's one switch for all local-* groups. We considered
  per-group flags but rejected as overkill for v1.
- **Audited in Postgres.** Unlock events don't write a row to `model_calls`
  or `execution_runs`. Adding that is straightforward later if you want a
  history.
- **A privilege escalation.** It does nothing to cloud, external writes, or
  any other gate. Day unlock is *only* for local model loads.

---

## What unlock does NOT open

Worth repeating because this is the most likely source of confusion:

1. **Claude / cloud Claude / `cloud-claude-opus`** — still blocked. The cloud
   path has its own six gates in `assert_cloud_allowed` (file-in-review-dir,
   work-packet allowance, ANTHROPIC_API_KEY present, high-stakes-or-failed,
   budget remaining, fallback enabled). Day unlock touches none of them.
2. **External sends** — email, Slack, calendar, external API writes. Blocked
   in v1 by `assert_no_external_write`.
3. **Original-source mutation** — files outside the configured write roots
   (`output/`, `archive/`, `logs/`, `work_packets/`, vault) remain protected
   by `assert_original_file_write_allowed`.

If you ever want a separate "cloud unlock" or "external send unlock", it
should be a separate switch with its own ceremony — not a knob on day_unlock.

---

## Testing it yourself

```bash
# State should start locked.
ls ~/LocalAI/state/day_unlock.flag 2>&1   # → "No such file or directory"

# This should print the SafetyError.
.venv/bin/python - <<'PY'
from assistant_core.safety import assert_model_allowed, SafetyError
try:
    assert_model_allowed("local-main", "DAY_MODE", manual_override=False)
    print("BAD: gate did not block")
except SafetyError as e:
    print("OK blocked:", e)
PY

# Flip it on.
bash scripts/day_unlock.sh "manual test"

# Now the same call succeeds silently.
.venv/bin/python - <<'PY'
from assistant_core.safety import assert_model_allowed
assert_model_allowed("local-main", "DAY_MODE", manual_override=False)
print("OK unlocked")
PY

# Cloud is still blocked, even unlocked.
.venv/bin/python - <<'PY'
from assistant_core.safety import assert_model_allowed, SafetyError
try:
    assert_model_allowed("cloud-claude-opus", "DAY_MODE", manual_override=True)
    print("BAD: cloud allowed")
except SafetyError as e:
    print("OK blocked:", e)
PY

# Flip it back off.
bash scripts/day_lock.sh

# Back to locked.
.venv/bin/python - <<'PY'
from assistant_core.safety import day_unlock_active
print("active?", day_unlock_active())   # → False
PY
```

The same logic is covered by automated tests in
[`tests/test_safety.py`](../tests/test_safety.py); run `bash scripts/run_tests.sh`
to execute the whole suite.

---

## Troubleshooting

**The Streamlit banner shows ACTIVE but I ran `day_lock.sh`.**
Refresh the browser. Streamlit reads the file only when it re-runs the
script. Also check `echo $LOCALAI_DAY_UNLOCK` — if it's set in the shell
that launched Streamlit, the env-var channel is still on. Run
`unset LOCALAI_DAY_UNLOCK` and restart Streamlit.

**`day_unlock.sh` succeeded but my CLI call still blocks.**
Check the path: `cat ~/LocalAI/state/day_unlock.flag`. If you set
`LOCALAI_STATE_DIR` in your shell, you might have unlocked a different
directory than the safety module reads. The default the safety module reads
is hardcoded to `~/LocalAI/state` (see `DEFAULT_STATE_DIR` in `safety.py`).

**Tests fail after I ran `day_unlock.sh`.**
They shouldn't — `tests/conftest.py` redirects the safety module to a
per-test tmp directory specifically to avoid this. If they do fail, the
conftest fixture is broken. Run with `pytest -vv` and check the
`isolate_day_unlock` fixture.

**I want unlock to expire automatically.**
Not built. Either lock manually with `day_lock.sh`, or add expiry as a
future enhancement: store an `expires_at` in the flag file and have
`day_unlock_active()` parse + compare it. That's a deliberate v1 omission
to keep the file an opaque sentinel.

---

## Future enhancements (not built)

These are listed for awareness; none are needed today.

- **Auto-expiry.** `day_unlock.sh --hours 4` writes an `expires_at` and
  `day_unlock_active` ignores the flag past that time. Trades simplicity for
  a guard against forgetting.
- **Audit log.** Insert a row into a new `policy_overrides` table whenever
  the flag is created/removed, with the reason. Useful if multiple humans
  share the box; not useful for a single-user Mac.
- **Slack or email reminder when unlocked > N hours.** Would violate the
  "no external writes" rule and is anti-pattern for a local-first system.
  Skip.
- **Per-model-group unlock.** `day_unlock --group local-reasoner` to unlock
  only the 8B distill while keeping 30B/70B locked. Useful if you ever want
  quick reasoning in the day but no chunky model loads. Currently you'd
  just call `assert_model_allowed("local-reasoner", "DAY_MODE", manual_override=True)`
  in the code path that needs it.
- **Lock-on-shutdown launchd hook.** Have launchd run `day_lock.sh` at
  system shutdown so a forgotten flag doesn't survive a reboot. Currently
  the flag does survive reboots, which is by design (matches the
  "persistent until you flip it back" contract).
