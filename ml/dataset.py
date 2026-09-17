import pandas as pd
import numpy as np
from pathlib import Path
from ml.preprocessing import FEATURE_ORDER, CATEGORICAL_MAPPING

def generate_synthetic_dataset(num_samples: int = 1000) -> pd.DataFrame:
    """
    Generates a synthetic dataset for water stress.
    Strictly for unit testing, integration testing, and verifying the pipeline code.
    NOT FOR REAL-WORLD VALIDATION.
    """
    np.random.seed(42)
    data = {}
    
    # Generate numerical features
    data["ndvi_current"] = np.random.uniform(0.1, 0.9, num_samples)
    data["ndvi_7d_change"] = np.random.normal(0, 0.05, num_samples)
    data["ndvi_30d_change"] = np.random.normal(0, 0.1, num_samples)
    data["ndmi_current"] = np.random.uniform(-0.2, 0.6, num_samples)
    data["ndmi_change"] = np.random.normal(0, 0.05, num_samples)
    data["rainfall_7d"] = np.random.exponential(10, num_samples)
    data["rainfall_30d"] = np.random.exponential(40, num_samples)
    data["rainfall_anomaly"] = data["rainfall_30d"] - 40 + np.random.normal(0, 5, num_samples)
    data["temperature_mean"] = np.random.normal(30, 3, num_samples)
    data["temperature_anomaly"] = np.random.normal(0, 1.5, num_samples)
    data["soil_moisture"] = np.random.uniform(0.1, 0.4, num_samples)
    data["soil_moisture_change"] = np.random.normal(0, 0.02, num_samples)
    data["historical_deviation"] = np.random.normal(0, 0.1, num_samples)
    data["neighboring_deviation"] = np.random.normal(0, 0.1, num_samples)
    
    # Generate categorical features
    crops = list(CATEGORICAL_MAPPING["crop"].keys())
    crops.remove("unknown")
    data["crop"] = np.random.choice([CATEGORICAL_MAPPING["crop"][c] for c in crops], num_samples)
    
    stages = list(CATEGORICAL_MAPPING["crop_stage"].keys())
    stages.remove("unknown")
    data["crop_stage"] = np.random.choice([CATEGORICAL_MAPPING["crop_stage"][s] for s in stages], num_samples)
    
    df = pd.DataFrame(data)[FEATURE_ORDER]
    
    # Introduce missing values to simulate real-world data
    for col in FEATURE_ORDER:
        mask = np.random.rand(num_samples) < 0.05
        df.loc[mask, col] = np.nan
        
    # Generate synthetic target
    # High stress if: low soil moisture, low rainfall anomaly, declining ndvi, declining ndmi
    stress_score = (
        -2.0 * df["soil_moisture"].fillna(0.25) +
        -0.05 * df["rainfall_anomaly"].fillna(0) +
        -10.0 * df["ndvi_7d_change"].fillna(0) +
        -10.0 * df["ndmi_change"].fillna(0) +
        0.2 * df["temperature_anomaly"].fillna(0)
    )
    
    # Add some noise
    stress_score += np.random.normal(0, 0.5, num_samples)
    
    # Convert to classes: 0 = low, 1 = moderate, 2 = high
    threshold_low = np.percentile(stress_score, 33)
    threshold_high = np.percentile(stress_score, 66)
    
    target = np.zeros(num_samples)
    target[stress_score > threshold_low] = 1
    target[stress_score > threshold_high] = 2
    
    df["target"] = target
    df["dataset_type"] = "synthetic"
    
    return df
