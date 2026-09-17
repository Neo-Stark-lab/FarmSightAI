import pandas as pd
import numpy as np
import yaml
from pathlib import Path

# Load manifest
MANIFEST_PATH = Path(__file__).parent / "feature_manifest.yaml"
with open(MANIFEST_PATH, "r") as f:
    manifest = yaml.safe_load(f)

FEATURE_ORDER = [feat["name"] for feat in manifest["features"]]
CATEGORICAL_MAPPING = {
    "crop": {"rice": 0, "groundnut": 1, "maize": 2, "unknown": -1},
    "crop_stage": {"initial": 0, "vegetative": 1, "reproductive": 2, "maturity": 3, "unknown": -1}
}

def preprocess_features(features_dict: dict) -> pd.DataFrame:
    """
    Converts a feature dictionary to a DataFrame matching the canonical feature order.
    Missing values (None) are converted to np.nan.
    Categorical values are encoded.
    """
    row = {}
    for feature in FEATURE_ORDER:
        val = features_dict.get(feature, None)
        
        # Handle categorical encoding
        if feature in CATEGORICAL_MAPPING:
            if val is None or val == "unknown":
                row[feature] = CATEGORICAL_MAPPING[feature]["unknown"]
            else:
                row[feature] = CATEGORICAL_MAPPING[feature].get(val, CATEGORICAL_MAPPING[feature]["unknown"])
        else:
            row[feature] = float(val) if val is not None else np.nan
            
    return pd.DataFrame([row], columns=FEATURE_ORDER)
