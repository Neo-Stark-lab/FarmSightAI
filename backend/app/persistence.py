"""Local/test repository adapter; production is intentionally replaceable by PostGIS."""
class Repository:
    def __init__(self):
        self.farms, self.zones, self.runs, self.results, self.evidence, self.recommendations, self.keys = {}, {}, {}, {}, {}, {}, {}
        self.users = {
            "user1": {"id": "user1", "name": "Arjun Kumar", "email": "arjun@example.com", "created_at": "2024-01-01T00:00:00Z", "status": "active"},
            "user2": {"id": "user2", "name": "Meena Ravi", "email": "meena@example.com", "created_at": "2024-01-01T00:00:00Z", "status": "active"},
            "user3": {"id": "user3", "name": "Kumaravel S", "email": "kumaravel@example.com", "created_at": "2024-01-01T00:00:00Z", "status": "active"}
        }
        self._seed()
    def replay(self, scope, key, fingerprint):
        record = self.keys.get((scope, key)) if key else None
        if record and record["fingerprint"] != fingerprint: raise ValueError("idempotency_conflict")
        return record["item"] if record else None
    def remember(self, scope, key, fingerprint, item):
        if key: self.keys[(scope, key)] = {"fingerprint": fingerprint, "item": item}

    def _seed(self):
        from backend.app.services import area_hectares
        from datetime import datetime, timezone
        from uuid import uuid4
        stamp = datetime.now(timezone.utc).isoformat()
        seeds = [
            ("user1", "Cauvery Delta Rice Farm", "rice", {"type":"Point","coordinates":[79.13, 10.78]}, {"type":"Polygon","coordinates":[[[79.125,10.775],[79.135,10.775],[79.135,10.785],[79.125,10.785],[79.125,10.775]]]}),
            ("user1", "Thanjavur Rice Field", "rice", {"type":"Point","coordinates":[79.14, 10.79]}, {"type":"Polygon","coordinates":[[[79.135,10.785],[79.145,10.785],[79.145,10.795],[79.135,10.795],[79.135,10.785]]]}),
            ("user2", "Villupuram Groundnut Field", "groundnut", {"type":"Point","coordinates":[79.48, 11.94]}, {"type":"Polygon","coordinates":[[[79.475,11.935],[79.485,11.935],[79.485,11.945],[79.475,11.945],[79.475,11.935]]]}),
            ("user3", "Salem Maize Field", "maize", {"type":"Point","coordinates":[78.14, 11.66]}, {"type":"Polygon","coordinates":[[[78.135,11.655],[78.145,11.655],[78.145,11.665],[78.135,11.665],[78.135,11.655]]]})
        ]
        for owner, name, crop, loc, bound in seeds:
            ident = str(uuid4())
            farm = {"id": ident, "owner_user_id": owner, "name": name, "location": loc, "boundary": bound, "area_hectares": area_hectares(bound), "crop": crop, "sowing_date": "2024-06-01", "timezone": "Asia/Kolkata", "status": "active", "created_at": stamp, "updated_at": stamp}
            self.farms[ident] = farm
            zone = {"id": str(uuid4()), "farm_id": ident, "name": "Farm zone", "geometry": bound, "area_hectares": farm["area_hectares"], "zone_method": "manual", "status": "active", "created_at": stamp, "updated_at": stamp}
            self.zones[zone["id"]] = zone
