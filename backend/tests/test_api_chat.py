"""
API integration tests for Chat, Conversations, and Query Execution Traces.
"""
import io


def test_chat_flow_and_tracing(client):
    # Ingest document first
    content = b"The platform features automated query rewriting and deterministic citation verification. All citations map directly to source chunks."
    files = {"file": ("features.txt", io.BytesIO(content), "text/plain")}
    client.post("/api/documents/upload", files=files)

    # 1. Send Chat Request
    payload = {
        "query": "What does the platform feature regarding citations?",
        "retrieval_method": "hybrid"
    }
    chat_res = client.post("/api/chat", json=payload)
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "conversation_id" in data
    assert "execution_id" in data
    assert "trace_id" in data
    assert data["message"]["role"] == "assistant"
    assert data["answer_response"]["confidence_label"] == "supported"
    assert len(data["answer_response"]["citations"]) >= 1

    conv_id = data["conversation_id"]
    exec_id = data["execution_id"]

    # 2. Verify Conversation Retrieval
    conv_res = client.get(f"/api/conversations/{conv_id}")
    assert conv_res.status_code == 200
    assert len(conv_res.json()["messages"]) == 2  # user and assistant

    # 3. Verify Query Execution Trace
    trace_res = client.get(f"/api/query-executions/{exec_id}")
    assert trace_res.status_code == 200
    trace_data = trace_res.json()
    assert trace_data["trace_id"] == data["trace_id"]
    assert trace_data["fused_count"] >= 1
    assert len(trace_data["retrieval_results"]) >= 1

    # 4. Check Metrics Endpoint
    metrics_res = client.get("/api/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_queries"] >= 1
    assert metrics["total_documents"] >= 1
