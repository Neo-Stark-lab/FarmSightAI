from datetime import date, datetime, timezone
from uuid import UUID, uuid4
from data.pipeline import DataPipeline
from ml.inference import WaterStressInference
from ml.explainability import evidence_from_prediction
from backend.app.rules.recommendation_engine import recommend

SUPPORTED_CROPS = {"rice", "groundnut", "maize"}


class DomainError(Exception):
    def __init__(self, code, message, status=422, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details or []


def now(): return datetime.now(timezone.utc)


def validate_polygon(geometry):
    if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise DomainError("invalid_geometry", "boundary must be a GeoJSON Polygon or MultiPolygon")
    coordinates = geometry.get("coordinates")
    rings = coordinates if geometry["type"] == "Polygon" else (coordinates[0] if coordinates else [])
    if not rings or not isinstance(rings[0], list) or len(rings[0]) < 4 or rings[0][0] != rings[0][-1]:
        raise DomainError("invalid_geometry", "boundary must have a closed exterior ring")
    for point in rings[0]:
        if not isinstance(point, list) or len(point) < 2 or not all(isinstance(v, (int, float)) for v in point[:2]):
            raise DomainError("invalid_geometry", "boundary coordinates must be numeric longitude/latitude pairs")
        if not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
            raise DomainError("invalid_geometry", "boundary coordinates are outside EPSG:4326 bounds")
    ring = rings[0]
    def orientation(a, b, c): return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    def crosses(a, b, c, d): return orientation(a, b, c) * orientation(a, b, d) < 0 and orientation(c, d, a) * orientation(c, d, b) < 0
    for i in range(len(ring) - 1):
        for j in range(i + 2, len(ring) - 1):
            if i == 0 and j == len(ring) - 2: continue
            if crosses(ring[i], ring[i + 1], ring[j], ring[j + 1]):
                raise DomainError("invalid_geometry", "boundary must not self-intersect")


def area_hectares(boundary):
    # Small-area planar approximation only for display; original geometry is preserved.
    ring = boundary["coordinates"][0] if boundary["type"] == "Polygon" else boundary["coordinates"][0][0]
    area = abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1))) / 2
    return round(area * 1232100, 4)


class FarmService:
    def __init__(self, repo): self.repo = repo

    def create(self, payload, idempotency_key=None):
        replay = self.repo.replay("farm", idempotency_key)
        if replay: return replay
        crop = payload.get("crop", "").lower()
        if crop not in SUPPORTED_CROPS: raise DomainError("invalid_crop", "crop must be rice, groundnut, or maize")
        try: sowing_date = date.fromisoformat(payload.get("sowing_date", ""))
        except ValueError: raise DomainError("invalid_date", "sowing_date must be an ISO date")
        if sowing_date > date.today(): raise DomainError("invalid_date", "sowing_date cannot be in the future")
        boundary, location = payload.get("boundary"), payload.get("location")
        validate_polygon(boundary)
        if not isinstance(location, dict) or location.get("type") != "Point" or len(location.get("coordinates", [])) < 2:
            raise DomainError("invalid_geometry", "location must be a GeoJSON Point")
        if not payload.get("name") or len(payload["name"]) > 120: raise DomainError("invalid_farm", "name is required and must be at most 120 characters")
        timestamp, farm_id = now().isoformat(), str(uuid4())
        farm = {"id": farm_id, "name": payload["name"], "location": location, "boundary": boundary, "area_hectares": area_hectares(boundary), "crop": crop, "sowing_date": sowing_date.isoformat(), "timezone": payload.get("timezone", "Asia/Kolkata"), "status": "active", "created_at": timestamp, "updated_at": timestamp}
        self.repo.farms[farm_id] = farm
        zone = {"id": str(uuid4()), "farm_id": farm_id, "name": "Farm zone", "geometry": boundary, "area_hectares": farm["area_hectares"], "zone_method": "manual", "status": "active", "created_at": timestamp, "updated_at": timestamp}
        self.repo.zones[zone["id"]] = zone
        self.repo.remember("farm", idempotency_key, farm)
        return farm

    def farm(self, farm_id):
        farm = self.repo.farms.get(farm_id)
        if not farm: raise DomainError("farm_not_found", "farm was not found", 404)
        return farm


class AnalysisService:
    def __init__(self, repo, pipeline=None, inference=None):
        self.repo, self.pipeline, self.inference = repo, pipeline or DataPipeline(), inference or WaterStressInference()

    def submit(self, farm_id, payload, idempotency_key=None):
        farm = FarmService(self.repo).farm(farm_id)
        replay = self.repo.replay("analysis:" + farm_id, idempotency_key)
        if replay: return replay, True
        reference = now()
        if payload.get("reference_time"):
            try: reference = datetime.fromisoformat(payload["reference_time"].replace("Z", "+00:00"))
            except (ValueError, AttributeError): raise DomainError("invalid_date", "reference_time must be RFC3339")
        run = {"id": str(uuid4()), "farm_id": farm_id, "requested_at": now().isoformat(), "started_at": None, "completed_at": None, "status": "queued", "zone_count": len(self.repo.zones_for(farm_id)), "completed_zone_count": 0, "analysis_reference_time": reference.isoformat()}
        self.repo.runs[run["id"]] = run
        self.repo.remember("analysis:" + farm_id, idempotency_key, run)
        # The job boundary is retained; the local fixture worker runs inline for a usable demo.
        self.run(run["id"])
        return run, False

    def run(self, run_id):
        run = self.repo.runs[run_id]
        farm = self.repo.farms[run["farm_id"]]
        run.update(status="running", started_at=now().isoformat())
        partial = False
        try:
            reference = datetime.fromisoformat(run["analysis_reference_time"])
            for zone in self.repo.zones_for(farm["id"]):
                feature_set = self.pipeline.build_feature_set(farm=farm, zone=zone, analysis_run_id=run_id, reference_time=reference)
                prediction = self.inference.score(feature_set)
                evidence = feature_set["observations"] + evidence_from_prediction(prediction, feature_set)
                recommendation = recommend(farm=farm, zone_id=zone["id"], analysis_run_id=run_id, prediction=prediction, evidence=evidence, reference_time=reference)
                self.repo.results[(run_id, zone["id"])] = {"feature_set": feature_set, "prediction": prediction, "evidence": evidence, "recommendation": recommendation}
                run["completed_zone_count"] += 1
                partial |= feature_set["quality_status"] != "complete" or prediction["status"] != "valid"
            run["status"] = "partial" if partial else "completed"
        except Exception as error:
            run.update(status="failed", failure_code="analysis_failure", failure_message="Analysis could not be completed")
        run["completed_at"] = now().isoformat()
        return run

    def get_run(self, run_id):
        run = self.repo.runs.get(run_id)
        if not run: raise DomainError("analysis_not_found", "analysis run was not found", 404)
        return run
