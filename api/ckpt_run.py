from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.ckpt_merge import to_path


class TinyByteRuntime:
    def __init__(self, ref: str) -> None:
        try:
            import torch  # type: ignore
            from torch import nn  # type: ignore
        except Exception as exc:
            raise RuntimeError("torch is required") from exc
        path = to_path(ref)
        if path is None or not path.exists():
            raise RuntimeError("checkpoint not found: " + ref)
        obj = torch.load(path, map_location="cpu")
        state = obj.get("state_dict")
        if not state:
            raise RuntimeError("checkpoint has no state_dict")
        hidden = int(obj.get("hidden_size") or 64)
        self.torch = torch
        self.model = nn.Sequential(nn.Embedding(256, hidden), nn.Linear(hidden, 256))
        self.model.load_state_dict(state)
        self.model.eval()
        self.meta = {k: v for k, v in obj.items() if k != "state_dict"}

    def run(self, prompt: str, max_new: int = 80) -> str:
        torch = self.torch
        data = list(prompt.encode("utf-8", errors="ignore") or b"A")
        with torch.no_grad():
            for _ in range(max(1, min(max_new, 256))):
                x = torch.tensor([data[-1]], dtype=torch.long)
                logits = self.model(x)[-1]
                nxt = int(torch.argmax(logits).item())
                data.append(nxt)
        raw = bytes([item % 256 for item in data])
        text = raw.decode("utf-8", errors="ignore")
        extra = text[len(prompt) :].strip()
        return extra or text.strip() or "Ailovanta checkpoint loaded."


def run_ckpt(prompt: str, ref: str, max_new: int = 80) -> dict[str, Any]:
    rt = TinyByteRuntime(ref)
    return {"answer": rt.run(prompt, max_new), "source": "ailovanta-merged-checkpoint", "checkpoint_ref": ref, "model": rt.meta}


def newest_ref(root: str | Path = "runtime_data/merged_models") -> str | None:
    folder = Path(root)
    if folder.exists():
        files = sorted(folder.glob("*.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            return "file://" + str(files[0].resolve())
    return restored_promoted_ref()


def restored_promoted_ref() -> str | None:
    reg_path = Path("runtime_data/model_registry.json")
    if not reg_path.exists():
        return None
    try:
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    models = [item for item in reg.get("models", []) if item.get("status") == "promoted" and item.get("manifest_ref")]
    if not models:
        return None
    models.sort(key=lambda item: float(item.get("eval_score") or 0), reverse=True)
    manifest_ref = str(models[0]["manifest_ref"])
    manifest_path = to_path(manifest_ref)
    if manifest_path is None or not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = Path("runtime_data/runtime_cache") / str(manifest.get("artifact_name") or "promoted.pt")
    if output.exists():
        return "file://" + str(output.resolve())
    try:
        from api.pool_store import get

        get(manifest, output)
    except Exception:
        return None
    return "file://" + str(output.resolve()) if output.exists() else None
