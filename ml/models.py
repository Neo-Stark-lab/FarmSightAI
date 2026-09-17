import xgboost as xgb
import pandas as pd
from pathlib import Path
import json

MODEL_DIR = Path(__file__).parent / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "water_stress_xgboost.json"

class WaterStressModel:
    def __init__(self):
        self.model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            max_depth=4,
            learning_rate=0.1,
            n_estimators=50,
            missing=float("nan"), # Explicitly handles NaNs
            random_state=42
        )
        self.is_trained = False

    def train(self, df: pd.DataFrame, target_col: str = "target"):
        X = df.drop(columns=[target_col, "dataset_type"], errors="ignore")
        y = df[target_col]
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict_proba(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.is_trained:
            raise ValueError("Model is not trained.")
        return self.model.predict_proba(X)

    def predict(self, X: pd.DataFrame) -> pd.Series:
        if not self.is_trained:
            raise ValueError("Model is not trained.")
        return self.model.predict(X)

    def save(self):
        if not self.is_trained:
            raise ValueError("Model is not trained.")
        self.model.save_model(str(MODEL_PATH))
        
    def load(self):
        if MODEL_PATH.exists():
            self.model.load_model(str(MODEL_PATH))
            self.is_trained = True
        else:
            raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
