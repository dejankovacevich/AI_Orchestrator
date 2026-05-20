## Summary

One or two sentences. What changed, why.

## Linked issue

Closes #___

## What this PR does

- Specific change 1
- Specific change 2

## Implementation notes

How you approached it. Tradeoffs you considered. Anything reviewers
should look at carefully.

## How to verify locally

```bash
# Commands a reviewer can run to see the change in action:
```

## Checklist

- [ ] `bash scripts/run_tests.sh` is green
- [ ] New behavior has new tests
- [ ] Defaults are conservative (new capabilities OFF by default)
- [ ] Docs updated if user-facing (regenerate PDFs with `.venv/bin/python scripts/build_pdfs.py` and commit them)
- [ ] No `/Users/<your-name>` absolute paths, hostnames, or real personal data in the diff
- [ ] No new cloud calls without going through `assert_cloud_allowed`
- [ ] No new model calls without going through `assert_model_allowed`
- [ ] Distinguished "implemented" vs "scaffolded" in user-facing strings
- [ ] AGENTS.md rules respected (no destructive ops, no external writes, no Docker volume deletion)
