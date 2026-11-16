"""Builds the locator outline (land, Great Lakes, national borders) from Natural Earth 1:50m data,
projected with an Albers equal-area conic, clipped to the frame and simplified. Prints a JS snippet."""
import json, math, sys

src = sys.argv[1]
LON0, LAT0, P1, P2 = -96.0, 23.0, 29.5, 45.5
r = math.radians
n = (math.sin(r(P1)) + math.sin(r(P2))) / 2
C = math.cos(r(P1)) ** 2 + 2 * n * math.sin(r(P1))
rho0 = math.sqrt(C - 2 * n * math.sin(r(LAT0))) / n


def albers(lon, lat):
    rho = math.sqrt(C - 2 * n * math.sin(r(lat))) / n
    th = n * r(lon - LON0)
    return rho * math.sin(th), rho0 - rho * math.cos(th)


# Frame: wide enough for Seattle to Boston, Toronto to Durham, with sea and neighbours around them.
edge = [(lon, 24.0) for lon in range(-126, -64)] + [(lon, 50.5) for lon in range(-126, -64)] + \
       [(-125.5, lat) for lat in range(24, 51)] + [(-65.5, lat) for lat in range(24, 51)]
xs, ys = zip(*[albers(*p) for p in edge])
W = 760
S = W / (max(xs) - min(xs))
X0, Y1 = min(xs), max(ys)
H = round((max(ys) - min(ys)) * S)


def proj(lon, lat):
    x, y = albers(lon, lat)
    return ((x - X0) * S, (Y1 - y) * S)


def clip(poly):
    """Sutherland-Hodgman clip of a closed polygon to [0,W]x[0,H] (with a small margin)."""
    m = 2
    for inside, cut in [
        (lambda p: p[0] >= -m, lambda a, b: (-m, a[1] + (b[1] - a[1]) * (-m - a[0]) / (b[0] - a[0]))),
        (lambda p: p[0] <= W + m, lambda a, b: (W + m, a[1] + (b[1] - a[1]) * (W + m - a[0]) / (b[0] - a[0]))),
        (lambda p: p[1] >= -m, lambda a, b: (a[0] + (b[0] - a[0]) * (-m - a[1]) / (b[1] - a[1]), -m)),
        (lambda p: p[1] <= H + m, lambda a, b: (a[0] + (b[0] - a[0]) * (H + m - a[1]) / (b[1] - a[1]), H + m))]:
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
        poly = out
        if not poly:
            break
    return poly


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        best, idx = 0, None
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / L
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def simplify_closed(p, tol):
    """A closed ring starts and ends at the same point, so split it at the vertex farthest from the start."""
    far = max(range(len(p)), key=lambda i: (p[i][0] - p[0][0]) ** 2 + (p[i][1] - p[0][1]) ** 2)
    a = simplify(p[:far + 1], tol)
    b = simplify(p[far:] + [p[0]], tol)
    return a[:-1] + b[:-1]


def area(p):
    return abs(sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))) / 2


def rings(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [ring for poly in geom["coordinates"] for ring in poly]
    return []


def near(ring):
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return max(lons) > -135 and min(lons) < -55 and max(lats) > 18 and min(lats) < 58


def d_closed(polys):
    return "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in p) + "Z" for p in polys)


def load(name):
    return json.load(open(f"{src}/{name}.geojson", encoding="utf-8"))["features"]


TOL = 0.5
land = []
for f in load("ne_50m_land"):
    for ring in rings(f["geometry"]):
        if not near(ring):
            continue
        p = clip([proj(lon, lat) for lon, lat in ring])
        if len(p) >= 3:
            p = simplify_closed(p, TOL)
            if len(p) >= 3 and area(p) > 4:
                land.append(p)

lakes = []
for f in load("ne_50m_lakes"):
    for ring in rings(f["geometry"])[:1]:
        if not near(ring):
            continue
        p = clip([proj(lon, lat) for lon, lat in ring])
        if len(p) >= 3:
            p = simplify_closed(p, TOL)
            if len(p) >= 3 and area(p) > 40:
                lakes.append(p)

borders = []
for f in load("ne_50m_admin_0_boundary_lines_land"):
    g = f["geometry"]
    lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for line in lines:
        if not near(line):
            continue
        seg = []
        for lon, lat in line:
            x, y = proj(lon, lat)
            if -2 <= x <= W + 2 and -2 <= y <= H + 2:
                seg.append((x, y))
            else:
                if len(seg) > 1:
                    borders.append(simplify(seg, TOL))
                seg = []
        if len(seg) > 1:
            borders.append(simplify(seg, TOL))

d_border = "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in s) for s in borders)
print(f"/* Outline: Natural Earth 1:50m (public domain), Albers equal-area conic, built by make_outline.py. */")
print(f"const OUTLINE = {{ W: {W}, H: {H}, lon0: {LON0}, lat0: {LAT0}, p1: {P1}, p2: {P2}, x0: {X0:.6f}, y1: {Y1:.6f}, s: {S:.4f},")
print(f'  land: "{d_closed(land)}",')
print(f'  lakes: "{d_closed(lakes)}",')
print(f'  border: "{d_border}" }};')
sys.stderr.write(f"W={W} H={H} land={len(land)} pts={sum(map(len, land))} lakes={len(lakes)} borders={len(borders)}\n")
