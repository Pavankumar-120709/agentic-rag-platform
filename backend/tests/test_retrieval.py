"""
Integration tests for Sparse BM25, Dense Retrieval, and Cross-Encoder Reranking.
"""
from app.services.sparse_bm25_service import BM25Index
from app.services.embedding_service import EmbeddingService
from app.services.reranking_service import RerankingService
from app.schemas.retrieval import RetrievedChunk


def test_bm25_technical_token_matching():
    index = BM25Index()
    docs = [
        {"id": "c1", "document_id": "d1", "filename": "auth.txt", "chunk_index": 0, "original_text": "Set API_KEY=xyz in environment settings.", "token_count": 10},
        {"id": "c2", "document_id": "d2", "filename": "db.txt", "chunk_index": 0, "original_text": "PostgreSQL database connection string.", "token_count": 8},
    ]
    index.build_index(docs)

    results = index.search("API_KEY", top_k=2)
    assert len(results) == 1
    assert results[0][0]["id"] == "c1"
    assert results[0][1] > 0.0


def test_embedding_cosine_similarity():
    emb1 = EmbeddingService.get_embedding("Vector database and hybrid retrieval")
    emb2 = EmbeddingService.get_embedding("Vector database and sparse hybrid search")
    emb3 = EmbeddingService.get_embedding("Chocolate chip cookie recipe")

    sim_related = EmbeddingService.cosine_similarity(emb1, emb2)
    sim_unrelated = EmbeddingService.cosine_similarity(emb1, emb3)

    assert sim_related > sim_unrelated
    assert sim_related > 0.4


def test_reranker_relevance_sorting():
    query = "What database supports pgvector?"
    candidates = [
        RetrievedChunk(chunk_id="c1", document_id="d1", filename="cooking.txt", chunk_index=0, original_text="Bake cookies at 350 degrees.", token_count=8, rrf_score=0.01),
        RetrievedChunk(chunk_id="c2", document_id="d2", filename="db.txt", chunk_index=0, original_text="PostgreSQL supports pgvector for dense embeddings.", token_count=10, rrf_score=0.02)
    ]

    reranked = RerankingService.rerank(query, candidates, top_k=2)
    assert len(reranked) == 2
    assert reranked[0].chunk_id == "c2"
    assert (reranked[0].rerank_score or 0) > (reranked[1].rerank_score or 0)
