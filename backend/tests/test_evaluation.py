"""
Unit and API integration tests for the Offline Evaluation (RAGAS) service.
"""
from app.services.evaluation_service import EvaluationService
from app.schemas.evaluation import EvaluationSample


def test_ragas_metrics_computation():
    question = "What is the token budget?"
    ground_truth = "The token budget is 2500 tokens."
    context = "The context selector limits token budget to 2500 tokens maximum according to system specification."
    answer = "Based on the specification, the token budget is 2500 tokens."

    faithfulness = EvaluationService.compute_faithfulness(answer, [context])
    assert faithfulness >= 0.6

    relevancy = EvaluationService.compute_answer_relevancy(question, answer)
    assert relevancy > 0.5

    precision = EvaluationService.compute_context_precision(ground_truth, [context, "Unrelated text"])
    assert precision > 0.5

    recall = EvaluationService.compute_context_recall(ground_truth, [context])
    assert recall > 0.5


def test_evaluation_api_endpoints(client):
    # Ingest document
    import io
    content = b"The context token budget is strictly constrained to 2500 tokens by default."
    files = {"file": ("budget.txt", io.BytesIO(content), "text/plain")}
    res_upload = client.post("/api/documents/upload", files=files)
    assert res_upload.status_code == 201

    # Trigger Evaluation Run
    payload = {
        "name": "Integration Test Run",
        "configuration_name": "hybrid_with_rerank",
        "custom_samples": [
            {
                "question": "What is the context token budget?",
                "ground_truth": "2500 tokens by default.",
                "reference_contexts": ["The context token budget is strictly constrained to 2500 tokens by default."]
            }
        ]
    }
    run_res = client.post("/api/evaluation/run", json=payload)
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["status"] == "completed"
    assert run_data["avg_faithfulness"] is not None
    assert run_data["avg_answer_relevancy"] is not None
    run_id = run_data["id"]

    # List Runs
    list_res = client.get("/api/evaluation/runs")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Get Single Run
    single_res = client.get(f"/api/evaluation/runs/{run_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == run_id
    assert len(single_res.json()["results"]) == 1
