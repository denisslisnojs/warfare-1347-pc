import json, math, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world")
RADIUS = {"towns": 7, "castles": 5, "villages": 4}
CAPITAL_RADIUS = 9
HEIGHT_SCALE = 42.0
MAX_RELIEF = 0.15
MAX_RISE = 2.0
BLEND = 2.4
RISE_RING = 1.6
SEARCH = int(sys.argv[sys.argv.index("--search") + 1]) if "--search" in sys.argv else 16
WATERLINE = 0.004
RIVER_GAP = 0.8
RIVER_SIDE = 6.0

meta = json.load(open(os.path.join(DATA, "world.json")))
W, H = meta["width"], meta["height"]
raw = np.fromfile(os.path.join(DATA, "height.r16"), "<u2").reshape(H, W)
height = meta["heightMin"] + raw / 65535.0 * (meta["heightMax"] - meta["heightMin"])
biome = np.asarray(Image.open(os.path.join(DATA, "biome.png")))
if biome.ndim == 3:
    biome = biome[..., 0]
bk = biome.shape[1] / W
names = {v: k for k, v in meta["biomes"].items()}


def px(lon, lat):
    return (lon - meta["lonMin"]) * meta["pxPerDegLat"] * meta["lonFactor"], (meta["latMax"] - lat) * meta["pxPerDegLat"]


def geo(x, y):
    return x / (meta["pxPerDegLat"] * meta["lonFactor"]) + meta["lonMin"], meta["latMax"] - y / meta["pxPerDegLat"]


rivers = [(np.array(rv["pts"], float).reshape(-1, 2), 1.4 + 0.6 * rv["width"]) for rv in json.load(open(os.path.join(DATA, "rivers.json"), encoding="utf-8"))["rivers"]]


SEG_A = np.vstack([pts[:-1] for pts, _ in rivers])
SEG_AB = np.vstack([pts[1:] - pts[:-1] for pts, _ in rivers])
SEG_HALF = np.concatenate([np.full(len(pts) - 1, half) for pts, half in rivers])
SEG_RIVER = np.concatenate([np.full(len(pts) - 1, i) for i, (pts, _) in enumerate(rivers)])


def river_near(x, y):
    p = np.array((x, y))
    t = np.clip(((p - SEG_A) * SEG_AB).sum(1) / np.maximum((SEG_AB * SEG_AB).sum(1), 1e-9), 0, 1)
    d = np.hypot(*(SEG_A + SEG_AB * t[:, None] - p).T) - SEG_HALF
    i = int(d.argmin())
    return float(d[i]), int(SEG_RIVER[i]), d


def river_dist(x, y, river=None):
    best, idx, d = river_near(x, y)
    return best if river is None else float(d[SEG_RIVER == river].min())


def probe(x, y, r, f):
    xi, yi = int(round(x)), int(round(y))
    R = int(math.ceil(r * BLEND))
    ys, xs = np.ogrid[-R:R + 1, -R:R + 1]
    dist = np.sqrt(xs * xs + ys * ys) + np.zeros((2 * R + 1, 2 * R + 1))
    win = height[max(0, yi - R):yi + R + 1, max(0, xi - R):xi + R + 1]
    dist = dist[:win.shape[0], :win.shape[1]]
    inner = win[dist <= r]
    target = max(0.012, float(inner.mean()))
    t = np.clip((dist - r) / (r * BLEND - r), 0, 1)
    k = 1 - t * t * (3 - 2 * t)
    shaped = np.where((win < WATERLINE) & (dist > r), win, win + (target - win) * k)
    ring = shaped[(dist > r) & (dist <= r * RISE_RING)]
    rise = (float(ring.max()) - target) * HEIGHT_SCALE
    b = biome[min(biome.shape[0] - 1, int(y * bk)), min(biome.shape[1] - 1, int(x * bk))]
    wet = float((inner < WATERLINE).mean())
    wet_foot = float((win[dist <= f + 0.5] < WATERLINE).mean())
    return float(inner.max() - inner.min()), float(height[yi, xi]), names.get(int(b), str(b)), wet, rise, wet_foot


