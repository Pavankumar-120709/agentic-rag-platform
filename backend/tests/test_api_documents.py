"""
API integration tests for Document Upload, Listing, Status, and Deletion endpoints.
"""
import io


def test_document_lifecycle(client):
    content = b"LangGraph enables stateful agent orchestration. Reciprocal Rank Fusion combines sparse and dense search."
    files = {"file": ("orchestration.txt", io.BytesIO(content), "text/plain")}

    # 1. Upload
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201
    doc_data = res.json()
    assert doc_data["filename"] == "orchestration.txt"
    assert doc_data["status"] == "indexed"
    assert doc_data["total_chunks"] >= 1
    doc_id = doc_data["id"]

    # 2. Duplicate Detection (409 Conflict)
    files_dup = {"file": ("orchestration_copy.txt", io.BytesIO(content), "text/plain")}
    dup_res = client.post("/api/documents/upload", files=files_dup)
    assert dup_res.status_code == 409

    # 3. List Documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)

    # 4. Get Document Detail with Chunks
    detail_res = client.get(f"/api/documents/{doc_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["chunks"]) >= 1

    # 5. Get Document Status
    status_res = client.get(f"/api/documents/{doc_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "indexed"

    # 6. Delete Document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 204

    # 7. Verify Document Gone
    get_after = client.get(f"/api/documents/{doc_id}")
    assert get_after.status_code == 404
