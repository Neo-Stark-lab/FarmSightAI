from fastapi.testclient import TestClient
from backend.app.main import app

client=TestClient(app)
payload={"name":"North field","location":{"type":"Point","coordinates":[80.27,13.08]},"boundary":{"type":"Polygon","coordinates":[[[80.27,13.08],[80.28,13.08],[80.28,13.09],[80.27,13.08]]]},"crop":"rice","sowing_date":"2026-08-01","timezone":"Asia/Kolkata"}

def test_health_and_contract_flow():
    assert client.get("/health").status_code==200
    farm=client.post("/api/v1/farms",json=payload,headers={"Idempotency-Key":"farm"}); assert farm.status_code==201
    ident=farm.json()["farm"]["id"]
    assert client.post("/api/v1/farms",json=payload,headers={"Idempotency-Key":"farm"}).json()["farm"]["id"]==ident
    run=client.post(f"/api/v1/farms/{ident}/analyze",json={},headers={"Idempotency-Key":"run"}); assert run.status_code==202
    run_id=run.json()["analysis_run"]["id"]; assert client.get(f"/api/v1/analysis-runs/{run_id}").status_code==200
    zones=client.get(f"/api/v1/farms/{ident}/zones").json()["zones"]; zone_id=zones[0]["zone"]["id"]
    assert client.get(f"/api/v1/zones/{zone_id}/evidence").status_code==200
    assert client.get(f"/api/v1/zones/{zone_id}/recommendation").status_code==200

def test_invalid_crop_and_geometry():
    assert client.post("/api/v1/farms",json={**payload,"crop":"cotton"}).status_code==422
    assert client.post("/api/v1/farms",json={**payload,"boundary":{"type":"Point","coordinates":[1,2]}}).status_code==422
