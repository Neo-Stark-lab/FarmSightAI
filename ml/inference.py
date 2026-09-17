"""ML adapter boundary.

No Lap 3 artifact is present in this checkout. The fixture adapter is explicitly
demo-only and must be replaced by the existing artifact loader for live use.
"""


class ModelError(RuntimeError):
    pass


class WaterStressInference:
    def score(self, feature_set):
        features = feature_set["features"]
        required = ("ndvi_current", "ndmi_current", "rainfall_7d", "temperature_mean")
        if any(features.get(key) is None for key in required):
            return {"prediction_type": "water_stress_risk", "risk_level": "unknown", "probability": None, "confidence": {"level": "low", "score": None, "basis": ["required observations unavailable"]}, "model_name": "fixture-adapter", "model_version": "demo-only", "feature_schema_version": "1.0", "predicted_at": feature_set["reference_time"], "status": "insufficient_data", "input_quality_flags": ["insufficient_data"], "contributions": []}
        score = sum((.25 if features["ndmi_change"] < 0 else 0, .25 if features["rainfall_anomaly"] < 0 else 0, .2 if features["temperature_anomaly"] > 0 else 0, .2 if features["ndvi_30d_change"] < 0 else 0))
        risk = "high" if score >= .7 else "moderate" if score >= .35 else "low"
        keys = ("ndmi_change", "rainfall_anomaly", "temperature_anomaly", "ndvi_30d_change")
        contributions = [{"feature": key, "direction": "increases_risk", "magnitude": abs(features[key]), "method": "fixture_adapter", "source_observation_ids": feature_set["feature_metadata"][key]["source_observation_ids"]} for key in keys if features[key] is not None]
        return {"prediction_type": "water_stress_risk", "risk_level": risk, "probability": None, "confidence": {"level": "low", "score": None, "basis": ["DEMO DATA — fixture analysis", "soil moisture unavailable", "demo adapter is not validated ML"]}, "model_name": "fixture-adapter", "model_version": "demo-only", "feature_schema_version": "1.0", "predicted_at": feature_set["reference_time"], "status": "valid", "input_quality_flags": ["soil_moisture:not_available", "demo_fixture"], "contributions": contributions}
