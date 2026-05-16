from __future__ import annotations

import requests


class OllamaError(RuntimeError):
    """Raised when the local Ollama-compatible runtime fails."""


def generate(
    prompt: str,
    *,
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 180,
) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise OllamaError(f"Ollama generate failed with HTTP {response.status_code}: {response.text[:500]}")
    payload = response.json()
    return str(payload.get("response", ""))


def list_models(base_url: str = "http://localhost:11434", timeout: int = 5) -> list[str]:
    response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
    if response.status_code >= 400:
        raise OllamaError(f"Ollama tags failed with HTTP {response.status_code}: {response.text[:500]}")
    payload = response.json()
    return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
