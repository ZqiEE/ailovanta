from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class OllamaConfig:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    context_length: int = int(os.getenv("OLLAMA_CONTEXT_LENGTH", "32768"))


class OllamaUnavailable(RuntimeError):
    pass


class OllamaAdapter:
    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()

    def chat(self, prompt: str, mode: str = "open", memory: list[str] | None = None) -> str:
        return self.chat_messages([{"role": "user", "content": prompt}], mode=mode, memory=memory)

    def chat_messages(self, messages: list[dict], mode: str = "open", memory: list[str] | None = None) -> str:
        clean_messages = self._clean_messages(messages)
        if not any(message["role"] == "user" for message in clean_messages):
            raise OllamaUnavailable("at least one user message is required")
        payload = {
            "model": self.config.model,
            "stream": False,
            "messages": [{"role": "system", "content": self._system_prompt(mode, memory or [])}, *clean_messages],
            "options": {"num_ctx": self.config.context_length, "temperature": 0.2},
        }
        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                response = client.post(f"{self.config.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise OllamaUnavailable(str(exc)) from exc
        content = str((data.get("message") or {}).get("content") or "").strip()
        if not content:
            raise OllamaUnavailable("empty Ollama response")
        return content

    @staticmethod
    def _clean_messages(messages: list[dict]) -> list[dict]:
        clean = []
        for message in messages:
            role = str(message.get("role", "")).strip()
            content = str(message.get("content", "")).strip()
            if role in {"user", "assistant", "system"} and content:
                clean.append({"role": role, "content": content})
        return clean

    @staticmethod
    def _system_prompt(mode: str, memory: list[str]) -> str:
        memory_text = "\n".join(f"- {item}" for item in memory[-8:]) or "No stored memory."
        if mode == "coding":
            return (
                "You are Ailovanta, one unified coding model. Your job is to build, modify and repair real software. "
                "Be precise, inspect project context before changing code, preserve unrelated behavior, and prefer robust minimal changes. "
                "You combine frontend product quality, repository-level backend engineering, and debugging discipline in one model. "
                "Never claim a test or command ran unless execution output was actually provided."
            )
        return (
            "You are Ailovanta, a practical coding assistant. Answer directly, focus on software creation and debugging, "
            "and use conversation history when it helps.\n"
            f"Current mode: {mode}.\nLocal user memory:\n{memory_text}"
        )
