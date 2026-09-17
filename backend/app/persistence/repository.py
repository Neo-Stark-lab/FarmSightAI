"""Repository boundary. In-memory storage is limited to development and tests.
Production deployments should supply a PostgreSQL/PostGIS adapter."""


class InMemoryRepository:
    def __init__(self):
        self.farms, self.zones, self.runs, self.results, self.idempotency = {}, {}, {}, {}, {}

    def replay(self, scope, key):
        return self.idempotency.get((scope, key)) if key else None

    def remember(self, scope, key, value):
        if key:
            self.idempotency[(scope, key)] = value

    def zones_for(self, farm_id):
        return [zone for zone in self.zones.values() if zone["farm_id"] == farm_id]

    def latest_run_for(self, farm_id):
        eligible = [run for run in self.runs.values() if run["farm_id"] == farm_id and run["status"] in {"completed", "partial"}]
        return max(eligible, key=lambda run: run["requested_at"], default=None)
