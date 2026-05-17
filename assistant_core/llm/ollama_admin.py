"""Direct administration of the local Ollama runtime.

This module is the panel's way to talk to Ollama. It NEVER bypasses
``assert_model_allowed`` for any operation that loads a model into memory or
asks the model to produce output. Listing the model inventory and listing
currently-loaded models are read-only and pass through ungated.

The single source of truth for tag-to-group mapping is
``config/models.yaml``. If a tag is pulled into Ollama but does not appear
in that mapping, it is treated as a local-* tag for the purpose of the
safety gate (fail-closed): the load will be blocked in strict DAY_MODE.
"""

from __future__ import annotations

from typing import Any

import requests

from assistant_core.config import load_assistant_config, load_models
from assistant_core.llm.model_policy import assert_model_group_allowed
from assistant_core.safety import LOCAL_MODEL_GROUPS, SafetyError


class OllamaUnavailable(RuntimeError):
    """Raised when the local Ollama runtime is not reachable."""


_DEFAULT_TIMEOUT = 5
_LOAD_TIMEOUT = 600
_PROMPT_TIMEOUT = 300


def _base_url() -> str:
    return load_assistant_config().ollama_base_url.rstrip("/")


def _get(path: str, *, timeout: int = _DEFAULT_TIMEOUT) -> dict[str, Any]:
    try:
        response = requests.get(f"{_base_url()}{path}", timeout=timeout)
    except requests.RequestException as exc:
        raise OllamaUnavailable(str(exc)) from exc
    if response.status_code >= 400:
        raise OllamaUnavailable(f"HTTP {response.status_code}: {response.text[:200]}")
    return response.json()


def _post(path: str, payload: dict[str, Any], *, timeout: int) -> dict[str, Any]:
    try:
        response = requests.post(f"{_base_url()}{path}", json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise OllamaUnavailable(str(exc)) from exc
    if response.status_code >= 400:
        raise OllamaUnavailable(f"HTTP {response.status_code}: {response.text[:300]}")
    return response.json()


def ollama_available() -> bool:
    """Return True when Ollama responds to a quick tags query."""
    try:
        _get("/api/tags", timeout=2)
        return True
    except OllamaUnavailable:
        return False


def list_pulled_models() -> list[dict[str, Any]]:
    """Return models on disk in Ollama's local store.

    Each entry: ``{name, size, size_human, modified_at, digest}``.
    """
    payload = _get("/api/tags")
    entries: list[dict[str, Any]] = []
    for raw in payload.get("models", []):
        size_bytes = int(raw.get("size", 0))
        entries.append(
            {
                "name": raw.get("name", ""),
                "size_bytes": size_bytes,
                "size_human": _human_bytes(size_bytes),
                "modified_at": raw.get("modified_at"),
                "digest": (raw.get("digest") or "")[:12],
            }
        )
    entries.sort(key=lambda item: item["name"])
    return entries


def list_loaded_models() -> list[dict[str, Any]]:
    """Return models currently held in memory by Ollama.

    Each entry: ``{name, size, size_human, expires_at}``. Empty list when
    nothing is loaded.
    """
    payload = _get("/api/ps")
    entries: list[dict[str, Any]] = []
    for raw in payload.get("models", []):
        size_bytes = int(raw.get("size_vram", raw.get("size", 0)))
        entries.append(
            {
                "name": raw.get("name", ""),
                "size_bytes": size_bytes,
                "size_human": _human_bytes(size_bytes),
                "expires_at": raw.get("expires_at"),
            }
        )
    return entries


def tag_to_group_mapping() -> dict[str, str]:
    """Return Ollama-tag → model-group from config/models.yaml.

    Reverse of the stored mapping. Used by ``resolve_group_for_tag``.
    """
    mapping: dict[str, str] = {}
    for group, tag in load_models().items():
        if not isinstance(tag, str):
            continue
        mapping[tag] = group
    return mapping


def resolve_group_for_tag(tag: str) -> str:
    """Resolve an Ollama tag to a known model group.

    Falls back to ``local-main`` when the tag is not in ``models.yaml``,
    so that any unmapped local model still goes through the strict
    DAY_MODE gate (fail-closed).
    """
    return tag_to_group_mapping().get(tag, "local-main")


def local_groups_only() -> list[str]:
    """Return the sorted list of local-* groups that the panel may target."""
    return sorted(LOCAL_MODEL_GROUPS)


def load_model(
    tag: str,
    *,
    mode: str,
    manual_override: bool = False,
    keep_alive: str = "30m",
) -> dict[str, Any]:
    """Pull a model into memory.

    Performs the safety gate first (raises ``SafetyError`` if blocked),
    then asks Ollama to load by issuing a no-op generation that pins
    the model with the requested keep-alive. Returns Ollama's response.
    """
    group = resolve_group_for_tag(tag)
    assert_model_group_allowed(group, mode, manual_override=manual_override)
    return _post(
        "/api/generate",
        {"model": tag, "prompt": "", "stream": False, "keep_alive": keep_alive},
        timeout=_LOAD_TIMEOUT,
    )


def unload_model(tag: str) -> dict[str, Any]:
    """Drop a model from memory immediately.

    No safety gate: unloading is always safe.

    Ollama 0.x treats ``keep_alive: 0`` (int) as "use default" (5m) on
    some versions, which silently re-pins the model instead of unloading
    it. The string form ``"0s"`` is parsed as a Go duration of zero
    seconds and unloads immediately, matching the behavior of
    ``ollama stop <tag>``.
    """
    return _post(
        "/api/generate",
        {"model": tag, "prompt": "", "stream": False, "keep_alive": "0s"},
        timeout=_DEFAULT_TIMEOUT,
    )


def quick_prompt(
    tag: str,
    prompt: str,
    *,
    mode: str,
    manual_override: bool = False,
    keep_alive: str = "5m",
) -> str:
    """Single-shot completion for verifying a model. Not a chat.

    Gated through ``assert_model_group_allowed``. Returns the response text.
    """
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    group = resolve_group_for_tag(tag)
    assert_model_group_allowed(group, mode, manual_override=manual_override)
    payload = _post(
        "/api/generate",
        {"model": tag, "prompt": prompt, "stream": False, "keep_alive": keep_alive},
        timeout=_PROMPT_TIMEOUT,
    )
    return str(payload.get("response", "")).strip()


def _human_bytes(n: int) -> str:
    step = 1024.0
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    for unit in units:
        if value < step:
            return f"{value:.1f} {unit}"
        value /= step
    return f"{value:.1f} PB"


__all__ = [
    "OllamaUnavailable",
    "SafetyError",
    "ollama_available",
    "list_pulled_models",
    "list_loaded_models",
    "tag_to_group_mapping",
    "resolve_group_for_tag",
    "local_groups_only",
    "load_model",
    "unload_model",
    "quick_prompt",
]
