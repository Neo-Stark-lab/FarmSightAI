import unittest

from app.rules import RecommendationEngine


ALL_FEATURES = ["ndvi_current", "ndvi_7d_change", "ndvi_30d_change", "ndmi_current", "ndmi_change", "rainfall_7d", "rainfall_30d", "rainfall_anomaly", "temperature_mean", "temperature_anomaly", "soil_moisture", "soil_moisture_change", "historical_deviation", "neighboring_deviation"]


def payload(crop="rice", stage="vegetative", risk="high", status="valid", **changes):
    features = {key: 0.0 for key in ALL_FEATURES}
    features.update({"crop": crop, "crop_stage": stage})
    features.update(changes.pop("features", {}))
    metadata = {key: {"source_observation_ids": [f"obs-{key}"], "freshness": {"status": "fresh"}, "missing_reason": None} for key in ALL_FEATURES}
    metadata.update(changes.pop("metadata", {}))
    return {"prediction": {"risk_level": risk, "status": status}, "features": features, "feature_metadata": metadata, "evidence_flags": changes.pop("evidence_flags", {}), **changes}


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self): self.engine = RecommendationEngine()

    def test_high_multi_signal_case(self):
        result = self.engine.evaluate(payload(features={"ndmi_change": -.1, "rainfall_anomaly": -1, "soil_moisture_change": -.1}))
        self.assertEqual(result["action_type"], "CONSIDER_IRRIGATION")
        self.assertEqual(result["rule_ids"][0], "WS001")

    def test_low_soil_moisture_with_recent_rain(self):
        result = self.engine.evaluate(payload(features={"rainfall_anomaly": -1}, evidence_flags={"soil_moisture_low": True, "recent_rainfall": True}))
        self.assertEqual(result["action_type"], "REASSESS_AFTER_RAINFALL")

    def test_missing_soil_moisture_is_exposed(self):
        result = self.engine.evaluate(payload(features={"soil_moisture": None, "soil_moisture_change": None}))
        self.assertTrue(any("soil_moisture is unavailable" in note for note in result["limitations"]))

    def test_missing_weather_is_exposed(self):
        result = self.engine.evaluate(payload(features={"rainfall_anomaly": None, "rainfall_7d": None, "rainfall_30d": None}))
        self.assertTrue(any("rainfall_anomaly is unavailable" in note for note in result["limitations"]))

    def test_stale_satellite_reduces_recommendation(self):
        result = self.engine.evaluate(payload(features={"ndmi_change": -.1}, metadata={"ndmi_change": {"source_observation_ids": ["old"], "freshness": {"status": "stale"}, "missing_reason": None}}))
        self.assertEqual(result["action_type"], "PRIORITIZE_FIELD_CHECK")

    def test_conflicting_evidence(self):
        result = self.engine.evaluate(payload(features={"ndmi_change": -.1, "rainfall_anomaly": -1}, evidence_flags={"recent_rainfall": True}))
        self.assertEqual(result["rule_ids"][0], "WS002")

    def test_rice_stage_specific_rule(self):
        result = self.engine.evaluate(payload(crop="rice", stage="reproductive", features={"ndmi_change": -.1, "rainfall_anomaly": -1}))
        self.assertIn("CS001", result["rule_ids"])

    def test_groundnut_supported(self):
        self.assertEqual(self.engine.evaluate(payload(crop="groundnut"))["crop"], "groundnut")

    def test_maize_supported(self):
        self.assertEqual(self.engine.evaluate(payload(crop="maize"))["crop"], "maize")

    def test_multiple_possible_causes(self):
        result = self.engine.evaluate(payload(features={"ndmi_change": -.1, "temperature_anomaly": 2}))
        self.assertEqual([cause["cause"] for cause in result["possible_causes"]], ["water_stress", "heat_stress", "nutrient_stress", "pest_disease_related_stress"])

    def test_no_evidence_returns_not_available_when_prediction_invalid(self):
        result = self.engine.evaluate(payload(risk="unknown", status="insufficient_data", features={key: None for key in ALL_FEATURES}))
        self.assertEqual(result["status"], "not_available")
        self.assertEqual(result["action"], None)

    def test_output_is_deterministic(self):
        request = payload(features={"ndmi_change": -.1, "rainfall_anomaly": -1})
        self.assertEqual(self.engine.evaluate(request), self.engine.evaluate(request))


if __name__ == "__main__":
    unittest.main()
