"""Provider interfaces and small, dependency-free provider implementations.

Live providers are deliberately isolated here.  Tests use ``FixtureProvider``;
it is mock data and must never be presented as an external observation.
"""
from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol, Sequence
from urllib.parse import urlencode
from urllib.request import urlopen

from .pipeline import AnalysisContext, Observation

logger = logging.getLogger(__name__)

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
    WEATHER_HISTORY_DAYS = 30

    def __init__(self, endpoint: str | None = None, timeout_seconds: int = 15):
        self.endpoint = endpoint or os.getenv(
            "OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive"
        )
        self.timeout_seconds = timeout_seconds

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        if not context.location:
            raise ValueError("Open-Meteo requires a representative latitude/longitude")
        latitude, longitude = context.location
        # The pipeline's 30-day window is start-exclusive/end-inclusive, so
        # request 30 daily records including the analysis reference date.
        start_date = context.reference_time.date() - timedelta(days=self.WEATHER_HISTORY_DAYS - 1)
        query = urlencode({
            "latitude": latitude, "longitude": longitude,
            "start_date": start_date.isoformat(),
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
            # Open-Meteo can return None if data is missing for a particular day
            if rain is not None:
                rows.append(Observation(metric="rainfall", value=rain, unit="mm", **common))
            if temperature is not None:
                rows.append(Observation(metric="temperature", value=temperature, unit="degC", **common))
        return rows


class GoogleEarthEngineProvider:
    """Explicit integration boundary for configured Earth Engine retrieval.
    """
    name = "google_earth_engine"

    def __init__(self):
        try:
            import ee
            self.ee = ee
            try:
                ee.Initialize(project=os.getenv("EE_PROJECT", None))
            except Exception:
                pass # Might already be initialized, or if it failed we catch it below or it fails on fetch
            self.initialized = True
        except Exception as e:
            logger.warning(f"Google Earth Engine failed to initialize: {e}")
            self.initialized = False
            self.ee_error = str(e)

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        if not self.initialized:
            raise RuntimeError(f"Google Earth Engine is not authenticated/configured: {self.ee_error}")
        
        boundary = context.boundary
        if not boundary:
            if context.location:
                geom = self.ee.Geometry.Point([context.location[1], context.location[0]])
            else:
                return []
        else:
            geom = self.ee.Geometry(boundary)

        end_date = context.reference_time.date()
        start_date = end_date - timedelta(days=30)
        
        collection = (self.ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                      .filterBounds(geom)
                      .filterDate(start_date.isoformat(), end_date.isoformat()))
                      
        def reduce_image(img):
            qa = img.select('QA60')
            mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
            masked_img = img.updateMask(mask)
            
            stats = masked_img.select(['B8', 'B4', 'B11']).reduceRegion(
                reducer=self.ee.Reducer.mean(),
                geometry=geom,
                scale=10,
                maxPixels=1e9
            )
            # scale the results back to 0-1 for Sentinel 2 SR
            stats = stats.map(lambda k, v: self.ee.Number(v).divide(10000))
            
            return self.ee.Feature(None, {
                'system:time_start': img.get('system:time_start'),
                'system:id': img.get('system:index'),
                'B8': stats.get('B8'),
                'B4': stats.get('B4'),
                'B11': stats.get('B11'),
                # approximate cloud fraction for QA by checking how much is masked
                'qa_cloud_fraction': img.select('QA60').bitwiseAnd(1 << 10).gt(0).reduceRegion(
                    reducer=self.ee.Reducer.mean(), geometry=geom, scale=10, maxPixels=1e9
                ).get('QA60')
            })
            
        try:
            features = collection.map(reduce_image).getInfo().get('features', [])
        except Exception as e:
            raise RuntimeError(f"Google Earth Engine API query failed: {e}")
        
        rows = []
        for feat in features:
            props = feat.get('properties', {})
            time_ms = props.get('system:time_start')
            if not time_ms:
                continue
            dt = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
            
            b8 = props.get('B8')
            b4 = props.get('B4')
            b11 = props.get('B11')
            img_id = props.get('system:id', 'unknown')
            qa_cloud_fraction = props.get('qa_cloud_fraction')
            
            quality_flags = []
            if b8 is None or b4 is None or b11 is None:
                quality_flags.append("cloud")
            elif qa_cloud_fraction is not None and qa_cloud_fraction > 0.2:
                quality_flags.append("cloud")
                
            rows.append(Observation(
                metric="sentinel_bands",
                value=0.0, # Sentinel bands are stored in properties; value is ignored for this metric
                unit="unitless",
                observed_at=dt,
                retrieved_at=context.reference_time,
                source={"provider": "Google Earth Engine", "dataset": "COPERNICUS/S2_SR_HARMONIZED", "product": "satellite", "image_id": img_id},
                spatial_aggregation="polygon_mean",
                spatial_resolution_m=10.0,
                quality_flags=tuple(quality_flags),
                properties={"nir": b8, "red": b4, "swir": b11}
            ))
            
        return rows


class ERA5LandProvider:
    """Explicit boundary for approved ERA5-Land soil-moisture retrieval."""
    name = "era5_land"

    def __init__(self):
        try:
            import ee
            self.ee = ee
            try:
                ee.Initialize(project=os.getenv("EE_PROJECT", None))
            except Exception:
                pass
            self.initialized = True
        except Exception as e:
            logger.warning(f"Google Earth Engine failed to initialize: {e}")
            self.initialized = False
            self.ee_error = str(e)

    def fetch(self, context: AnalysisContext) -> Sequence[Observation]:
        if not self.initialized:
            raise RuntimeError(f"Google Earth Engine is not authenticated/configured: {self.ee_error}")
        
        boundary = context.boundary
        if not boundary:
            if context.location:
                geom = self.ee.Geometry.Point([context.location[1], context.location[0]])
            else:
                return []
        else:
            geom = self.ee.Geometry(boundary)

        end_date = context.reference_time.date()
        start_date = end_date - timedelta(days=30)
        
        # We need individual observations. To prevent hitting payload limits, we will query daily means.
        def make_daily(dayOffset):
            day = self.ee.Date(start_date.isoformat()).advance(dayOffset, 'day')
            daily_img = (self.ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
                        .filterDate(day, day.advance(1, 'day'))
                        .select('volumetric_soil_water_layer_1')
                        .mean())
            stats = daily_img.reduceRegion(
                reducer=self.ee.Reducer.mean(),
                geometry=geom,
                scale=11132, # ERA5-Land resolution is ~11km
                maxPixels=1e9
            )
            return self.ee.Feature(None, {
                'system:time_start': day.millis(),
                'soil_moisture': stats.get('volumetric_soil_water_layer_1')
            })
            
        try:
            days = self.ee.List.sequence(0, 30)
            features = self.ee.FeatureCollection(days.map(make_daily)).getInfo().get('features', [])
        except Exception as e:
            raise RuntimeError(f"Google Earth Engine API query failed: {e}")
        
        rows = []
        for feat in features:
            props = feat.get('properties', {})
            time_ms = props.get('system:time_start')
            sm = props.get('soil_moisture')
            
            if sm is None or time_ms is None:
                continue
                
            dt = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
            rows.append(Observation(
                metric="soil_moisture",
                value=sm,
                unit="m3_m3",
                observed_at=dt,
                retrieved_at=context.reference_time,
                source={"provider": "Google Earth Engine", "dataset": "ECMWF/ERA5_LAND/HOURLY", "product": "climate"},
                spatial_aggregation="polygon_mean",
                spatial_resolution_m=11132.0,
            ))
            
        return rows
