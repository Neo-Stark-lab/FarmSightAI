"""Traceable translation of model contributions; direction is toward HIGH risk."""
from uuid import uuid4


def evidence_from_prediction(prediction, feature_set):
    return [{"id": str(uuid4()), "kind": "model_contribution", "label": item["feature"], "value": item["magnitude"], "unit": feature_set["feature_metadata"][item["feature"]]["unit"], "direction": item["direction"], "source_observation_ids": item["source_observation_ids"], "feature_set_id": feature_set["id"], "created_at": feature_set["reference_time"]} for item in prediction.get("contributions", [])]
