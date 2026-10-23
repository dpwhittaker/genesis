"""Base map for the Session 11 Table of Nations map.

Projects Natural Earth (public domain) land, lakes and rivers into an Albers
equal-area conic and returns SVG path strings. No GIS libraries: polygons are
clipped to a lon/lat box (Sutherland-Hodgman) and simplified in pixel space.
Natural Earth GeoJSON is fetched once into ./ne/ (not committed).

The green "watered land" layer comes from the Köppen-Geiger climate map for
1991-2020 at 1 km (Beck et al. 2023, CC BY 4.0, fetched once into ./kg/): every
class except desert (BWh, BWk). The deserts' river valleys are added on top.
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

KG = os.path.join(HERE, 'kg')
KG_URL = 'https://ndownloader.figshare.com/files/61012822'   # koppen_geiger_tif.zip
KG_TIF = '1991_2020/koppen_geiger_0p00833333.tif'
KG_REGION = (-5, 5, 75, 52)   # w, s, e, n: everything either map can show

def koppen():
    """Köppen-Geiger classes (0 = sea, 4/5 = desert) for KG_REGION at 1/120°,
    north row first. Returns (grid, west, north, step)."""
    import numpy as np
    step = 1 / 120
    cache = os.path.join(KG, 'region.npy')
    if not os.path.exists(cache):
        import zipfile
        from PIL import Image
        os.makedirs(KG, exist_ok=True)
        z = os.path.join(KG, 'koppen_geiger_tif.zip')
        if not os.path.exists(z):
            urllib.request.urlretrieve(KG_URL, z)
        Image.MAX_IMAGE_PIXELS = None
        with zipfile.ZipFile(z) as zf, zf.open(KG_TIF) as f:
            a = np.asarray(Image.open(f))   # global grid from (-180, 90)
        w, s, e, n = KG_REGION
        np.save(cache, a[round((90 - n) / step):round((90 - s) / step),
                         round((w + 180) / step):round((e + 180) / step)])
    return np.load(cache), KG_REGION[0], KG_REGION[3], step

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

# The deserts' river valleys, watered by the river rather than by rain. Buffers
# (degrees of latitude either side of the Natural Earth centerline) by river and
# stretch; the Nile Delta, the Fayum and the Mesopotamian alluvium as outlines.
VALLEYS = [
    ({'Nile'}, (24.0, 30.2), 0.10),                       # Aswan to the Delta
    ({'Nile', 'El Bahr el Abyad', 'El Bahr el Azraq', 'Atbara'}, (0, 24.0), 0.035),
    ({'Euphrates', 'Firat', 'Al Furat', 'Tigris', 'Dicle', 'Shatt al Arab',
      'Karkheh'}, (0, 90), 0.05),
]
PLAINS = [
    # Nile Delta: from the apex north of Cairo to the coast, Alexandria to Port Said.
    [(31.13, 30.17), (30.75, 30.45), (30.35, 30.80), (30.05, 31.05), (29.85, 31.35),
     (32.40, 31.40), (32.25, 31.05), (32.00, 30.85), (31.75, 30.55), (31.45, 30.30)],
    # The Fayum, west of the Nile.
    [(30.55, 29.40), (30.70, 29.55), (30.95, 29.50), (31.10, 29.30), (30.95, 29.10),
     (30.65, 29.15)],
    # The alluvial plain of Mesopotamia: Hit and Samarra down to the Gulf; on the
    # east, Jebel Hamrin and the Zagros foothills (Mandali, Badra), taking in the
    # Diyala; on the west, the desert edge (Najaf, Samawah, Ur).
    [(42.80, 33.65), (43.85, 34.20), (44.60, 34.15), (45.20, 33.95), (45.55, 33.75),
     (45.95, 33.10), (46.45, 32.85), (47.05, 32.50), (47.45, 32.15), (47.70, 31.60),
     (48.10, 30.90),
     (48.40, 30.40),
     (48.60, 29.90), (47.90, 29.85), (47.60, 30.20), (46.90, 30.55), (46.00, 30.85),
     (45.30, 31.20), (44.75, 31.55), (44.30, 31.95), (44.00, 32.55), (43.75, 32.95),
     (43.30, 33.35)],
]

def watered(frame, clipbox, step, sigma, tol, valleys=True, minarea=2.0):
    """Land that is not desert, plus (if valleys) the river valleys, as SVG
    paths with holes (fill-rule evenodd). The 1 km grid is averaged to `step`
    degrees, smoothed by `sigma` cells and traced at the halfway line."""
    import numpy as np
    from scipy import ndimage, spatial
    import contourpy
    from matplotlib.path import Path
    kg, kw, kn, ks = koppen()
    f = max(1, round(step / ks)); step = f * ks
    w, s, e, n = clipbox
    r0, c0 = round((kn - n) / ks), round((w - kw) / ks)
    rows, cols = (round((n - s) / ks) // f) * f, (round((e - w) / ks) // f) * f
    k = kg[r0:r0 + rows, c0:c0 + cols]
    land = (k > 0).reshape(rows // f, f, cols // f, f).mean(axis=(1, 3))
    green = ((k > 0) & (k != 4) & (k != 5)).reshape(rows // f, f, cols // f, f).mean(axis=(1, 3))
    z = np.where(land > 0, green / np.maximum(land, 1e-9), 0)
    # Sea cells take their nearest land value, so the coast is traced by the
    # land clip and not pulled inland by averaging with water.
    _, (ir, ic) = ndimage.distance_transform_edt(land == 0, return_indices=True)
    z = z[ir, ic]
    lon = w + (np.arange(z.shape[1]) + 0.5) * step
    lat = n - (np.arange(z.shape[0]) + 0.5) * step
    if valleys:
        LON, LAT = np.meshgrid(lon, lat)
        pts = np.column_stack([LON.ravel() * np.cos(np.radians(LAT.ravel())), LAT.ravel()])
        add = np.zeros(len(pts), bool)
        rivers = load('ne_10m_rivers_lake_centerlines')['features']
        for names, (lo, hi), r in VALLEYS:
            seg = []
            for ft in rivers:
                if ft['properties'].get('name') not in names: continue
                for ln in lines(ft['geometry']):
                    for (x1, y1), (x2, y2) in zip(ln, ln[1:]):
                        m = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.01))
                        for t in np.linspace(0, 1, m):
                            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                            if lo <= y < hi: seg.append((x * math.cos(math.radians(y)), y))
            if seg:
                d, _ = spatial.cKDTree(seg).query(pts, distance_upper_bound=r)
                add |= d <= r
        for poly in PLAINS:
            add |= Path(poly).contains_points(np.column_stack([LON.ravel(), LAT.ravel()]))
        z = np.maximum(z, add.reshape(z.shape).astype(float))
    z = ndimage.gaussian_filter(z, sigma)
    gen = contourpy.contour_generator(lon, lat[::-1], z[::-1],
                                      fill_type=contourpy.FillType.OuterOffset)
    out = []
    for p, offs in zip(*gen.filled(0.5, 2.0)):
        parts = []
        for a, b in zip(offs, offs[1:]):
            px = simplify_ring([frame(x, y) for x, y in p[a:b]], tol)
            if len(px) < 3: continue
            area = 0.5 * abs(sum(px[i][0]*px[i-1][1] - px[i-1][0]*px[i][1] for i in range(len(px))))
            if area < minarea and not parts: break   # a speck: drop it with its holes
            if area >= minarea: parts.append(path_d(px, True))
        if parts: out.append(''.join(parts))
    return out
