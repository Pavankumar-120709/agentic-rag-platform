"""
Hybrid Retrieval Engine implementing Dense pgvector retrieval, Sparse BM25, and Reciprocal Rank Fusion (RRF).
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.models import DocumentChunk
from app.schemas.retrieval import RetrievedChunk, HybridRetrievalResult
from app.services.embedding_service import EmbeddingService
from app.services.sparse_bm25_service import global_bm25_index
from app.services.reranking_service import RerankingService
from app.core.logging import get_logger

logger = get_logger("hybrid_retrieval")


class HybridRetrievalService:
    @classmethod
    def reciprocal_rank_fusion(
        cls,
        dense_results: List[RetrievedChunk],
        sparse_results: List[RetrievedChunk],
        k: int = 60
    ) -> List[RetrievedChunk]:
        """
        Combines dense and sparse rankings using Reciprocal Rank Fusion:
        RRF(d) = sum(1 / (k + rank_i(d)))
        Deterministic, deduplicated, and scale-independent.
        """
        fused_map: Dict[str, RetrievedChunk] = {}
        rrf_scores: Dict[str, float] = {}

        # Process Dense results
        for chunk in dense_results:
            cid = chunk.chunk_id
            rank = chunk.dense_rank if chunk.dense_rank is not None else 100
            score_contrib = 1.0 / (k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score_contrib
            if cid not in fused_map:
                fused_map[cid] = chunk.model_copy()
            else:
                fused_map[cid].dense_rank = chunk.dense_rank
                fused_map[cid].dense_score = chunk.dense_score

        # Process Sparse results
        for chunk in sparse_results:
            cid = chunk.chunk_id
            rank = chunk.sparse_rank if chunk.sparse_rank is not None else 100
            score_contrib = 1.0 / (k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score_contrib
            if cid not in fused_map:
                fused_map[cid] = chunk.model_copy()
            else:
                fused_map[cid].sparse_rank = chunk.sparse_rank
                fused_map[cid].sparse_score = chunk.sparse_score

        # Attach RRF scores and sort descending
        fused_list: List[RetrievedChunk] = []
        for cid, chunk in fused_map.items():
            chunk.rrf_score = round(rrf_scores[cid], 6)
            fused_list.append(chunk)

        # Sort descending by rrf_score, breaking ties deterministically by chunk_id
        fused_list.sort(key=lambda x: (x.rrf_score or 0.0, x.chunk_id), reverse=True)
        return fused_list

    @classmethod
    def search_dense(
        cls,
        db: Session,
        query: str,
        top_k: int = 10
    ) -> List[RetrievedChunk]:
        """
        Executes dense vector search against PostgreSQL pgvector or dialect-aware fallback.
        """
        query_embedding = EmbeddingService.get_embedding(query)
        dialect = db.bind.dialect.name if db.bind else "sqlite"

        if dialect == "postgresql":
            # PostgreSQL with pgvector cosine distance: embedding <=> query_embedding
            try:
                sql = text("""
                    SELECT id, document_id, filename, chunk_index, page_number, 
                           original_text, token_count, metadata_json,
                           1 - (embedding <=> :query_vec) AS similarity
                    FROM document_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> :query_vec ASC
                    LIMIT :top_k
                """)
                res = db.execute(sql, {"query_vec": str(query_embedding), "top_k": top_k}).fetchall()
                results = []
                for rank, row in enumerate(res, start=1):
                    results.append(RetrievedChunk(
                        chunk_id=row.id,
                        document_id=row.document_id,
                        filename=row.filename,
                        chunk_index=row.chunk_index,
                        page_number=row.page_number,
                        original_text=row.original_text,
                        token_count=row.token_count,
                        metadata=row.metadata_json or {},
                        dense_score=round(float(row.similarity), 4),
                        dense_rank=rank
                    ))
                return results
            except Exception as e:
                logger.warning(f"pgvector query error ({str(e)}). Falling back to in-memory cosine comparison.")

        # Dialect fallback (SQLite / Test mode): compute cosine similarity across loaded chunks
        chunks = db.query(DocumentChunk).all()
        scored_chunks = []
        for c in chunks:
            if c.embedding is not None:
                sim = EmbeddingService.cosine_similarity(query_embedding, c.embedding)
                scored_chunks.append((c, sim))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_scored = scored_chunks[:top_k]

        results = []
        for rank, (c, sim) in enumerate(top_scored, start=1):
            results.append(RetrievedChunk(
                chunk_id=c.id,
                document_id=c.document_id,
                filename=c.filename,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                original_text=c.original_text,
                token_count=c.token_count,
                metadata=c.metadata_json or {},
                dense_score=round(float(sim), 4),
                dense_rank=rank
            ))
        return results

    @classmethod
    def search_sparse(
        cls,
        db: Session,
        query: str,
        top_k: int = 10
    ) -> List[RetrievedChunk]:
        """
        Executes sparse BM25 keyword search.
        """
        # Ensure BM25 index is populated
        if not global_bm25_index.chunk_ids:
            cls.sync_bm25_index(db)

        raw_results = global_bm25_index.search(query, top_k=top_k)
        results = []
        for chunk_data, score, rank in raw_results:
            results.append(RetrievedChunk(
                chunk_id=chunk_data["id"],
                document_id=chunk_data["document_id"],
                filename=chunk_data["filename"],
                chunk_index=chunk_data["chunk_index"],
                page_number=chunk_data.get("page_number"),
                original_text=chunk_data["original_text"],
                token_count=chunk_data["token_count"],
                metadata=chunk_data.get("metadata_json", {}),
                sparse_score=round(score, 4),
                sparse_rank=rank
            ))
        return results

    @classmethod
    def sync_bm25_index(cls, db: Session) -> None:
        """Loads all existing chunks into the BM25 index."""
        chunks = db.query(DocumentChunk).all()
        chunk_dicts = [
            {
                "id": c.id,
                "document_id": c.document_id,
                "filename": c.filename,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "original_text": c.original_text,
                "token_count": c.token_count,
                "metadata_json": c.metadata_json or {}
            }
            for c in chunks
        ]
        global_bm25_index.build_index(chunk_dicts)

    @classmethod
    def execute_hybrid_retrieval(
        cls,
        db: Session,
        query: str,
        retrieval_method: str = "hybrid",
        retrieval_top_k: int = 10,
        rerank_top_k: int = 5,
        k_rrf: int = 60
    ) -> HybridRetrievalResult:
        """
        Orchestrates dense search, sparse search, RRF fusion, and cross-encoder reranking.
        """
        dense_results: List[RetrievedChunk] = []
        sparse_results: List[RetrievedChunk] = []

        if retrieval_method in ["hybrid", "dense_only"]:
            dense_results = cls.search_dense(db, query, top_k=retrieval_top_k)

        if retrieval_method in ["hybrid", "sparse_only"]:
            sparse_results = cls.search_sparse(db, query, top_k=retrieval_top_k)

        if retrieval_method == "dense_only":
            fused = dense_results
        elif retrieval_method == "sparse_only":
            fused = sparse_results
        else:
            fused = cls.reciprocal_rank_fusion(dense_results, sparse_results, k=k_rrf)

        # Cross-encoder rerank
        reranked = RerankingService.rerank(query, fused, top_k=rerank_top_k)

        return HybridRetrievalResult(
            sparse_candidates=sparse_results,
            dense_candidates=dense_results,
            fused_candidates=fused,
            reranked_candidates=reranked,
            selected_context=[]
        )
