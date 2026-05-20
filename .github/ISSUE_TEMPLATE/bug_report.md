---
name: Bug report
about: Something the orchestrator does that it shouldn't, or vice versa
title: "[bug] "
labels: bug
---

## What happened

A clear, one-paragraph description.

## What you expected to happen



## Steps to reproduce

```
1.
2.
3.
```

## Environment

- macOS version (`sw_vers`):
- Hardware (chip + unified memory):
- Python version (`.venv/bin/python --version`):
- Ollama version (`ollama --version`):
- Docker Desktop version (`docker --version`):
- Branch + commit (`git log --oneline -1`):

## Output of `bash scripts/check_system.sh` (trim sensitive bits)

```
<paste here>
```

## Relevant log excerpts

If applicable, attach:

- Streamlit terminal output
- `docker logs --tail=50 localai-postgres`
- `docker logs --tail=50 localai-temporal`
- `~/LocalAI/logs/*.log`

## Notes

Anything else.
