from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4
from backend.app.config import API_PREFIX, CORS_ORIGINS
from backend.app.persistence import Repository
from backend.app.services import AnalysisService, DomainError, FarmService

repo=Repository(); farms=FarmService(repo); analysis=AnalysisService(repo)
app=FastAPI(title="FarmSightAI")
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_methods=["GET","POST"],allow_headers=["Content-Type","Idempotency-Key"])
def envelope(**body): return {"request_id":str(uuid4()),**body}
@app.exception_handler(DomainError)
async def errors(_, exc): return JSONResponse(exc.status,envelope(error={"code":exc.code,"message":exc.message,"details":[]}))
@app.get("/health")
def health(): return envelope(status="ok")
@app.post(API_PREFIX+"/farms",status_code=201)
async def create_farm(request:Request,idempotency_key:str|None=Header(None,alias="Idempotency-Key")): return envelope(farm=farms.create(await request.json(),idempotency_key))
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
    run=repo.runs.get(run_id) if run_id else max(runs,key=lambda r:r["requested_at"],default=None)
    return zone,run,repo.results.get((run["id"],zone_id)) if run else None
@app.get(API_PREFIX+"/farms/{farm_id}/zones")
def zones(farm_id:str,analysis_run_id:str|None=None):
    farms.get(farm_id); items=[]
    for zone in [z for z in repo.zones.values() if z["farm_id"]==farm_id]:
        _,run,item=result(zone["id"],analysis_run_id); items.append({"zone":zone,"latest_prediction":item["prediction"] if item else {"status":"insufficient_data","risk_level":"unknown"},"recommendation_status":item["recommendation"]["status"] if item else "not_available"})
    return envelope(farm_id=farm_id,analysis_run_id=analysis_run_id,zones=items)
@app.get(API_PREFIX+"/zones/{zone_id}/evidence")
def evidence(zone_id:str,analysis_run_id:str|None=None):
    zone,run,item=result(zone_id,analysis_run_id); fs=item["feature_set"] if item else None
    return envelope(zone_id=zone_id,analysis_run_id=run["id"] if run else None,prediction=item["prediction"] if item else None,evidence=[] if not fs else [{"feature_name":k,"value":v,"unit":fs["feature_metadata"][k]["unit"],"source":fs["feature_metadata"][k].get("source",{}),"observation_time":fs["feature_metadata"][k].get("observation_timestamp"),"quality_flags":[]} for k,v in fs["features"].items() if v is not None],data_freshness={"overall_status":"missing","items":[]},limitations=item["recommendation"]["limitations"] if item else ["No analysis available"])
@app.get(API_PREFIX+"/zones/{zone_id}/recommendation")
def recommendation(zone_id:str,analysis_run_id:str|None=None):
    _,run,item=result(zone_id,analysis_run_id); return envelope(zone_id=zone_id,analysis_run_id=run["id"] if run else None,recommendation=item["recommendation"] if item else {"status":"not_available","action":None,"limitations":["No analysis available"]})
