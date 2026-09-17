"""Provider interfaces and small, dependency-free provider implementations.

Live providers are deliberately isolated here.  Tests use ``FixtureProvider``;
it is mock data and must never be presented as an external observation.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Protocol, Sequence
from urllib.parse import urlencode
from urllib.request import urlopen

from .pipeline import AnalysisContext, Observation


class ObservationProvider(Protocol):
    name: str

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]: ...


class FixtureProvider:
    """Deterministic local provider used only by tests and demos."""
    name = "fixture"

    def __init__(self, observations: Sequence[Observation]):
        self._observations = tuple(observations)

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        return self._observations


class OpenMeteoProvider:
    """Fetch daily precipitation and mean temperature from Open-Meteo.

    Open-Meteo supplies operational weather observations; it does not supply the
    historical baseline required for anomaly features, so those remain missing
    unless a separate approved baseline provider supplies them.
    """
    name = "open_meteo"

    def __init__(self, endpoint: str | None = None, timeout_seconds: int = 15):
        self.endpoint = endpoint or os.getenv(
            "OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive"
        )
        self.timeout_seconds = timeout_seconds

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        if not context.location:
            raise ValueError("Open-Meteo requires a representative latitude/longitude")
        latitude, longitude = context.location
        query = urlencode({
            "latitude": latitude, "longitude": longitude,
            "start_date": (context.reference_time.date()).isoformat(),
            "end_date": context.reference_time.date().isoformat(),
            "daily": "precipitation_sum,temperature_2m_mean", "timezone": "UTC",
        })
        with urlopen(f"{self.endpoint}?{query}", timeout=self.timeout_seconds) as response:
            payload = json.load(response)
        daily = payload.get("daily", {})
        rows: list[Observation] = []
        for day, rain, temperature in zip(
            daily.get("time", []), daily.get("precipitation_sum", []), daily.get("temperature_2m_mean", [])
        ):
            observed_at = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
            common = dict(observed_at=observed_at, retrieved_at=context.reference_time,
                          source={"provider": "Open-Meteo", "dataset": "daily", "product": "archive"},
                          spatial_aggregation="representative_point")
            rows.extend((
                Observation(metric="rainfall", value=rain, unit="mm", **common),
                Observation(metric="temperature", value=temperature, unit="degC", **common),
            ))
        return rows


class GoogleEarthEngineProvider:
    """Explicit integration boundary for configured Earth Engine retrieval.

    Earth Engine authentication/query configuration is deployment-specific.  A
    caller must inject an authenticated adapter rather than silently generating
    satellite values locally.
    """
    name = "google_earth_engine"

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        raise RuntimeError(
            "Google Earth Engine is not configured. Inject an authenticated provider "
            "that returns cloud-screened, zone-aggregated Sentinel-2 observations."
        )


class ERA5LandProvider:
    """Explicit boundary for approved ERA5-Land soil-moisture retrieval."""
    name = "era5_land"

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        raise RuntimeError(
            "ERA5-Land retrieval is not configured. Inject an approved provider; "
            "coarse modelled soil moisture must retain its resolution and provenance."
        )
