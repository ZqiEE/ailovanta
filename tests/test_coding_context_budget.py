from __future__ import annotations

import json
from pathlib import Path

from api.coding_agent import CodingAgent
from api.project_store import ProjectStore


class BudgetConfig:
    model = "budget-test"
    context_length = 8192


class BudgetModel:
    config = BudgetConfig()

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def chat_messages(self, messages, mode="open", memory=None):
        assert mode == "coding"
        prompt = messages[0]["content"]
        self.prompts.append(prompt)
        if "FIRST PROPOSAL:" in prompt:
            return json.dumps(
                {
                    "summary": "reviewed",
                    "explanation": "checked",
                    "changes": [{"path": "app.py", "content": "print('reviewed')\n"}],
                }
            )
        return json.dumps(
            {
                "summary": "first",
                "explanation": "draft",
                "changes": [{"path": "app.py", "content": "print('first')\n"}],
            }
        )


def test_repo_context_budget_scales_to_actual_model_window(tmp_path: Path):
    store = ProjectStore(tmp_path / "projects")
    project_id = store.create("local", "Budget")["project_id"]
    store.put_file(project_id, "app.py", "# relevant task\n" + ("x = 1\n" * 5000))
    model = BudgetModel()
    agent = CodingAgent(store=store, model=model)

    proposal = agent.propose(project_id, "change relevant task", "backend")
    expected_budget = int(BudgetConfig.context_length * 1.6)
    assert proposal["context_char_budget"] == expected_budget
    assert proposal["context_chars_used"] <= expected_budget
    assert proposal["self_reviewed"] is True
    assert proposal["inference_passes"] == 2
    assert len(model.prompts) == 2
    # Prompt overhead exists, but repository context itself must stay bounded so
    # Ollama does not silently discard the most useful files.
    assert len(model.prompts[0]) < expected_budget + 3000


class TinyReviewConfig:
    model = "tiny-review-test"
    context_length = 2048


class HugeProposalModel:
    config = TinyReviewConfig()

    def __init__(self) -> None:
        self.calls = 0

    def chat_messages(self, messages, mode="open", memory=None):
        self.calls += 1
        return json.dumps(
            {
                "summary": "large first pass",
                "explanation": "large but valid",
                "changes": [{"path": "large.txt", "content": "z" * 15000}],
            }
        )


def test_self_review_is_skipped_instead_of_truncating_large_proposal_json(tmp_path: Path):
    store = ProjectStore(tmp_path / "projects")
    project_id = store.create("local", "Large")["project_id"]
    store.put_file(project_id, "input.txt", "hello\n")
    model = HugeProposalModel()
    proposal = CodingAgent(store=store, model=model).propose(project_id, "rewrite", "auto")
    assert model.calls == 1
    assert proposal["self_reviewed"] is False
    assert "too large" in str(proposal["review_skipped_reason"])
