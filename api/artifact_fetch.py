from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from urllib import request


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_artifact(url: str, output_dir: str, expected_sha256: str | None = None) -> dict:
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http/https artifact urls are supported")
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = url.rstrip("/").split("/")[-1] or "artifact.bin"
    target = target_dir / filename
    with request.urlopen(url, timeout=120) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    digest = sha256_file(target)
    if expected_sha256 and digest != expected_sha256:
        target.unlink(missing_ok=True)
        raise ValueError("artifact sha256 mismatch")
    return {"path": str(target), "sha256": digest, "bytes": target.stat().st_size}
