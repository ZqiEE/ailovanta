from __future__ import annotations

from api.corpus_pipeline import CorpusPipeline


def test_pipeline_cleans_hashes_scores_and_tags() -> None:
    pipeline = CorpusPipeline()
    doc = pipeline.process("local://doc", "Model Notes", "Model notes with local compute and corpus workflow. This is useful.")
    assert doc["url"] == "local://doc"
    assert doc["content_hash"]
    assert doc["quality_score"] > 0
    assert doc["tags"]


def test_pipeline_hash_is_stable() -> None:
    pipeline = CorpusPipeline()
    first = pipeline.process("local://a", "A", "same text")
    second = pipeline.process("local://b", "B", "same text")
    assert first["content_hash"] == second["content_hash"]
