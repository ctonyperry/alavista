from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Protocol

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    SentenceTransformer = None  # type: ignore
    _HAS_ST = False


class EmbeddingError(Exception):
    pass


class EmbeddingService(Protocol):
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return one vector per input text in the same order."""


@dataclass
class SentenceTransformersEmbeddingService:
    model_name: str = "all-MiniLM-L6-v2"
    batch_size: int = 32

    def __post_init__(self):
        if not _HAS_ST:
            raise EmbeddingError("sentence-transformers is not installed")
        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception as e:
            raise EmbeddingError("failed to load SentenceTransformer model") from e

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if texts is None:
            raise EmbeddingError("texts must be a list of strings")

        loop = asyncio.get_event_loop()
        try:
            results = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                # use keyword args to avoid confusion with prompt_name parameter
                emb = await loop.run_in_executor(None, lambda b: self._model.encode(b, convert_to_numpy=True), batch)
                for v in emb:
                    results.append(list(map(float, v)))
            return results
        except Exception as e:
            raise EmbeddingError("embedding backend failed") from e


@dataclass
class DeterministicFallbackEmbeddingService:
    dim: int = 384
    batch_size: int = 64

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if texts is None:
            raise EmbeddingError("texts must be a list of strings")
        out: List[List[float]] = []
        for t in texts:
            h = 1469598103934665603
            for ch in t:
                h ^= ord(ch)
                h *= 1099511628211
                h &= (1 << 64) - 1
            vec = []
            x = h
            for i in range(self.dim):
                x = (6364136223846793005 * x + 1442695040888963407) & ((1 << 64) - 1)
                vec.append(((x >> 1) / float(1 << 63)) * 2.0 - 1.0)
            out.append(vec)
        return out


def get_default_embedding_service() -> EmbeddingService:
    if _HAS_ST:
        try:
            return SentenceTransformersEmbeddingService()
        except EmbeddingError:
            return DeterministicFallbackEmbeddingService()
    return DeterministicFallbackEmbeddingService()
