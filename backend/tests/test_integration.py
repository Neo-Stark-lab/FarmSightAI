from fastapi.testclient import TestClient
from backend.app.main import app, repo
from backend.app.persistence.repository import InMemoryRepository
from backend.app.services import FarmService, AnalysisService
from data.pipeline import DataPipeline
from data.providers import ProviderError
from ml.inference import ModelError

client = TestClient(app)
boundary = {"type": "Polygon", "coordinates": [[[80.27, 13.08], [80.28, 13.08], [80.28, 13.09], [80.27, 13.08]]]}
farm_payload = {"name": "North field", "location": {"type": "Point", "coordinates": [80.275, 13.085]}, "boundary": boundary, "crop": "rice", "sowing_date": "2026-08-01", "timezone": "Asia/Kolkata"}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_complete_fixture_flow_and_idempotency():
    first = client.post("/api/v1/farms", json=farm_payload, headers={"Idempotency-Key": "farm-1"})
    assert first.status_code == 201
    second = client.post("/api/v1/farms", json=farm_payload, headers={"Idempotency-Key": "farm-1"})
    farm_id = first.json()["farm"]["id"]
    assert second.json()["farm"]["id"] == farm_id
    submitted = client.post(f"/api/v1/farms/{farm_id}/analyze", json={}, headers={"Idempotency-Key": "analysis-1"})
    assert submitted.status_code == 202 and submitted.json()["analysis_run"]["status"] == "queued"
    run_id = submitted.json()["analysis_run"]["id"]
    assert client.get(f"/api/v1/analysis-runs/{run_id}").json()["analysis_run"]["status"] == "partial"
    zones = client.get(f"/api/v1/farms/{farm_id}/zones").json()["zones"]
    assert len(zones) == 1 and zones[0]["latest_prediction"]["risk_level"] in {"low", "moderate", "high"}
    zone_id = zones[0]["zone"]["id"]
    evidence = client.get(f"/api/v1/zones/{zone_id}/evidence").json()
    assert evidence["data_freshness"]["items"] and any(item["value"] is None for item in evidence["evidence"])
    assert client.get(f"/api/v1/zones/{zone_id}/recommendation").json()["recommendation"]["action"]


def test_invalid_crop_and_geometry_are_rejected():
    invalid_crop = client.post("/api/v1/farms", json={**farm_payload, "crop": "cotton"})
    invalid_geometry = client.post("/api/v1/farms", json={**farm_payload, "boundary": {"type": "Point", "coordinates": [1, 2]}})
    assert invalid_crop.status_code == invalid_geometry.status_code == 422


def test_provider_and_model_failures_produce_failed_runs():
    class BrokenProvider:
        def observations(self, _): raise ProviderError("unavailable")
    class BrokenModel:
        def score(self, _): raise ModelError("unavailable")
    for pipeline, model in ((DataPipeline(BrokenProvider()), None), (DataPipeline(), BrokenModel())):
        storage = InMemoryRepository()
        farm = FarmService(storage).create(farm_payload)
        run, _ = AnalysisService(storage, pipeline=pipeline, inference=model).submit(farm["id"], {})
        assert run["status"] == "failed"
