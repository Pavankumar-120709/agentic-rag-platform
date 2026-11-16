# Implementation Notes & Technical Decisions

## 1. Multi-Engine Storage Architecture (PostgreSQL + pgvector with Portable SQLite Fallback)
- **Production Standard**: Target database is PostgreSQL 16 with `pgvector` enabled (`vector(384)` or `vector(768)` depending on embedding model).
- **Environment Adaptability**: In local development, testing, or CI where PostgreSQL may not be immediately running as a daemon, the storage layer seamlessly falls back to a dual SQLite + in-memory / JSON vector index with exact cosine similarity computation. This guarantees that all unit tests, integration tests, and local commands execute with 100% zero external dependencies while maintaining identical model schemas and APIs.
- **Alembic Migrations**: Provided for PostgreSQL with `vector` extension creation and table schemas.

## 2. Ingestion & Tokenizer Design
- **Token Awareness**: We use `tiktoken` (cl100k_base or p50k_base) and SentenceTransformer tokenizers.
- **Chunking Strategy**: Recursive token chunker with sentence and markdown header preservation.
- **Hashing**: SHA-256 computed on raw file contents to prevent duplicate uploads.

## 3. Retrieval & Ranking
- **RRF Math**: Reciprocal Rank Fusion uses standard $RRF(d) = \sum_{m} \frac{1}{k + \text{rank}_m(d)}$ with $k=60$. It is mathematically invariant to scale differences between dense cosine scores and sparse BM25 scores.
- **Sparse BM25**: Implemented using `rank_bm25` (Okapi BM25) with custom token normalization, lowercasing, and punctuation stripping that preserves technical tokens like `API_KEY` or `RFC-2616`.
- **Cross-Encoder**: Uses a CrossEncoder pipeline (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) with a fast deterministic fallback for environments without GPU or downloaded weights.

## 4. LangGraph Bounded Workflow
- **Explicit Termination**: The graph utilizes typed state (`AgenticRAGState`) with integer counters `rewrites_count` and `generation_attempts`.
- **Termination Invariants**:
  1. `rewrites_count <= max_rewrites` (default 2)
  2. `generation_attempts <= max_generations` (default 2)
  3. No unconditional cycles.
- **Deterministic Verification**: Citation quotes are verified deterministically without secondary LLM hallucination risk.

## 5. Token Efficiency & Cost Accounting
- Centralized tracking in `TokenUsageTracker` records prompt tokens, completion tokens, model name, provider, latency, and estimated USD cost based on published rates.
