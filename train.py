from ml.dataset import generate_synthetic_dataset
from ml.models import WaterStressModel

print("Generating synthetic dataset...")
df = generate_synthetic_dataset(num_samples=2000)

print(f"Generated {len(df)} samples.")
print("Training XGBoost model...")
model = WaterStressModel()
model.train(df)

print("Saving model artifact...")
model.save()
print("Done. Model trained and saved successfully.")
