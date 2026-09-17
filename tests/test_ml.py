import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from ml.dataset import generate_synthetic_dataset
from ml.preprocessing import preprocess_features, FEATURE_ORDER
from ml.models import WaterStressModel
from ml.explainability import SHAPExplainer
from ml.inference import score_water_stress

@pytest.fixture
def synthetic_data():
    return generate_synthetic_dataset(num_samples=100)

@pytest.fixture
def trained_model(synthetic_data):
    model = WaterStressModel()
    model.train(synthetic_data)
    return model

@pytest.fixture
def explainer(trained_model):
    return SHAPExplainer(trained_model)

def test_feature_manifest_validation():
    manifest_path = Path(__file__).parent.parent / "ml" / "feature_manifest.yaml"
    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)
    features = [f["name"] for f in manifest["features"]]
    assert len(features) == len(FEATURE_ORDER)
    assert features == FEATURE_ORDER

def test_preprocessing_order_and_encoding():
    raw_features = {
        "crop": "rice",
        "crop_stage": "vegetative",
        "ndvi_current": 0.62,
        "ndvi_7d_change": -0.03
    }
    df = preprocess_features(raw_features)
    assert list(df.columns) == FEATURE_ORDER
    # rice -> 0
    assert df["crop"].iloc[0] == 0
    # vegetative -> 1
    assert df["crop_stage"].iloc[0] == 1
    assert df["ndvi_current"].iloc[0] == 0.62
    # Missing features should be NaN
    assert pd.isna(df["soil_moisture"].iloc[0])

def test_unknown_crop_handling():
    raw_features = {"crop": "unknown", "crop_stage": "unknown"}
    df = preprocess_features(raw_features)
    assert df["crop"].iloc[0] == -1
    assert df["crop_stage"].iloc[0] == -1

def test_missing_feature_handling():
    raw_features = {"ndvi_current": None}
    df = preprocess_features(raw_features)
    assert pd.isna(df["ndvi_current"].iloc[0])

def test_model_training_and_saving(synthetic_data, tmp_path):
    model = WaterStressModel()
    model.train(synthetic_data)
    assert model.is_trained
    
    import ml.models
    original_path = ml.models.MODEL_PATH
    ml.models.MODEL_PATH = tmp_path / "test_model.json"
    
    model.save()
    assert ml.models.MODEL_PATH.exists()
    
    new_model = WaterStressModel()
    new_model.load()
    assert new_model.is_trained
    
    ml.models.MODEL_PATH = original_path

def test_deterministic_inference(trained_model):
    raw_features = {"crop": "rice", "ndvi_current": 0.5, "rainfall_anomaly": -10}
    df = preprocess_features(raw_features)
    
    pred1 = trained_model.predict_proba(df)[0]
    pred2 = trained_model.predict_proba(df)[0]
    
    assert np.allclose(pred1, pred2)

def test_prediction_contract(trained_model, explainer):
    request = {
        "schema_version": "1.0",
        "request_id": "req-123",
        "features": {
            "crop": "maize",
            "ndvi_current": 0.4
        },
        "feature_metadata": {
            "ndvi_current": {
                "source_observation_ids": ["obs-1"]
            },
            "soil_moisture": {
                "missing_reason": "not_available"
            }
        },
        "quality_status": "partial"
    }
    
    response = score_water_stress(request, trained_model, explainer)
    
    assert response["schema_version"] == "1.0"
    assert response["request_id"] == "req-123"
    
    pred = response["prediction"]
    assert pred["prediction_type"] == "water_stress_risk"
    assert pred["risk_level"] in ["low", "moderate", "high", "unknown"]
    assert pred["status"] == "valid"
    assert "soil_moisture:not_available" in pred["input_quality_flags"]
    assert pred["confidence"]["level"] == "medium"
    
    contribs = pred["contributions"]
    assert len(contribs) > 0
    for c in contribs:
        assert "feature" in c
        assert "direction" in c
        assert "magnitude" in c
        assert "method" in c
        assert "source_observation_ids" in c
        if c["feature"] == "ndvi_current":
            assert c["source_observation_ids"] == ["obs-1"]

def test_insufficient_data_behavior(trained_model):
    request = {
        "schema_version": "1.0",
        "request_id": "req-999",
        "features": {},
        "quality_status": "insufficient_data"
    }
    
    response = score_water_stress(request, trained_model)
    pred = response["prediction"]
    
    assert pred["status"] == "insufficient_data"
    assert pred["risk_level"] == "unknown"
    assert pred["probability"] is None
    assert pred["confidence"]["level"] == "low"
    assert len(pred["contributions"]) == 0
