import datetime
from ml.preprocessing import preprocess_features
from ml.models import WaterStressModel
from ml.explainability import SHAPExplainer

# Load model globally (assuming it's already trained/saved in production)
_model_instance = WaterStressModel()
try:
    _model_instance.load()
except FileNotFoundError:
    pass # Tests will handle training

RISK_MAPPING = {0: "low", 1: "moderate", 2: "high"}

def evaluate_confidence(request: dict) -> dict:
    """
    Evaluates model/data confidence based on quality_status and missing data.
    """
    quality = request.get("quality_status", "complete")
    flags = []
    basis = []
    
    metadata = request.get("feature_metadata", {})
    for feat, meta in metadata.items():
        if meta.get("missing_reason"):
            reason = meta["missing_reason"]
            flags.append(f"{feat}:{reason}")
            basis.append(f"{feat} unavailable: {reason}")
            
        freshness = meta.get("freshness", {})
        if freshness.get("status") == "stale":
            flags.append(f"{feat}:stale")
            basis.append(f"{feat} is stale")

    if quality == "insufficient_data":
        level = "low"
        basis.insert(0, "Insufficient data for reliable scoring")
    elif quality == "partial" or len(flags) > 0:
        level = "medium"
        if not basis:
            basis.append("Partial data quality")
    else:
        level = "high"
        basis.append("Complete and fresh data")

    return {
        "level": level,
        "score": None, # Uncalibrated for now
        "basis": basis
    }, flags

def score_water_stress(request: dict, model=None, explainer=None) -> dict:
    """
    Implements the ml-contract.md WaterStressScoringRequest -> WaterStressScoringResponse.
    """
    # Schema validation
    if request.get("schema_version") != "1.0":
        return _build_error_response(request, "failed", "Unsupported schema version")

    if model is None:
        model = _model_instance

    if not model.is_trained:
        return _build_error_response(request, "failed", "Model not trained")

    confidence, quality_flags = evaluate_confidence(request)
    
    if request.get("quality_status") == "insufficient_data":
        return {
            "schema_version": "1.0",
            "request_id": request.get("request_id"),
            "prediction": {
                "prediction_type": "water_stress_risk",
                "risk_level": "unknown",
                "probability": None,
                "confidence": confidence,
                "model_name": "water-stress-xgboost",
                "model_version": "1.0.0",
                "feature_schema_version": "1.0",
                "predicted_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "insufficient_data",
                "input_quality_flags": quality_flags,
                "contributions": []
            }
        }

    try:
        # Preprocess features
        features_dict = request.get("features", {})
        X = preprocess_features(features_dict)
        
        # Predict
        probs = model.predict_proba(X)[0]
        pred_class = int(model.predict(X)[0])
        risk_level = RISK_MAPPING.get(pred_class, "unknown")
        probability = float(probs[pred_class])
        
        # Explanations
        if explainer is None:
            explainer = SHAPExplainer(model)
        
        raw_contributions = explainer.explain_instance(X, pred_class)
        
        # Map source observations
        metadata = request.get("feature_metadata", {})
        contributions = []
        for contrib in raw_contributions:
            feat_name = contrib["feature"]
            source_ids = metadata.get(feat_name, {}).get("source_observation_ids", [])
            contrib["source_observation_ids"] = source_ids
            contributions.append(contrib)
            
        return {
            "schema_version": "1.0",
            "request_id": request.get("request_id"),
            "prediction": {
                "prediction_type": "water_stress_risk",
                "risk_level": risk_level,
                "probability": probability,
                "confidence": confidence,
                "model_name": "water-stress-xgboost",
                "model_version": "1.0.0",
                "feature_schema_version": "1.0",
                "predicted_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "valid",
                "input_quality_flags": quality_flags,
                "contributions": contributions
            }
        }
    except Exception as e:
        return _build_error_response(request, "failed", str(e))

def _build_error_response(request: dict, status: str, reason: str) -> dict:
    return {
        "schema_version": "1.0",
        "request_id": request.get("request_id"),
        "prediction": {
            "prediction_type": "water_stress_risk",
            "risk_level": "unknown",
            "probability": None,
            "confidence": {"level": "low", "score": None, "basis": [reason]},
            "model_name": "water-stress-xgboost",
            "model_version": "1.0.0",
            "feature_schema_version": "1.0",
            "predicted_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": status,
            "input_quality_flags": [],
            "contributions": []
        }
    }
