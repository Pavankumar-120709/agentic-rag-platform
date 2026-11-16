"""
Cross-Encoder Reranking Service.
Scores query-document pairs to produce high-precision contextual relevance signals.
"""
import re
from typing import List
from app.schemas.retrieval import RetrievedChunk
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("reranker_service")

_RERANKER_MODEL = None
_RERANKER_FAILED = False


def _get_cross_encoder():
    global _RERANKER_MODEL, _RERANKER_FAILED
    if _RERANKER_MODEL is not None:
        return _RERANKER_MODEL
    if _RERANKER_FAILED:
        return None
    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"Loading CrossEncoder: {settings.RERANKER_MODEL_NAME}")
        _RERANKER_MODEL = CrossEncoder(settings.RERANKER_MODEL_NAME)
        return _RERANKER_MODEL
    except Exception as e:
        logger.warning(f"CrossEncoder model unavailable ({str(e)}). Using deterministic lexical-semantic reranker fallback.")
        _RERANKER_FAILED = True
        return None


class RerankingService:
    @classmethod
    def rerank(
        cls,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """
        Reranks a list of candidate chunks against the user query.
        Returns the top_k reranked candidates with updated rerank_score.
        """
        if not candidates:
            return []

        model = _get_cross_encoder()
        if model is not None:
            try:
                pairs = [[query, c.original_text] for c in candidates]
                scores = model.predict(pairs)
                for chunk, score in zip(candidates, scores):
                    chunk.rerank_score = float(score)
                # Sort descending by cross-encoder score
                sorted_candidates = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
                return sorted_candidates[:top_k]
            except Exception as e:
                logger.warning(f"CrossEncoder inference failed: {str(e)}. Using fallback scoring.")

        # Robust lexical-semantic fallback scoring:
        for chunk in candidates:
            term_score = cls._compute_lexical_density(query, chunk.original_text)
            rrf_contrib = chunk.rrf_score or 0.0
            # Scale RRF score (typical max is ~0.033) up to [0.0, 1.0] range
            normalized_rrf = min(1.0, rrf_contrib * 30.0)
            chunk.rerank_score = round(0.4 * normalized_rrf + 0.6 * term_score, 4)

        sorted_candidates = sorted(candidates, key=lambda c: c.rerank_score or 0.0, reverse=True)
        return sorted_candidates[:top_k]

    @staticmethod
    def _compute_lexical_density(query: str, text: str) -> float:
        """
        Calculates punctuation-stripped, stem-aware token overlap density
        between query and candidate text.
        """
        STOPWORDS = {"what", "does", "the", "a", "an", "is", "are", "in", "of", "to", "and", "or", "for", "with", "regarding", "can", "you", "tell", "me"}
        query_tokens = [
            t for t in re.findall(r"\b[a-z0-9_]+\b", query.lower())
            if t not in STOPWORDS and len(t) > 1
        ]
        if not query_tokens:
            query_tokens = re.findall(r"\b[a-z0-9_]+\b", query.lower())
        if not query_tokens:
            return 0.0

        text_tokens = set(re.findall(r"\b[a-z0-9_]+\b", text.lower()))
        if not text_tokens:
            return 0.0

        matches = 0
        for qt in query_tokens:
            # Check exact match or prefix/stem match (e.g. citation vs citations, feature vs features)
            if any(qt in tt or tt in qt for tt in text_tokens):
                matches += 1

        return min(1.0, matches / len(query_tokens))
