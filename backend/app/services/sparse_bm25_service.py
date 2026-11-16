"""
Sparse BM25 Indexing and Keyword Retrieval Service.
Uses BM25Okapi / BM25Plus with token normalization that preserves technical entities, acronyms, and codes.
"""
import re
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi, BM25Plus
from app.schemas.retrieval import RetrievedChunk
from app.core.logging import get_logger

logger = get_logger("bm25_service")


class BM25Index:
    def __init__(self):
        self.chunk_ids: List[str] = []
        self.chunks_data: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Any = None

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenizes text while retaining technical tokens like API_KEY, RFC-2616, v1.2, camelCase.
        """
        if not text:
            return []
        cleaned = text.lower()
        # Extract alphanumeric words, plus hyphenated or dotted technical codes
        tokens = re.findall(r"[a-z0-9_]+(?:[-.][a-z0-9_]+)*", cleaned)
        return tokens

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Constructs the BM25 index from chunk dictionaries."""
        self.chunk_ids = []
        self.chunks_data = []
        self.corpus_tokens = []

        for chunk in chunks:
            self.chunk_ids.append(chunk["id"])
            self.chunks_data.append(chunk)
            tokens = self.tokenize(chunk["original_text"])
            self.corpus_tokens.append(tokens)

        if self.corpus_tokens:
            # BM25Plus guarantees positive IDF and handles small documents robustly
            self.bm25 = BM25Plus(self.corpus_tokens)
            logger.info(f"Built BM25 index with {len(self.chunk_ids)} chunks.")
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float, int]]:
        """
        Queries BM25 index and returns list of (chunk_dict, score, rank).
        """
        if not self.bm25 or not self.chunk_ids:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Keep documents that match at least one query token or have a positive score
        scored_indices = []
        for idx, score in enumerate(scores):
            # Check if chunk contains any query token
            chunk_tokens_set = set(self.corpus_tokens[idx])
            has_term_match = any(qt in chunk_tokens_set for qt in query_tokens)
            if has_term_match and score > 0.0:
                scored_indices.append((idx, float(score)))

        # Sort descending by score
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        scored_indices = scored_indices[:top_k]

        results = []
        for rank, (idx, score) in enumerate(scored_indices, start=1):
            results.append((self.chunks_data[idx], float(score), rank))

        return results


# Global singleton instance of BM25Index in memory (synced on chunk mutations)
global_bm25_index = BM25Index()
