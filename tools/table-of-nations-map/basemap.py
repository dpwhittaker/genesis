"""Base map for the Session 11 Table of Nations map.

Projects Natural Earth (public domain) land, lakes and rivers into an Albers
equal-area conic and returns SVG path strings. No GIS libraries: polygons are
clipped to a lon/lat box (Sutherland-Hodgman) and simplified in pixel space.
Natural Earth GeoJSON is fetched once into ./ne/ (not committed).
"""
import json, math, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
NE = os.path.join(HERE, 'ne')
NE_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson'

def load(name):
    os.makedirs(NE, exist_ok=True)
    path = os.path.join(NE, name + '.geojson')
    if not os.path.exists(path):
        urllib.request.urlretrieve(NE_URL.format(name), path)
    return json.load(open(path))

class Albers:
    def __init__(self, lon0, lat0, p1, p2):
        r = math.radians
        self.l0 = r(lon0)
        n = (math.sin(r(p1)) + math.sin(r(p2))) / 2
        C = math.cos(r(p1)) ** 2 + 2 * n * math.sin(r(p1))
        self.n, self.C = n, C
        self.rho0 = math.sqrt(C - 2 * n * math.sin(r(lat0))) / n
    def __call__(self, lon, lat):
        r = math.radians
        rho = math.sqrt(self.C - 2 * self.n * math.sin(r(lat))) / self.n
        th = self.n * (r(lon) - self.l0)
        return rho * math.sin(th), self.rho0 - rho * math.cos(th)

def clip_ring(ring, box):
    """Sutherland-Hodgman clip of a closed lon/lat ring to box (w, s, e, n)."""
    w, s, e, n = box
    edges = [(lambda p: p[0] >= w, lambda a, b: (w, a[1] + (b[1]-a[1]) * (w-a[0]) / (b[0]-a[0]))),
             (lambda p: p[0] <= e, lambda a, b: (e, a[1] + (b[1]-a[1]) * (e-a[0]) / (b[0]-a[0]))),
             (lambda p: p[1] >= s, lambda a, b: (a[0] + (b[0]-a[0]) * (s-a[1]) / (b[1]-a[1]), s)),
             (lambda p: p[1] <= n, lambda a, b: (a[0] + (b[0]-a[0]) * (n-a[1]) / (b[1]-a[1]), n))]
    out = ring
    for inside, cross in edges:
        if not out: break
        src, out = out, []
        prev = src[-1]
        for cur in src:
            if inside(cur):
                if not inside(prev): out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
            prev = cur
    return out

def clip_line(line, box):
    """Split a polyline into the runs that fall inside box (points only; fine at this scale)."""
    w, s, e, n = box
    runs, cur = [], []
    for p in line:
        if w <= p[0] <= e and s <= p[1] <= n:
            cur.append(p)
        else:
            if len(cur) > 1: runs.append(cur)
            cur = []
    if len(cur) > 1: runs.append(cur)
    return runs

def simplify(pts, tol):
    """Douglas-Peucker in pixel space."""
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1e-9
        best, idx = 0, None
        for i in range(a + 1, b):
            px, py = pts[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / L
            if d > best: best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]

def simplify_ring(pts, tol):
    """Closed ring: split at the point farthest from the first, simplify each half."""
    if len(pts) > 1 and pts[0] == pts[-1]: pts = pts[:-1]
    if len(pts) < 4: return pts
    x0, y0 = pts[0]
    far = max(range(len(pts)), key=lambda i: (pts[i][0]-x0)**2 + (pts[i][1]-y0)**2)
    a = simplify(pts[:far + 1], tol); b = simplify(pts[far:] + [pts[0]], tol)
    return a[:-1] + b[:-1]

def polys(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon': return [c]
    if t == 'MultiPolygon': return c
    return []

def rings(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon': return c
    if t == 'MultiPolygon': return [r for poly in c for r in poly]
    return []

def lines(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'LineString': return [c]
    if t == 'MultiLineString': return c
    return []

class Frame:
    """A pixel rectangle cut from the projection: x spans west..east along the
    middle parallel, y spans south..north along the central meridian. Data is
    clipped to a wider lon/lat box and the SVG viewBox crops the rest, so the
    map edge is a clean rectangle rather than the conic's fan."""
    def __init__(self, box, width, proj, lon_c, lat_c):
        self.proj = proj
        w, s, e, n = box
        xa, _ = proj(w, lat_c); xb, _ = proj(e, lat_c)
        _, ya = proj(lon_c, s); _, yb = proj(lon_c, n)
        self.x0, self.x1, self.y0, self.y1 = xa, xb, ya, yb
        self.k = width / (self.x1 - self.x0)
        self.width = width
        self.height = (self.y1 - self.y0) * self.k
    def __call__(self, lon, lat):
        x, y = self.proj(lon, lat)
        return (x - self.x0) * self.k, (self.y1 - y) * self.k

def path_d(pts, close):
    if not pts: return ''
    s = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return s + ('Z' if close else '')

def polygons(fc, frame, clipbox, tol=0.45, minarea=1.5, want=lambda p: True):
    """One SVG path per polygon, holes included (draw with fill-rule evenodd)."""
    out = []
    for f in fc['features']:
        if not want(f['properties']): continue
        for poly in polys(f['geometry']):
            parts = []
            for ring in poly:
                r = clip_ring([tuple(p) for p in ring], clipbox)
                if len(r) < 3: continue
                px = simplify_ring([frame(*p) for p in r], tol)
                if len(px) < 3: continue
                a = 0.5 * abs(sum(px[i][0]*px[i-1][1] - px[i-1][0]*px[i][1] for i in range(len(px))))
                if a < minarea: continue
                parts.append(path_d(px, True))
            if parts: out.append(''.join(parts))
    return out

def polylines(fc, frame, clipbox, tol=0.45, want=lambda p: True):
    out = []
    for f in fc['features']:
        if not want(f['properties']): continue
        for ln in lines(f['geometry']):
            for run in clip_line(ln, clipbox):
                px = simplify([frame(*p) for p in run], tol)
                if len(px) > 1: out.append(path_d(px, False))
    return out
