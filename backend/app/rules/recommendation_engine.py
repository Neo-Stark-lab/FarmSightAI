"""Conservative recommendation boundary, separate from prediction."""
from datetime import timedelta
from uuid import uuid4


def recommend(*, farm, zone_id, analysis_run_id, prediction, evidence, reference_time):
    limitations = list(prediction["confidence"]["basis"])
    if prediction["status"] != "valid":
        return {"status": "not_available", "priority": "low", "action": None, "conditions": [], "limitations": limitations, "rule_set_version": "fixture-conservative-1"}
    return {"id": str(uuid4()), "farm_id": farm["id"], "zone_id": zone_id, "analysis_run_id": analysis_run_id, "status": "active", "priority": {"low": "low", "moderate": "medium", "high": "high"}[prediction["risk_level"]], "action": "Prioritize field verification and consider irrigation assessment if the root zone is dry; reassess if meaningful rainfall is expected.", "conditions": ["Verify field conditions before acting", "Do not infer an exact irrigation quantity from this analysis"], "rationale_evidence_ids": [item["id"] for item in evidence], "rule_set_version": "fixture-conservative-1", "issued_at": reference_time.isoformat(), "valid_until": (reference_time + timedelta(days=2)).isoformat(), "limitations": limitations}
