"""
LangGraph workflow nodes implementing the 15 required stages of Agentic RAG.
Each node is a pure function taking (state, db) and returning state mutations.
"""
import time
import json
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.workflow.state import AgenticRAGState
from app.core.config import settings
from app.core.security import detect_prompt_injection
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.services.token_service import TokenService
from app.schemas.chat import AnswerResponse, Citation
from app.workflow.llm_provider import LLMClient
from app.core.logging import get_logger

logger = get_logger("workflow_nodes")


class WorkflowNodes:
    @staticmethod
    def classify_query(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 1: Classifies query intent and scans for prompt injection threats."""
        injected, pattern = detect_prompt_injection(state.query)
        if injected:
            logger.warning(f"Prompt injection pattern detected: '{pattern}'")
            state.fallback_reason = "prompt_injection_detected"
            state.evidence_sufficient = False
            state.final_status = "fallback"
            return state

        # Determine query nature
        words = state.query.lower().split()
        if any(w in words for w in ["what", "when", "who", "where", "how", "list", "describe"]):
            state.query_type = "factual"
        elif any(w in words for w in ["compare", "contrast", "explain", "why"]):
            state.query_type = "conceptual"
        else:
            state.query_type = "general"

        return state

    @staticmethod
    def retrieve_hybrid(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 2: Executes dense and sparse searches."""
        top_k = settings.RETRIEVAL_TOP_K
        if state.retrieval_method in ["hybrid", "dense_only"]:
            state.dense_candidates = HybridRetrievalService.search_dense(db, state.query, top_k=top_k)
        if state.retrieval_method in ["hybrid", "sparse_only"]:
            state.sparse_candidates = HybridRetrievalService.search_sparse(db, state.query, top_k=top_k)
        return state

    @staticmethod
    def fuse_results(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 3: Combines retrieval results using Reciprocal Rank Fusion."""
        if state.retrieval_method == "dense_only":
            state.fused_candidates = state.dense_candidates
        elif state.retrieval_method == "sparse_only":
            state.fused_candidates = state.sparse_candidates
        else:
            state.fused_candidates = HybridRetrievalService.reciprocal_rank_fusion(
                state.dense_candidates,
                state.sparse_candidates,
                k=settings.RRF_K
            )
        return state

    @staticmethod
    def rerank_documents(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 4: Cross-Encoder reranking of fused candidates."""
        from app.services.reranking_service import RerankingService
        state.reranked_candidates = RerankingService.rerank(
            state.query,
            state.fused_candidates,
            top_k=settings.RERANK_TOP_K
        )
        return state

    @staticmethod
    def assess_retrieval(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """
        Node 5: Assesses retrieval quality against relevance thresholds.
        Evaluates candidate counts, reranker scores, and coverage.
        """
        if not state.reranked_candidates:
            state.evidence_sufficient = False
            state.retrieval_quality_score = 0.0
            return state

        # Compute top rerank score
        top_score = max((c.rerank_score or 0.0) for c in state.reranked_candidates)
        avg_top_3 = sum((c.rerank_score or 0.0) for c in state.reranked_candidates[:3]) / min(3, len(state.reranked_candidates))
        quality = 0.6 * top_score + 0.4 * avg_top_3
        state.retrieval_quality_score = round(quality, 4)

        if quality >= settings.MIN_RELEVANCE_SCORE_THRESHOLD:
            state.evidence_sufficient = True
        else:
            state.evidence_sufficient = False

        return state

    @staticmethod
    def rewrite_query(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """
        Node 6: Bounded query rewriting preserving intent and technical entities.
        """
        state.rewrite_count += 1
        current = state.query
        
        # Strip stop-question prefixes to focus on core technical entities
        cleaned = re.sub(r"^(can you tell me|what is|how to|where does|explain)\s+", "", current, flags=re.IGNORECASE)
        # Formulate targeted technical search
        rewritten = f"{cleaned.strip()} key technical specifications details"
        
        # Avoid duplicate rewrites
        if rewritten in state.rewritten_queries or rewritten == current:
            rewritten = f"{current} overview summary"

        state.rewritten_queries.append(rewritten)
        state.query = rewritten
        logger.info(f"Query rewrite {state.rewrite_count}/{state.max_rewrites}: '{current}' -> '{rewritten}'")
        return state

    @staticmethod
    def retrieve_again(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 7: Retries retrieval with rewritten query."""
        state = WorkflowNodes.retrieve_hybrid(state, db)
        state = WorkflowNodes.fuse_results(state, db)
        state = WorkflowNodes.rerank_documents(state, db)
        return state

    @staticmethod
    def select_context(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 8: Enforces token budget and context deduplication."""
        candidates = state.reranked_candidates or state.fused_candidates
        selected, total_tokens = TokenService.fit_chunks_within_budget(
            candidates,
            max_token_budget=state.context_token_budget
        )
        state.selected_context = selected
        state.selected_context_tokens = total_tokens
        return state

    @staticmethod
    def generate_answer(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 9: Grounded answer generation using selected context."""
        state.generation_attempts += 1
        system_prompt = (
            "You are a strict, grounded AI assistant for enterprise document intelligence.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Answer ONLY using the facts present in the provided context chunks.\n"
            "2. For every assertion, provide a citation with the exact chunk_id, document_id, filename, and verbatim quoted_text.\n"
            "3. If evidence is insufficient, state this clearly with confidence_label='insufficient_evidence'.\n"
            "4. Output MUST be valid JSON adhering to AnswerResponse schema:\n"
            "   {\n"
            "     'answer': string,\n"
            "     'citations': [{'document_id': str, 'filename': str, 'chunk_id': str, 'page_number': int, 'quoted_text': str}],\n"
            "     'confidence_label': 'supported' | 'partially_supported' | 'insufficient_evidence',\n"
            "     'evidence_summary': string,\n"
            "     'warnings': [string]\n"
            "   }"
        )

        context_str = "\n\n".join([
            f"--- [CHUNK ID: {c.chunk_id}] (Doc: {c.filename}, Page: {c.page_number}) ---\n{c.original_text}"
            for c in state.selected_context
        ])

        user_prompt = f"Context:\n{context_str}\n\nQuestion: {state.original_query}"

        raw_out, p_tokens, c_tokens = LLMClient.call_llm(
            system_prompt,
            user_prompt,
            context_chunks=state.selected_context
        )
        state.raw_generation_output = raw_out
        state.prompt_tokens += p_tokens
        state.completion_tokens += c_tokens
        state.total_tokens = state.prompt_tokens + state.completion_tokens
        return state

    @staticmethod
    def validate_output(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 10: Validates structured Pydantic schema compliance."""
        if not state.raw_generation_output:
            state.output_valid = False
            state.validation_errors.append("No generation output received.")
            return state

        try:
            # Parse JSON
            raw = state.raw_generation_output.strip()
            # Clean possible markdown fence blocks ```json ... ```
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)

            parsed = json.loads(raw)
            state.answer_response = AnswerResponse(**parsed)
            state.output_valid = True
        except Exception as e:
            state.output_valid = False
            state.validation_errors.append(f"Schema validation error: {str(e)}")
            logger.warning(f"Schema validation failed: {str(e)}")

        return state

    @staticmethod
    def validate_citations(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """
        Node 11: Deterministic citation verification.
        Verifies chunk IDs exist in selected context and quoted_text exists in chunk.
        """
        if not state.answer_response:
            state.citation_valid = False
            return state

        if state.answer_response.confidence_label == "insufficient_evidence":
            state.citation_valid = True
            return state

        valid_chunk_map = {c.chunk_id: c for c in state.selected_context}
        valid = True

        for cite in state.answer_response.citations:
            if cite.chunk_id not in valid_chunk_map:
                valid = False
                state.validation_errors.append(f"Citation refers to unretrieved chunk_id '{cite.chunk_id}'.")
                continue

            ref_chunk = valid_chunk_map[cite.chunk_id]
            # Verify quoted_text exists in the referenced chunk
            clean_quote = re.sub(r"\s+", " ", cite.quoted_text.strip().lower())
            clean_chunk = re.sub(r"\s+", " ", ref_chunk.original_text.strip().lower())

            if clean_quote not in clean_chunk:
                # Check character overlap ratio if not exact substring
                from difflib import SequenceMatcher
                matcher = SequenceMatcher(None, clean_quote, clean_chunk)
                match = matcher.find_longest_match(0, len(clean_quote), 0, len(clean_chunk))
                overlap_ratio = match.size / max(1, len(clean_quote))
                if overlap_ratio < 0.85:
                    valid = False
                    state.validation_errors.append(
                        f"Citation quoted_text not found in chunk '{cite.chunk_id}' (overlap: {overlap_ratio:.2f})."
                    )

        state.citation_valid = valid
        return state

    @staticmethod
    def evaluate_faithfulness(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """
        Node 12: Evaluates faithfulness of generated answer claims against selected context.
        """
        if not state.answer_response or state.answer_response.confidence_label == "insufficient_evidence":
            state.faithfulness_score = 1.0
            state.faithfulness_passed = True
            return state

        if not state.citation_valid or not state.output_valid:
            state.faithfulness_score = 0.0
            state.faithfulness_passed = False
            return state

        # Deterministic claim verification heuristic:
        # Check that answer nouns/entities correspond to retrieved context
        answer_words = set(re.findall(r"\b[A-Za-z0-9_]{4,}\b", state.answer_response.answer.lower()))
        context_words = set()
        for c in state.selected_context:
            context_words.update(re.findall(r"\b[A-Za-z0-9_]{4,}\b", c.original_text.lower()))

        if not answer_words:
            overlap = 1.0
        else:
            overlap = len(answer_words.intersection(context_words)) / len(answer_words)

        state.faithfulness_score = round(min(1.0, overlap * 1.1), 2)
        state.faithfulness_passed = state.faithfulness_score >= 0.65
        return state

    @staticmethod
    def regenerate_answer(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 13: Bounded regeneration attempting to correct citation or faithfulness errors."""
        logger.info(f"Regenerating answer (attempt {state.generation_attempts + 1}). Errors: {state.validation_errors}")
        state = WorkflowNodes.generate_answer(state, db)
        state = WorkflowNodes.validate_output(state, db)
        state = WorkflowNodes.validate_citations(state, db)
        state = WorkflowNodes.evaluate_faithfulness(state, db)
        return state

    @staticmethod
    def finalize_answer(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """Node 14: Finalizes successful answer response."""
        state.final_status = "success"
        return state

    @staticmethod
    def fallback_answer(state: AgenticRAGState, db: Session) -> AgenticRAGState:
        """
        Node 15: Automated bounded fallbacks for weak retrieval, injection, or schema errors.
        """
        state.final_status = "fallback"
        reason = state.fallback_reason or "insufficient_evidence"

        if reason == "prompt_injection_detected":
            msg = "Query blocked: input triggered security policy for potential prompt injection."
            label = "insufficient_evidence"
            summary = "Security filter intervention."
        elif not state.evidence_sufficient:
            msg = (
                "I investigated the uploaded knowledge base but could not find sufficient grounded evidence "
                f"to answer: '{state.original_query}'. Please upload relevant documents or refine your query."
            )
            label = "insufficient_evidence"
            summary = "Retrieval quality below threshold after query rewriting."
        elif not state.output_valid:
            msg = "An error occurred formatting the response. Please try again."
            label = "insufficient_evidence"
            summary = "Output schema generation failure."
        else:
            msg = (
                "The available documents contain partial context, but the answer cannot be verified with high certainty."
            )
            label = "partially_supported"
            summary = "Unverified claims detected during faithfulness check."

        state.answer_response = AnswerResponse(
            answer=msg,
            citations=[],
            confidence_label=label,
            evidence_summary=summary,
            warnings=[f"Fallback triggered: {reason}"]
        )
        return state
