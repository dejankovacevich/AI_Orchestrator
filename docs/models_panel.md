# Models Tab — User Manual & Design

## What it is, in one sentence

A panel-level interface to **deliberately load and unload local Ollama
models** into VRAM, with a single-shot "quick test" form for verifying a
model works. Not a chat. All actions pass through the same safety gate
that protects the rest of the system, so in strict DAY_MODE the buttons
are inert.

The point: give you a one-click way to wake up a specific model when you
want to use it during the day, and a one-click way to put it back to sleep
when you're done — without ever using a chat interface or memorizing
Ollama CLI flags.

---

## TL;DR

| You want to… | Where |
|---|---|
| See what models are on disk | Models tab → *Pulled models (on disk)* |
| See what models are currently in VRAM | Models tab → *Currently loaded* |
| Load a model right now | *Pulled models* → "Load" button |
| Unload a model now (free VRAM) | *Currently loaded* → "Unload" button |
| Test a model with a single prompt | Models tab → *Quick test prompt* |
| Have a real conversation with a model | Open WebUI at http://localhost:3000 |

---

## How to use it

### Open the panel
```
bash scripts/start_control_panel.sh
# browse to http://127.0.0.1:8501
```
Click the **Models** tab.

### Currently loaded
The top section shows everything Ollama is holding in VRAM right now (via
`/api/ps`). Each entry has its size, an `expires_at` timestamp (when
Ollama plans to auto-unload it via its `keep_alive` timer), and an
**Unload** button. Clicking Unload immediately drops the model from
memory.

If nothing is loaded, you'll see "Nothing loaded. VRAM is idle."

### Pulled models (on disk)
Below that, every model already pulled into your local Ollama store. The
caption under each name shows which model group it maps to (`local-main`,
`local-coder`, etc.) — that group is what the safety gate checks.

The **Load** button does two things:
1. Calls `assert_model_allowed(<group>, <current_mode>)`. If you're in
   strict DAY_MODE without unlock, this raises `SafetyError` and the
   button is disabled with a warning at the top of the tab.
2. If allowed, posts a no-op generation to Ollama with `keep_alive: 30m`,
   which loads the weights into VRAM and pins them for 30 minutes of idle
   time.

The model now appears in *Currently loaded*.

### Quick test prompt
The bottom section is a single-shot verification form:

- **Model**: dropdown of currently-loaded models (falls back to pulled
  models if nothing is loaded yet).
- **Prompt**: any text. Default: "Say hi in one short sentence."
- **Send**: gated through `assert_model_allowed`. Returns Ollama's
  response in a code block.

The response is shown in the page; nothing is saved to the database,
filesystem, or Obsidian. This is for sanity-checking — not for doing
work. For real structured work, use **Create Work Packet**.

---

## How it works underneath

### The flow of a "Load" click

```
Streamlit click
  → ollama_admin.load_model(tag, mode=current_mode())
    → resolve_group_for_tag(tag)              # config/models.yaml lookup
    → assert_model_group_allowed(group, mode) # safety.py
      → assert_model_allowed(group, mode)
        → if local-* and DAY_MODE and not unlocked: raise SafetyError
    → POST /api/generate {model, prompt: "", keep_alive: "30m"}
      → Ollama loads weights into VRAM, returns 200
  → Streamlit shows success toast, reruns to refresh the table
```

### The flow of a "Quick test" click

```
Streamlit click
  → ollama_admin.quick_prompt(tag, prompt, mode=current_mode())
    → resolve_group_for_tag(tag)
    → assert_model_group_allowed(group, mode)
    → POST /api/generate {model, prompt, stream: false, keep_alive: "5m"}
      → Ollama runs inference, returns 200 with {"response": "..."}
  → Streamlit renders response in a code block
```

The keep_alive on a quick test is short (5 min) so a single test doesn't
pin VRAM for half an hour. The dedicated Load button is what you use for
longer-lived loads.

### Tag → group resolution

`config/models.yaml` is the single source of truth:

```yaml
local-main:       qwen3:30b-a3b
local-secondary:  llama3.3:70b
local-coder:      qwen3-coder:30b
local-reasoner:   deepseek-r1:8b
cloud-claude-opus: claude-opus-4-7
```

`ollama_admin.resolve_group_for_tag(tag)` reverses this mapping. If you
pull a tag not in this map (e.g. `qwen3:14b`), the resolver falls back
to `local-main` — meaning the gate still applies and DAY_MODE still
blocks. **Fail-closed by design.**

---

## Tools and code involved

