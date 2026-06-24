from __future__ import annotations

ALLOWED_ROLES = {"system", "user", "assistant"}


def build_chat_context(messages: list[dict], latest_prompt: str, max_messages: int = 12) -> list[dict]:
    """Build a compact chat context for model adapters.

    The conversation store already persists the latest user message before
    the model is called. This helper keeps recent user/assistant messages,
    avoids duplicating the latest prompt, and returns the role/content shape
    expected by chat-style model runtimes.
    """
    normalized: list[dict] = []
    for message in messages:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role not in ALLOWED_ROLES or not content:
            continue
        normalized.append({"role": role, "content": content})

    prompt = latest_prompt.strip()
    if prompt:
        has_latest = bool(normalized and normalized[-1]["role"] == "user" and normalized[-1]["content"] == prompt)
        if not has_latest:
            normalized.append({"role": "user", "content": prompt})

    if max_messages <= 0:
        return []
    return normalized[-max_messages:]


def context_to_text(messages: list[dict]) -> str:
    """Render chat context into a readable text block for tests and fallbacks."""
    lines = []
    for message in messages:
        role = str(message.get("role", "unknown")).upper()
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)
