import os
import json
from datetime import datetime, timezone

# We override the environment variable before importing services
os.environ["PROVIDER_MODE"] = "real"

from backend.app.persistence import Repository
from backend.app.services import FarmService, AnalysisService

def run_smoke_test():
    print("=" * 60)
    print("LAP 7: REAL DATA INTEGRATION - E2E SMOKE TEST")
    print("=" * 60)
    
    # 1. Realistic Tamil Nadu Farm (Thanjavur, Cauvery Delta region)
    payload = {
        "name": "Cauvery Delta Field",
        "location": {"type": "Point", "coordinates": [79.13, 10.78]}, # lon, lat
        "boundary": {
            "type": "Polygon",
            "coordinates": [
                [
                    [79.13, 10.78],
                    [79.14, 10.78],
                    [79.14, 10.79],
                    [79.13, 10.79],
                    [79.13, 10.78]
                ]
            ]
        },
        "crop": "rice",
        "sowing_date": "2026-08-01",
        "timezone": "Asia/Kolkata"
    }

    repo = Repository()
    
    # Run 1: REAL MODE
    print("\n[ RUN 1: REAL DATA MODE ]")
    print(f"Submitting Tamil Nadu Farm at Coordinates: {payload['location']['coordinates']}")
    
    farm_svc = FarmService(repo)
    farm = farm_svc.create(payload, "smoke-test-key-1")
    
    analysis_svc = AnalysisService(repo)
    run = analysis_svc.submit(farm["id"], {"reference_time": datetime.now(timezone.utc).isoformat()}, "smoke-test-run-1")
    
    result = analysis_svc.execute(run["id"])
    
    print("\n--- Pipeline Execution Status ---")
    print(f"Status: {result['status']}")
    if result.get('failure_message'):
        print(f"Failure: {result['failure_message']}")
        
    for key, val in repo.results.items():
        if key[0] == run["id"]:
            evidence = repo.evidence[val["evidence_id"]]
            features = evidence["feature_set"]
            
            print("\n--- REAL Feature Evidence ---")
            for feature in ["rainfall_30d", "temperature_mean", "ndvi_current", "soil_moisture"]:
                meta = features["feature_metadata"].get(feature, {})
                val = features["features"].get(feature)
                source = meta.get("source", {}).get("provider", "Unknown")
                reason = meta.get("missing_reason")
                status = meta.get("freshness", {}).get("status")
                
                if val is not None:
                    print(f"[+] {feature:20}: {val:7.2f} {meta.get('unit')} (Source: {source} | Freshness: {status})")
                else:
                    print(f"[-] {feature:20}: MISSING (Reason: {reason})")
                    if meta.get("calculation"):
                        print(f"   -> Details: {meta['calculation']}")
            
            print("\n--- Final Quality Status ---")
            print(features["quality_status"])

    # Run 2: FIXTURE MODE
    print("\n[ RUN 2: FIXTURE DATA MODE ]")
    os.environ["PROVIDER_MODE"] = "fixture"
    # We must instantiate a new AnalysisService to pick up the new env var
    analysis_svc_fixture = AnalysisService(repo)
    
    run_fixture = analysis_svc_fixture.submit(farm["id"], {"reference_time": datetime.now(timezone.utc).isoformat()}, "smoke-test-run-fixture")
    result_fixture = analysis_svc_fixture.execute(run_fixture["id"])
    
    for key, val in repo.results.items():
        if key[0] == run_fixture["id"]:
            evidence = repo.evidence[val["evidence_id"]]
            features = evidence["feature_set"]
            
            print("\n--- FIXTURE Feature Evidence ---")
            print(f"Quality Status: {features['quality_status']}")
            source = features['feature_metadata']['ndvi_current'].get('source', {}).get('provider', 'fixture')
            print(f"NDVI Current: {features['features']['ndvi_current']} (Source: {source})")
            
    print("\n============================================================")
    print("SMOKE TEST COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    run_smoke_test()
