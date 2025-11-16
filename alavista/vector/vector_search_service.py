from __future__ import annotations

from dataclasses import dataclass, field
from json import load as json_load, dump as json_dump
from math import sqrt
from pathlib import Path
from typing import List, Protocol, Tuple

import numpy as np
from pydantic import BaseModel

try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except Exception:  # pragma: no cover - exercised by alt backend selection
    faiss = None  # type: ignore
    _HAS_FAISS = False


class VectorSearchError(Exception):
    """Raised when vector search operations fail."""


class VectorHit(BaseModel):
    document_id: str
    chunk_id: str
    score: float


class VectorSearchService(Protocol):
    async def index_embeddings(
        self,
        corpus_id: str,
        items: List[Tuple[str, str, List[float]]],  # (document_id, chunk_id, vector)
    ) -> None:
        ...

    async def search(self, corpus_id: str, query_vector: List[float], k: int = 20) -> List[VectorHit]:
        ...


@dataclass
class _CorpusIndex:
    dim: int
    vectors: List[List[float]] = field(default_factory=list)
    keys: List[Tuple[str, str]] = field(default_factory=list)
    key_index: dict[Tuple[str, str], int] = field(default_factory=dict)


@dataclass
class InMemoryVectorSearchService:
    """
    Simple in-memory implementation of the VectorSearchService.

    This follows the roadmap for Phase 3.2 by providing:
    - per-corpus vector storage
    - optional L2 normalization for cosine similarity
    - kNN search with inner product scoring
    """

    normalize: bool = True

    def __post_init__(self) -> None:
        self._corpora: dict[str, _CorpusIndex] = {}

    async def index_embeddings(
        self,
        corpus_id: str,
        items: List[Tuple[str, str, List[float]]],
    ) -> None:
        if items is None:
            raise VectorSearchError("items cannot be None")
        if not items:
            return

        first_vector = items[0][2]
        if not first_vector:
            raise VectorSearchError("embedding vectors cannot be empty")
        dim = len(first_vector)

        corpus_idx = self._corpora.get(corpus_id)
        if corpus_idx is None:
            corpus_idx = _CorpusIndex(dim=dim)
            self._corpora[corpus_id] = corpus_idx
        elif corpus_idx.dim != dim:
            raise VectorSearchError(
                f"dimension mismatch for corpus {corpus_id}: expected {corpus_idx.dim}, got {dim}"
            )

        for document_id, chunk_id, vector in items:
            key = (document_id, chunk_id)
            if key in corpus_idx.key_index:
                raise VectorSearchError(
                    f"duplicate embedding for corpus={corpus_id} document_id={document_id} chunk_id={chunk_id}"
                )
            if len(vector) != corpus_idx.dim:
                raise VectorSearchError(
                    f"embedding dimension mismatch: expected {corpus_idx.dim}, got {len(vector)}"
                )
            processed = self._normalize(vector) if self.normalize else vector
            corpus_idx.vectors.append(processed)
            corpus_idx.keys.append(key)
            corpus_idx.key_index[key] = len(corpus_idx.vectors) - 1

    async def search(self, corpus_id: str, query_vector: List[float], k: int = 20) -> List[VectorHit]:
        corpus_idx = self._corpora.get(corpus_id)
        if corpus_idx is None or not corpus_idx.vectors:
            return []

        if len(query_vector) != corpus_idx.dim:
            raise VectorSearchError(
                f"query vector dimension mismatch: expected {corpus_idx.dim}, got {len(query_vector)}"
            )

        processed_query = self._normalize(query_vector) if self.normalize else query_vector

        scores: list[tuple[int, float]] = []
        for idx, vec in enumerate(corpus_idx.vectors):
            score = self._dot(processed_query, vec)
            scores.append((idx, score))

        scores.sort(key=lambda item: item[1], reverse=True)

        limit = min(max(k, 0), len(scores))
        results: list[VectorHit] = []
        for idx, score in scores[:limit]:
            document_id, chunk_id = corpus_idx.keys[idx]
            results.append(VectorHit(document_id=document_id, chunk_id=chunk_id, score=score))
        return results

    def _normalize(self, vector: List[float]) -> List[float]:
        norm = sqrt(sum(v * v for v in vector))
        if norm == 0:
            raise VectorSearchError("cannot normalize zero vector")
        return [v / norm for v in vector]

    def _dot(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            raise VectorSearchError("dimension mismatch during dot product")
        return float(sum(x * y for x, y in zip(a, b)))


@dataclass
class _FaissCorpus:
    dim: int
    index: "faiss.IndexFlatIP"
    keys: list[Tuple[str, str]]
    key_index: dict[Tuple[str, str], int]
    meta_path: Path
    index_path: Path


@dataclass
class FaissVectorSearchService:
    """
    FAISS-backed implementation aligned with Phase 3.2 requirements.

    Persist indexes and metadata per corpus under `root_dir`.
    """

    root_dir: Path
    normalize: bool = True

    def __post_init__(self) -> None:
        if not _HAS_FAISS:
            raise VectorSearchError("faiss is not installed; cannot use FaissVectorSearchService")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._corpora: dict[str, _FaissCorpus] = {}

    async def index_embeddings(
        self,
        corpus_id: str,
        items: List[Tuple[str, str, List[float]]],
    ) -> None:
        if items is None:
            raise VectorSearchError("items cannot be None")
        if not items:
            return

        first_vector = items[0][2]
        if not first_vector:
            raise VectorSearchError("embedding vectors cannot be empty")
        dim = len(first_vector)

        corpus_idx = self._load_or_create_corpus(corpus_id, dim)

        for document_id, chunk_id, vector in items:
            key = (document_id, chunk_id)
            if key in corpus_idx.key_index:
                raise VectorSearchError(
                    f"duplicate embedding for corpus={corpus_id} document_id={document_id} chunk_id={chunk_id}"
                )
            if len(vector) != corpus_idx.dim:
                raise VectorSearchError(
                    f"embedding dimension mismatch: expected {corpus_idx.dim}, got {len(vector)}"
                )
            arr = self._prepare_vector(vector)
            corpus_idx.index.add(arr)
            corpus_idx.keys.append(key)
            corpus_idx.key_index[key] = len(corpus_idx.keys) - 1

        self._persist_corpus(corpus_idx)

    async def search(self, corpus_id: str, query_vector: List[float], k: int = 20) -> List[VectorHit]:
        corpus_idx = self._load_corpus_if_exists(corpus_id)
        if corpus_idx is None or corpus_idx.index.ntotal == 0:
            return []

        if len(query_vector) != corpus_idx.dim:
            raise VectorSearchError(
                f"query vector dimension mismatch: expected {corpus_idx.dim}, got {len(query_vector)}"
            )

        query = self._prepare_vector(query_vector)
        limit = min(max(k, 0), corpus_idx.index.ntotal)
        # FAISS expects shape (n_queries, dim)
        scores, ids = corpus_idx.index.search(query, limit)
        # scores shape (1, limit), ids shape (1, limit)
        hits: list[VectorHit] = []
        for idx, score in zip(ids[0], scores[0]):
            if idx == -1:
                continue
            document_id, chunk_id = corpus_idx.keys[idx]
            hits.append(VectorHit(document_id=document_id, chunk_id=chunk_id, score=float(score)))
        return hits

    def _prepare_vector(self, vector: List[float]) -> np.ndarray:
        arr = np.array(vector, dtype=np.float32)
        if arr.ndim != 1:
            raise VectorSearchError("embedding vector must be one-dimensional")
        if self.normalize:
            norm = np.linalg.norm(arr)
            if norm == 0:
                raise VectorSearchError("cannot normalize zero vector")
            arr = arr / norm
        return arr.reshape(1, -1)

    def _load_or_create_corpus(self, corpus_id: str, dim: int) -> _FaissCorpus:
        existing = self._load_corpus_if_exists(corpus_id)
        if existing:
            if existing.dim != dim:
                raise VectorSearchError(
                    f"dimension mismatch for corpus {corpus_id}: expected {existing.dim}, got {dim}"
                )
            return existing
        index_path, meta_path = self._paths_for_corpus(corpus_id)
        index = faiss.IndexFlatIP(dim)
        corpus = _FaissCorpus(
            dim=dim,
            index=index,
            keys=[],
            key_index={},
            meta_path=meta_path,
            index_path=index_path,
        )
        self._corpora[corpus_id] = corpus
        return corpus

    def _load_corpus_if_exists(self, corpus_id: str) -> _FaissCorpus | None:
        if corpus_id in self._corpora:
            return self._corpora[corpus_id]
        index_path, meta_path = self._paths_for_corpus(corpus_id)
        if not index_path.exists() or not meta_path.exists():
            return None

        try:
            with meta_path.open("r", encoding="utf-8") as f:
                meta = json_load(f)
            dim = int(meta["dim"])
            keys = [tuple(item) for item in meta.get("keys", [])]
            index = faiss.read_index(str(index_path))
            corpus = _FaissCorpus(
                dim=dim,
                index=index,
                keys=list(keys),
                key_index={k: i for i, k in enumerate(keys)},
                meta_path=meta_path,
                index_path=index_path,
            )
            self._corpora[corpus_id] = corpus
            return corpus
        except Exception as e:  # pragma: no cover - defensive
            raise VectorSearchError(f"failed to load corpus index for {corpus_id}") from e

    def _paths_for_corpus(self, corpus_id: str) -> tuple[Path, Path]:
        index_path = self.root_dir / f"{corpus_id}.index"
        meta_path = self.root_dir / f"{corpus_id}.meta.json"
        return index_path, meta_path

    def _persist_corpus(self, corpus: _FaissCorpus) -> None:
        faiss.write_index(corpus.index, str(corpus.index_path))
        with corpus.meta_path.open("w", encoding="utf-8") as f:
            json_dump({"dim": corpus.dim, "keys": corpus.keys}, f)
