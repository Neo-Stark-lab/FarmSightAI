from datetime import date, datetime, timezone
from uuid import uuid4
from data.pipeline import AnalysisContext, DataPipeline
from data.providers import FixtureProvider
from ml.inference import score_water_stress
from backend.app.rules.recommendation_engine import RecommendationEngine

class DomainError(Exception):
    def __init__(self, code, message, status=422): self.code, self.message, self.status = code, message, status
def utcnow(): return datetime.now(timezone.utc)

def geometry(value, point=False):
    wanted = "Point" if point else "Polygon"
    if not isinstance(value, dict) or value.get("type") != wanted: raise DomainError("invalid_geometry", f"must be GeoJSON {wanted}")
    coords = value.get("coordinates", []); ring = coords if point else (coords[0] if coords else [])
    if point:
        valid = len(coords) == 2 and all(isinstance(n, (int, float)) for n in coords)
    else: valid = len(ring) >= 4 and ring[0] == ring[-1] and all(len(p) >= 2 and all(isinstance(n, (int,float)) for n in p[:2]) for p in ring)
    if not valid: raise DomainError("invalid_geometry", "coordinates are malformed")

class FarmService:
    def __init__(self, repo): self.repo = repo
    def create(self, value, key):
        if cached := self.repo.replay("farm", key): return cached
        crop = value.get("crop", "").lower()
        if crop not in {"rice","groundnut","maize"}: raise DomainError("invalid_crop", "crop must be rice, groundnut, or maize")
        try: sowing = date.fromisoformat(value["sowing_date"])
        except (KeyError, ValueError): raise DomainError("invalid_date", "sowing_date must be ISO-8601")
        if sowing > date.today(): raise DomainError("invalid_date", "sowing_date cannot be in the future")
        geometry(value.get("boundary")); geometry(value.get("location"), True)
        if not isinstance(value.get("name"), str) or not value["name"].strip(): raise DomainError("invalid_farm", "name is required")
        stamp, ident = utcnow().isoformat(), str(uuid4())
        farm = {"id":ident,"name":value["name"],"location":value["location"],"boundary":value["boundary"],"area_hectares":None,"crop":crop,"sowing_date":sowing.isoformat(),"timezone":value.get("timezone","Asia/Kolkata"),"status":"active","created_at":stamp,"updated_at":stamp}
        self.repo.farms[ident] = farm
        zone = {"id":str(uuid4()),"farm_id":ident,"name":"Farm zone","geometry":farm["boundary"],"area_hectares":None,"zone_method":"manual","status":"active","created_at":stamp,"updated_at":stamp}
        self.repo.zones[zone["id"]] = zone; self.repo.remember("farm", key, farm); return farm
    def get(self, ident):
        if ident not in self.repo.farms: raise DomainError("farm_not_found", "farm was not found", 404)
        return self.repo.farms[ident]

class AnalysisService:
    def __init__(self, repo, providers=()): self.repo, self.providers, self.rules = repo, providers, RecommendationEngine()
    def submit(self, farm_id, payload, key):
        FarmService(self.repo).get(farm_id)
        if cached := self.repo.replay("analysis:"+farm_id, key): return cached
        ref = utcnow(); ident = str(uuid4()); run={"id":ident,"farm_id":farm_id,"requested_at":ref.isoformat(),"status":"queued","zone_count":len([z for z in self.repo.zones.values() if z["farm_id"]==farm_id]),"completed_zone_count":0,"analysis_reference_time":ref.isoformat()}
        self.repo.runs[ident]=run; self.repo.remember("analysis:"+farm_id,key,run); return run
    def execute(self, run_id):
        run=self.repo.runs[run_id]; farm=self.repo.farms[run["farm_id"]]; run["status"]="running"; partial=False
        for zone in [z for z in self.repo.zones.values() if z["farm_id"]==farm["id"]]:
            context=AnalysisContext(farm_id=farm["id"],zone_id=zone["id"],crop=farm["crop"],sowing_date=date.fromisoformat(farm["sowing_date"]),reference_time=datetime.fromisoformat(run["analysis_reference_time"]),analysis_run_id=run_id,feature_set_id=str(uuid4()),request_id=str(uuid4()),boundary=zone["geometry"],location=tuple(farm["location"]["coordinates"][::-1]))
            features=DataPipeline(self.providers).build(context); response=score_water_stress(features); prediction=response["prediction"]
            recommendation=self.rules.evaluate({"prediction":prediction,"features":features["features"],"feature_metadata":features["feature_metadata"],"quality_status":features["quality_status"]})
            self.repo.results[(run_id,zone["id"])]={"feature_set":features,"prediction":prediction,"recommendation":recommendation}; run["completed_zone_count"]+=1; partial |= features["quality_status"]!="complete" or prediction["status"]!="valid"
        run["status"]="partial" if partial else "completed"; run["completed_at"]=utcnow().isoformat(); return run
