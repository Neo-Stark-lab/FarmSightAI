"""Deterministic agricultural interpretation; it never modifies ML risk."""

from __future__ import annotations

from typing import Any

from .rule_loader import load_rules
from .schemas import RuleInput


SATELLITE_FEATURES = {"ndvi_current", "ndvi_7d_change", "ndvi_30d_change", "ndmi_current", "ndmi_change"}
WEATHER_FEATURES = {"rainfall_7d", "rainfall_30d", "rainfall_anomaly", "temperature_mean", "temperature_anomaly"}


class RecommendationEngine:
    def __init__(self, policy_path: str | None = None) -> None:
        self.policy = load_rules(policy_path)
        self.version = self.policy["version"]

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = RuleInput.from_payload(payload)
        prediction = data.prediction
        risk = prediction.get("risk_level", "unknown")
        valid = prediction.get("status") == "valid" and risk in {"low", "moderate", "high"}
        limitations = self._limitations(data)
        refs = self._references(data)
        signals = self._water_signals(data)
        conflicts = self._conflicts(data)
        causes = self._causes(data, signals)
        rule_ids: list[str] = []

        if not valid:
            rule_ids.append("WS005")
            return self._result(data, "not_available", "medium", None, None, rule_ids, [],
                                refs, causes or [{"cause": "unknown", "evidence_strength": "very_low"}],
                                limitations + ["A valid water-stress prediction is unavailable."],
                                "A reliable recommendation is unavailable because the prediction is not valid.")

        stage_priority = data.crop_stage == "reproductive" and risk in {"moderate", "high"}
        if stage_priority:
            rule_ids.append("CS001")

        if risk == "high" and len(signals) >= 2 and not conflicts:
            rule_ids.insert(0, "WS001")
            return self._result(data, "active", "high", "CONSIDER_IRRIGATION",
                                "Prioritize checking this zone and consider irrigation based on local field conditions.",
                                rule_ids, signals, refs, causes, limitations,
                                self._water_explanation(signals))

        if signals and conflicts:
            rule_ids.insert(0, "WS002")
            return self._result(data, "active", "high" if stage_priority else "medium", "REASSESS_AFTER_RAINFALL",
                                "Reassess this zone after recent rainfall and verify field conditions before irrigating.",
                                rule_ids, signals + conflicts, refs, causes,
                                limitations + ["Water-stress signals conflict with recent rainfall or recovery indicators."],
                                "Water-stress signals conflict with " + ", ".join(conflicts) + ".")

        if self._has_stale_satellite(data) or self._missing_key_context(data):
            rule_ids.insert(0, "WS003")
            return self._result(data, "active", "high" if stage_priority else "medium", "PRIORITIZE_FIELD_CHECK",
                                "Prioritize a field check because available evidence is incomplete, stale, or conflicting.",
                                rule_ids, signals, refs, causes, limitations,
                                "Recommendation strength is reduced by incomplete or stale supporting evidence.")

        if risk in {"moderate", "high"}:
            rule_ids.insert(0, "WS004")
            return self._result(data, "active", "high" if stage_priority else "medium", "PRIORITIZE_FIELD_CHECK",
                                "Prioritize checking this zone before making an irrigation decision.",
                                rule_ids, signals, refs, causes, limitations,
                                "The model indicates water-stress risk, but supporting field-context evidence is limited.")

        return self._result(data, "active", "low", "MONITOR",
                            "Monitor this zone and check crop condition if visible changes continue.",
                            ["WS006"], signals, refs, causes or [{"cause": "unknown", "evidence_strength": "very_low"}],
                            limitations, "Available evidence does not support a stronger action at this time.")

    def _fresh(self, data: RuleInput, key: str) -> bool:
        return data.features.get(key) is not None and data.feature_metadata.get(key, {}).get("freshness", {}).get("status") != "stale"

    def _negative(self, data: RuleInput, key: str) -> bool:
        return self._fresh(data, key) and isinstance(data.features[key], (int, float)) and data.features[key] < 0

    def _water_signals(self, data: RuleInput) -> list[str]:
        signals: list[str] = []
        if self._negative(data, "ndvi_7d_change") or self._negative(data, "ndvi_30d_change") or self._negative(data, "ndmi_change"):
            signals.append("declining vegetation or moisture indicator")
        if self._negative(data, "rainfall_anomaly"):
            signals.append("rainfall below its documented baseline")
        if self._negative(data, "soil_moisture_change") or data.evidence_flags.get("soil_moisture_low"):
            signals.append("declining or low source-attributed soil-moisture context")
        return signals

    def _conflicts(self, data: RuleInput) -> list[str]:
        conflicts: list[str] = []
        if data.evidence_flags.get("recent_rainfall"):
            conflicts.append("recent source-attributed rainfall")
        trend_keys = ("ndvi_7d_change", "ndmi_change", "soil_moisture_change")
        # A stable feature is not a recovery signal when another contemporaneous
        # feature already records decline. This prevents one neutral indicator
        # from cancelling a converging multi-source pattern.
        if not any(self._negative(data, key) for key in trend_keys):
            for key in trend_keys:
                value = data.features.get(key)
                if self._fresh(data, key) and isinstance(value, (int, float)) and value >= 0:
                    conflicts.append("stable or improving " + key)
                    break
        return conflicts

    def _causes(self, data: RuleInput, water_signals: list[str]) -> list[dict[str, str]]:
        causes: list[dict[str, str]] = []
        risk = data.prediction.get("risk_level")
        if risk in {"moderate", "high"} or water_signals:
            causes.append({"cause": "water_stress", "evidence_strength": "high" if len(water_signals) >= 2 and risk == "high" else "moderate"})
        if self._fresh(data, "temperature_anomaly") and data.features["temperature_anomaly"] > 0:
            causes.append({"cause": "heat_stress", "evidence_strength": "moderate"})
        vegetation = any("vegetation" in signal for signal in water_signals)
        if vegetation and len(water_signals) < 2:
            causes.extend([
                {"cause": "nutrient_stress", "evidence_strength": "low"},
                {"cause": "pest_disease_related_stress", "evidence_strength": "low"},
            ])
        return causes

    def _limitations(self, data: RuleInput) -> list[str]:
        notes: list[str] = []
        for key in sorted(data.features):
            meta = data.feature_metadata.get(key, {})
            if data.features[key] is None:
                reason = meta.get("missing_reason", "not documented")
                notes.append(f"{key} is unavailable ({reason}).")
        if data.crop_stage == "unknown":
            notes.append("Crop stage is unavailable; stage-dependent interpretation is limited.")
        if self._has_stale_satellite(data):
            notes.append("Satellite-derived evidence is stale and is not treated as current field condition.")
        return notes

    def _has_stale_satellite(self, data: RuleInput) -> bool:
        return any(data.feature_metadata.get(key, {}).get("freshness", {}).get("status") == "stale" for key in SATELLITE_FEATURES)

    def _missing_key_context(self, data: RuleInput) -> bool:
        return all(data.features.get(key) is None for key in ("rainfall_anomaly", "soil_moisture", "soil_moisture_change"))

    def _references(self, data: RuleInput) -> list[str]:
        refs = set()
        for meta in data.feature_metadata.values():
            refs.update(meta.get("source_observation_ids", []) or [])
        return sorted(refs)

    def _water_explanation(self, signals: list[str]) -> str:
        return "Water-stress risk is elevated because " + ", ".join(signals) + "."

    def _result(self, data: RuleInput, status: str, priority: str, action_type: str | None, action: str | None,
                rule_ids: list[str], conditions: list[str], references: list[str], causes: list[dict[str, str]],
                limitations: list[str], explanation: str) -> dict[str, Any]:
        return {
            "status": status, "priority": priority, "action_type": action_type, "action": action,
            "rule_set_version": self.version, "rule_ids": rule_ids,
            "triggered_conditions": conditions, "supporting_features": conditions,
            "rationale_evidence_ids": references, "crop": data.crop, "crop_stage": data.crop_stage,
            "data_freshness": {key: meta.get("freshness", {"status": "unknown"}) for key, meta in sorted(data.feature_metadata.items())},
            "possible_causes": causes, "limitations": sorted(set(limitations)), "explanation": explanation,
        }
