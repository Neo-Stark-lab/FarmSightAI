"""Feature engineering from source-attributed observations to ML contract v1.0."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence
from uuid import NAMESPACE_URL, uuid5

import yaml

from ml.preprocessing import CATEGORICAL_MAPPING, FEATURE_ORDER

MANIFEST_PATH = __import__("pathlib").Path(__file__).parents[1] / "ml" / "feature_manifest.yaml"
MISSING_REASONS = {"not_available", "cloud_obscured", "out_of_coverage", "provider_error", "invalid"}


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class AnalysisContext:
    farm_id: str
    zone_id: str
    crop: str
    sowing_date: date
    reference_time: datetime
    analysis_run_id: str = "analysis-run"
    feature_set_id: str = "feature-set"
    request_id: str = "request"
    boundary: Mapping[str, Any] | None = None
    location: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if self.crop not in CATEGORICAL_MAPPING["crop"] or self.crop == "unknown":
            raise ValueError("crop must be rice, groundnut, or maize")
        object.__setattr__(self, "reference_time", _utc(self.reference_time))


@dataclass(frozen=True)
class Observation:
    metric: str
    value: float | None
    unit: str
    observed_at: datetime
    source: Mapping[str, str]
    retrieved_at: datetime
    spatial_aggregation: str
    observation_id: str | None = None
    processed_at: datetime | None = None
    quality_flags: tuple[str, ...] = ()
    missing_reason: str | None = None
    spatial_resolution_m: float | None = None
    properties: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.missing_reason and self.missing_reason not in MISSING_REASONS:
            raise ValueError("unsupported missing reason")
        object.__setattr__(self, "observed_at", _utc(self.observed_at))
        object.__setattr__(self, "retrieved_at", _utc(self.retrieved_at))
        if self.processed_at:
            object.__setattr__(self, "processed_at", _utc(self.processed_at))
        if not self.observation_id:
            identity = f"{self.metric}:{self.observed_at.isoformat()}:{self.source}:{self.value}"
            object.__setattr__(self, "observation_id", str(uuid5(NAMESPACE_URL, identity)))


def normalized_difference(numerator: float, denominator: float) -> float | None:
    """Return a band index safely; zero denominator is invalid, not zero."""
    total = numerator + denominator
    return None if total == 0 else (numerator - denominator) / total


def ndvi(nir: float, red: float) -> float | None:
    return normalized_difference(nir, red)


def ndmi(nir: float, swir: float) -> float | None:
    return normalized_difference(nir, swir)


class DataPipeline:
    """Build a contract-valid FeatureSet without imputing unavailable data."""
    def __init__(self, providers: Sequence[Any] = (), freshness_hours: Mapping[str, float] | None = None):
        self.providers = tuple(providers)
        self.freshness_hours = {"satellite": 120, "weather": 48, "soil_moisture": 168, **(freshness_hours or {})}
        with MANIFEST_PATH.open(encoding="utf-8") as handle:
            self.manifest = yaml.safe_load(handle)
        self.units = {item["name"]: item.get("unit", "categorical") for item in self.manifest["features"]}

    def build(self, context: AnalysisContext) -> dict[str, Any]:
        observations, provider_failures = self._acquire(context)
        observations = self._expand_satellite_bands(observations)
        features: dict[str, Any] = {name: None for name in FEATURE_ORDER}
        metadata: dict[str, dict[str, Any]] = {}
        features["crop"] = context.crop
        metadata["crop"] = self._derived_metadata("categorical", "farm input", context)
        features["crop_stage"] = self._crop_stage(context)
        metadata["crop_stage"] = self._derived_metadata("categorical", "unknown: no documented crop calendar", context,
                                                          "not_available")

        self._vegetation(features, metadata, observations, context)
        self._weather(features, metadata, observations, context)
        self._soil(features, metadata, observations, context)
        self._context_deviations(features, metadata, observations, context)
        for name in FEATURE_ORDER:
            metadata.setdefault(name, self._missing_metadata(name, context, "not_available"))
        if provider_failures:
            for meta in metadata.values():
                if meta["missing_reason"] == "not_available":
                    meta["missing_reason"] = "provider_error"
                    meta["calculation"] += "; provider failure: " + ", ".join(provider_failures)
        result = {
            "schema_version": "1.0", "request_id": context.request_id,
            "analysis_run_id": context.analysis_run_id, "feature_set_id": context.feature_set_id,
            "farm_id": context.farm_id, "zone_id": context.zone_id,
            "reference_time": context.reference_time.isoformat().replace("+00:00", "Z"),
            "features": {name: features[name] for name in FEATURE_ORDER},
            "feature_metadata": {name: metadata[name] for name in FEATURE_ORDER},
            "quality_status": self._quality(features),
            "pipeline_status": "partial" if provider_failures else "completed",
            "provider_failures": provider_failures,
        }
        self.validate(result)
        return result

    def validate(self, feature_set: Mapping[str, Any]) -> None:
        if feature_set.get("schema_version") != "1.0": raise ValueError("unsupported schema version")
        features, metadata = feature_set.get("features", {}), feature_set.get("feature_metadata", {})
        if list(features) != FEATURE_ORDER or set(metadata) != set(FEATURE_ORDER):
            raise ValueError("features must exactly match canonical manifest order")
        for name in FEATURE_ORDER:
            value, meta = features[name], metadata[name]
            if meta.get("unit") != self.units[name]: raise ValueError(f"incorrect unit for {name}")
            if value is None and not meta.get("missing_reason"): raise ValueError(f"missing reason required for {name}")
            if value is not None and name not in CATEGORICAL_MAPPING and not isinstance(value, (int, float)):
                raise ValueError(f"numeric feature {name} is not numeric")
            if name in CATEGORICAL_MAPPING and value not in CATEGORICAL_MAPPING[name]:
                raise ValueError(f"unsupported categorical value for {name}")

    def _acquire(self, context: AnalysisContext) -> tuple[list[Observation], list[str]]:
        rows, failures = [], []
        for provider in self.providers:
            try: rows.extend(provider.fetch(context))
            except Exception as error: failures.append(f"{getattr(provider, 'name', type(provider).__name__)}: {error}")
        return rows, failures

    def _expand_satellite_bands(self, rows: Iterable[Observation]) -> list[Observation]:
        expanded = list(rows)
        for row in rows:
            if row.metric != "sentinel_bands" or "cloud" in row.quality_flags: continue
            nir, red, swir = row.properties.get("nir"), row.properties.get("red"), row.properties.get("swir")
            for metric, value in (("ndvi", ndvi(nir, red) if nir is not None and red is not None else None),
                                  ("ndmi", ndmi(nir, swir) if nir is not None and swir is not None else None)):
                expanded.append(Observation(metric=metric, value=value, unit="unitless", observed_at=row.observed_at,
                    source=row.source, retrieved_at=row.retrieved_at, processed_at=row.processed_at,
                    spatial_aggregation=row.spatial_aggregation, quality_flags=row.quality_flags,
                    missing_reason="invalid" if value is None else None, spatial_resolution_m=row.spatial_resolution_m,
                    properties={"calculation": f"zone aggregation after {metric.upper()} band calculation"}))
        return expanded

    def _valid(self, rows: Iterable[Observation], metric: str) -> list[Observation]:
        return sorted((r for r in rows if r.metric == metric and r.value is not None and not r.missing_reason and "cloud" not in r.quality_flags), key=lambda r: r.observed_at)

    def _pick(self, rows: list[Observation], target: datetime, tolerance_days: int = 3) -> Observation | None:
        candidates = [r for r in rows if abs((r.observed_at - target).total_seconds()) <= tolerance_days * 86400]
        return min(candidates, key=lambda r: abs((r.observed_at - target).total_seconds())) if candidates else None

    def _vegetation(self, f: dict, m: dict, rows: list[Observation], c: AnalysisContext) -> None:
        for metric, current_name, change_names in (("ndvi", "ndvi_current", [("ndvi_7d_change", 7), ("ndvi_30d_change", 30)]),
                                                    ("ndmi", "ndmi_current", [("ndmi_change", 7)])):
            valid = self._valid(rows, metric)
            current = self._pick(valid, c.reference_time, 30)
            self._set_observation(f, m, current_name, current, c, "satellite", "latest cloud-screened zone observation")
            for name, days in change_names:
                prior = self._pick(valid, c.reference_time - timedelta(days=days))
                if current and prior:
                    f[name] = current.value - prior.value
                    m[name] = self._derived_from(name, [current, prior], c, "unitless", f"current minus observation nearest {days}d target")
                else: m[name] = self._missing_metadata(name, c, "cloud_obscured" if not valid else "not_available")

    def _weather(self, f: dict, m: dict, rows: list[Observation], c: AnalysisContext) -> None:
        for output, metric, days, aggregate in (("rainfall_7d", "rainfall", 7, sum), ("rainfall_30d", "rainfall", 30, sum), ("temperature_mean", "temperature", 30, fmean)):
            selected = [r for r in self._valid(rows, metric) if c.reference_time - timedelta(days=days) < r.observed_at <= c.reference_time]
            if selected:
                f[output] = aggregate([r.value for r in selected])
                m[output] = self._derived_from(output, selected, c, self.units[output], f"{days}d {metric} aggregation")
            else: m[output] = self._missing_metadata(output, c, "not_available")
        for output, current, baseline_metric in (("rainfall_anomaly", "rainfall_30d", "rainfall_baseline"), ("temperature_anomaly", "temperature_mean", "temperature_baseline")):
            baselines = self._valid(rows, baseline_metric)
            baseline = self._pick(baselines, c.reference_time, 366)
            if f[current] is not None and baseline:
                f[output] = f[current] - baseline.value
                m[output] = self._derived_from(output, [baseline], c, self.units[output], "current aggregate minus supplied historical baseline")
            else: m[output] = self._missing_metadata(output, c, "not_available")

    def _soil(self, f: dict, m: dict, rows: list[Observation], c: AnalysisContext) -> None:
        valid, current = self._valid(rows, "soil_moisture"), None
        current = self._pick(valid, c.reference_time, 30)
        self._set_observation(f, m, "soil_moisture", current, c, "soil_moisture", "latest approved soil-moisture context")
        previous = self._pick(valid, c.reference_time - timedelta(days=7), 3)
        if current and previous:
            f["soil_moisture_change"] = current.value - previous.value
            m["soil_moisture_change"] = self._derived_from("soil_moisture_change", [current, previous], c, "m3_m3", "current minus observation nearest 7d target")
        else: m["soil_moisture_change"] = self._missing_metadata("soil_moisture_change", c, "not_available")

    def _context_deviations(self, f: dict, m: dict, rows: list[Observation], c: AnalysisContext) -> None:
        current = self._pick(self._valid(rows, "ndvi"), c.reference_time, 30)
        for output, baseline_metric, label in (("historical_deviation", "historical_ndvi_baseline", "same-field"), ("neighboring_deviation", "neighboring_ndvi_baseline", "comparable nearby-field")):
            candidates = [r for r in self._valid(rows, baseline_metric) if r.properties.get("comparable") is True]
            base = self._pick(candidates, c.reference_time, 366)
            if current and base:
                f[output] = current.value - base.value
                m[output] = self._derived_from(output, [current, base], c, "unitless", f"current NDVI minus {label} comparable baseline")
            else: m[output] = self._missing_metadata(output, c, "not_available")

    def _crop_stage(self, c: AnalysisContext) -> str:
        # Rules explicitly prohibit imposing a universal calendar; no approved day ranges exist.
        return "unknown"

    def _set_observation(self, f, m, name, observation, context, source_kind, calculation):
        if observation:
            f[name] = observation.value
            m[name] = self._derived_from(name, [observation], context, self.units[name], calculation, source_kind)
        else: m[name] = self._missing_metadata(name, context, "not_available")

    def _derived_from(self, name, rows, context, unit, calculation, source_kind=None):
        freshest = max(rows, key=lambda r: r.observed_at)
        threshold = self.freshness_hours[source_kind or ("satellite" if name.startswith("nd") else "weather")]
        age = max(0.0, (context.reference_time - freshest.observed_at).total_seconds() / 3600)
        return {"unit": unit, "source_observation_ids": [r.observation_id for r in rows],
                "freshness": {"age_hours": round(age, 3), "status": "fresh" if age <= threshold else "stale", "threshold_hours": threshold},
                "missing_reason": None, "calculation": calculation,
                "source": dict(freshest.source), "observation_timestamp": freshest.observed_at.isoformat().replace("+00:00", "Z"),
                "retrieval_timestamp": freshest.retrieved_at.isoformat().replace("+00:00", "Z"),
                "spatial_aggregation": freshest.spatial_aggregation, "spatial_resolution_m": freshest.spatial_resolution_m}

    def _missing_metadata(self, name, context, reason):
        unit = self.units[name]
        return {"unit": unit, "source_observation_ids": [], "freshness": {"age_hours": None, "status": "unknown", "threshold_hours": None},
                "missing_reason": reason, "calculation": "no valid source observation available"}

    def _derived_metadata(self, unit, calculation, context, reason=None):
        return {"unit": unit, "source_observation_ids": [], "freshness": {"age_hours": 0, "status": "fresh", "threshold_hours": None}, "missing_reason": reason, "calculation": calculation}

    @staticmethod
    def _quality(features):
        numeric = [name for name in FEATURE_ORDER if name not in CATEGORICAL_MAPPING]
        present = sum(features[name] is not None for name in numeric)
        return "complete" if present == len(numeric) and features["crop_stage"] != "unknown" else ("partial" if present else "insufficient_data")
