from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_models_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "default_model" in data
    assert "models" in data
    assert len(data["models"]) >= 4


def test_run_eval_with_mock_default_model() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/run-eval",
        json={
            "cases": [
                {
                    "id": "c1",
                    "question": "What is 5 + 7?",
                    "reference_answer": "12",
                }
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_id"] == "mock-local"
    assert payload["created_at"] is not None
    assert payload["version_info"]["prompt_version"] == "v1"
    assert payload["version_info"]["dataset_version"] == "v1"
    assert payload["summary"]["total_cases"] == 1


def test_eval_gate_fails_when_threshold_is_unrealistic() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/eval-gate",
        json={
            "model_id": "mock-local",
            "prompt_version": "prompt-2026-02-09",
            "dataset_version": "dataset-2026-02-09",
            "cases": [
                {"id": "c1", "question": "What is 5 + 7?", "reference_answer": "12"},
                {"id": "c2", "question": "Capital of France?", "reference_answer": "Paris"},
            ],
            "thresholds": {
                "min_accuracy": 1.0,
                "max_hallucination_risk": 0.0,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["passed"] is False
    assert len(payload["reasons"]) >= 1


def test_eval_gate_passes_with_relaxed_threshold() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/eval-gate",
        json={
            "model_id": "mock-local",
            "cases": [{"id": "c1", "question": "What is 5 + 7?"}],
            "thresholds": {
                "min_accuracy": 0.0,
                "max_hallucination_risk": 1.0,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["passed"] is True


def test_metrics_endpoint() -> None:
    client = TestClient(create_app())
    _ = client.post(
        "/api/v1/run-eval",
        json={
            "model_id": "mock-local",
            "prompt_version": "prompt-v1",
            "dataset_version": "baseline-v1",
            "cases": [{"id": "c1", "question": "What is 5 + 7?", "reference_answer": "12"}],
        },
    )
    response = client.get("/api/v1/metrics?model_id=mock-local&limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] >= 1
    assert "summary" in payload
    assert "items" in payload


def test_model_comparison_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/model-comparison?limit=20")
    assert response.status_code == 200
    payload = response.json()
    assert "total_models" in payload
    assert "models" in payload


def test_benchmarks_list() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    payload = response.json()
    assert "benchmarks" in payload
    names = [b["name"] for b in payload["benchmarks"]]
    assert "mmlu_sample" in names
    assert "truthfulqa_sample" in names
    assert "reasoning_sample" in names
    assert "coding_sample" in names
    assert all(b["total_cases"] == 10 for b in payload["benchmarks"])


def test_run_benchmark_with_mock() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/benchmarks/run",
        json={"benchmark": "mmlu_sample", "model_id": "mock-local"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["benchmark"] == "mmlu_sample"
    assert payload["run"]["model_id"] == "mock-local"
    assert payload["run"]["summary"]["total_cases"] == 10


def test_tasks_list() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    payload = response.json()
    assert "tasks" in payload
    task_ids = [t["id"] for t in payload["tasks"]]
    assert "reasoning" in task_ids
    assert "coding" in task_ids
    assert "knowledge" in task_ids
    assert "creative" in task_ids
    assert "analysis" in task_ids


def test_task_recommend() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/tasks/reasoning/recommend")
    assert response.status_code == 200
    payload = response.json()
    assert payload["task"]["id"] == "reasoning"
    assert payload["task"]["benchmark"] == "reasoning_sample"
    assert "available_models" in payload


def test_run_task_with_mock() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/tasks/run",
        json={"task_id": "knowledge", "model_id": "mock-local"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["task"]["id"] == "knowledge"
    assert payload["benchmark_run"]["model_id"] == "mock-local"
    assert payload["benchmark_run"]["summary"]["total_cases"] == 10


def test_openrouter_models_listed() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    payload = response.json()
    model_ids = [m["id"] for m in payload["models"]]
    assert "openrouter/meta-llama/llama-3.3-70b-instruct" in model_ids
    assert "openrouter/mistralai/mistral-large-2" in model_ids
    assert "openrouter/google/gemini-2.0-flash" in model_ids
