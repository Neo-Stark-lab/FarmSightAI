import shap
import pandas as pd
from ml.models import WaterStressModel
from ml.preprocessing import FEATURE_ORDER

class SHAPExplainer:
    def __init__(self, model: WaterStressModel):
        if not model.is_trained:
            raise ValueError("Cannot initialize explainer with untrained model.")
        self.model = model.model
        self.explainer = shap.TreeExplainer(self.model)

    def explain_instance(self, X: pd.DataFrame, predicted_class: int):
        """
        Returns feature contributions for a single instance.
        Only considers features that are not NaN.
        """
        # SHAP values for the predicted class
        shap_values = self.explainer.shap_values(X)
        
        # shap_values shape: (num_samples, num_features, num_classes) or (num_samples, num_features)
        # XGBClassifier multi-class returns list of arrays (one per class)
        if isinstance(shap_values, list):
            class_shap = shap_values[predicted_class][0]
        else:
            # If shap returns (num_samples, num_features, num_classes)
            if len(shap_values.shape) == 3:
                class_shap = shap_values[0, :, predicted_class]
            else:
                class_shap = shap_values[0]

        contributions = []
        for i, feature in enumerate(FEATURE_ORDER):
            val = X.iloc[0, i]
            # Skip if value is missing
            if pd.isna(val):
                continue
                
            contribution_value = class_shap[i]
            
            # Determine direction based on contribution to the predicted class
            if contribution_value > 0.01:
                direction = "increases_risk"
            elif contribution_value < -0.01:
                direction = "decreases_risk"
            else:
                direction = "neutral"
                
            if direction != "neutral":
                contributions.append({
                    "feature": feature,
                    "direction": direction,
                    "magnitude": round(abs(float(contribution_value)), 4),
                    "method": "shap",
                })
                
        # Sort by magnitude descending
        contributions.sort(key=lambda x: x["magnitude"], reverse=True)
        return contributions
