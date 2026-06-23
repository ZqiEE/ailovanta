from __future__ import annotations

from dataclasses import asdict, dataclass

from api.content_addressing import hash_object


@dataclass(frozen=True)
class RuntimeCheckReport:
    node_id: str
    runtime_hash: str
    environment_type: str
    quote_hash: str
    passed: bool
    reason: str


class RuntimeCheckPolicy:
    def __init__(self, allowed_runtime_hashes: set[str] | None = None, allowed_environment_types: set[str] | None = None) -> None:
        self.allowed_runtime_hashes = allowed_runtime_hashes or set()
        self.allowed_environment_types = allowed_environment_types or {"tdx", "sev-snp", "confidential-gpu", "simulated-safe-box"}

    def verify(self, node_id: str, runtime_hash: str, environment_type: str, quote: dict) -> dict:
        quote_hash = hash_object(quote)
        if environment_type not in self.allowed_environment_types:
            return asdict(RuntimeCheckReport(node_id, runtime_hash, environment_type, quote_hash, False, "environment type not allowed"))
        if self.allowed_runtime_hashes and runtime_hash not in self.allowed_runtime_hashes:
            return asdict(RuntimeCheckReport(node_id, runtime_hash, environment_type, quote_hash, False, "runtime hash not allowed"))
        if quote.get("node_id") != node_id:
            return asdict(RuntimeCheckReport(node_id, runtime_hash, environment_type, quote_hash, False, "quote node mismatch"))
        return asdict(RuntimeCheckReport(node_id, runtime_hash, environment_type, quote_hash, True, "runtime check accepted"))
