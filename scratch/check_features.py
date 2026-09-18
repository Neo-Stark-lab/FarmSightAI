import os
import json
from datetime import datetime, timezone
import yaml

os.environ["PROVIDER_MODE"] = "real"
from backend.app.persistence import Repository
from backend.app.services import FarmService, AnalysisService
from ml.preprocessing import FEATURE_ORDER

def run():
    payload = {
        "name": "Cauvery Delta Field",
        "location": {"type": "Point", "coordinates": [79.13, 10.78]}, # lon, lat
        "boundary": {
            "type": "Polygon",
            "coordinates": [[[79.13, 10.78], [79.14, 10.78], [79.14, 10.79], [79.13, 10.79], [79.13, 10.78]]]
        },
        "crop": "rice",
        "sowing_date": "2026-08-01",
        "timezone": "Asia/Kolkata"
    }

    repo = Repository()
    farm_svc = FarmService(repo)
    farm = farm_svc.create(payload, "smoke-test-key-1")
    
    analysis_svc = AnalysisService(repo)
    run = analysis_svc.submit(farm["id"], {"reference_time": datetime.now(timezone.utc).isoformat()}, "smoke-test-run-1")
    
    result = analysis_svc.execute(run["id"])
    
    for key, val in repo.results.items():
        if key[0] == run["id"]:
            evidence = repo.evidence[val["evidence_id"]]
            features = evidence["feature_set"]
            
            print("=== QUALITY STATUS ===")
            print(features["quality_status"])
            
            print("\n=== 16-FEATURE VECTOR ===")
            for f in FEATURE_ORDER:
                val = features["features"].get(f)
                meta = features["feature_metadata"].get(f, {})
                print(f"{f:25} = {val} ({meta.get('missing_reason')})")
                
            print("\n=== NDMI PROVENANCE ===")
            print(json.dumps(features["feature_metadata"].get("ndmi_current"), indent=2))
            
            print("\n=== NDVI PROVENANCE ===")
            print(json.dumps(features["feature_metadata"].get("ndvi_current"), indent=2))
            
            print("\n=== ERA5 PROVENANCE ===")
            print(json.dumps(features["feature_metadata"].get("soil_moisture"), indent=2))
            
            print("\n=== MISSING REASONS ===")
            for f in FEATURE_ORDER:
                meta = features["feature_metadata"].get(f, {})
                if meta.get("missing_reason"):
                    print(f"{f}: {meta.get('missing_reason')} -> {meta.get('calculation')}")

run()
