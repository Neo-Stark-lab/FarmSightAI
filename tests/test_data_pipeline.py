import io
import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest

from data.pipeline import AnalysisContext, DataPipeline, Observation, ndmi, ndvi
from data.providers import FixtureProvider, OpenMeteoProvider
from ml.inference import score_water_stress
from ml.models import WaterStressModel
from ml.preprocessing import FEATURE_ORDER, preprocess_features

REF = datetime(2026, 9, 17, tzinfo=timezone.utc)


def context():
    return AnalysisContext("farm-1", "zone-1", "rice", date(2026, 7, 1), REF,
                           analysis_run_id="run-1", feature_set_id="set-1", request_id="request-1")


def observation(metric, value, when=REF, unit="unitless", **properties):
    return Observation(metric=metric, value=value, unit=unit, observed_at=when,
                       retrieved_at=REF, source={"provider": "fixture", "dataset": "test", "product": "local"},
                       spatial_aggregation="zone_mean", properties=properties)


def complete_observations():
    rows = [
        observation("sentinel_bands", None, REF, nir=.7, red=.3, swir=.5),
        observation("sentinel_bands", None, REF - timedelta(days=7), nir=.6, red=.3, swir=.5),
        observation("sentinel_bands", None, REF - timedelta(days=30), nir=.5, red=.3, swir=.5),
        observation("soil_moisture", .24, REF, "m3_m3", resolution_m=9000),
        observation("soil_moisture", .28, REF - timedelta(days=7), "m3_m3", resolution_m=9000),
        observation("rainfall_baseline", 50, REF, "mm"),
        observation("temperature_baseline", 28, REF, "degC"),
        observation("historical_ndvi_baseline", .4, REF, comparable=True),
        observation("neighboring_ndvi_baseline", .45, REF, comparable=True, crop="rice", stage="unknown", season="kharif"),
    ]
    for offset in range(30):
        when = REF - timedelta(days=offset)
        rows += [observation("rainfall", 1, when, "mm"), observation("temperature", 30, when, "degC")]
    return rows


def pipeline(rows=None, **kwargs):
    return DataPipeline([FixtureProvider(rows if rows is not None else complete_observations())], **kwargs)


def test_ndvi_and_ndmi_calculations():
    assert ndvi(.7, .3) == pytest.approx(.4)
    assert ndmi(.7, .5) == pytest.approx(1 / 6)
    assert ndvi(0, 0) is None


def test_sentinel_temporal_features_and_provenance():
    result = pipeline().build(context())
    features, metadata = result["features"], result["feature_metadata"]
    assert features["ndvi_current"] == pytest.approx(.4)
    assert features["ndvi_7d_change"] == pytest.approx(.4 - (1 / 3))
    assert features["ndvi_30d_change"] == pytest.approx(.4 - .25)
    assert features["ndmi_change"] == pytest.approx((1 / 6) - (1 / 11))
    assert len(metadata["ndvi_7d_change"]["source_observation_ids"]) == 2
    assert metadata["ndvi_current"]["observation_timestamp"] == "2026-09-17T00:00:00Z"


def test_cloudy_satellite_observation_is_not_used():
    row = observation("sentinel_bands", None, REF, nir=.8, red=.2, swir=.4)
    row = Observation(**{**row.__dict__, "quality_flags": ("cloud",)})
    result = pipeline([row]).build(context())
    assert result["features"]["ndvi_current"] is None
    assert result["feature_metadata"]["ndvi_current"]["missing_reason"] == "not_available"


def test_weather_windows_and_anomalies():
    result = pipeline().build(context())
    assert result["features"]["rainfall_7d"] == 7
    assert result["features"]["rainfall_30d"] == 30
    assert result["features"]["rainfall_anomaly"] == -20
    assert result["features"]["temperature_mean"] == 30
    assert result["features"]["temperature_anomaly"] == 2


