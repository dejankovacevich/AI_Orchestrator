"""Test fixtures that keep tests isolated from real user state.

Without this fixture, a real ``~/LocalAI/state/day_unlock.flag`` left over from
manual experimentation would silently flip the safety gates and make the strict
DAY_MODE tests fail. The autouse fixture redirects the safety module's default
state directory to a fresh per-test tmp dir and clears the env-var override.
"""

from __future__ import annotations

import pytest

import assistant_core.safety as safety


@pytest.fixture(autouse=True)
def isolate_day_unlock(tmp_path, monkeypatch):
    monkeypatch.delenv(safety.DAY_UNLOCK_ENV_VAR, raising=False)
    isolated_state_dir = tmp_path / "localai_state"
    isolated_state_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(safety, "DEFAULT_STATE_DIR", isolated_state_dir)
    return isolated_state_dir
