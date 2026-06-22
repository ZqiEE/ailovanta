from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VerificationResult:
    score: float
    passed: bool
    reason: str


class VerificationEngine:
    """Lightweight local result verifier for v0.8.

    This is not a security system yet. It gives the scheduler a first scoring
    layer so completed jobs are not blindly trusted.
    """

    def score_result(self, job_id: str, node_id: str, status: str, output_summary: str) -> VerificationResult:
        if status != "ok":
            return VerificationResult(score=0.0, passed=False, reason="job reported failure")
        text = output_summary.strip()
        if not text:
            return VerificationResult(score=0.0, passed=False, reason="empty output")
        score = 0.55
        if job_id:
            score += 0.10
        if node_id:
            score += 0.10
        if len(text) >= 24:
            score += 0.15
        if "simulated" in text.lower() or "result" in text.lower():
            score += 0.10
        score = min(round(score, 3), 1.0)
        return VerificationResult(score=score, passed=score >= 0.7, reason="heuristic verification")
