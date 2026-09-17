from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
from backend.app.config import settings
from backend.app.persistence.repository import InMemoryRepository
from backend.app.services import AnalysisService, DomainError, FarmService

repo = InMemoryRepository()
farms, analysis = FarmService(repo), AnalysisService(repo)
app = FastAPI(title="FarmSightAI", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Idempotency-Key"])


def response(**body): return {"request_id": str(uuid4()), **body}


@app.exception_handler(DomainError)
async def domain_error(_, exc):
    return JSONResponse(status_code=exc.status, content=response(error={"code": exc.code, "message": exc.message, "details": exc.details}))


@app.get("/health")
def health(): return response(status="ok", provider_mode=settings.provider_mode)


@app.post(f"{settings.api_prefix}/farms", status_code=201)
async def create_farm(request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    return response(farm=farms.create(await request.json(), idempotency_key))


@app.get(f"{settings.api_prefix}/farms/{{farm_id}}")
def get_farm(farm_id: str):
    farm = farms.farm(farm_id)
    latest = repo.latest_run_for(farm_id)
    return response(farm=farm, **({"latest_analysis": {key: latest[key] for key in ("id", "status", "analysis_reference_time")}} if latest else {}))


@app.post(f"{settings.api_prefix}/farms/{{farm_id}}/analyze", status_code=202)
async def analyze(farm_id: str, request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    run, replayed = analysis.submit(farm_id, await request.json(), idempotency_key)
    # Contract submission response is queued even though the local fixture worker has completed it inline.
    submission = {key: run[key] for key in ("id", "farm_id", "requested_at", "analysis_reference_time")}
    submission["status"] = "queued" if not replayed else run["status"]
    return response(analysis_run=submission)


@app.get(f"{settings.api_prefix}/analysis-runs/{{analysis_run_id}}")
def get_analysis(analysis_run_id: str): return response(analysis_run=analysis.get_run(analysis_run_id))


def selected_run(farm_id, analysis_run_id):
    run = analysis.get_run(analysis_run_id) if analysis_run_id else repo.latest_run_for(farm_id)
    if run and run["farm_id"] != farm_id: raise DomainError("analysis_not_found", "analysis run does not belong to this farm", 404)
    return run


@app.get(f"{settings.api_prefix}/farms/{{farm_id}}/zones")
def zones(farm_id: str, analysis_run_id: str | None = None):
    farms.farm(farm_id); run = selected_run(farm_id, analysis_run_id)
    items = []
    for zone in repo.zones_for(farm_id):
        result = repo.results.get((run["id"], zone["id"])) if run else None
        items.append({"zone": zone, "latest_prediction": result["prediction"] if result else {"status": "insufficient_data", "risk_level": "unknown"}, "data_freshness": overall_freshness(result), "recommendation_status": result["recommendation"]["status"] if result else "not_available"})
    return response(farm_id=farm_id, analysis_run_id=run["id"] if run else None, zones=items)


@app.get(f"{settings.api_prefix}/zones/{{zone_id}}")
def get_zone(zone_id: str, analysis_run_id: str | None = None):
    zone = repo.zones.get(zone_id)
    if not zone: raise DomainError("zone_not_found", "zone was not found", 404)
    run = selected_run(zone["farm_id"], analysis_run_id)
    result = repo.results.get((run["id"], zone_id)) if run else None
    return response(zone=zone, farm=farms.farm(zone["farm_id"]), analysis_run_id=run["id"] if run else None, latest_prediction=result["prediction"] if result else None, data_freshness=overall_freshness(result), latest_recommendation=result["recommendation"] if result else None)


def overall_freshness(result):
    if not result: return {"overall_status": "unknown", "items": []}
    items = [o["freshness"] | {"metric": o["metric"]} for o in result["feature_set"]["observations"]]
    return {"overall_status": "stale" if any(x["status"] == "stale" for x in items) else "fresh", "items": items}


@app.get(f"{settings.api_prefix}/zones/{{zone_id}}/evidence")
def evidence(zone_id: str, analysis_run_id: str | None = None):
    zone = repo.zones.get(zone_id)
    if not zone: raise DomainError("zone_not_found", "zone was not found", 404)
    run = selected_run(zone["farm_id"], analysis_run_id)
    result = repo.results.get((run["id"], zone_id)) if run else None
    return response(zone_id=zone_id, analysis_run_id=run["id"] if run else None, prediction=result["prediction"] if result else None, evidence=result["evidence"] if result else [], data_freshness=overall_freshness(result), limitations=result["recommendation"]["limitations"] if result else ["No completed analysis is available"])


@app.get(f"{settings.api_prefix}/zones/{{zone_id}}/recommendation")
def recommendation(zone_id: str, analysis_run_id: str | None = None):
    zone = repo.zones.get(zone_id)
    if not zone: raise DomainError("zone_not_found", "zone was not found", 404)
    run = selected_run(zone["farm_id"], analysis_run_id)
    result = repo.results.get((run["id"], zone_id)) if run else None
    recommendation = result["recommendation"] if result else {"status": "not_available", "action": None, "limitations": ["No completed analysis is available"]}
    return response(zone_id=zone_id, analysis_run_id=run["id"] if run else None, recommendation=recommendation)
