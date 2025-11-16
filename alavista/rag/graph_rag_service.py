"""Graph-guided RAG service implementation."""

import logging
import re
from typing import Any

from alavista.core.corpus_store import CorpusStore
from alavista.core.models import Chunk
from alavista.graph.graph_service import GraphService
from alavista.personas.persona_base import PersonaBase
from alavista.rag.models import EvidenceItem, GraphContext, GraphRAGResult
from alavista.search.search_service import SearchService

logger = logging.getLogger(__name__)


class GraphRAGService:
    """Service for graph-guided retrieval-augmented generation."""

    def __init__(
        self,
        graph_service: GraphService,
        search_service: SearchService,
        corpus_store: CorpusStore,
    ):
        """Initialize GraphRAGService.

        Args:
            graph_service: Service for graph queries
            search_service: Service for semantic/keyword search
            corpus_store: Store for accessing documents
        """
        self.graph_service = graph_service
        self.search_service = search_service
        self.corpus_store = corpus_store

    def answer(
        self,
        question: str,
        persona: PersonaBase,
        topic_corpus_id: str | None = None,
        k: int = 20,
    ) -> GraphRAGResult:
        """Answer a question using graph-guided RAG.

        Args:
            question: The question to answer
            persona: Persona providing context and filters
            topic_corpus_id: Optional corpus to search within
            k: Number of search results to retrieve

        Returns:
            GraphRAGResult with answer and supporting evidence
        """
        logger.info(f"Graph-guided RAG query: {question[:100]}...")

        # Step 1: Extract entities and categorize question
        entities = self._extract_entity_names(question)
        question_category = persona.categorize_question(question)
        logger.info(
            f"Extracted {len(entities)} entities, category: {question_category.category}"
        )

        # Step 2: Graph narrowing - find relevant entities and context
        graph_context = []
        relevant_doc_ids = set()

        for entity_name in entities[:5]:  # Limit to top 5 entities
            try:
                # Find entities in graph
                nodes = self.graph_service.find_entity(entity_name)
                if not nodes:
                    continue

                # For each found entity, get neighborhood
                for node in nodes[:2]:  # Limit to top 2 matches per entity
                    depth = 2 if question_category.category == "structural" else 1

                    neighbors_nodes, neighbors_edges = self.graph_service.get_neighbors(
                        node.id, depth=depth
                    )

                    # Collect document IDs from nodes and edges
                    for n in [node] + neighbors_nodes:
                        if "document_id" in n.metadata:
                            relevant_doc_ids.add(n.metadata["document_id"])

                    for edge in neighbors_edges:
                        if "document_id" in edge.metadata:
                            relevant_doc_ids.add(edge.metadata["document_id"])

                    # Store graph context
                    graph_context.append(
                        GraphContext(
                            context_type="neighborhood",
                            nodes=[
                                {
                                    "id": n.id,
                                    "type": n.type,
                                    "name": n.name,
                                    "properties": n.properties,
                                }
                                for n in [node] + neighbors_nodes
                            ],
                            edges=[
                                {
                                    "source": e.source_id,
                                    "target": e.target_id,
                                    "relation": e.relation_type,
                                }
                                for e in neighbors_edges
                            ],
                            summary=f"Neighborhood of {node.name} ({node.type})",
                        )
                    )

            except Exception as e:
                logger.debug(f"Failed to process entity '{entity_name}': {e}")

        logger.info(
            f"Found {len(relevant_doc_ids)} relevant documents from graph traversal"
        )

        # Step 3: Semantic narrowing - search within relevant documents
        evidence_items = []

        if topic_corpus_id:
            # Get documents from corpus
            documents = self.corpus_store.list_documents(topic_corpus_id)

            # Filter to relevant doc_ids if we have graph context
            if relevant_doc_ids:
                documents = [doc for doc in documents if doc.id in relevant_doc_ids]

            # Create chunks for search
            chunks = []
            for doc in documents:
                chunk = Chunk(
                    id=f"{doc.id}::chunk_0",
                    document_id=doc.id,
                    corpus_id=topic_corpus_id,
                    text=doc.text,
                    start_offset=0,
                    end_offset=len(doc.text),
                    metadata={"chunk_index": 0, "total_chunks": 1},
                )
                chunks.append(chunk)

            if chunks:
                # Run search
                results = self.search_service.search_bm25(
                    corpus_id=topic_corpus_id,
                    chunks=chunks,
                    query=question,
                    k=k,
                )

                # Convert to evidence items
                for result in results:
                    evidence_items.append(
                        EvidenceItem(
                            document_id=result.doc_id,
                            chunk_id=result.chunk_id,
                            score=result.score,
                            excerpt=result.excerpt,
                            metadata=result.metadata,
                        )
                    )

        # Step 4: Construct answer
        answer_text = self._construct_answer(
            question=question,
            evidence_items=evidence_items,
            graph_context=graph_context,
            persona=persona,
        )

        # Build retrieval summary
        retrieval_summary = (
            f"Used graph-guided RAG with {len(entities)} entities, "
            f"{len(graph_context)} graph contexts, "
            f"{len(evidence_items)} evidence documents"
        )

        return GraphRAGResult(
            answer_text=answer_text,
            evidence_docs=evidence_items[:10],  # Limit in response
            graph_context=graph_context[:5],  # Limit in response
            retrieval_summary=retrieval_summary,
            persona_id=persona.id,
        )

    def _extract_entity_names(self, question: str) -> list[str]:
        """Extract potential entity names from question.

        This is a simple heuristic. In production, use NER or LLM.

        Args:
            question: The question text

        Returns:
            List of potential entity names
        """
        # Simple heuristic: capitalized words/phrases
        words = question.split()
        entities = []

        # Extract single capitalized words (excluding question words)
        question_words = {"What", "When", "Where", "Who", "Why", "How", "Which"}
        for word in words:
            cleaned = re.sub(r'[^\w\s]', '', word)
            if cleaned and cleaned[0].isupper() and cleaned not in question_words:
                entities.append(cleaned)

        # Extract capitalized bigrams
        for i in range(len(words) - 1):
            word1 = re.sub(r'[^\w\s]', '', words[i])
            word2 = re.sub(r'[^\w\s]', '', words[i + 1])
            if (
                word1
                and word2
                and word1[0].isupper()
                and word2[0].isupper()
                and word1 not in question_words
            ):
                entities.append(f"{word1} {word2}")

        return list(set(entities))  # Deduplicate

    def _construct_answer(
        self,
        question: str,
        evidence_items: list[EvidenceItem],
        graph_context: list[GraphContext],
        persona: PersonaBase,
    ) -> str:
        """Construct answer from evidence and graph context.

        This is simplified. In production, use an LLM for synthesis.

        Args:
            question: The original question
            evidence_items: Evidence from document search
            graph_context: Graph context (paths, neighborhoods)
            persona: The persona instance

        Returns:
            Answer text
        """
        if not evidence_items and not graph_context:
            return (
                f"I could not find sufficient evidence in the knowledge graph "
                f"or document corpus to answer: '{question}'. "
                f"Try adding more documents or entities to the system."
            )

        parts = []

        # Summarize graph context
        if graph_context:
            entity_names = []
            for ctx in graph_context[:3]:
                for node in ctx.nodes[:3]:
                    entity_names.append(node.get("name", "unknown"))

            parts.append(
                f"[Graph Context] The knowledge graph shows relationships involving: "
                f"{', '.join(entity_names[:5])}."
            )

        # Summarize evidence
        if evidence_items:
            parts.append(
                f"Found {len(evidence_items)} relevant document(s). "
                f"Most relevant excerpt: {evidence_items[0].excerpt[:200]}..."
            )

        # Add persona note
        parts.append(
            f"\n\nNote: This answer combines graph structure analysis with document "
            f"retrieval using the '{persona.name}' persona. "
            f"All statements are grounded in source documents and graph relationships."
        )

        return " ".join(parts)
