"""Canonical 16-feature FeatureSet production boundary."""
from uuid import uuid4
from data.providers import FixtureProvider

FEATURES = ("ndvi_current", "ndvi_7d_change", "ndvi_30d_change", "ndmi_current", "ndmi_change", "rainfall_7d", "rainfall_30d", "rainfall_anomaly", "temperature_mean", "temperature_anomaly", "soil_moisture", "soil_moisture_change", "crop", "crop_stage", "historical_deviation", "neighboring_deviation")


class DataPipeline:
    def __init__(self, provider=None): self.provider = provider or FixtureProvider()

    def build_feature_set(self, *, farm, zone, analysis_run_id, reference_time):
        values, metadata, observations = {}, {}, []
        for feature, (value, unit, observed_at, threshold) in self.provider.observations(reference_time).items():
            age = round((reference_time - observed_at).total_seconds() / 3600, 2)
            freshness = {"age_hours": age, "status": "fresh" if age <= threshold else "stale", "threshold_hours": threshold}
            observation_id, missing = str(uuid4()), "not_available" if value is None else None
            values[feature] = value
            metadata[feature] = {"unit": unit, "source_observation_ids": [observation_id], "freshness": freshness, "missing_reason": missing}
            observations.append({"id": observation_id, "metric": feature, "value": value, "unit": unit, "observed_at": observed_at.isoformat(), "source": {"provider": self.provider.name, "dataset": "deterministic_fixture", "product": "DEMO DATA"}, "retrieved_at": reference_time.isoformat(), "processed_at": reference_time.isoformat(), "spatial_aggregation": "zone_mean", "quality_flags": ["demo_fixture"], "missing_reason": missing, "freshness": freshness})
        values.update(crop=farm["crop"], crop_stage="unknown")
        for feature in ("crop", "crop_stage"):
            metadata[feature] = {"unit": "category", "source_observation_ids": [], "freshness": {"age_hours": 0, "status": "unknown"}, "missing_reason": None, "calculation": "farm context"}
        return {"id": str(uuid4()), "schema_version": "1.0", "analysis_run_id": analysis_run_id, "farm_id": farm["id"], "zone_id": zone["id"], "reference_time": reference_time.isoformat(), "features": values, "feature_metadata": metadata, "quality_status": "partial" if any(v is None for v in values.values()) else "complete", "generated_at": reference_time.isoformat(), "observations": observations}
