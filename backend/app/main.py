from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
from backend.app.config import API_PREFIX, CORS_ORIGINS
from backend.app.persistence import Repository
from backend.app.services import AnalysisService, DomainError, FarmService

repo=Repository(); farms=FarmService(repo); analysis=AnalysisService(repo)
app=FastAPI(title="FarmSightAI")
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_methods=["GET","POST"],allow_headers=["Content-Type","Idempotency-Key","X-Demo-User-Id"])
def envelope(**body): return {"request_id":str(uuid4()),**body}
@app.exception_handler(DomainError)
async def errors(_, exc): return JSONResponse(status_code=exc.status,content=envelope(error={"code":exc.code,"message":exc.message,"details":[]}))
@app.get("/health")
def health(): return envelope(status="ok")
@app.get(API_PREFIX+"/users/{user_id}/farms")
def user_farms(user_id:str):
    if user_id not in repo.users: raise DomainError("invalid_user", "User not found", 404)
    user_farm_list = [f for f in repo.farms.values() if f.get("owner_user_id") == user_id]
    return envelope(farms=user_farm_list)
@app.post(API_PREFIX+"/farms",status_code=201)
async def create_farm(request:Request,idempotency_key:str|None=Header(None,alias="Idempotency-Key"),demo_user_id:str|None=Header(None,alias="X-Demo-User-Id")): return envelope(farm=farms.create(await request.json(),idempotency_key,demo_user_id))
@app.get(API_PREFIX+"/farms/{farm_id}")
def farm(farm_id:str): return envelope(farm=farms.get(farm_id))
@app.post(API_PREFIX+"/farms/{farm_id}/analyze",status_code=202)
async def submit(farm_id:str,request:Request,idempotency_key:str|None=Header(None,alias="Idempotency-Key")):
    run=analysis.submit(farm_id,await request.json(),idempotency_key); return envelope(analysis_run=run)
@app.get(API_PREFIX+"/analysis-runs/{run_id}")
def get_run(run_id:str):
    if run_id not in repo.runs: raise DomainError("analysis_not_found","analysis run was not found",404)
    # Minimal local job runner: submission remains queued; the polling boundary runs
    # the existing integrations without introducing a queue dependency.
    if repo.runs[run_id]["status"] == "queued": analysis.execute(run_id)
    return envelope(analysis_run=repo.runs[run_id])
def result(zone_id,run_id=None):
    zone=repo.zones.get(zone_id)
    if not zone: raise DomainError("zone_not_found","zone was not found",404)
    runs=[r for r in repo.runs.values() if r["farm_id"]==zone["farm_id"] and r["status"] in {"completed","partial"}]
    if run_id and run_id not in repo.runs: raise DomainError("analysis_not_found","analysis run was not found",404)
    run=repo.runs.get(run_id) if run_id else max(runs,key=lambda r:r["requested_at"],default=None)
    if run and run["farm_id"] != zone["farm_id"]: raise DomainError("analysis_not_found","analysis run does not belong to this farm",404)
    res = repo.results.get((run["id"],zone_id)) if run else None
    if not res: return zone, run, None, None
    ev = repo.evidence.get(res["evidence_id"])
    rec = repo.recommendations.get(res["recommendation_id"])
    return zone, run, ev, rec
def freshness(item):
    if not item: return {"overall_status":"missing","items":[]}
    metadata=item["feature_set"]["feature_metadata"]
    items=[{"signal_type":name,"status":meta["freshness"]["status"],"last_observation_time":meta.get("observation_timestamp"),"source":meta.get("source",{}),"freshness":meta["freshness"],"missing_reason":meta.get("missing_reason")} for name,meta in metadata.items()]
    statuses={entry["status"] for entry in items}; return {"overall_status":"stale" if "stale" in statuses else "fresh" if "fresh" in statuses else "missing","items":items}
@app.get(API_PREFIX+"/farms/{farm_id}/zones")
def zones(farm_id:str,analysis_run_id:str|None=None):
    farms.get(farm_id); items=[]
    for zone in [z for z in repo.zones.values() if z["farm_id"]==farm_id]:
        _,run,ev,rec=result(zone["id"],analysis_run_id); items.append({"zone":zone,"latest_prediction":ev["prediction"] if ev else {"status":"insufficient_data","risk_level":"unknown"},"data_freshness":freshness(ev),"recommendation_status":rec["recommendation"]["status"] if rec else "not_available"})
    return envelope(farm_id=farm_id,analysis_run_id=analysis_run_id,zones=items)
@app.get(API_PREFIX+"/zones/{zone_id}/evidence")
def evidence(zone_id:str,analysis_run_id:str|None=None):
    zone,run,ev,rec=result(zone_id,analysis_run_id); fs=ev["feature_set"] if ev else None
    return envelope(zone_id=zone_id,analysis_run_id=run["id"] if run else None,prediction=ev["prediction"] if ev else None,evidence=[] if not fs else [{"feature_name":k,"value":v,"unit":fs["feature_metadata"][k]["unit"],"source":fs["feature_metadata"][k].get("source"),"source_observation_ids":fs["feature_metadata"][k].get("source_observation_ids",[]),"observation_time":fs["feature_metadata"][k].get("observation_timestamp"),"retrieval_timestamp":fs["feature_metadata"][k].get("retrieval_timestamp"),"spatial_aggregation":fs["feature_metadata"][k].get("spatial_aggregation"),"spatial_resolution_m":fs["feature_metadata"][k].get("spatial_resolution_m"),"calculation":fs["feature_metadata"][k].get("calculation"),"freshness":fs["feature_metadata"][k]["freshness"],"missing_reason":fs["feature_metadata"][k].get("missing_reason"),"quality_flags":[]} for k,v in fs["features"].items()],data_freshness=freshness(ev),limitations=rec["recommendation"]["limitations"] if rec else ["No analysis available"])
@app.get(API_PREFIX+"/zones/{zone_id}/recommendation")
def recommendation(zone_id:str,analysis_run_id:str|None=None):
    _,run,ev,rec=result(zone_id,analysis_run_id); return envelope(zone_id=zone_id,analysis_run_id=run["id"] if run else None,recommendation=rec["recommendation"] if rec else {"status":"not_available","action":None,"limitations":["No analysis available"]})
