import os

API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
PROVIDER_MODE = os.getenv("PROVIDER_MODE", "fixture")
CORS_ORIGINS = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if value.strip()]
