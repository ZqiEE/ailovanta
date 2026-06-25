from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


def run_model_shard(job: dict[str, Any], output_dir: str | Path = "runtime_data/model_deltas") -> dict[str, Any]:
    try:
        import torch  # type: ignore
        from torch import nn  # type: ignore
    except Exception as exc:
        raise RuntimeError("torch is required for real model_shard execution") from exc

    payload = job.get("payload", {})
    data_uri = str(payload.get("data_uri") or payload.get("dataset_uri") or "")
    path = local_path(data_uri)
    if path is None or not path.exists() or not path.is_file():
        raise RuntimeError("model_shard data file not found: " + data_uri)

    token_start = int(payload.get("token_start") or 0)
    token_count = int(payload.get("token_count") or 4096)
    raw = path.read_bytes()[token_start : token_start + token_count + 1]
    if len(raw) < 2:
        raise RuntimeError("model_shard data slice is too small")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    values = torch.tensor(list(raw), dtype=torch.long, device=device)
    x = values[:-1]
    y = values[1:]

    hidden = int(payload.get("hidden_size") or 64)
    steps = max(1, min(int(payload.get("steps") or 8), 64))
    model = nn.Sequential(nn.Embedding(256, hidden), nn.Linear(hidden, 256)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(payload.get("learning_rate") or 0.005))
    loss_fn = nn.CrossEntropyLoss()

    losses: list[float] = []
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        opt.step()
        losses.append(float(loss.detach().cpu()))

    plan_id = str(payload.get("plan_id") or "plan")
    job_id = str(job.get("id") or job.get("job_id") or "job")
    target = Path(output_dir) / safe(plan_id)
    target.mkdir(parents=True, exist_ok=True)
    delta_path = target / (safe(job_id) + ".pt")
    torch.save(
        {
            "schema_version": "ailovanta.model_delta.v1",
            "job_id": job_id,
            "plan_id": plan_id,
            "model_id": payload.get("model_id"),
            "version": payload.get("version") or payload.get("target_version"),
            "stage": payload.get("stage"),
            "token_start": token_start,
            "token_count": token_count,
            "device": device,
            "hidden_size": hidden,
            "steps": steps,
            "losses": losses,
            "state_dict": model.state_dict(),
        },
        delta_path,
    )
    digest = sha256_file(delta_path)
    return {
        "schema_version": "ailovanta.model_delta.v1",
        "job_id": job_id,
        "plan_id": plan_id,
        "model_id": payload.get("model_id"),
        "version": payload.get("version") or payload.get("target_version"),
        "stage": payload.get("stage"),
        "device": device,
        "train_loss": losses[-1],
        "initial_loss": losses[0],
        "delta_hash": digest,
        "delta_ref": "file://" + str(delta_path.resolve()),
    }


def local_path(value: str) -> Path | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "file":
        if parsed.path and parsed.path not in {"/", ""}:
            p = unquote(parsed.path)
            if len(p) >= 3 and p[0] == "/" and p[2] == ":":
                p = p[1:]
            return Path(p)
        raw = value.removeprefix("file://")
        return Path(unquote(raw)) if raw else None
    if parsed.scheme == "":
        return Path(value)
    return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:120]


def summary_json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True)
