from __future__ import annotations

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
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return "file://" + str(files[0].resolve()) if files else None
