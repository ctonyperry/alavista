"""
CLI utility to (re)embed and index a corpus.

Usage:
    python scripts/embed_corpus.py <corpus_id>
"""

import argparse

from alavista.core.container import Container
from alavista.core.embeddings import EmbeddingPipeline, get_default_embedding_service


def main():
    parser = argparse.ArgumentParser(description="Embed and index a corpus.")
    parser.add_argument("corpus_id", help="Target corpus ID")
    parser.add_argument("--force", action="store_true", help="Force re-embedding existing chunks")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    args = parser.parse_args()

    corpus_store = Container.get_corpus_store()
    vector_service = Container.get_vector_search_service()
    embedding_service = get_default_embedding_service()

    pipeline = EmbeddingPipeline(
        corpus_store=corpus_store,
        embedding_service=embedding_service,
        vector_search_service=vector_service,
        batch_size=args.batch_size,
    )
    embedded = pipeline.embed_corpus(args.corpus_id, force=args.force)
    print(f"Embedded {embedded} chunks for corpus {args.corpus_id}")


if __name__ == "__main__":
    main()
