"""Local/test repository adapter; production is intentionally replaceable by PostGIS."""
class Repository:
    def __init__(self): self.farms, self.zones, self.runs, self.results, self.keys = {}, {}, {}, {}, {}
    def replay(self, scope, key): return self.keys.get((scope, key)) if key else None
    def remember(self, scope, key, item):
        if key: self.keys[(scope, key)] = item
