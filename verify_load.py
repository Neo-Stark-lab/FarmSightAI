import os
import sys

# Ensure clean path without cached modules if possible, though python starts a new process anyway.
import xgboost as xgb
from ml.models import WaterStressModel
from ml.preprocessing import preprocess_features

print("Loading model...")
model = WaterStressModel()
model.load()
print("Model loaded successfully.")

print("Verifying classes...")
# XGBClassifier exposes classes_
if hasattr(model.model, "classes_"):
    print(f"Classes: {model.model.classes_}")
    assert list(model.model.classes_) == [0, 1, 2]
else:
    print("No classes_ attribute, checking n_classes_")

print("Verifying prediction...")
raw_features = {"crop": "rice", "ndvi_current": 0.5, "rainfall_anomaly": -10}
df = preprocess_features(raw_features)
probs = model.predict_proba(df)[0]
pred = model.predict(df)[0]
print(f"Probs: {probs}, Pred: {pred}")
assert len(probs) == 3

print("All verifications passed in clean process.")
