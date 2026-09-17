"""Local/test repository adapter; production is intentionally replaceable by PostGIS."""
class Repository:
    def __init__(self): self.farms, self.zones, self.runs, self.results, self.evidence, self.recommendations, self.keys = {}, {}, {}, {}, {}, {}, {}
    def replay(self, scope, key, fingerprint):
        record = self.keys.get((scope, key)) if key else None
        if record and record["fingerprint"] != fingerprint: raise ValueError("idempotency_conflict")
        return record["item"] if record else None
    def remember(self, scope, key, fingerprint, item):
        if key: self.keys[(scope, key)] = {"fingerprint": fingerprint, "item": item}
