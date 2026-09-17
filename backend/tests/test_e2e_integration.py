import pytest
from datetime import datetime, timezone
from backend.app.persistence import Repository
from backend.app.services import FarmService, AnalysisService
from data.pipeline import Observation
import os
from unittest.mock import patch

from ml.dataset import generate_synthetic_dataset
import ml.inference

@pytest.fixture(autouse=True)
def setup_model():
    if not ml.inference._model_instance.is_trained:
        df = generate_synthetic_dataset(100)
        ml.inference._model_instance.train(df)
        
@pytest.fixture
def repo():
    return Repository()

@pytest.fixture
def farm_service(repo):
    return FarmService(repo)

@pytest.fixture
def analysis_service(repo):
    os.environ["PROVIDER_MODE"] = "fixture"
    # We will use fixture mode but inject a complete dataset or partial dataset to test the ML gating.
    # We can patch DataPipeline or just use FixtureProvider
    return AnalysisService(repo)

def test_insufficient_data_ml_gating(repo, farm_service, analysis_service):
    # Test that when there is insufficient data, ML is gated, probability is None, and SHAP is empty.
    payload = {
        "name": "Test Farm",
        "location": {"type": "Point", "coordinates": [0, 0]},
        "boundary": {"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]},
        "crop": "rice",
        "sowing_date": "2026-08-01",
        "timezone": "UTC"
    }
    farm = farm_service.create(payload, "key-insufficient")
    
    # We pass empty observations to FixtureProvider
    with patch("backend.app.services.FixtureProvider.fetch", return_value=[]):
        run = analysis_service.submit(farm["id"], {"reference_time": datetime.now(timezone.utc).isoformat()}, "key-run")
        analysis_service.execute(run["id"])
        
    res = list(repo.results.values())[0]
    ev = repo.evidence[res["evidence_id"]]
    rec = repo.recommendations[res["recommendation_id"]]
    
    prediction = ev["prediction"]
    assert prediction["status"] == "insufficient_data"
    assert prediction["probability"] is None
    assert prediction["risk_level"] == "unknown"
    assert len(prediction["contributions"]) == 0
    assert prediction["confidence"]["level"] == "low"
    
    # Recommendation should also handle this gracefully
    assert any("A valid water-stress prediction is unavailable" in str(x) for x in rec["recommendation"]["limitations"])
    assert rec["recommendation"]["status"] == "not_available"


def test_valid_prediction_and_shap(repo, farm_service, analysis_service):
    # Mocking complete valid observations to trigger a full prediction
    obs = []
    t = datetime.now(timezone.utc)
    # Give all required features to avoid insufficient data
    # (Just passing raw values to pipeline)
    # The fixture provider just returns a list of Observations. 
    # Let's provide basic valid observations to ensure status="valid"
    source = {"provider": "fixture", "dataset": "test"}
    obs.append(Observation("rainfall", 50, "mm", t, source, t, "point"))
    obs.append(Observation("temperature", 25, "degC", t, source, t, "point"))
    obs.append(Observation("soil_moisture", 0.3, "m3_m3", t, source, t, "polygon_mean"))
    
    # We just need to make sure 'insufficient_data' is not triggered.
    # For full prediction, it needs all 13 numeric features!
    # Instead of mocking all 13 perfectly, we can mock preprocess_features?
    # No, we test E2E. We'll patch `DataPipeline.build` to return a fully populated feature set.
    
    payload = {
        "name": "Test Farm Complete",
        "location": {"type": "Point", "coordinates": [0, 0]},
        "boundary": {"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]},
        "crop": "rice",
        "sowing_date": "2026-08-01",
        "timezone": "UTC"
    }
    farm = farm_service.create(payload, "key-complete")
    
    mock_features = {
        "schema_version": "1.0",
        "request_id": "test_req",
        "features": {
            "ndvi_current": 0.5, "ndvi_7d_change": 0.0, "ndvi_30d_change": 0.0,
            "ndmi_current": 0.3, "ndmi_change": 0.0,
            "rainfall_7d": 10.0, "rainfall_30d": 50.0, "rainfall_anomaly": 0.0,
            "temperature_mean": 25.0, "temperature_anomaly": 0.0,
            "soil_moisture": 0.3, "soil_moisture_change": 0.0,
            "historical_deviation": 0.0, "neighboring_deviation": 0.0,
            "crop": "rice", "crop_stage": "vegetative"
        },
        "feature_metadata": {k: {"missing_reason": None, "freshness": {"status": "fresh"}} for k in [
            "ndvi_current", "ndvi_7d_change", "ndvi_30d_change", "ndmi_current", "ndmi_change",
            "rainfall_7d", "rainfall_30d", "rainfall_anomaly", "temperature_mean", "temperature_anomaly",
            "soil_moisture", "soil_moisture_change", "historical_deviation", "neighboring_deviation",
            "crop", "crop_stage"
        ]},
        "quality_status": "complete"
    }
    
    with patch("backend.app.services.DataPipeline.build", return_value=mock_features):
        run = analysis_service.submit(farm["id"], {"reference_time": datetime.now(timezone.utc).isoformat()}, "key-run-2")
        analysis_service.execute(run["id"])
        
    res = list(repo.results.values())[-1]
    ev = repo.evidence[res["evidence_id"]]
    prediction = ev["prediction"]
    
    # ML gating passed
    if prediction["status"] == "failed":
        print(f"Prediction failed. Error: {prediction['confidence']['basis']}")
    assert prediction["status"] == "valid"
    assert prediction["probability"] is not None
    assert prediction["risk_level"] in ["low", "moderate", "high"]
    
    # SHAP only for valid predictions, and HIGH-risk direction
    assert len(prediction["contributions"]) > 0
    for contrib in prediction["contributions"]:
        assert contrib["direction"] in ["increases_risk", "decreases_risk", "neutral"]
        
    # Confidence vs probability separation
    assert "level" in prediction["confidence"]
    assert prediction["confidence"]["level"] == "high" # since quality_status is complete
    
    # API E2E
    rec = repo.recommendations[res["recommendation_id"]]
    assert rec["recommendation"]["status"] == "active"
