from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, List, Protocol

from alavista.core.chunking import chunk_text
from alavista.core.models import Chunk, Document
from alavista.vector import VectorSearchService


class EmbeddingServiceProtocol(Protocol):
    async def embed_texts(self, texts: List[str]) -> List[List[float]]: ...


class CorpusStoreProtocol(Protocol):
    def get_corpus(self, corpus_id: str) -> object | None: ...

    def list_documents(self, corpus_id: str) -> List[Document]: ...


@dataclass
class EmbeddingPipeline:
    """
    Embedding pipeline for (re)building chunk embeddings per corpus.

    Responsibilities:
    - Build chunks from stored documents
    - Embed only chunks that are not yet marked as embedded
    - Index embeddings via VectorSearchService
    """

    corpus_store: CorpusStoreProtocol
    embedding_service: EmbeddingServiceProtocol
    vector_search_service: VectorSearchService
    batch_size: int = 32
    min_chunk_size: int = 500
    max_chunk_size: int = 1500

    def embed_corpus(self, corpus_id: str, force: bool = False) -> int:
        """Embed all documents in a corpus, skipping already-embedded chunks unless forced."""
        if not self.corpus_store.get_corpus(corpus_id):
            raise ValueError(f"Corpus {corpus_id} not found")
        documents = self.corpus_store.list_documents(corpus_id)
        chunks: list[Chunk] = []
        for doc in documents:
            chunks.extend(self._chunk_document(doc))
        return self.embed_chunks(corpus_id, chunks, force=force)

    def embed_chunks(self, corpus_id: str, chunks: Iterable[Chunk], force: bool = False) -> int:
        """Embed a provided iterable of chunks."""
        to_process: list[Chunk] = []
        for chunk in chunks:
            if not force and chunk.metadata.get("embedded"):
                continue
            to_process.append(chunk)

        if not to_process:
            return 0

        total_embedded = 0
        for i in range(0, len(to_process), self.batch_size):
            batch = to_process[i : i + self.batch_size]
            texts = [c.text for c in batch]
            vectors = self._run_coro(self.embedding_service.embed_texts(texts))
            items = [
                (chunk.document_id, chunk.id, vectors[j])
                for j, chunk in enumerate(batch)
            ]
            self._run_coro(self.vector_search_service.index_embeddings(corpus_id, items))
            for chunk in batch:
                chunk.metadata["embedded"] = True
            total_embedded += len(batch)
        return total_embedded

    def _chunk_document(self, document: Document) -> list[Chunk]:
        chunk_infos = chunk_text(
            document.text,
            min_chunk_size=self.min_chunk_size,
            max_chunk_size=self.max_chunk_size,
        )
        chunks: list[Chunk] = []
        for i, info in enumerate(chunk_infos):
            chunks.append(
                Chunk(
                    id=f"{document.id}::chunk_{i}",
                    document_id=document.id,
                    corpus_id=document.corpus_id,
                    text=info.text,
                    start_offset=info.start_offset,
                    end_offset=info.end_offset,
                    metadata={"chunk_index": i, "total_chunks": len(chunk_infos)},
                )
            )
        return chunks

    def _run_coro(self, coro):
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        except RuntimeError:
            return asyncio.run(coro)
