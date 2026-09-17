import os
import json
from datetime import datetime, timezone

# Override the environment variable before importing services
os.environ["PROVIDER_MODE"] = "real"

from backend.app.persistence import Repository
from backend.app.services import FarmService, AnalysisService
from ml.dataset import generate_synthetic_dataset
import ml.inference

def run_smoke_test():
    print("=" * 60)
    print("LAP 8: E2E INTELLIGENCE INTEGRATION - SMOKE TEST")
    print("=" * 60)
    
    # Train the model so it can predict (in a real production environment this would be pre-loaded)
    if not ml.inference._model_instance.is_trained:
        print("[System] Training model quickly for E2E validation...")
        df = generate_synthetic_dataset(100)
        ml.inference._model_instance.train(df)

    # 1. Realistic Tamil Nadu Farm
    payload = {
        "name": "Tamil Nadu Rice Field",
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
            prediction = evidence["prediction"]
            rec = repo.recommendations[val["recommendation_id"]]["recommendation"]
            
            print("\n--- 1. REAL Feature Evidence (Sample) ---")
            for feature in ["rainfall_30d", "temperature_mean", "ndvi_current", "soil_moisture"]:
                meta = features["feature_metadata"].get(feature, {})
                v = features["features"].get(feature)
                source = meta.get("source", {}).get("provider", "Unknown")
                reason = meta.get("missing_reason")
                status = meta.get("freshness", {}).get("status")
                
                if v is not None:
                    print(f"[+] {feature:20}: {v:7.2f} {meta.get('unit')} (Source: {source} | Freshness: {status})")
                else:
                    print(f"[-] {feature:20}: MISSING (Reason: {reason})")
            
            print("\n--- 2. ML Integration ---")
            print(f"ML Status: {prediction['status']}")
            print(f"Risk Level: {prediction['risk_level']}")
            print(f"Probability: {prediction['probability']}")
            print(f"Confidence Level: {prediction['confidence']['level']}")
            print(f"Confidence Basis: {prediction['confidence']['basis']}")

            print("\n--- 3. SHAP Explanations ---")
            if not prediction["contributions"]:
                print("(No SHAP contributions generated because prediction status is not valid)")
            for contrib in prediction["contributions"][:3]: # print top 3
                print(f"- {contrib['feature']}: {contrib['direction']} (Magnitude: {contrib['magnitude']})")
                
            print("\n--- 4. Recommendation Engine ---")
            print(f"Status: {rec['status']}")
            print(f"Action: {rec['action_type']}")
            print(f"Explanation: {rec['explanation']}")

    # Run 2: FIXTURE MODE
    print("\n[ RUN 2: FIXTURE DATA MODE ]")
    os.environ["PROVIDER_MODE"] = "fixture"
    analysis_svc_fixture = AnalysisService(repo)
    
    run_fixture = analysis_svc_fixture.submit(farm["id"], {"reference_time": datetime.now(timezone.utc).isoformat()}, "smoke-test-run-fixture")
    result_fixture = analysis_svc_fixture.execute(run_fixture["id"])
    
    for key, val in repo.results.items():
        if key[0] == run_fixture["id"]:
            evidence = repo.evidence[val["evidence_id"]]
            features = evidence["feature_set"]
            prediction = evidence["prediction"]
            rec = repo.recommendations[val["recommendation_id"]]["recommendation"]
            
            print("\n--- FIXTURE Evidence ---")
            source = features['feature_metadata']['ndvi_current'].get('source', {}).get('provider', 'fixture')
            print(f"NDVI Current: {features['features']['ndvi_current']} (Source: {source})")
            print(f"ML Status: {prediction['status']} (Risk: {prediction['risk_level']})")
            print(f"Recommendation: {rec['action_type']}")
            
    print("\n============================================================")
    print("SMOKE TEST COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    run_smoke_test()
