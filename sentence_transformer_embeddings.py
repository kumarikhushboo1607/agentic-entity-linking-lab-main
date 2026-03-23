"""Sentence-transformers helpers for candidate retrieval demos."""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_SENTENCE_TRANSFORMER_CACHE_DIR = Path(".cache/sentence-transformers")


def _import_sentence_transformers() -> tuple[Any, Any]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is not installed. "
            "Run: uv sync --extra vectors"
        ) from exc
    import numpy as np

    return SentenceTransformer, np


class SentenceTransformerEmbeddingProvider:
    """Embedding provider backed by sentence-transformers."""

    def __init__(
        self,
        model_name: str = DEFAULT_SENTENCE_TRANSFORMER_MODEL,
        *,
        cache_folder: str | Path = DEFAULT_SENTENCE_TRANSFORMER_CACHE_DIR,
    ) -> None:
        SentenceTransformer, _ = _import_sentence_transformers()
        self.model_name = model_name
        self.cache_folder = str(cache_folder)
        self.model = SentenceTransformer(model_name, cache_folder=self.cache_folder)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.astype(float).tolist() for vector in vectors]


def download_sentence_transformer_model(
    model_name: str = DEFAULT_SENTENCE_TRANSFORMER_MODEL,
    *,
    cache_folder: str | Path = DEFAULT_SENTENCE_TRANSFORMER_CACHE_DIR,
) -> dict[str, Any]:
    """Download the model and run a tiny encode to verify it works."""
    provider = SentenceTransformerEmbeddingProvider(
        model_name=model_name,
        cache_folder=cache_folder,
    )
    vectors = provider.embed_texts(["entity linking with wikidata", "irish politicians"])
    vector_size = len(vectors[0]) if vectors else 0
    return {
        "model_name": model_name,
        "cache_folder": str(cache_folder),
        "vector_size": vector_size,
        "example_count": len(vectors),
    }
