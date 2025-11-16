"""Persona runtime for executing persona-scoped reasoning."""

import logging
from typing import Any, Optional

from alavista.core.corpus_store import CorpusStore
from alavista.core.models import Chunk
from alavista.graph.graph_service import GraphService
from alavista.personas.models import PersonaAnswer
from alavista.personas.persona_base import PersonaBase
from alavista.personas.persona_registry import PersonaRegistry
from alavista.search.search_service import SearchService

logger = logging.getLogger(__name__)


class PersonaRuntimeError(Exception):
    """Raised when persona runtime encounters an error."""

    pass


class PersonaRuntime:
    """Runtime for executing persona-scoped question answering."""

    def __init__(
        self,
        persona_registry: PersonaRegistry,
        search_service: SearchService,
        graph_service: GraphService,
        corpus_store: CorpusStore,
        graph_rag_service=None,
    ):
        """Initialize the runtime.

        Args:
            persona_registry: Registry of available personas
            search_service: Service for semantic/keyword search
            graph_service: Service for graph queries
            corpus_store: Store for corpus/document access
            graph_rag_service: Optional GraphRAGService for graph-guided retrieval
        """
        self.persona_registry = persona_registry
        self.search_service = search_service
        self.graph_service = graph_service
        self.corpus_store = corpus_store
        self.graph_rag_service = graph_rag_service

    def answer_question(
        self,
        persona_id: str,
        question: str,
        corpus_id: str,
        k: int = 20,
        use_persona_manual: bool = True,
    ) -> PersonaAnswer:
        """Answer a question using a specific persona.

        Args:
            persona_id: ID of the persona to use
            question: The user's question
            corpus_id: ID of the corpus to search
            k: Number of search results to retrieve
            use_persona_manual: Whether to include persona manual corpus content as context

        Returns:
            PersonaAnswer object with answer and evidence

        Raises:
            PersonaRuntimeError: If persona not found or execution fails
        """
        # 1. Retrieve persona
        persona = self.persona_registry.get_persona(persona_id)
        if not persona:
            raise PersonaRuntimeError(f"Persona '{persona_id}' not found")

        # 2. Categorize question
        category = persona.categorize_question(question)
        logger.info(
            f"Question categorized as '{category.category}' "
            f"(confidence: {category.confidence:.2f})"
        )

        # 2a. Use GraphRAG for structural questions if available
        if (
            self.graph_rag_service
            and category.category in ["structural", "timeline", "comparison"]
        ):
            logger.info("Using Graph-guided RAG for structural question")
            try:
                graph_rag_result = self.graph_rag_service.answer(
                    question=question,
                    persona=persona,
                    topic_corpus_id=corpus_id,
                    k=k,
                )

                # Convert GraphRAGResult to PersonaAnswer
                return PersonaAnswer(
                    answer_text=graph_rag_result.answer_text,
                    evidence=[
                        {
                            "document_id": ev.document_id,
                            "chunk_id": ev.chunk_id,
                            "score": ev.score,
                            "excerpt": ev.excerpt,
                            "metadata": ev.metadata,
                        }
                        for ev in graph_rag_result.evidence_docs
                    ],
                    graph_evidence=[
                        {
                            "type": ctx.context_type,
                            "nodes": ctx.nodes,
                            "edges": ctx.edges,
                            "summary": ctx.summary,
                        }
                        for ctx in graph_rag_result.graph_context
                    ],
                    reasoning_summary=graph_rag_result.retrieval_summary,
                    persona_id=persona_id,
                    disclaimers=persona.safety_config.get("disclaimers", []),
                )
            except Exception as e:
                logger.warning(f"GraphRAG failed, falling back to standard retrieval: {e}")
                # Fall through to standard retrieval

        # 3. Select tools
        tools = persona.select_tools(question, category)
        logger.info(f"Selected tools: {tools}")

        # 4. Run retrieval based on selected tools
        evidence = []
        graph_evidence = []

        # 4a. Optionally retrieve from persona manual corpus
        persona_manual_context = []
        if use_persona_manual:
            persona_manual_corpus_id = self.persona_registry.get_persona_corpus_id(persona_id)
            if persona_manual_corpus_id:
                logger.info(f"Retrieving context from persona manual corpus: {persona_manual_corpus_id}")
                persona_manual_context = self._run_search(
                    corpus_id=persona_manual_corpus_id,
                    query=question,
                    mode="bm25",
                    k=3,  # Retrieve a small number of manual docs
                )
                if persona_manual_context:
                    logger.info(f"Found {len(persona_manual_context)} persona manual context items")

        # Execute search tools
        if "semantic_search" in tools or "keyword_search" in tools:
            search_mode = "hybrid" if "semantic_search" in tools else "bm25"
            evidence.extend(
                self._run_search(
                    corpus_id=corpus_id,
                    query=question,
                    mode=search_mode,
                    k=k,
                )
            )

        # Execute graph tools
        if any(
            tool in tools for tool in ["graph_find_entity", "graph_neighbors", "graph_paths"]
        ):
            graph_evidence.extend(
                self._run_graph_queries(
                    question=question,
                    tools=tools,
                    persona=persona,
                )
            )

        # 5. Aggregate evidence
        evidence = self._deduplicate_evidence(evidence)
        graph_evidence = self._deduplicate_graph_evidence(graph_evidence)

        # 6. Construct answer
        answer_text = self._construct_answer(
            question=question,
            evidence=evidence,
            graph_evidence=graph_evidence,
            persona=persona,
            category=category,
            persona_manual_context=persona_manual_context,
        )

        # 7. Apply safety rules
        disclaimers = persona.safety_config.get("disclaimers", [])

        # 8. Create PersonaAnswer
        return PersonaAnswer(
            answer_text=answer_text,
            evidence=evidence[:10],  # Limit evidence in response
            graph_evidence=graph_evidence[:10],
            reasoning_summary=f"Used {category.category} approach with tools: {', '.join(tools)}",
            persona_id=persona_id,
            disclaimers=disclaimers,
        )

    def _run_search(
        self,
        corpus_id: str,
        query: str,
        mode: str = "hybrid",
        k: int = 20,
    ) -> list[dict[str, Any]]:
        """Run search and return evidence.

        Args:
            corpus_id: Corpus to search
            query: Search query
            mode: Search mode (bm25, vector, hybrid)
            k: Number of results

        Returns:
            List of evidence dictionaries
        """
        try:
            # Get chunks from corpus
            documents = self.corpus_store.list_documents(corpus_id)
            chunks = []
            for doc in documents:
                doc_chunks = [
                    Chunk(
                        id=f"{doc.id}::chunk_{i}",
                        document_id=doc.id,
                        corpus_id=corpus_id,
                        text=doc.text,  # Simplified - would use actual chunks
                        start_offset=0,
                        end_offset=len(doc.text),
                        metadata={"chunk_index": i, "total_chunks": 1},
                    )
                    for i in range(1)
                ]
                chunks.extend(doc_chunks)

            # Run search
            results = self.search_service.search_bm25(
                corpus_id=corpus_id,
                chunks=chunks,
                query=query,
                k=k,
            )

            # Convert to evidence format
            return [
                {
                    "document_id": result.doc_id,
                    "chunk_id": result.chunk_id,
                    "score": result.score,
                    "excerpt": result.excerpt,
                    "metadata": result.metadata,
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _run_graph_queries(
        self,
        question: str,
        tools: list[str],
        persona: PersonaBase,
    ) -> list[dict[str, Any]]:
        """Run graph queries and return evidence.

        Args:
            question: The question being answered
            tools: List of tools to use
            persona: The persona instance

        Returns:
            List of graph evidence dictionaries
        """
        evidence = []

        # Extract potential entity names from question (simple heuristic)
        # In production, this would use NER or LLM
        words = question.split()
        potential_entities = [
            " ".join(words[i : i + 2])
            for i in range(len(words) - 1)
            if words[i][0].isupper()
        ]

        if "graph_find_entity" in tools:
            for entity_name in potential_entities[:3]:  # Limit searches
                try:
                    nodes = self.graph_service.find_entity(entity_name)
                    for node in nodes[:2]:  # Limit results
                        evidence.append(
                            {
                                "type": node.type,
                                "name": node.name,
                                "id": node.id,
                                "metadata": node.metadata,
                            }
                        )
                except Exception as e:
                    logger.debug(f"Entity search for '{entity_name}' failed: {e}")

        return evidence

    def _deduplicate_evidence(self, evidence: list[dict]) -> list[dict]:
        """Deduplicate evidence by chunk_id.

        Args:
            evidence: List of evidence dicts

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []
        for ev in evidence:
            chunk_id = ev.get("chunk_id")
            if chunk_id and chunk_id not in seen:
                seen.add(chunk_id)
                result.append(ev)
        return result

    def _deduplicate_graph_evidence(self, evidence: list[dict]) -> list[dict]:
        """Deduplicate graph evidence by node/edge ID.

        Args:
            evidence: List of graph evidence dicts

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []
        for ev in evidence:
            ev_id = ev.get("id")
            if ev_id and ev_id not in seen:
                seen.add(ev_id)
                result.append(ev)
        return result

    def _construct_answer(
        self,
        question: str,
        evidence: list[dict],
        graph_evidence: list[dict],
        persona: PersonaBase,
        category: Any,
        persona_manual_context: Optional[list[dict]] = None,
    ) -> str:
        """Construct answer text from evidence.

        This is a simplified implementation. In production, this would use an LLM
        to synthesize a proper answer.

        Args:
            question: The original question
            evidence: Document evidence
            graph_evidence: Graph evidence
            persona: The persona instance
            category: Question category
            persona_manual_context: Optional context from persona manual corpus

        Returns:
            Answer text
        """
        if not evidence and not graph_evidence and not persona_manual_context:
            return (
                f"Based on the available corpus, I could not find sufficient evidence "
                f"to answer: '{question}'. "
                f"Try rephrasing your question or adding more documents to the corpus."
            )

        parts = []

        # Include persona manual context first (best practices, etc.)
        if persona_manual_context:
            parts.append(
                f"[Persona Context] Based on {len(persona_manual_context)} reference "
                f"document(s) in the persona manual corpus: "
                f"{persona_manual_context[0]['excerpt'][:100]}..."
            )

        # Summarize document evidence
        if evidence:
            parts.append(
                f"Found {len(evidence)} relevant document(s) in the corpus. "
                f"The most relevant excerpt discusses: {evidence[0]['excerpt'][:150]}..."
            )

        # Summarize graph evidence
        if graph_evidence:
            entity_names = [ge.get("name", "unknown") for ge in graph_evidence[:3]]
            parts.append(
                f"The knowledge graph contains {len(graph_evidence)} relevant "
                f"entities including: {', '.join(entity_names)}."
            )

        # Add reasoning note
        parts.append(
            f"\n\nNote: This answer is based on {category.category} analysis "
            f"of the available corpus. All statements are grounded in source documents."
        )

        return " ".join(parts)
