from __future__ import annotations

import json
import os
from typing import Any
from uuid import uuid4

from api.task_router import TaskRouter


def row_to_dict(row: Any) -> dict | None:
    return dict(row) if row else None


class PostgresStore:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.environ.get("DATABASE_URL", "")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required for PostgresStore")
        self.router = TaskRouter()
        self._init_db()
        self.seed_jobs()

    def connect(self):
        try:
            import psycopg  # type: ignore
            from psycopg.rows import dict_row  # type: ignore
        except Exception as exc:
            raise RuntimeError("psycopg is required for PostgresStore") from exc
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def _init_db(self) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS nodes (
                        node_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        cpu_threads INTEGER NOT NULL,
                        memory_gb DOUBLE PRECISION NOT NULL,
                        has_gpu BOOLEAN NOT NULL,
                        gpu_name TEXT,
                        contribution_percent INTEGER NOT NULL,
                        score INTEGER NOT NULL,
                        trust INTEGER NOT NULL DEFAULT 30,
                        status TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        job_type TEXT NOT NULL,
                        payload_json JSONB NOT NULL,
                        status TEXT NOT NULL DEFAULT 'queued',
                        assigned_to TEXT,
                        attempts INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        assigned_at TIMESTAMPTZ,
                        finished_at TIMESTAMPTZ
                    );
                    CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at);
                    CREATE TABLE IF NOT EXISTS results (
                        result_id TEXT PRIMARY KEY,
                        node_id TEXT NOT NULL,
                        job_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        output_summary TEXT NOT NULL,
                        submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS verifications (
                        verification_id TEXT PRIMARY KEY,
                        result_id TEXT NOT NULL,
                        job_id TEXT NOT NULL,
                        node_id TEXT NOT NULL,
                        score DOUBLE PRECISION NOT NULL,
                        passed BOOLEAN NOT NULL,
                        reason TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS model_versions (
                        model_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        base_model TEXT NOT NULL,
                        source_job_id TEXT NOT NULL,
                        notes TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )

    def seed_jobs(self) -> None:
        seeds = [
            ("job-rag-001", "rag_index", {"tokens": 1200, "priority": 50, "min_memory_gb": 4}),
            ("job-eval-001", "evaluation", {"samples": 12, "priority": 40, "min_cpu_threads": 2}),
            ("job-lora-001", "lora_micro", {"steps": 20, "priority": 90, "requires_gpu": True, "min_memory_gb": 8}),
            ("job-verify-001", "verification", {"samples": 6, "priority": 30}),
        ]
        with self.connect() as conn:
            with conn.cursor() as cur:
                for job_id, job_type, payload in seeds:
                    cur.execute("INSERT INTO jobs (job_id, job_type, payload_json) VALUES (%s, %s, %s) ON CONFLICT (job_id) DO NOTHING", (job_id, job_type, json.dumps(payload)))

    def enqueue_job(self, job_id: str, job_type: str, payload: dict) -> dict:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO jobs (job_id, job_type, payload_json) VALUES (%s, %s, %s)", (job_id, job_type, json.dumps(payload)))
        return self._api_job(self.get_job(job_id) or {})

    def list_jobs(self, status: str | None = None, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if status:
                    cur.execute("SELECT * FROM jobs WHERE status = %s ORDER BY created_at DESC LIMIT %s", (status, limit))
                else:
                    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s", (limit,))
                rows = cur.fetchall()
        return [self._api_job(dict(row)) for row in rows]

    def register_node(self, body: dict[str, Any]) -> dict:
        node_id = body.get("node_id") or "node_" + uuid4().hex[:12]
        score = body["cpu_threads"] * 8 + int(body["memory_gb"] * 10) + (60 if body.get("has_gpu") else 10)
        existing = self.get_node(node_id)
        trust = existing.get("trust", 30) if existing else 30
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO nodes (node_id, device_name, cpu_threads, memory_gb, has_gpu, gpu_name, contribution_percent, score, trust, status, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'online', NOW())
                    ON CONFLICT (node_id) DO UPDATE SET
                        device_name = EXCLUDED.device_name,
                        cpu_threads = EXCLUDED.cpu_threads,
                        memory_gb = EXCLUDED.memory_gb,
                        has_gpu = EXCLUDED.has_gpu,
                        gpu_name = EXCLUDED.gpu_name,
                        contribution_percent = EXCLUDED.contribution_percent,
                        score = EXCLUDED.score,
                        trust = EXCLUDED.trust,
                        status = 'online',
                        last_seen = NOW()
                    """,
                    (node_id, body["device_name"], body["cpu_threads"], body["memory_gb"], bool(body.get("has_gpu")), body.get("gpu_name"), body.get("contribution_percent", 30), score, trust),
                )
        return self.get_node(node_id) or {}

    def get_node(self, node_id: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM nodes WHERE node_id = %s", (node_id,))
                row = cur.fetchone()
        return row_to_dict(row)

    def list_nodes(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM nodes ORDER BY last_seen DESC LIMIT %s", (limit,))
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def update_heartbeat(self, node_id: str, status: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE nodes SET status = %s, last_seen = NOW() WHERE node_id = %s", (status, node_id))
        return self.get_node(node_id)

    def queued_route_preview(self, node_id: str, limit: int = 20) -> dict:
        node = self.get_node(node_id)
        if not node:
            return {"ok": False, "error": "node not found", "routes": []}
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT %s", (limit,))
                rows = cur.fetchall()
        explanations = [self.router.explain(node, dict(row)) for row in rows]
        explanations.sort(key=lambda item: (item["matched"], item["priority"]), reverse=True)
        return {"ok": True, "node_id": node_id, "routes": explanations}

    def claim_job(self, job_id: str, node_id: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'assigned', assigned_to = %s, assigned_at = NOW(), attempts = attempts + 1 WHERE job_id = %s AND status = 'queued' RETURNING *", (node_id, job_id))
                row = cur.fetchone()
        return self._api_job(dict(row)) if row else None

    def next_job(self, node_id: str) -> dict | None:
        node = self.get_node(node_id)
        if not node:
            return None
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM jobs WHERE status = 'queued' ORDER BY attempts ASC, created_at ASC LIMIT 50")
                candidates = [dict(row) for row in cur.fetchall()]
        matches = [job for job in candidates if self.router.can_assign(node, job)[0]]
        if not matches:
            return None
        matches.sort(key=lambda job: (self.router.job_priority(job), -int(job.get("attempts", 0))), reverse=True)
        return self.claim_job(matches[0]["job_id"], node_id)

    def get_job(self, job_id: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
                row = cur.fetchone()
        return row_to_dict(row)

    def submit_result(self, body: dict[str, Any]) -> dict:
        result_id = "result_" + uuid4().hex[:12]
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO results (result_id, node_id, job_id, status, output_summary) VALUES (%s, %s, %s, %s, %s)", (result_id, body["node_id"], body["job_id"], body["status"], body["output_summary"]))
                cur.execute("UPDATE jobs SET status = %s, finished_at = NOW() WHERE job_id = %s", ("done" if body["status"] == "ok" else "failed", body["job_id"]))
                cur.execute("UPDATE nodes SET trust = GREATEST(0, LEAST(100, trust + %s)) WHERE node_id = %s", (1 if body["status"] == "ok" else -2, body["node_id"]))
        return self.get_result(result_id) or {}

    def get_result(self, result_id: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM results WHERE result_id = %s", (result_id,))
                row = cur.fetchone()
        return row_to_dict(row)

    def record_verification(self, result: dict, score: float, passed: bool, reason: str) -> dict:
        verification_id = "verify_" + uuid4().hex[:12]
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO verifications (verification_id, result_id, job_id, node_id, score, passed, reason) VALUES (%s, %s, %s, %s, %s, %s, %s)", (verification_id, result["result_id"], result["job_id"], result["node_id"], score, passed, reason))
                cur.execute("UPDATE nodes SET trust = GREATEST(0, LEAST(100, trust + %s)) WHERE node_id = %s", (1 if passed else -3, result["node_id"]))
        return self.get_verification(verification_id) or {}

    def get_verification(self, verification_id: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM verifications WHERE verification_id = %s", (verification_id,))
                row = cur.fetchone()
        return row_to_dict(row)

    def register_model_version(self, record: dict) -> dict:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO model_versions (model_id, name, base_model, source_job_id, notes) VALUES (%s, %s, %s, %s, %s)", (record["model_id"], record["name"], record["base_model"], record["source_job_id"], record.get("notes", "")))
        return self.get_model_version(record["model_id"]) or {}

    def get_model_version(self, model_id: str) -> dict | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM model_versions WHERE model_id = %s", (model_id,))
                row = cur.fetchone()
        return row_to_dict(row)

    def list_model_versions(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM model_versions ORDER BY created_at DESC LIMIT %s", (limit,))
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def retry_failed_jobs(self, max_attempts: int = 3) -> dict:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'queued', assigned_to = NULL, assigned_at = NULL, finished_at = NULL WHERE status = 'failed' AND attempts < %s", (max_attempts,))
                rowcount = cur.rowcount
        return {"requeued_failed_jobs": rowcount, "max_attempts": max_attempts}

    def requeue_stale_assigned(self, older_than_minutes: int = 30) -> dict:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'queued', assigned_to = NULL, assigned_at = NULL WHERE status = 'assigned' AND assigned_at IS NOT NULL AND assigned_at < NOW() - (%s * INTERVAL '1 minute')", (older_than_minutes,))
                rowcount = cur.rowcount
        return {"requeued_stale_jobs": rowcount, "older_than_minutes": older_than_minutes}

    def status(self) -> dict:
        with self.connect() as conn:
            with conn.cursor() as cur:
                counts = {}
                for name, query in {
                    "nodes": "SELECT COUNT(*) FROM nodes",
                    "queued_jobs": "SELECT COUNT(*) FROM jobs WHERE status = 'queued'",
                    "assigned_jobs": "SELECT COUNT(*) FROM jobs WHERE status = 'assigned'",
                    "done_jobs": "SELECT COUNT(*) FROM jobs WHERE status = 'done'",
                    "failed_jobs": "SELECT COUNT(*) FROM jobs WHERE status = 'failed'",
                    "submitted_results": "SELECT COUNT(*) FROM results",
                    "verifications": "SELECT COUNT(*) FROM verifications",
                    "passed_verifications": "SELECT COUNT(*) FROM verifications WHERE passed = true",
                    "model_versions": "SELECT COUNT(*) FROM model_versions",
                }.items():
                    cur.execute(query)
                    counts[name] = cur.fetchone()["count"]
        return {**counts, "store": "postgres", "database_url": "postgres://***"}

    @staticmethod
    def _api_job(job: dict) -> dict:
        payload = job.get("payload_json") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        return {"id": job["job_id"], "type": job["job_type"], "payload": payload, "status": job.get("status"), "assigned_to": job.get("assigned_to"), "assigned_at": str(job.get("assigned_at")) if job.get("assigned_at") else None, "attempts": job.get("attempts", 0)}
