from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}


class UnsupportedFileType(ValueError):
    """Raised when v1 does not support reading a file type."""


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def profile_csv(path: Path) -> dict[str, Any]:
    frame = pd.read_csv(path)
    preview = frame.head(20).where(pd.notnull(frame), None).to_dict(orient="records")
    return {
        "row_count": int(len(frame)),
        "columns": list(frame.columns),
        "preview_rows": preview,
        "missing_values": {column: int(count) for column, count in frame.isna().sum().to_dict().items()},
    }


def load_supported_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path).expanduser()
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileType(f"Unsupported file type for v1: {suffix}")
    if suffix == ".csv":
        return {"path": str(file_path), "kind": "csv", "profile": profile_csv(file_path)}
    if suffix == ".json":
        content = _read_text(file_path)
        return {"path": str(file_path), "kind": "json", "content": content, "parsed": json.loads(content)}
    return {"path": str(file_path), "kind": suffix.lstrip("."), "content": _read_text(file_path)}


def chunk_text(content: str, max_chars: int) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    return [content[index : index + max_chars] for index in range(0, len(content), max_chars)] or [""]
