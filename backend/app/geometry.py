"""Pure-Python geometry validation for standard GeoJSON features.
Implements bounded ray-casting and segment intersection without heavyweight dependencies.
"""

def _ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def _segments_intersect(p1, p2, p3, p4):
    """Check if line segment p1-p2 intersects with p3-p4."""
    # Collinear segments are technically self-intersections but for this simplistic check,
    # we just use strict orientation.
    return _ccw(p1, p3, p4) != _ccw(p2, p3, p4) and _ccw(p1, p2, p3) != _ccw(p1, p2, p4)

def _has_self_intersection(ring):
    """Check if a single closed ring self-intersects."""
    n = len(ring)
    for i in range(n - 1):
        p1, p2 = ring[i], ring[i+1]
        for j in range(i + 2, n - 1):
            # The first edge and the last edge share the start/end point; skip check.
            if i == 0 and j == n - 2:
                continue
            p3, p4 = ring[j], ring[j+1]
            if _segments_intersect(p1, p2, p3, p4):
                return True
    return False

def _point_in_polygon(point, ring):
    """Ray-casting algorithm for point-in-polygon."""
    x, y = point
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i+1]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside

def _is_valid_polygon(coords):
    if not coords or not isinstance(coords, list):
        return False, "Polygon coordinates must be a list of rings"
    
    exterior = coords[0]
    if len(exterior) < 4:
        return False, "Exterior ring must have at least 4 points"
    if exterior[0] != exterior[-1]:
        return False, "Exterior ring must be closed (first and last point must match)"
        
    for p in exterior:
        if len(p) < 2: return False, "Coordinates must have at least 2 dimensions"
        if not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90):
            return False, "Coordinates out of bounds [-180,180], [-90,90]"
            
    if _has_self_intersection(exterior):
        return False, "Polygon exterior ring self-intersects"
        
    # We only check exterior ring here. Interior rings would also need validation,
    # but for Farm boundaries, exterior is the primary concern.
    return True, ""

def validate_geometry(value):
    """Validates GeoJSON Polygon or MultiPolygon."""
    if not isinstance(value, dict) or value.get("type") not in {"Polygon", "MultiPolygon"}:
        return False, "must be GeoJSON Polygon or MultiPolygon"
        
    coords = value.get("coordinates")
    if not coords or not isinstance(coords, list):
        return False, "coordinates are malformed"
        
    if value["type"] == "Polygon":
        valid, msg = _is_valid_polygon(coords)
        if not valid: return False, msg
    else: # MultiPolygon
        if not coords: return False, "MultiPolygon must contain at least one polygon"
        for poly_coords in coords:
            valid, msg = _is_valid_polygon(poly_coords)
            if not valid: return False, f"MultiPolygon contains invalid polygon: {msg}"
            
    return True, ""

def validate_point(value):
    """Validates GeoJSON Point."""
    if not isinstance(value, dict) or value.get("type") != "Point":
        return False, "must be GeoJSON Point"
    coords = value.get("coordinates")
    if not coords or not isinstance(coords, list) or len(coords) < 2:
        return False, "Point coordinates are malformed"
    if not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
        return False, "Coordinates out of bounds [-180,180], [-90,90]"
    return True, ""

def is_point_within_boundary(point_value, boundary_value):
    """Check if a GeoJSON point falls within a GeoJSON boundary (Polygon/MultiPolygon)."""
    pt = point_value.get("coordinates")[:2]
    
    if boundary_value["type"] == "Polygon":
        return _point_in_polygon(pt, boundary_value["coordinates"][0])
    elif boundary_value["type"] == "MultiPolygon":
        return any(_point_in_polygon(pt, poly[0]) for poly in boundary_value["coordinates"])
    return False
