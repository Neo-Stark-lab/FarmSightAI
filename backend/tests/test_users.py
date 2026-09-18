from fastapi.testclient import TestClient
from backend.app.main import app, repo
import pytest

client = TestClient(app)

def test_demo_users_seeded():
    assert "user1" in repo.users
    assert repo.users["user1"]["name"] == "Arjun Kumar"
    assert "user2" in repo.users
    assert "user3" in repo.users

def test_seeded_farms_exist():
    # Verify the predefined farms are in the repo and owned by user1, user2, user3
    farms = list(repo.farms.values())
    assert len(farms) >= 4
    
    user1_farms = [f for f in farms if f.get("owner_user_id") == "user1"]
    assert len(user1_farms) == 2
    assert any(f["name"] == "Cauvery Delta Rice Farm" for f in user1_farms)
    assert any(f["name"] == "Thanjavur Rice Field" for f in user1_farms)

def test_user_farm_listing():
    res = client.get("/api/v1/users/user1/farms")
    assert res.status_code == 200
    data = res.json()
    assert len(data["farms"]) == 2
    assert data["farms"][0]["owner_user_id"] == "user1"

    # User B should only see user B farms
    res2 = client.get("/api/v1/users/user2/farms")
    assert res2.status_code == 200
    assert len(res2.json()["farms"]) == 1

def test_invalid_user_lookup():
    res = client.get("/api/v1/users/nonexistent/farms")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "invalid_user"

def test_create_farm_with_demo_user():
    farm_payload = {
        "name": "New Test Farm",
        "crop": "maize",
        "sowing_date": "2024-06-01",
        "location": {"type": "Point", "coordinates": [78.14, 11.66]},
        "boundary": {"type": "Polygon", "coordinates": [[[78.135,11.655],[78.145,11.655],[78.145,11.665],[78.135,11.665],[78.135,11.655]]]},
        "timezone": "Asia/Kolkata"
    }
    # Test backward compatibility (no header)
    res_no_header = client.post("/api/v1/farms", json=farm_payload, headers={"Idempotency-Key": "test-key-1"})
    assert res_no_header.status_code == 201
    assert "owner_user_id" not in res_no_header.json()["farm"]

    # Test with X-Demo-User-Id
    res_with_header = client.post("/api/v1/farms", json=farm_payload, headers={"Idempotency-Key": "test-key-2", "X-Demo-User-Id": "user1"})
    assert res_with_header.status_code == 201
    assert res_with_header.json()["farm"]["owner_user_id"] == "user1"

    # Test invalid X-Demo-User-Id
    res_invalid_header = client.post("/api/v1/farms", json=farm_payload, headers={"Idempotency-Key": "test-key-3", "X-Demo-User-Id": "baduser"})
    assert res_invalid_header.status_code == 404
    assert res_invalid_header.json()["error"]["code"] == "invalid_user"