| Layer | File | Role |
|---|---|---|
| Backend admin API | [`assistant_core/llm/ollama_admin.py`](../assistant_core/llm/ollama_admin.py) | `ollama_available`, `list_pulled_models`, `list_loaded_models`, `load_model`, `unload_model`, `quick_prompt`, `resolve_group_for_tag` |
| Tag → group map | [`config/models.yaml`](../config/models.yaml) | source of truth |
| Safety gate | [`assistant_core/safety.py`](../assistant_core/safety.py) | `assert_model_allowed`, `day_unlock_active` |
| Day unlock | [`scripts/day_unlock.sh`](../scripts/day_unlock.sh), [`scripts/day_lock.sh`](../scripts/day_lock.sh) | flip the gate |
| Status reporting | [`assistant_core/scheduler_status.py`](../assistant_core/scheduler_status.py) | `ollama_up`, `litellm_up`, etc. |
| Panel UI | [`app/control_panel.py`](../app/control_panel.py) | `_render_models_tab` |
| Tests | [`tests/test_ollama_admin.py`](../tests/test_ollama_admin.py) | tag resolution, gate enforcement, quick prompt behavior |

---

## Why this design

### Design goals

1. **Deliberate, not magic.** Models load when you click; nothing auto-loads.
2. **Visible state.** You can always see at a glance what's in VRAM.
3. **Same gate as the rest of the system.** No bypass; the panel doesn't
   have privileges that the CLI doesn't.
4. **Not a chatbot.** One-shot prompts only. Chat lives in Open WebUI.
5. **Cheap to unload.** One click and the VRAM is back.

### Alternatives considered and rejected

| Approach | Verdict | Why |
|---|---|---|
| **Auto-load on panel open** | rejected | Violates the "no auto-loading during the day" principle. |
| **Keep-alive forever** | rejected | A pinned model with no expiry would creep state. 30-min default lets Ollama clean up if you walk away. |
| **Full chat UI** | rejected | That's what Open WebUI is for. We don't compete. |
| **Pull-new-model from the panel** | deferred | Pulls can take 10–30 minutes; Streamlit's UX for long async ops is poor. CLI (`ollama pull` or `bash scripts/pull_models.sh`) handles this better. |
| **Per-call manual_override checkbox** | rejected | Adds a footgun. The whole point of day-unlock is one decision, not per-call decisions. |
| **Show model perplexity / benchmark scores** | out of scope | Could be added later but isn't core to the "wake up models" use case. |

### What the panel does NOT let you do

- Bypass the safety gate. Even in admin sections.
- Call `cloud-claude-opus`. The dropdown only shows local-* tags.
- Configure a custom keep-alive per click. (Default 30m for load, 5m for
  quick test. Edit `ollama_admin.py` if you genuinely need different
  values; the values are constants.)
- Send a chat conversation. Each "Send" is a fresh prompt with no history.
- Pull a model. CLI only.
- Edit Ollama's environment variables (`OLLAMA_KEEP_ALIVE`, etc.). Edit
  via `brew services` or a launchd plist for the daemon, not via the
  panel.

---

## Safety summary

1. **Gate is unconditional.** Every load, every quick test goes through
   `assert_model_allowed`. There is no path that bypasses it.
2. **Cloud is hard-locked** at the model selection layer: even with the
   day unlock on, `cloud-claude-opus` raises `SafetyError`. The cloud
   path has separate six-gate checks (see README's *Cloud Policy*).
3. **Unknown tags fall back to `local-main`.** Pulled but unmapped tags
   are treated as gated local models.
4. **No background loops.** The panel only checks Ollama state when you
   open the tab or click a button — no timers, no auto-refresh.

---

## Troubleshooting

**"Ollama is not reachable at the configured base URL"**
Run `brew services start ollama` and refresh the panel. If still down:
`curl http://localhost:11434/api/tags` to confirm; if that hangs, the
daemon never started.

**"Load" button is disabled and grey**
You're in strict DAY_MODE. Either run `bash scripts/day_unlock.sh
"reason"` to open the gate for this session, or set
`LOCALAI_MODE=NIGHT_MODE` in the shell that started Streamlit and
restart it.

**Click "Load" but nothing seems to happen, then a SafetyError**
The current mode/unlock state changed between page render and click. The
gate raised `SafetyError`. Refresh the page; the banner will show the
true state.

**Loaded a model but my MacBook fan went insane**
That's Ollama pulling weights into VRAM (and possibly running the warmup
call). Once the green "Loaded" toast appears, the fan should ease. If
the model is too big for your hardware, Ollama may swap to disk and
performance tanks; pick a smaller tag or unload others first.

**Quick test response is empty / truncated**
The prompt may be triggering Ollama's safety filters or the model may be
in a degenerate state. Try `unload` then `load` to reset state, or try a
different prompt.

**Model in dropdown is not what I pulled**
Make sure you pulled it via `ollama pull <tag>` or the script. Refresh
the panel — the *Pulled models* table re-reads `/api/tags` on each load.

---

## Future enhancements (not built)

- Per-model keep-alive picker (the user picks 5m / 30m / 2h / off when
  loading).
- Streaming response for the quick-test prompt (current UX waits for
  full response, which is bad for long generations).
- Token-counts and time-to-first-token display.
- A "Pull a new tag" widget with progress streaming (would require
  background tasks and proper Streamlit async support).
- Mini benchmark: a "Quick health check" button that sends 3 fixed
  prompts to a loaded model and reports latency + token rate.
