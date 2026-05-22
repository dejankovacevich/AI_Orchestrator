from __future__ import annotations

import requests

from assistant_core.llm.model_policy import assert_model_group_allowed

CLOUD_MODEL_GROUP = "cloud-claude-opus"


class LiteLLMClientError(RuntimeError):
    """Raised when LiteLLM proxy calls fail."""


def chat_completion(
    messages: list[dict[str, str]],
    *,
    model_group: str,
    base_url: str = "http://localhost:4000",
    mode: str = "DAY_MODE",
    manual_override: bool = False,
    timeout: int = 180,
) -> str:
    # Cloud calls are authorized by assert_cloud_allowed before this function.
    # Local groups still use the model-group safety gate here.
    if model_group != CLOUD_MODEL_GROUP:
        assert_model_group_allowed(model_group, mode, manual_override=manual_override)
    response = requests.post(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        json={"model": model_group, "messages": messages},
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise LiteLLMClientError(f"LiteLLM failed with HTTP {response.status_code}: {response.text[:500]}")
    payload = response.json()
    try:
        return str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LiteLLMClientError("LiteLLM returned an unexpected response shape.") from exc
