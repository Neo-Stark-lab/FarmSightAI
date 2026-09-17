"""Small contract adapters for the rules boundary.

Validation of the full API/ML contracts belongs to the surrounding backend.
These helpers retain exactly the fields the rules layer may interpret.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_CROPS = {"rice", "groundnut", "maize"}
VALID_STAGES = {"initial", "vegetative", "reproductive", "maturity", "unknown"}


@dataclass(frozen=True)
class RuleInput:
    prediction: dict[str, Any]
    features: dict[str, Any]
    feature_metadata: dict[str, dict[str, Any]]
    crop: str
    crop_stage: str
    quality_status: str
    evidence_flags: dict[str, bool]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuleInput":
        prediction = payload.get("prediction", payload.get("ml_prediction", {}))
        features = payload.get("features", {})
        if not isinstance(prediction, dict) or not isinstance(features, dict):
            raise ValueError("prediction and features must be objects")
        crop = features.get("crop", payload.get("crop", ""))
        stage = features.get("crop_stage", payload.get("crop_stage", "unknown"))
        if crop not in VALID_CROPS:
            raise ValueError("crop must be rice, groundnut, or maize")
        if stage not in VALID_STAGES:
            raise ValueError("crop_stage is not supported by the ML contract")
        metadata = payload.get("feature_metadata", {})
        flags = payload.get("evidence_flags", {})
        if not isinstance(metadata, dict) or not isinstance(flags, dict):
            raise ValueError("feature_metadata and evidence_flags must be objects")
        return cls(prediction, features, metadata, crop, stage,
                   payload.get("quality_status", "partial"),
                   {key: value for key, value in flags.items() if value is True})
