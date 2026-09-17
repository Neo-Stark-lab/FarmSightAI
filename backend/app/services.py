from datetime import date, datetime, timezone
import hashlib, json, math
from zoneinfo import ZoneInfo
from uuid import uuid4
from data.pipeline import AnalysisContext, DataPipeline
from data.providers import FixtureProvider, OpenMeteoProvider, GoogleEarthEngineProvider, ERA5LandProvider
from backend.app.config import PROVIDER_MODE
from ml.inference import score_water_stress
from backend.app.rules.recommendation_engine import RecommendationEngine

class DomainError(Exception):
    def __init__(self, code, message, status=422): self.code, self.message, self.status = code, message, status
def utcnow(): return datetime.now(timezone.utc)

def geometry(value, point=False):
    wanted = "Point" if point else None
    if not isinstance(value, dict) or (point and value.get("type") != wanted) or (not point and value.get("type") not in {"Polygon","MultiPolygon"}): raise DomainError("invalid_geometry", "must be GeoJSON Point, Polygon, or MultiPolygon")
    coords = value.get("coordinates", []); ring = coords if point else (coords[0] if value["type"] == "Polygon" else coords[0][0] if coords else [])
    if point:
        valid = len(coords) == 2 and all(isinstance(n, (int, float)) for n in coords)
    else: valid = len(ring) >= 4 and ring[0] == ring[-1] and all(len(p) >= 2 and all(isinstance(n, (int,float)) and -180 <= p[0] <= 180 and -90 <= p[1] <= 90 for n in p[:2]) for p in ring)
    if not valid: raise DomainError("invalid_geometry", "coordinates are malformed")

def fingerprint(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",",":"), default=str).encode()).hexdigest()
def area_hectares(boundary):
    # Spherical-ring area (Chamberlain-Duquette); never treats degrees as metres.
    rings = boundary["coordinates"] if boundary["type"] == "Polygon" else [poly[0] for poly in boundary["coordinates"]]
    total = 0.0
    for ring in rings:
        total += abs(sum(math.radians(ring[i+1][0]-ring[i][0])*(2+math.sin(math.radians(ring[i][1]))+math.sin(math.radians(ring[i+1][1]))) for i in range(len(ring)-1))) * 6371008.8**2 / 2
    return round(total / 10000, 6)

class FarmService:
    def __init__(self, repo): self.repo = repo
    def create(self, value, key):
        try: cached = self.repo.replay("farm", key, fingerprint(value))
        except ValueError: raise DomainError("idempotency_conflict", "Idempotency-Key was already used with a different request", 409)
        if cached: return cached
        crop = value.get("crop", "").lower()
        if crop not in {"rice","groundnut","maize"}: raise DomainError("invalid_crop", "crop must be rice, groundnut, or maize")
        try: sowing = date.fromisoformat(value["sowing_date"])
        except (KeyError, ValueError): raise DomainError("invalid_date", "sowing_date must be ISO-8601")
        if sowing > date.today(): raise DomainError("invalid_date", "sowing_date cannot be in the future")
        geometry(value.get("boundary")); geometry(value.get("location"), True)
        try: ZoneInfo(value.get("timezone", "Asia/Kolkata"))
        except Exception: raise DomainError("invalid_farm", "timezone must be an IANA timezone")
        if not isinstance(value.get("name"), str) or not value["name"].strip(): raise DomainError("invalid_farm", "name is required")
        stamp, ident = utcnow().isoformat(), str(uuid4())
        farm = {"id":ident,"name":value["name"],"location":value["location"],"boundary":value["boundary"],"area_hectares":area_hectares(value["boundary"]),"crop":crop,"sowing_date":sowing.isoformat(),"timezone":value.get("timezone","Asia/Kolkata"),"status":"active","created_at":stamp,"updated_at":stamp}
        self.repo.farms[ident] = farm
        zone = {"id":str(uuid4()),"farm_id":ident,"name":"Farm zone","geometry":farm["boundary"],"area_hectares":farm["area_hectares"],"zone_method":"manual","status":"active","created_at":stamp,"updated_at":stamp}
        self.repo.zones[zone["id"]] = zone; self.repo.remember("farm", key, fingerprint(value), farm); return farm
    def get(self, ident):
        if ident not in self.repo.farms: raise DomainError("farm_not_found", "farm was not found", 404)
        return self.repo.farms[ident]

class AnalysisService:
    def __init__(self, repo, providers=None): self.repo, self.providers, self.rules = repo, self._providers() if providers is None else providers, RecommendationEngine()
    def _providers(self):
        if PROVIDER_MODE == "fixture": return (FixtureProvider(()),)
        if PROVIDER_MODE == "weather": return (OpenMeteoProvider(),)
        if PROVIDER_MODE == "live": return (OpenMeteoProvider(), GoogleEarthEngineProvider(), ERA5LandProvider())
        raise RuntimeError("unsupported PROVIDER_MODE")
    def submit(self, farm_id, payload, key):
        FarmService(self.repo).get(farm_id)
        try: cached=self.repo.replay("analysis:"+farm_id,key,fingerprint(payload))
        except ValueError: raise DomainError("idempotency_conflict", "Idempotency-Key was already used with a different request", 409)
        if cached: return cached
        try: ref=datetime.fromisoformat(payload.get("reference_time", utcnow().isoformat()).replace("Z","+00:00"))
        except (ValueError, AttributeError): raise DomainError("invalid_date", "reference_time must be RFC3339")
        ident = str(uuid4()); run={"id":ident,"farm_id":farm_id,"requested_at":utcnow().isoformat(),"status":"queued","zone_count":len([z for z in self.repo.zones.values() if z["farm_id"]==farm_id]),"completed_zone_count":0,"analysis_reference_time":ref.isoformat(),"force_refresh":bool(payload.get("force_refresh",False))}
        self.repo.runs[ident]=run; self.repo.remember("analysis:"+farm_id,key,fingerprint(payload),run); return run
    def execute(self, run_id):
        run=self.repo.runs[run_id]; farm=self.repo.farms[run["farm_id"]]; run["status"]="running"; partial=False
        try:
          for zone in [z for z in self.repo.zones.values() if z["farm_id"]==farm["id"]]:
            context=AnalysisContext(farm_id=farm["id"],zone_id=zone["id"],crop=farm["crop"],sowing_date=date.fromisoformat(farm["sowing_date"]),reference_time=datetime.fromisoformat(run["analysis_reference_time"]),analysis_run_id=run_id,feature_set_id=str(uuid4()),request_id=str(uuid4()),boundary=zone["geometry"],location=tuple(farm["location"]["coordinates"][::-1]))
            features=DataPipeline(self.providers).build(context); response=score_water_stress(features); prediction=response["prediction"]
            recommendation=self.rules.evaluate({"prediction":prediction,"features":features["features"],"feature_metadata":features["feature_metadata"],"quality_status":features["quality_status"]})
            self.repo.results[(run_id,zone["id"])]={"feature_set":features,"prediction":prediction,"recommendation":recommendation}; run["completed_zone_count"]+=1; partial |= features["quality_status"]!="complete" or prediction["status"]!="valid"
          run["status"]="partial" if partial else "completed"
        except Exception:
          run.update(status="failed",failure_code="analysis_execution_failed",failure_message="Analysis could not be completed safely")
        run["completed_at"]=utcnow().isoformat(); return run
