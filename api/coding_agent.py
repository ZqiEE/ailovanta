from __future__ import annotations

import json
from typing import Any

from api.coding_context import select_project_context
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable
from api.project_store import ProjectStore


class CodingAgentError(ValueError):
    pass


MODE_GUIDANCE = {
    "auto": "Solve the software task with the smallest correct engineering change.",
    "frontend": "Prioritize UI quality, responsiveness, accessibility and interactions.",
    "backend": "Prioritize repository correctness, APIs, data models, tests and maintainability.",
    "repair": "Prioritize root-cause repair, minimal changes and regression avoidance.",
}


class CodingAgent:
    def __init__(self, store: ProjectStore | None = None, model: OllamaAdapter | None = None) -> None:
        self.store = store or ProjectStore()
        self.model = model or OllamaAdapter()

    def propose(self, project_id: str, task: str, mode: str = "auto") -> dict[str, Any]:
        if mode not in MODE_GUIDANCE:
            raise CodingAgentError("invalid coding mode")
        clean_task = task.strip()
        if not clean_task:
            raise CodingAgentError("task is required")
        selected = select_project_context(self.store, project_id, clean_task)
        prompt = self._prompt(clean_task, mode, selected["context"])
        try:
            answer = self.model.chat_messages([{"role": "user", "content": prompt}], mode="coding", memory=[])
        except OllamaUnavailable as exc:
            raise CodingAgentError("coding model unavailable: " + str(exc)) from exc
        payload = self._parse(answer)
        return {
            "summary": str(payload.get("summary") or "Code changes proposed"),
            "explanation": str(payload.get("explanation") or ""),
            "changes": self._validate(payload.get("changes")),
            "model": self.model.config.model,
            "context_files": selected["selected_files"],
            "project_file_count": selected["total_files"],
        }

    @staticmethod
    def _prompt(task: str, mode: str, context: str) -> str:
        return (
            "You are Ailovanta, one unified coding model working on a software project.\n"
            + MODE_GUIDANCE[mode]
            + "\nRead the supplied files before changing anything. Preserve unrelated behavior. "
            "Return complete file contents, not snippets. Do not claim tests ran unless execution output was supplied. "
            "Return JSON only with keys summary, explanation, changes. "
            "Each change is either {path, content} or {path, delete:true}.\n\n"
            + "TASK:\n" + task + "\n\nPROJECT FILES:\n" + context
        )

    @staticmethod
    def _parse(answer: str) -> dict[str, Any]:
        text = answer.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise CodingAgentError("model did not return valid JSON")
            try:
                payload = json.loads(text[start : end + 1])
            except json.JSONDecodeError as exc:
                raise CodingAgentError("model did not return valid JSON") from exc
        if not isinstance(payload, dict):
            raise CodingAgentError("model response must be an object")
        return payload

    def _validate(self, changes: Any) -> list[dict[str, Any]]:
        if not isinstance(changes, list) or len(changes) > 32:
            raise CodingAgentError("invalid changeset")
        result: list[dict[str, Any]] = []
        for item in changes:
            if not isinstance(item, dict):
                raise CodingAgentError("invalid file change")
            path = self.store.safe_path(str(item.get("path") or "")).as_posix()
            if item.get("delete") is True:
                result.append({"path": path, "delete": True})
                continue
            if "content" not in item:
                raise CodingAgentError("file change missing content")
            content = str(item.get("content") or "")
            if len(content.encode("utf-8")) > self.store.max_file_bytes:
                raise CodingAgentError("generated file exceeds size limit")
            result.append({"path": path, "content": content})
        return result