def test_open_meteo_requests_30_day_history_and_feeds_weather_windows(monkeypatch):
    requested = {}
    days = [(REF.date() - timedelta(days=offset)).isoformat() for offset in range(29, -1, -1)]
    response = {"daily": {"time": days, "precipitation_sum": [1.0] * 30,
                          "temperature_2m_mean": [30.0] * 30}}

    class FakeResponse(io.StringIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()

    def fake_urlopen(url, timeout):
        requested.update(parse_qs(urlparse(url).query))
        return FakeResponse(json.dumps(response))

    monkeypatch.setattr("data.providers.urlopen", fake_urlopen)
    provider = OpenMeteoProvider(endpoint="https://weather.example/archive")
    live_context = AnalysisContext("farm-1", "zone-1", "rice", date(2026, 7, 1), REF,
                                   location=(13.08, 80.27))

    result = DataPipeline([provider]).build(live_context)

    assert requested["start_date"] == ["2026-08-19"]
    assert requested["end_date"] == ["2026-09-17"]
    assert len(provider.fetch(live_context)) == 60
    assert result["features"]["rainfall_7d"] == 7
    assert result["features"]["rainfall_30d"] == 30
    assert result["features"]["temperature_mean"] == 30


def test_anomaly_without_baseline_remains_missing():
    rows = [r for r in complete_observations() if r.metric not in {"rainfall_baseline", "temperature_baseline"}]
    result = pipeline(rows).build(context())
    assert result["features"]["rainfall_anomaly"] is None
    assert result["feature_metadata"]["rainfall_anomaly"]["missing_reason"] == "not_available"


def test_soil_missing_and_stale_observation_handling():
    result = pipeline([]).build(context())
    assert result["features"]["soil_moisture"] is None
    assert result["quality_status"] == "insufficient_data"
    stale = pipeline([observation("soil_moisture", .2, REF - timedelta(days=6), "m3_m3")]).build(context())
    assert stale["feature_metadata"]["soil_moisture"]["freshness"]["status"] == "fresh"
    stale_pipeline = pipeline([observation("soil_moisture", .2, REF - timedelta(days=6), "m3_m3")], freshness_hours={"soil_moisture": 24})
    assert stale_pipeline.build(context())["feature_metadata"]["soil_moisture"]["freshness"]["status"] == "stale"


def test_crop_stage_is_unknown_without_approved_calendar():
    result = pipeline().build(context())
    assert result["features"]["crop_stage"] == "unknown"
    assert result["feature_metadata"]["crop_stage"]["missing_reason"] == "not_available"


def test_historical_and_neighbouring_deviation_require_comparability():
    result = pipeline().build(context())
    assert result["features"]["historical_deviation"] == pytest.approx(0)
    assert result["features"]["neighboring_deviation"] == pytest.approx(-.05)
    rows = [r for r in complete_observations() if not r.metric.endswith("ndvi_baseline")]
    rows.append(observation("historical_ndvi_baseline", .2, REF, comparable=False))
    assert pipeline(rows).build(context())["features"]["historical_deviation"] is None


def test_manifest_order_missing_propagation_and_ml_encoding():
    result = pipeline().build(context())
    assert list(result["features"]) == FEATURE_ORDER
    assert list(result["feature_metadata"]) == FEATURE_ORDER
    encoded = preprocess_features(result["features"])
    assert list(encoded.columns) == FEATURE_ORDER
    assert encoded["crop"].iloc[0] == 0
    assert encoded["crop_stage"].iloc[0] == -1


def test_provider_failure_is_explicit_and_deterministic():
    class BrokenProvider:
        name = "broken"
        def fetch(self, ctx): raise RuntimeError("offline")
    first = DataPipeline([BrokenProvider()]).build(context())
    second = DataPipeline([BrokenProvider()]).build(context())
    assert first["pipeline_status"] == "partial"
    assert "broken: offline" in first["provider_failures"][0]
    assert first["features"] == second["features"]
    assert first["feature_metadata"]["ndvi_current"]["missing_reason"] == "provider_error"


def test_malformed_observation_is_rejected():
    with pytest.raises(ValueError, match="unsupported missing reason"):
        Observation(metric="ndvi", value=None, unit="unitless", observed_at=REF,
                    retrieved_at=REF, source={"provider": "fixture"},
                    spatial_aggregation="zone_mean", missing_reason="made_up")


def test_end_to_end_pipeline_to_ml_prediction():
    result = pipeline().build(context())
    model = WaterStressModel(); model.load()
    class NoopExplainer:
        def explain_instance(self, X, predicted_class): return []
    prediction = score_water_stress(result, model, NoopExplainer())
    assert prediction["prediction"]["status"] == "valid"
    assert prediction["prediction"]["risk_level"] in {"low", "moderate", "high"}
