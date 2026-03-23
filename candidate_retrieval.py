"""Candidate retrieval templates for Wikidata entity linking experiments."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Protocol


@dataclass
class EntityCandidate:
    """A candidate entity for retrieval or disambiguation."""

    uri: str
    label: str
    score: float
    metadata: dict[str, Any]


class EmbeddingProvider(Protocol):
    """Students can implement this with OpenAI, sentence-transformers, Ollama, or local code."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text."""


class SimpleVectorStoreTemplate:
    """A tiny in-memory vector retrieval scaffold.

    This is intentionally simple and dependency-free. Students can replace the
    embedding provider and storage backend while keeping the retrieval flow.
    """

    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider
        self._rows: list[dict[str, Any]] = []

    def index_entities(self, entities: list[dict[str, Any]]) -> None:
        texts = [entity["label"] for entity in entities]
        vectors = self.embedding_provider.embed_texts(texts)
        self._rows = [
            {
                "entity": entity,
                "vector": vector,
            }
            for entity, vector in zip(entities, vectors)
        ]

    def retrieve(self, mention: str, top_k: int = 5) -> list[EntityCandidate]:
        mention_vector = self.embedding_provider.embed_texts([mention])[0]
        scored: list[EntityCandidate] = []

        for row in self._rows:
            entity = row["entity"]
            score = _cosine_similarity(mention_vector, row["vector"])
            scored.append(
                EntityCandidate(
                    uri=entity["uri"],
                    label=entity["label"],
                    score=score,
                    metadata={
                        "current_offices": entity.get("current_offices", []),
                        "wikidata_id": entity.get("metadata", {}).get("wikidata_id"),
                    },
                )
            )

        return sorted(scored, key=lambda candidate: candidate.score, reverse=True)[:top_k]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
