"""Clip Natural Earth 1:10m land to northern Prince William Sound and write a compact JS file.
Usage: python3 geo.py <geo_dir> <out_js>"""
import json
import sys

GEO, OUT = sys.argv[1], sys.argv[2]
W, E, S, N = -147.75, -146.05, 60.52, 61.25


def rings(path):
    out = []
    for f in json.load(open(path))["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = poly[0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            if max(xs) < W or min(xs) > E or max(ys) < S or min(ys) > N:
                continue
            out.append(ring)
    return out


def clip_window(ring, pad=0.6):
    """Keep only the stretch of a huge ring that runs near the window (the mainland ring spans a continent)."""
    inside = [W - pad <= x <= E + pad and S - pad <= y <= N + pad for x, y in ring]
    if all(inside):
        return [ring]
    n, parts, cur = len(ring), [], []
    start = next(i for i in range(n) if not inside[i])
    for k in range(n):
        i = (start + k) % n
        if inside[i]:
            cur.append(ring[i])
        elif cur:
            parts.append(cur)
            cur = []
    if cur:
        parts.append(cur)
    return parts


land = []
for path in (f"{GEO}/ne_10m_land.geojson", f"{GEO}/ne_10m_minor_islands.geojson"):
    for ring in rings(path):
        for part in clip_window(ring):
            if len(part) >= 3:
                land.append([[round(x, 4), round(y, 4)] for x, y in part])

print("rings:", len(land), "points:", sum(len(r) for r in land))
for r in sorted(land, key=len, reverse=True)[:12]:
    xs = [p[0] for p in r]
    ys = [p[1] for p in r]
    print(f"  n={len(r):4d} lon {min(xs):9.3f}..{max(xs):9.3f} lat {min(ys):7.3f}..{max(ys):7.3f} closed={r[0] == r[-1]}")
open(OUT, "w").write("window.GEO_LAND=" + json.dumps(land, separators=(",", ":")) + ";\n")
