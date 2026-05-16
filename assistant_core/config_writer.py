"""Safe, validated edits to ``config/assistant.yaml``.

This is the only sanctioned way for the panel (or any code) to mutate the
assistant config file. It is intentionally narrow: only a small allow-list
of fields can be changed, every change is validated, and the write is
atomic (temp-file + rename) so a crash mid-write cannot corrupt the file.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml

from assistant_core.config import PROJECT_ROOT


ASSISTANT_CONFIG_PATH = PROJECT_ROOT / "config" / "assistant.yaml"

EDITABLE_FIELDS = frozenset(
    {
        "day_mode_start",
        "night_mode_start",
        "night_mode_end",
    }
)

_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class ConfigEditError(ValueError):
    """Raised when an attempted config edit is rejected by validation."""


def update_assistant_config(updates: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    """Apply ``updates`` to the assistant config and return the new dict.

    Raises ``ConfigEditError`` if any key is not in ``EDITABLE_FIELDS`` or
    any value fails validation.
    """
    target = path or ASSISTANT_CONFIG_PATH
    rejected = sorted(set(updates) - EDITABLE_FIELDS)
    if rejected:
        raise ConfigEditError(
            f"Refusing to edit fields outside the allow-list: {rejected}. "
            f"Editable fields: {sorted(EDITABLE_FIELDS)}"
        )

    cleaned: dict[str, Any] = {}
    for key, value in updates.items():
        cleaned[key] = _validate_field(key, value)

    current = _read_yaml(target)
    merged = {**current, **cleaned}
    _atomic_write_yaml(target, merged)
    return merged


def _validate_field(key: str, value: Any) -> str:
    if key in {"day_mode_start", "night_mode_start", "night_mode_end"}:
        if not isinstance(value, str) or not _TIME_PATTERN.match(value):
            raise ConfigEditError(
                f"{key} must be a 'HH:MM' 24-hour string, got: {value!r}"
            )
        return value
    raise ConfigEditError(f"No validator for editable field: {key}")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigEditError(f"Config file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ConfigEditError(f"Config file is not a YAML mapping: {path}")
    return loaded


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        yaml.safe_dump(data, tmp, sort_keys=False, default_flow_style=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


__all__ = [
    "ASSISTANT_CONFIG_PATH",
    "EDITABLE_FIELDS",
    "ConfigEditError",
    "update_assistant_config",
]
