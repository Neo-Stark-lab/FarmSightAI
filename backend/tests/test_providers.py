import pytest
from datetime import datetime, timezone
import json
from unittest.mock import patch, MagicMock

from data.providers import OpenMeteoProvider, GoogleEarthEngineProvider, ERA5LandProvider
from data.pipeline import AnalysisContext, Observation

@pytest.fixture
def dummy_context():
    return AnalysisContext(
        farm_id="f1",
        zone_id="z1",
        crop="rice",
        sowing_date=datetime(2026, 1, 1).date(),
        reference_time=datetime(2026, 6, 1, tzinfo=timezone.utc),
        boundary={"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]},
        location=(0.5, 0.5)
    )

def test_open_meteo_parsing(dummy_context):
    provider = OpenMeteoProvider()
    
    # Mock urlopen
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "daily": {
            "time": ["2026-05-30", "2026-05-31", "2026-06-01"],
            "precipitation_sum": [10.5, 0.0, None],
            "temperature_2m_mean": [25.1, 26.0, 24.5]
        }
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    
    with patch("data.providers.urlopen", return_value=mock_response):
        obs = provider.fetch(dummy_context)
        
    assert len(obs) == 5  # 3 temperatures, 2 rainfalls (1 is None, omitted)
    
    rain_obs = [o for o in obs if o.metric == "rainfall"]
    assert len(rain_obs) == 2
    assert rain_obs[0].value == 10.5
    
    temp_obs = [o for o in obs if o.metric == "temperature"]
    assert len(temp_obs) == 3
    assert temp_obs[0].value == 25.1

def test_gee_sentinel_parsing(dummy_context):
    with patch("ee.Initialize"):
        provider = GoogleEarthEngineProvider()
    
    assert provider.initialized is True
    
    mock_collection = MagicMock()
    mock_collection.filterBounds.return_value = mock_collection
    mock_collection.filterDate.return_value = mock_collection
    
    # Mock map().getInfo()
    mock_mapped = MagicMock()
    mock_mapped.getInfo.return_value = {
        "features": [
            {
                "properties": {
                    "system:time_start": 1600000000000,
                    "system:id": "test_id",
                    "B8": 0.4,
                    "B4": 0.1,
                    "B11": 0.2,
                    "qa_cloud_fraction": 0.0
                }
            },
            {
                "properties": {
                    "system:time_start": 1600086400000,
                    "system:id": "cloud_id",
                    "B8": None,
                    "B4": None,
                    "B11": None,
                    "qa_cloud_fraction": 1.0
                }
            }
        ]
    }
    mock_collection.map.return_value = mock_mapped
    
    with patch.object(provider.ee, "ImageCollection", return_value=mock_collection):
        with patch.object(provider.ee, "Geometry"):
            obs = provider.fetch(dummy_context)
            
    assert len(obs) == 2
    assert obs[0].metric == "sentinel_bands"
    assert obs[0].properties["nir"] == 0.4
    assert obs[0].properties["red"] == 0.1
    assert "cloud" not in obs[0].quality_flags
    
    assert obs[1].metric == "sentinel_bands"
    assert obs[1].properties["nir"] is None
    assert "cloud" in obs[1].quality_flags

def test_era5_parsing(dummy_context):
    with patch("ee.Initialize"):
        provider = ERA5LandProvider()
            
    assert provider.initialized is True
    
    mock_features = MagicMock()
    mock_features.getInfo.return_value = {
        "features": [
            {
                "properties": {
                    "system:time_start": 1600000000000,
                    "soil_moisture": 0.35
                }
            },
            {
                "properties": {
                    "system:time_start": 1600086400000,
                    "soil_moisture": None
                }
            }
        ]
    }
    
    with patch.object(provider.ee, "FeatureCollection", return_value=mock_features):
        with patch.object(provider.ee, "Geometry"):
            with patch.object(provider.ee.List, "sequence"):
                obs = provider.fetch(dummy_context)
                
    assert len(obs) == 1  # The None value is omitted
    assert obs[0].metric == "soil_moisture"
    assert obs[0].value == 0.35