def bad(kind, f, x, y, relief, h, b, wet, rise, wet_foot, margin=0.0, wet_limit=0.25):
    if b == "sea" or h < 0.006 or relief > MAX_RELIEF or wet > wet_limit or rise > MAX_RISE:
        return True
    return kind != "towns" and (wet_foot > 0 or river_dist(x, y) < f + RIVER_GAP + margin)


FOOT = {"capital": 8.3, "large": 6.9, "medium": 6.4, "towns": 7.0, "castles": 5.0, "villages": 3.8}


def foot(kind, s):
    if s.get("capital"):
        return FOOT["capital"]
    return FOOT.get(s.get("model", ""), FOOT[kind]) if kind == "towns" else FOOT[kind]


GAP = {frozenset(("castles", "towns")): 6.0, frozenset(("castles",)): 3.0}


def clearance(x, y, f, kind, others):
    return min((math.hypot(x - ox, y - oy) - f - of - GAP.get(frozenset((kind, ok)), 0.0) for ox, oy, of, ok in others), default=99.0)


src = sys.argv[1]
fix = "--fix" in sys.argv
free = set(sys.argv[sys.argv.index("--free") + 1].split(",")) if "--free" in sys.argv else set()
data = json.load(open(src, encoding="utf-8"))
items = [(kind, s) for kind in ("castles", "villages", "towns") for s in data[kind]]
foreign = []
for fn in os.listdir(os.path.dirname(os.path.abspath(src))):
    path = os.path.join(os.path.dirname(os.path.abspath(src)), fn)
    if fn.endswith(".json") and os.path.abspath(path) != os.path.abspath(src):
        other = json.load(open(path, encoding="utf-8"))
        foreign += [(*px(o["lon"], o["lat"]), foot(k, o), k) for k in ("towns", "castles", "villages") for o in other.get(k, [])]
problems = 0
for kind, s in items:
    r = CAPITAL_RADIUS if s.get("capital") else RADIUS[kind]
    f = foot(kind, s)
    x, y = px(s["lon"], s["lat"])
    c0 = probe(x, y, r, f)
    relief, h, b, wet, rise, wet_foot = c0
    others = [(*px(o["lon"], o["lat"]), foot(k, o), k) for k, o in items if o is not s] + foreign
    cl = clearance(x, y, f, kind, others)
    rd, home_river, _ = river_near(x, y)
    on_river = s["id"] not in free and (rd <= f * 0.6 if kind == "towns" else rd < f + RIVER_SIDE)
    wet_limit = 0.4 if kind == "towns" and on_river else 0.25
    flag = bad(kind, f, x, y, *c0, wet_limit=wet_limit) or cl < 0
    moved = ""
    if flag and fix:
        best = None
        for dy in range(-SEARCH, SEARCH + 1):
            for dx in range(-SEARCH, SEARCH + 1):
                d2 = dx * dx + dy * dy
                if d2 > SEARCH * SEARCH:
                    continue
                c = probe(x + dx, y + dy, r, f)
                if c[4] > MAX_RISE * 0.85 or clearance(x + dx, y + dy, f, kind, others) < 0.6 or bad(kind, f, x + dx, y + dy, *c, margin=0.5, wet_limit=wet_limit):
                    continue
                if on_river and river_dist(x + dx, y + dy, home_river) > (f * 0.6 if kind == "towns" else f + RIVER_SIDE):
                    continue
                score = d2 + c[4] * 20
                if best is None or score < best[0]:
                    lon2, lat2 = geo(x + dx, y + dy)
                    best = (score, round(lon2, 2), round(lat2, 2), c, math.sqrt(d2))
        if best:
            moved = f" -> moved {best[4]:.1f}px to {best[1]}, {best[2]}"
            s["lon"], s["lat"] = best[1], best[2]
            relief, h, b, wet, rise, wet_foot = best[3]
            rd = river_dist(*px(s["lon"], s["lat"]))
            cl = clearance(*px(s["lon"], s["lat"]), f, kind, others)
            flag = False
    problems += flag
    print(f"{'BAD ' if flag else 'ok  '}{kind[:-1]:7} {s['nameEn']:26} relief {relief:.3f} rise {rise:5.2f} {b:7} wet {wet:.2f}/{wet_foot:.2f} clear {cl:5.1f}px river {rd:5.1f}px{moved}")
if fix:
    json.dump(data, open(src, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(items)} settlements, {problems} problems")
