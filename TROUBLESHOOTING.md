# Troubleshooting Guide: Agentic RAG Platform

## 1. Common Issues and Resolutions

### Issue 1: `pgvector` extension missing in PostgreSQL
- **Symptom**: `OperationalError: type "vector" does not exist`.
- **Cause**: Standard PostgreSQL image used without the pgvector compiled extension.
- **Resolution**:
  Use the official `pgvector/pgvector:pg16` image specified in `docker-compose.yml`, or run:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
  In local testing mode, the system automatically detects SQLite and falls back to a portable JSON/in-process vector type without any schema errors.

### Issue 2: Duplicate Document Rejected (409 Conflict)
- **Symptom**: `POST /api/documents/upload` returns HTTP status 409.
- **Cause**: SHA-256 collision detection identified an identical file already indexed in the knowledge base.
- **Resolution**:
  This is expected system behavior to prevent duplicate chunks from diluting reciprocal rank fusion. To re-index an updated version, delete the existing document via `DELETE /api/documents/{id}` and re-upload.

### Issue 3: Low Retrieval Quality / Abstention Response
- **Symptom**: Assistant replies: *"I investigated the uploaded knowledge base but could not find sufficient grounded evidence..."* with `confidence_label: "insufficient_evidence"`.
- **Cause**: The cross-encoder relevance score fell below `MIN_RELEVANCE_SCORE_THRESHOLD` (default: 0.35) even after 2 bounded query rewrites.
- **Resolution**:
  1. Inspect the execution trace at `/traces/{execution_id}` to view BM25 candidates, dense candidates, and reranker scores.
  2. Verify that uploaded documents cover the query topic.
  3. Ensure terms in query are not overly ambiguous.

### Issue 4: Missing or Corrupt Document Text
- **Symptom**: `DocumentIngestionError: PDF document contains no extractable text`.
- **Cause**: The PDF file consists entirely of scanned raster images without an embedded OCR text layer.
- **Resolution**:
  Run an OCR pre-processing step (such as `tesseract` or Adobe OCR) to embed the text layer before uploading.

### Issue 5: Port Conflicts (5432, 8000, 3000)
- **Symptom**: `bind: address already in use`.
- **Resolution**:
  Check active ports using `netstat -ano | findstr 8000` or change port mapping in `docker-compose.yml` (e.g. `8001:8000` or `3001:3000`).
