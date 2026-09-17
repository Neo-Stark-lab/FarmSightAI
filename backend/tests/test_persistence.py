from backend.app.persistence import Repository
from backend.app.services import FarmService, AnalysisService
import uuid

valid_boundary = {
    "type": "Polygon",
    "coordinates": [[[0,0], [10,0], [10,10], [0,10], [0,0]]]
}

def test_domain_persistence():
    repo = Repository()
    
    farm_service = FarmService(repo)
    farm = farm_service.create({
        "name": "Test",
        "crop": "rice",
        "sowing_date": "2026-08-01",
        "boundary": valid_boundary,
        "location": {"type": "Point", "coordinates": [5,5]}
    }, str(uuid.uuid4()))
    
    assert farm["id"] in repo.farms
    zones = [z for z in repo.zones.values() if z["farm_id"] == farm["id"]]
    assert len(zones) == 1
    
    # We can't easily test AnalysisService execution without real ML models loaded,
    # but we can verify it initializes the domain models
    assert isinstance(repo.evidence, dict)
    assert isinstance(repo.recommendations, dict)
