# API Documentation: Agentic RAG Platform

## Base URL
- Production: `http://localhost:8000/api`
- OpenAPI Specification: `http://localhost:8000/api/openapi.json`
- Interactive Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## 1. Document Management Endpoints

### 1.1 Ingest Document
- **Endpoint**: `POST /api/documents/upload`
- **Content-Type**: `multipart/form-data`
- **Request Fields**:
  - `file`: Binary file (PDF, TXT, or Markdown up to 25MB).
  - `chunk_size` *(optional)*: Target token chunk size (default: 512).
  - `chunk_overlap` *(optional)*: Target token overlap (default: 64).
- **Responses**:
  - `201 Created`: Document successfully indexed.
  - `400 Bad Request`: File is empty or malformed.
  - `409 Conflict`: Duplicate file (SHA-256 collision detected).

### 1.2 List Documents
- **Endpoint**: `GET /api/documents`
- **Response**: Array of document objects with `id`, `filename`, `file_type`, `file_size_bytes`, `status`, `total_chunks`, and `total_tokens`.

### 1.3 Get Document Detail
- **Endpoint**: `GET /api/documents/{document_id}`
- **Response**: Document metadata and all child chunk records including `original_text`, `chunk_index`, and `page_number`.

### 1.4 Get Ingestion Status
- **Endpoint**: `GET /api/documents/{document_id}/status`
- **Response**: Ingestion status (`processing`, `indexed`, `failed`), error message (if any), and chunk counts.

### 1.5 Delete Document
- **Endpoint**: `DELETE /api/documents/{document_id}`
- **Response**: `204 No Content` (cascades deletion across chunks and resynchronizes BM25 index).

---

## 2. Conversational Agentic Chat Endpoints

### 2.1 Execute Chat Query
- **Endpoint**: `POST /api/chat`
- **Request Body**:
```json
{
  "query": "What are the context token limits and how are citations validated?",
  "conversation_id": "optional-uuid-string",
  "retrieval_method": "hybrid",
  "max_rewrites": 2,
  "context_token_budget": 2500
}
```
- **Response Body**:
```json
{
  "conversation_id": "fea77a29-c603-42ce-8470-8be0276e1fc3",
  "message": {
    "id": "msg-123",
    "conversation_id": "fea77a29-c603-42ce-8470-8be0276e1fc3",
    "role": "assistant",
    "content": "Based on system_spec.txt, the context token budget is strictly constrained to 2500 tokens.",
    "citations": [
      {
        "document_id": "doc-456",
        "filename": "system_spec.txt",
        "chunk_id": "chunk-789",
        "page_number": 1,
        "quoted_text": "the context token budget is strictly constrained to 2500 tokens"
      }
    ],
    "confidence_label": "supported",
    "token_count": 45,
    "execution_id": "exec-999",
    "created_at": "2026-11-16T22:00:00Z"
  },
  "answer_response": {
    "answer": "...",
    "citations": [...],
    "confidence_label": "supported",
    "evidence_summary": "Derived from system_spec.txt chunk chunk-789.",
    "warnings": []
  },
  "execution_id": "exec-999",
  "trace_id": "trace-a1b2c3d4",
  "latency_ms": 32.5,
  "token_usage": {
    "prompt_tokens": 320,
    "completion_tokens": 64,
    "total_tokens": 384,
    "estimated_cost_usd": 0.000086
  }
}
```

### 2.2 List Conversations
- **Endpoint**: `GET /api/conversations`
- **Response**: Array of conversations ordered by most recent update.

### 2.3 Get Conversation History
- **Endpoint**: `GET /api/conversations/{conversation_id}`
- **Response**: Conversation detail with ordered array of `messages`.

### 2.4 Delete Conversation
- **Endpoint**: `DELETE /api/conversations/{conversation_id}`
- **Response**: `204 No Content`.

---

## 3. Evaluation & RAGAS Benchmark Endpoints

### 3.1 Run Offline Evaluation Benchmark
- **Endpoint**: `POST /api/evaluation/run`
- **Request Body**:
```json
{
  "name": "Production Benchmark Suite",
  "configuration_name": "hybrid_with_rerank",
  "custom_samples": [
    {
      "question": "What is the token budget?",
      "ground_truth": "2500 tokens.",
      "reference_contexts": ["Context limits tokens to 2500 tokens."]
    }
  ]
}
```
- **Response**: `EvaluationRunRead` with aggregated `avg_faithfulness`, `avg_answer_relevancy`, `avg_context_precision`, `avg_context_recall`, and execution latency.

### 3.2 List Evaluation Runs
- **Endpoint**: `GET /api/evaluation/runs`
- **Response**: Array of historical benchmark runs.

### 3.3 Get Evaluation Run Detail
- **Endpoint**: `GET /api/evaluation/runs/{run_id}`
- **Response**: Evaluation run record with all per-sample scores and contexts.

---

## 4. Observability & Telemetry Endpoints

### 4.1 System Health
- **Endpoint**: `GET /api/health`
- **Response**: Status of database, embedding model, reranker, and LLM provider.

### 4.2 System Metrics
- **Endpoint**: `GET /api/metrics`
- **Response**: Aggregated counts of documents, chunks, queries, average latency, tokens consumed, and estimated cost.

### 4.3 Query Execution Trace Inspector
- **Endpoint**: `GET /api/query-executions/{execution_id}`
- **Response**: Complete step-by-step lineage of query execution: original query, rewritten queries, BM25 counts, dense counts, fusion RRF scores, cross-encoder scores, selected context chunks, and validation status.
