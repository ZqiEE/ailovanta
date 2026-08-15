from __future__ import annotations

import json
import os
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

        context_char_budget = self._context_char_budget()
        selected = select_project_context(
            self.store,
            project_id,
            clean_task,
            max_chars=context_char_budget,
        )
        context_chars_used = len(selected["context"])
        prompt = self._prompt(clean_task, mode, selected["context"])
        try:
            answer = self.model.chat_messages([{"role": "user", "content": prompt}], mode="coding", memory=[])
        except OllamaUnavailable as exc:
            raise CodingAgentError("coding model unavailable: " + str(exc)) from exc
        payload = self._parse(answer)
        changes = self._validate(payload.get("changes"))
        reviewed = False
        review_skipped_reason: str | None = None

        if self._self_review_enabled() and changes:
            first_payload = {
                "summary": str(payload.get("summary") or "Code changes proposed"),
                "explanation": str(payload.get("explanation") or ""),
                "changes": changes,
            }
            review_prompt = self._review_prompt(
                task=clean_task,
                mode=mode,
                context=selected["context"],
                first_payload=first_payload,
            )
            review_prompt_budget = self._review_prompt_char_budget()
            if len(review_prompt) > review_prompt_budget:
                review_skipped_reason = (
                    "self-review prompt too large for the model context; skipped instead of truncating proposal JSON"
                )
            else:
                try:
                    reviewed_answer = self.model.chat_messages(
                        [{"role": "user", "content": review_prompt}], mode="coding", memory=[]
                    )
                    reviewed_payload = self._parse(reviewed_answer)
                    reviewed_changes = self._validate(reviewed_payload.get("changes"))
                    if reviewed_changes:
                        payload = reviewed_payload
                        changes = reviewed_changes
                        reviewed = True
                    else:
                        review_skipped_reason = "self-review returned no usable changes"
                except (OllamaUnavailable, CodingAgentError):
                    # A failed critique must never destroy a usable first pass.
                    review_skipped_reason = "self-review failed; preserved the usable first pass"
        elif not self._self_review_enabled():
            review_skipped_reason = "self-review disabled"
        elif not changes:
            review_skipped_reason = "no changes to review"

        return {
            "summary": str(payload.get("summary") or "Code changes proposed"),
            "explanation": str(payload.get("explanation") or ""),
            "changes": changes,
            "model": self.model.config.model,
            "context_files": selected["selected_files"],
            "project_file_count": selected["total_files"],
            "context_char_budget": context_char_budget,
            "context_chars_used": context_chars_used,
            "self_reviewed": reviewed,
            "review_skipped_reason": review_skipped_reason,
            "inference_passes": 2 if reviewed else 1,
        }

    def _context_length(self) -> int:
        try:
            return max(1024, int(getattr(self.model.config, "context_length", 32768)))
        except (TypeError, ValueError):
            return 32768

    def _context_char_budget(self) -> int:
        # Use a deliberately conservative repository budget. Roughly 1.6 source
        # characters per model token reserves substantial room for instructions,
        # task text, generated output, and tokenizer variance instead of relying
        # on Ollama to silently truncate the least convenient part of the prompt.
        return int(self._context_length() * 1.6)

    def _review_prompt_char_budget(self) -> int:
        # The review includes both repository context and the complete first-pass
        # JSON. Cap it below a rough 4 chars/token upper estimate so the model has
        # output headroom. If the full JSON cannot fit, skip review rather than
        # truncate a file-level changeset into invalid or misleading JSON.
        return int(self._context_length() * 3.2)

    @staticmethod
    def _self_review_enabled() -> bool:
        return os.getenv("AILOVANTA_SELF_REVIEW", "true").strip().lower() not in {"0", "false", "no", "off"}

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
    def _review_prompt(task: str, mode: str, context: str, first_payload: dict[str, Any]) -> str:
        return (
            "You are the final engineering reviewer for Ailovanta. Review the proposed changes before the user sees them.\n"
            + MODE_GUIDANCE[mode]
            + "\nCheck requirement coverage, API consistency, imports, obvious syntax mistakes, cross-file dependencies, "
            "regressions, security-sensitive mistakes, and whether unrelated behavior was changed. "
            "Fix the proposal when needed. If it is already correct, return it unchanged. "
            "Do not invent test results. Return JSON only with keys summary, explanation, changes; each changed file must contain complete contents.\n\n"
            + "TASK:\n" + task
            + "\n\nPROJECT CONTEXT:\n" + context
            + "\n\nFIRST PROPOSAL:\n" + json.dumps(first_payload, ensure_ascii=False)
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
