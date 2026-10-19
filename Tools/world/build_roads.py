import heapq, json, math, os, time
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world")
HEIGHT_SCALE = 42.0
SEA_E = 0.15 / HEIGHT_SCALE
G = 2
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


meta = json.load(open(os.path.join(DATA, "world.json")))
W, H = meta["width"], meta["height"]
raw = np.fromfile(os.path.join(DATA, "height.r16"), "<u2").reshape(H, W)
elev = meta["heightMin"] + raw / 65535.0 * (meta["heightMax"] - meta["heightMin"])


def px(lon, lat):
    return (lon - meta["lonMin"]) * meta["pxPerDegLat"] * meta["lonFactor"], (meta["latMax"] - lat) * meta["pxPerDegLat"]


gw, gh = W // G, H // G
fw, fh = meta.get("fullWidth", W) // G, meta.get("fullHeight", H) // G
e = elev[: gh * G, : gw * G].reshape(gh, G, gw, G).mean(axis=(1, 3))
water = e < SEA_E
wide = np.asarray(Image.fromarray((water * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7))) == 255
gy, gx = np.gradient(e * HEIGHT_SCALE / G)
slope = np.hypot(gx, gy)
cost = 1.0 + 7.0 * slope ** 2 + np.maximum(e * HEIGHT_SCALE - 7.0, 0.0) * 0.35
def value_noise(scale, seed):
    r = np.random.default_rng(seed)
    g = (r.random((fh // scale + 3, fw // scale + 3)) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(g).resize((fw + 3 * scale, fh + 3 * scale), Image.BICUBIC), np.float32)[scale:scale + gh, scale:scale + gw] / 255.0


wander = 0.6 * value_noise(26, 11) + 0.4 * value_noise(10, 12)
cost = cost * (1.0 + 1.6 * np.clip(wander, 0.0, 1.0) ** 1.5)
cost = np.where(water, 16.0, cost)
cost = np.where(wide, np.inf, cost)
road = np.zeros((gh, gw), np.float32)
log(f"grid {gw}x{gh}, water {water.mean() * 100:.1f}%")

NB = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (1, 1, 1.4142)]


def astar(a, b, margin=70, limit=600000, grid=None, reuse=True):
    ax, ay = a
    bx, by = b
    x0, x1 = max(0, min(ax, bx) - margin), min(gw - 1, max(ax, bx) + margin)
    y0, y1 = max(0, min(ay, by) - margin), min(gh - 1, max(ay, by) + margin)
    base = cost if grid is None else grid
    sub = base[y0:y1 + 1, x0:x1 + 1] * (np.where(road[y0:y1 + 1, x0:x1 + 1] > 0, 0.35, 1.0) if reuse else 1.0)
    sw, sh = sub.shape[1], sub.shape[0]
    start = (ay - y0) * sw + (ax - x0)
    goal = (by - y0) * sw + (bx - x0)
    if not np.isfinite(sub.flat[start]) or not np.isfinite(sub.flat[goal]):
        return None
    dist = np.full(sw * sh, np.inf)
    prev = np.full(sw * sh, -1, np.int64)
    dist[start] = 0.0
    gxg, gyg = bx - x0, by - y0
    heap = [(0.0, start)]
    n = 0
    flat = sub.ravel()
    while heap:
        f, cur = heapq.heappop(heap)
        if cur == goal:
            break
        n += 1
        if n > limit:
            return None
        cy, cx = divmod(cur, sw)
        dc = dist[cur]
        for dx, dy, step in NB:
            nx, ny = cx + dx, cy + dy
            if nx < 0 or ny < 0 or nx >= sw or ny >= sh:
                continue
            ni = ny * sw + nx
            c = flat[ni]
            if c == np.inf:
                continue
            nd = dc + step * 0.5 * (c + flat[cur])
            if nd < dist[ni]:
                dist[ni] = nd
                prev[ni] = cur
                heapq.heappush(heap, (nd + 0.35 * math.hypot(gxg - nx, gyg - ny), ni))
    if prev[goal] < 0 and goal != start:
        return None
    path = []
    cur = goal
    while cur >= 0:
        cy, cx = divmod(cur, sw)
        path.append((cx + x0, cy + y0))
        if cur == start:
            break
        cur = prev[cur]
    return path[::-1]


def smooth(path, it=3):
    P = np.array(path, np.float64)
    for _ in range(it):
        if len(P) < 4:
            break
        Q = [P[0]]
        for i in range(len(P) - 1):
            Q.append(P[i] * 0.75 + P[i + 1] * 0.25)
            Q.append(P[i] * 0.25 + P[i + 1] * 0.75)
        Q.append(P[-1])
        P = np.array(Q)
    return P


factions = {}
for fn in sorted(os.listdir(os.path.join(DATA, "factions"))):
    if fn.endswith(".json"):
        d = json.load(open(os.path.join(DATA, "factions", fn), encoding="utf-8"))
        items = []
        for kind in ("towns", "castles", "villages"):
            for s in d.get(kind, []):
                x, y = px(s["lon"], s["lat"])
                items.append({"id": s["id"], "kind": kind, "capital": bool(s.get("capital")), "x": x, "y": y, "g": (min(gw - 1, int(x / G)), min(gh - 1, int(y / G)))})
        factions[d["faction"]] = items

edges = []
for fac, items in factions.items():
    towns = [s for s in items if s["kind"] == "towns"]
    linked = {towns[0]["id"]} if towns else set()
    while len(linked) < len(towns):
        best = min(((math.hypot(a["x"] - b["x"], a["y"] - b["y"]), a, b) for a in towns if a["id"] in linked for b in towns if b["id"] not in linked), key=lambda t: t[0])
        if best[0] <= 110:
            edges.append(("main", best[1], best[2]))
        linked.add(best[2]["id"])
    for a in towns:
        near = sorted((math.hypot(a["x"] - b["x"], a["y"] - b["y"]), b["id"], b) for b in towns if b is not a)
        if near and near[0][0] < 110 and not any({a["id"], near[0][2]["id"]} == {x[1]["id"], x[2]["id"]} for x in edges):
            edges.append(("main", a, near[0][2]))
    for s in items:
        if s["kind"] == "towns":
            continue
        hubs = [t for t in items if t["kind"] == "towns" or (s["kind"] == "villages" and t["kind"] == "castles")]
        d0, hub = min(((math.hypot(s["x"] - t["x"], s["y"] - t["y"]), t) for t in hubs), key=lambda t: t[0])
        if s["kind"] == "villages" and d0 > 60:
            others = [v for v in items if v["kind"] == "villages" and v is not s]
            if others:
                d1, v = min(((math.hypot(s["x"] - t["x"], s["y"] - t["y"]), t) for t in others), key=lambda t: t[0])
                if d1 < d0:
                    hub, d0 = v, d1
        if d0 > (55 if s["kind"] == "villages" else 75):
            continue
        edges.append(("side", s, hub))

facs = list(factions)
for i in range(len(facs)):
    for j in range(i + 1, len(facs)):
        ta = [s for s in factions[facs[i]] if s["kind"] == "towns"]
        tb = [s for s in factions[facs[j]] if s["kind"] == "towns"]
        d, a, b = min(((math.hypot(a["x"] - b["x"], a["y"] - b["y"]), a, b) for a in ta for b in tb), key=lambda t: t[0])
        if d < 110:
            edges.append(("trade", a, b))

order = {"main": 0, "trade": 1, "side": 2}
edges.sort(key=lambda t: (order[t[0]], math.hypot(t[1]["x"] - t[2]["x"], t[1]["y"] - t[2]["y"])))
log(f"edges: {len(edges)}")

roads, bridges, failed = [], [], 0
for kind, a, b in edges:
    path = astar(a["g"], b["g"], margin=90 if kind == "trade" else 60)
    if path is None or len(path) < 2:
        failed += 1
        continue
    for x, y in path:
        road[y, x] = 1.0
    run = []
    for i, (x, y) in enumerate(path + [(-1, -1)]):
        wet = x >= 0 and water[y, x]
        if wet:
            run.append((x, y))
        elif run:
            if 1 <= len(run) <= 6:
                p0, p1 = np.array(run[0], float), np.array(run[-1], float)
                mid = (p0 + p1) / 2 * G + G / 2
                d = p1 - p0
                if np.hypot(*d) < 0.5 and i < len(path):
                    q = np.array(path[min(len(path) - 1, i)], float) - np.array(path[max(0, i - len(run) - 1)], float)
                    d = q
                d = d / max(np.hypot(*d), 1e-6)
                bridges.append({"x": round(float(mid[0]), 2), "y": round(float(mid[1]), 2), "dx": round(float(d[0]), 3), "dy": round(float(d[1]), 3),
                                "len": round(float(len(run) * G + 3.0), 2), "kind": "stone" if kind != "side" else "wood"})
            run = []
    P = smooth(path) * G + G / 2
    roads.append({"kind": kind, "pts": [round(float(v), 2) for xy in P for v in xy]})

sea_cost = np.where(wide, 1.0, np.where(water, 4.0, np.inf))
open_sea = wide


def port(s, reach=7):
    cx, cy = s["g"]
    best = None
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            x, y = cx + dx, cy + dy
            if 0 <= x < gw and 0 <= y < gh and open_sea[y, x]:
                d = dx * dx + dy * dy
                if best is None or d < best[0]:
                    best = (d, (x, y))
    return best[1] if best else None


sea_routes, fishing = [], []
ports = {}
for fac, items in factions.items():
    for s in items:
        if s["kind"] in ("towns", "villages"):
            p = port(s, 25 if s["kind"] == "towns" else 18)
            if p:
                ports[s["id"]] = (fac, s, p)
ship_of = {"vallerois": "cog", "varden": "cog", "vinland": "longship", "grim": "galley"}
pairs = set()
for sid, (fac, s, p) in ports.items():
    if s["kind"] != "towns":
        continue
    same = [(math.hypot(o["x"] - s["x"], o["y"] - s["y"]), oid) for oid, (f2, o, _) in ports.items() if oid != sid and f2 == fac and o["kind"] == "towns"]
    other = [(math.hypot(o["x"] - s["x"], o["y"] - s["y"]), oid) for oid, (f2, o, _) in ports.items() if f2 != fac and o["kind"] == "towns"]
    for lst, cap in ((same, 260), (other, 420)):
        if lst:
            d, oid = min(lst)
            if d < cap:
                pairs.add(tuple(sorted((sid, oid))))
seen_ports = set()
for a_id, b_id in sorted(pairs):
    fa, a, pa = ports[a_id]
    fb, b, pb = ports[b_id]
    key = tuple(sorted((pa, pb)))
    if pa == pb or key in seen_ports or math.dist(pa, pb) < 12:
        continue
    seen_ports.add(key)
    path = astar(pa, pb, margin=120, limit=900000, grid=sea_cost, reuse=False)
    if path is None or len(path) < 6:
        continue
    P = smooth(path, 4) * G + G / 2
    ship = ship_of.get(fa) or ship_of.get(fb) or "dhow"
    sea_routes.append({"ship": ship, "faction": fa if ship_of.get(fa) == ship or ship == "dhow" else fb, "pts": [round(float(v), 2) for xy in P for v in xy]})
for sid, (fac, s, p) in ports.items():
    if s["kind"] != "villages":
        continue
    vx, vy = s["g"]
    ox, oy = p[0] - vx, p[1] - vy
    on = max(math.hypot(ox, oy), 1e-6)
    for radius in (6, 5, 4, 3):
        cx, cy = p[0] + ox / on * (radius + 1), p[1] + oy / on * (radius + 1)
        loop = [(cx + math.cos(k / 12 * math.tau) * radius, cy + math.sin(k / 12 * math.tau) * radius * 0.7) for k in range(12)]
        if all(0 <= int(x) < gw and 0 <= int(y) < gh and water[int(y), int(x)] for x, y in loop):
            fishing.append({"ship": "boat", "faction": fac, "pts": [round(float(v * G + G / 2), 2) for xy in loop for v in xy]})
            break

json.dump({"roads": roads, "bridges": bridges, "sea": sea_routes, "fishing": fishing}, open(os.path.join(DATA, "roads.json"), "w", encoding="utf-8"))
log(f"roads: {len(roads)}, bridges: {len(bridges)}, failed: {failed}, sea routes: {len(sea_routes)}, fishing: {len(fishing)}")
