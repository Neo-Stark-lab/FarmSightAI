from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    provider_mode: str = os.getenv("PROVIDER_MODE", "fixture")
    cors_origins: tuple[str, ...] = tuple(
        item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if item.strip()
    )
    model_artifact: str = os.getenv("ML_MODEL_URI", "ml/artifacts/water_stress_xgboost.json")


settings = Settings()
