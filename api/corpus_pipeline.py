from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict


@dataclass
class ProcessedDocument:
    url: str
    title: str
    text: str
    content_hash: str
    quality_score: float
    tags: list[str]


class CorpusPipeline:
    def process(self, url: str, title: str, raw_text: str) -> dict:
        text = self.clean_text(raw_text)
        doc = ProcessedDocument(
            url=url,
            title=self.clean_text(title)[:240],
            text=text,
            content_hash=self.hash_text(text),
            quality_score=self.quality_score(text),
            tags=self.tags(title + " " + text),
        )
        return asdict(doc)

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text or "").strip()
        text = re.sub(r"(cookie|subscribe|advertisement|sign up)", "", text, flags=re.I)
        return text

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def quality_score(text: str) -> float:
        words = text.split()
        if not words:
            return 0.0
        unique_ratio = len(set(words)) / max(len(words), 1)
        length_score = min(len(words) / 500, 1.0)
        punctuation_score = 0.1 if any(mark in text for mark in [".", "。", "?", "？"]) else 0.0
        return round(min(1.0, unique_ratio * 0.45 + length_score * 0.45 + punctuation_score), 3)

    @staticmethod
    def tags(text: str) -> list[str]:
        text_l = text.lower()
        tags: list[str] = []
        rules = {
            "ai": ["ai", "model", "llm", "人工智能", "模型"],
            "compute": ["gpu", "cuda", "compute", "算力"],
            "privacy": ["privacy", "private", "隐私"],
            "training": ["training", "finetune", "lora", "训练", "微调"],
            "web": ["web", "crawler", "corpus", "网页", "语料"],
        }
        for tag, keywords in rules.items():
            if any(keyword in text_l for keyword in keywords):
                tags.append(tag)
        return tags or ["general"]
