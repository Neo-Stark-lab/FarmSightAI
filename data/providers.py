"""Provider boundary; route handlers never contact providers directly."""
from datetime import timedelta


class ProviderError(RuntimeError):
    pass


class FixtureProvider:
    """Deterministic DEMO observations, never live measurements."""
    name = "fixture_demo"

    def observations(self, reference_time):
        observed_at = reference_time - timedelta(hours=24)
        return {
            "ndvi_current": (0.52, "unitless", observed_at, 120), "ndvi_7d_change": (-0.03, "unitless", observed_at, 120),
            "ndvi_30d_change": (-0.08, "unitless", observed_at, 120), "ndmi_current": (0.14, "unitless", observed_at, 120),
            "ndmi_change": (-0.05, "unitless", observed_at, 120), "rainfall_7d": (12.4, "mm", observed_at, 48),
            "rainfall_30d": (54.1, "mm", observed_at, 48), "rainfall_anomaly": (-18.2, "mm", observed_at, 48),
            "temperature_mean": (31.1, "degC", observed_at, 48), "temperature_anomaly": (1.4, "degC", observed_at, 48),
            "soil_moisture": (None, "m3_m3", observed_at, 168), "soil_moisture_change": (None, "m3_m3", observed_at, 168),
            "historical_deviation": (-0.11, "unitless", observed_at, 120), "neighboring_deviation": (-0.07, "unitless", observed_at, 120),
        }


class OpenMeteoProvider: pass
class GoogleEarthEngineProvider: pass
class ERA5LandProvider: pass
