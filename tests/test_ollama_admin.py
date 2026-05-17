from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from assistant_core.llm import ollama_admin
from assistant_core.safety import SafetyError


SAMPLE_TAGS = {
    "models": [
        {
            "name": "qwen3:30b-a3b",
            "size": 18_000_000_000,
            "modified_at": "2026-05-16T10:00:00Z",
            "digest": "abcdef1234567890",
        },
        {
            "name": "deepseek-r1:8b",
            "size": 5_000_000_000,
            "modified_at": "2026-05-16T11:00:00Z",
            "digest": "1234567890abcdef",
        },
    ]
}

SAMPLE_PS = {
    "models": [
        {
            "name": "qwen3:30b-a3b",
            "size_vram": 18_000_000_000,
            "expires_at": "2026-05-16T12:30:00Z",
        }
    ]
}

SAMPLE_GENERATE_RESPONSE: dict[str, Any] = {
    "model": "qwen3:30b-a3b",
    "response": "hi",
    "done": True,
}


def _fake_get(payload: dict[str, Any]):
    def _impl(path: str, *, timeout: int = 5) -> dict[str, Any]:
        return payload

    return _impl


def _fake_post(payload: dict[str, Any]):
    def _impl(path: str, body: dict[str, Any], *, timeout: int) -> dict[str, Any]:
        _impl.last_call = (path, body, timeout)  # type: ignore[attr-defined]
        return payload

    _impl.last_call = None  # type: ignore[attr-defined]
    return _impl


def test_list_pulled_models_normalizes_entries():
    with patch.object(ollama_admin, "_get", side_effect=_fake_get(SAMPLE_TAGS)):
        entries = ollama_admin.list_pulled_models()
    assert [entry["name"] for entry in entries] == [
        "deepseek-r1:8b",
        "qwen3:30b-a3b",
    ]
    assert entries[1]["size_human"].endswith("GB")
    assert entries[1]["digest"] == "abcdef123456"


def test_list_loaded_models_returns_ps_entries():
    with patch.object(ollama_admin, "_get", side_effect=_fake_get(SAMPLE_PS)):
        loaded = ollama_admin.list_loaded_models()
    assert len(loaded) == 1
    assert loaded[0]["name"] == "qwen3:30b-a3b"
    assert loaded[0]["expires_at"] == "2026-05-16T12:30:00Z"


def test_resolve_group_for_tag_uses_models_yaml_mapping():
    with patch.object(
        ollama_admin,
        "tag_to_group_mapping",
        return_value={
            "qwen3:30b-a3b": "local-main",
            "deepseek-r1:8b": "local-reasoner",
        },
    ):
        assert ollama_admin.resolve_group_for_tag("qwen3:30b-a3b") == "local-main"
        assert ollama_admin.resolve_group_for_tag("deepseek-r1:8b") == "local-reasoner"


def test_resolve_group_for_unknown_tag_falls_back_to_local_main():
    with patch.object(ollama_admin, "tag_to_group_mapping", return_value={}):
        assert ollama_admin.resolve_group_for_tag("some-random:tag") == "local-main"


def test_load_model_blocked_in_strict_day_mode():
    with patch.object(
        ollama_admin,
        "tag_to_group_mapping",
        return_value={"qwen3:30b-a3b": "local-main"},
    ):
        with pytest.raises(SafetyError, match="DAY_MODE"):
            ollama_admin.load_model(
                "qwen3:30b-a3b", mode="DAY_MODE", manual_override=False
            )


def test_load_model_allowed_with_manual_override_calls_generate():
    poster = _fake_post(SAMPLE_GENERATE_RESPONSE)
    with patch.object(
        ollama_admin,
        "tag_to_group_mapping",
        return_value={"qwen3:30b-a3b": "local-main"},
    ), patch.object(ollama_admin, "_post", side_effect=poster):
        ollama_admin.load_model(
            "qwen3:30b-a3b",
            mode="DAY_MODE",
            manual_override=True,
            keep_alive="30m",
        )
    path, body, _ = poster.last_call
    assert path == "/api/generate"
    assert body["model"] == "qwen3:30b-a3b"
    assert body["prompt"] == ""
    assert body["keep_alive"] == "30m"


def test_unload_model_sends_keep_alive_zero_seconds_string():
    poster = _fake_post(SAMPLE_GENERATE_RESPONSE)
    with patch.object(ollama_admin, "_post", side_effect=poster):
        ollama_admin.unload_model("qwen3:30b-a3b")
    _, body, _ = poster.last_call
    # Must be the string "0s" not the integer 0: some Ollama versions
    # treat int 0 as "use default keep_alive" and silently re-pin the
    # model instead of unloading. "0s" is a Go duration that always
    # parses as zero.
    assert body["keep_alive"] == "0s"
    assert body["prompt"] == ""


def test_quick_prompt_blocked_in_strict_day_mode():
    with patch.object(
        ollama_admin,
        "tag_to_group_mapping",
        return_value={"qwen3:30b-a3b": "local-main"},
    ):
        with pytest.raises(SafetyError, match="DAY_MODE"):
            ollama_admin.quick_prompt(
                "qwen3:30b-a3b", "hello", mode="DAY_MODE", manual_override=False
            )


def test_quick_prompt_empty_input_rejected():
    with pytest.raises(ValueError, match="empty"):
        ollama_admin.quick_prompt(
            "qwen3:30b-a3b", "   ", mode="NIGHT_MODE", manual_override=False
        )


def test_quick_prompt_returns_trimmed_response():
    poster = _fake_post({"response": "  hi there  \n", "done": True})
    with patch.object(
        ollama_admin,
        "tag_to_group_mapping",
        return_value={"qwen3:30b-a3b": "local-main"},
    ), patch.object(ollama_admin, "_post", side_effect=poster):
        result = ollama_admin.quick_prompt(
            "qwen3:30b-a3b",
            "hello",
            mode="NIGHT_MODE",
            manual_override=False,
        )
    assert result == "hi there"


def test_local_groups_only_returns_sorted_local_groups():
    groups = ollama_admin.local_groups_only()
    assert "local-main" in groups
    assert "cloud-claude-opus" not in groups
    assert groups == sorted(groups)


def test_ollama_available_false_when_get_raises():
    with patch.object(
        ollama_admin,
        "_get",
        side_effect=ollama_admin.OllamaUnavailable("boom"),
    ):
        assert ollama_admin.ollama_available() is False
