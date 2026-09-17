import os

API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
PROVIDER_MODE = os.getenv("PROVIDER_MODE", "fixture")
CORS_ORIGINS = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if value.strip()]
APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL")
ML_MODEL_URI = os.getenv("ML_MODEL_URI", "ml/artifacts/water_stress_xgboost.json")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
