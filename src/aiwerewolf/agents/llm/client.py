"""OpenAI-compatible chat client for structured JSON responses."""

from __future__ import annotations

import json
from typing import Any

_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
}


def resolve_base_url(provider: str, base_url: str) -> str:
    if base_url:
        return base_url.rstrip("/")
    return _DEFAULT_BASE_URLS.get(provider, _DEFAULT_BASE_URLS["openai"])


def chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    timeout_sec: int = 60,
) -> str:
    """POST /v1/chat/completions with json_object mode. Returns message content."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "openai package required — pip install -e '.[agents]'"
        ) from exc

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout_sec,
    )
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("empty LLM response")
    return content


def parse_json_response(raw: str) -> dict[str, Any]:
    return json.loads(raw)
