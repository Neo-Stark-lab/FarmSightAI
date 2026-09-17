import pytest
from backend.app.services import FarmService, DomainError
from backend.app.persistence import Repository

valid_polygon = {
    "type": "Polygon",
    "coordinates": [[[0,0], [10,0], [10,10], [0,10], [0,0]]]
}

valid_multipolygon = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[0,0], [10,0], [10,10], [0,10], [0,0]]],
        [[[20,20], [30,20], [30,30], [20,30], [20,20]]]
    ]
}

invalid_self_intersecting = {
    "type": "Polygon",
    "coordinates": [[[0,0], [10,10], [10,0], [0,10], [0,0]]]
}

invalid_bounds = {
    "type": "Polygon",
    "coordinates": [[[0,0], [200,0], [10,10], [0,10], [0,0]]]
}

valid_point_inside = {"type": "Point", "coordinates": [5, 5]}
valid_point_inside_multi = {"type": "Point", "coordinates": [25, 25]}
invalid_point_outside = {"type": "Point", "coordinates": [15, 15]}

def _farm_payload(boundary, location):
    return {
        "name": "Test Farm",
        "crop": "rice",
        "sowing_date": "2026-08-01",
        "boundary": boundary,
        "location": location,
    }

def test_geometry_validation():
    repo = Repository()
    service = FarmService(repo)
    
    # Valid Polygon
    farm = service.create(_farm_payload(valid_polygon, valid_point_inside), "k1")
    assert farm["id"] is not None
    
    # Valid MultiPolygon
    farm2 = service.create(_farm_payload(valid_multipolygon, valid_point_inside_multi), "k2")
    assert farm2["id"] is not None
    
    # Invalid Location Outside Boundary
    with pytest.raises(DomainError) as exc:
        service.create(_farm_payload(valid_polygon, invalid_point_outside), "k3")
    assert "location is outside boundary" in exc.value.message

    # Self-intersecting polygon
    with pytest.raises(DomainError) as exc:
        service.create(_farm_payload(invalid_self_intersecting, {"type":"Point","coordinates":[5,5]}), "k4")
    assert "self-intersects" in exc.value.message

    # Invalid bounds
    with pytest.raises(DomainError) as exc:
        service.create(_farm_payload(invalid_bounds, {"type":"Point","coordinates":[5,5]}), "k5")
    assert "out of bounds" in exc.value.message
