import zlib
import json, math, os, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world")
os.makedirs(OUT, exist_ok=True)

LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = -12.0, 124.0, 12.0, 71.0
LON_FACTOR = 0.7071
ROCK_HEIGHT = (9.0, 15.0)
PPD = 24
W = int(round((LON_MAX - LON_MIN) * PPD * LON_FACTOR))
H = int(round((LAT_MAX - LAT_MIN) * PPD))
CS = 2
CW, CH = W * CS, H * CS
KEEP_LON_MAX, KEEP_LAT_MIN = 92.0, 22.0
KW = int(round((KEEP_LON_MAX - LON_MIN) * PPD * LON_FACTOR))
KH = int(round((LAT_MAX - KEEP_LAT_MIN) * PPD))
rng = np.random.default_rng(1347)
t0 = time.time()


def log(msg):
    print(f"[{time.time() - t0:5.1f}s] {msg}", flush=True)


def to_px(lon, lat, s=1):
    return ((lon - LON_MIN) * PPD * LON_FACTOR * s, (LAT_MAX - lat) * PPD * s)


ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
LON = LON_MIN + xs / (PPD * LON_FACTOR)
LAT = LAT_MAX - ys / PPD


def noise(scale, octaves=4, seed=0, w=W, h=H):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        gw = max(2, int(w / scale * (2 ** o)) + 2)
        gh = max(2, int(h / scale * (2 ** o)) + 2)
        g = Image.fromarray((r.random((gh, gw)) * 255).astype(np.uint8))
        layer = np.asarray(g.resize((w, h), Image.BICUBIC), np.float32) / 255.0
        out += amp * layer
        norm += amp
        amp *= 0.5
    return out / norm


def blur(arr, radius):
    img = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255.0


def fblur(arr, sigma):
    r = int(np.ceil(sigma * 3))
    w = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    w /= w.sum()
    out = arr.astype(np.float64)
    for axis in (0, 1):
        pad = np.pad(out, [(r, r) if a == axis else (0, 0) for a in (0, 1)], mode="edge")
        n = out.shape[axis]
        out = sum(wk * np.take(pad, np.arange(k, k + n), axis=axis) for k, wk in enumerate(w))
    return out


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def meander(pts, seed, amp=0.07, step=0.12):
    rr = np.random.default_rng(seed)
    P = np.array(pts, np.float64)
    ext = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        n = max(2, int(np.hypot(*(p2 - p1)) / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(P[-1])
    Q = np.array(out)
    seg = np.hypot(*np.diff(Q, axis=0).T)
    L = np.concatenate([[0.0], np.cumsum(seg)])
    tang = np.gradient(Q, axis=0)
    tang /= np.maximum(np.hypot(tang[:, 0], tang[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    ph = rr.uniform(0, 2 * np.pi, 4)
    f = rr.uniform(0.9, 1.4)
    off = amp * (1.2 * np.sin(L * f * 0.9 + ph[3]) + np.sin(L * f * 2.2 + ph[0]) + 0.5 * np.sin(L * f * 5.3 + ph[1]) + 0.25 * np.sin(L * f * 11.0 + ph[2]))
    taper = np.sin(np.pi * np.clip(L / max(L[-1], 1e-6), 0, 1)) ** 0.5
    return (Q + nrm * (off * taper)[:, None]).tolist()


land_raw = json.load(open(os.path.join(HERE, "data", "land.json")))
geo = json.load(open(os.path.join(HERE, "data", "geodata.json"), encoding="utf-8"))
extra = json.load(open(os.path.join(HERE, "data", "ranges_extra.json"), encoding="utf-8"))
geo["ranges"].extend({"pts": r["pts"], "width": r["width"], "height": r["height"]} for r in extra["ranges"])
edits = json.load(open(os.path.join(HERE, "data", "edits.json"), encoding="utf-8"))
WIDTH_K = 0.75

log(f"raster {W}x{H}, color {CW}x{CH}")
land = np.zeros((H, W), bool)
for poly in land_raw:
    for ring in poly:
        pts = [to_px(ring[i], ring[i + 1]) for i in range(0, len(ring) - 1, 2)]
        if len(pts) < 3:
            continue
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=1)
        land ^= np.asarray(m, bool)
erase = Image.new("L", (W, H), 0)
coast_cut = Image.new("L", (W, H), 0)
bent_cut = Image.new("L", (W, H), 0)
for zone in edits["erase"]:
    target = (bent_cut if zone.get("bend") else coast_cut) if zone.get("natural") else erase
    ImageDraw.Draw(target).polygon([to_px(a, b) for a, b in zone["pts"]], fill=1)
land &= ~np.asarray(erase, bool)
gy, gx = np.mgrid[0:H, 0:W]
bx = np.clip(gx + (noise(130, 3, 521) - 0.5) * 260, 0, W - 1).astype(np.int32)
by = np.clip(gy + (noise(130, 3, 522) - 0.5) * 260, 0, H - 1).astype(np.int32)
bent = np.asarray(bent_cut, np.float32)[by, bx]
cut = blur(np.maximum(np.asarray(coast_cut, np.float32), bent), 26)
warp = (noise(70, 4, 501) - 0.5) * 0.75 + (noise(18, 3, 502) - 0.5) * 0.3 + (noise(6, 2, 503) - 0.5) * 0.1
land &= ~(cut > 0.7 - warp * 0.45)

lakes = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(lakes)
for i, lk in enumerate(geo["lakes"]):
    (cx, cy), rx, ry = lk["c"], lk["rx"], lk["ry"]
    ph = np.random.default_rng(100 + i).uniform(0, 2 * np.pi, 3)
    ring_pts = []
    for k in range(64):
        a = k / 64 * 2 * np.pi
        m = 1 + 0.16 * np.sin(3 * a + ph[0]) + 0.09 * np.sin(5 * a + ph[1]) + 0.05 * np.sin(9 * a + ph[2])
        ring_pts.append(to_px(cx + np.cos(a) * rx * m, cy + np.sin(a) * ry * m))
    d.polygon(ring_pts, fill=1)
for i, ll in enumerate(geo["longLakes"]):
    line = meander(ll["pts"], 200 + i, ll["width"] * 0.25, 0.04)
    rr = np.random.default_rng(300 + i)
    for k, (a, b) in enumerate(line):
        px_, py_ = to_px(a, b)
        r = ll["width"] * PPD * (0.75 + 0.5 * (0.5 + 0.5 * np.sin(k * 0.37 + rr.uniform(0, 6))))
        d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r], fill=1)
land &= ~np.asarray(lakes, bool)
lake_mask = np.asarray(lakes, bool)
land = (blur(land.astype(np.float32), 2.0) - 0.5 + (noise(9, 3, 77) - 0.5) * 0.3) > 0
land &= np.minimum(KW - xs - 50 - (noise(40, 3, 78) - 0.5) * 60, KH - ys - 30 - (noise(40, 3, 79) - 0.5) * 40) > 0
log(f"land {land.mean() * 100:.1f}%")

landf = land.astype(np.float32)
inland_near = blur(landf, 3)
inland_mid = blur(landf, 14)
inland_far = blur(landf, 45)

n_hill = noise(90, 5, 1)
n_fine = noise(14, 3, 2)
n_ridge = 1 - np.abs(noise(16, 4, 3) * 2 - 1)
n_warp = noise(30, 3, 5) - 0.5

ridges = np.zeros((H, W), np.float32)
plateau = np.zeros((H, W), np.float32)
for rg in geo["ranges"]:
    pts = [to_px(a, b) for a, b in rg["pts"]]
    width_px = rg["width"] * PPD * WIDTH_K
    pad = width_px * 3
    xs_r = [p[0] for p in pts]
    ys_r = [p[1] for p in pts]
    x0, x1 = int(max(0, min(xs_r) - pad)), int(min(W, max(xs_r) + pad))
    y0, y1 = int(max(0, min(ys_r) - pad)), int(min(H, max(ys_r) + pad))
    sx, sy = xs[y0:y1, x0:x1], ys[y0:y1, x0:x1]
    dist = np.full(sx.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy or 1.0
        t = np.clip(((sx - ax) * dx + (sy - ay) * dy) / l2, 0, 1)
        dist = np.minimum(dist, np.hypot(sx - (ax + dx * t), sy - (ay + dy * t)))
    dist = np.maximum(dist + n_warp[y0:y1, x0:x1] * width_px * 1.4, 0)
    core = np.exp(-(dist / width_px) ** 2)
    rough = 0.3 + 0.7 * n_ridge[y0:y1, x0:x1] ** 1.6
    ridges[y0:y1, x0:x1] = np.maximum(ridges[y0:y1, x0:x1], rg["height"] * core * rough)
    if rg["width"] >= 2.0:
        plateau[y0:y1, x0:x1] = np.maximum(plateau[y0:y1, x0:x1], rg["height"] * 0.55 * np.exp(-(dist / (width_px * 1.6)) ** 2))
log("ranges done")

coastal = 0.3 + 0.7 * smoothstep(0.45, 0.82, inland_mid)
ridges *= coastal
plateau *= 0.5 + 0.5 * coastal
foothills = blur(np.clip(ridges, 0, 1), 8) * 0.26
elev_land = 0.012 + inland_mid * 0.035 + (n_hill - 0.5) * 0.06 * inland_mid + foothills
elev_land = np.maximum(elev_land, plateau) + ridges * 0.9
elev_land = np.clip(elev_land, 0.004, 1.0)
coast_fade = smoothstep(0.5, 0.75, inland_near)
elev_land *= 0.35 + 0.65 * coast_fade

depth = (1 - inland_far) * 0.09 + (1 - inland_mid) * 0.03
shelf_near = smoothstep(0.5, 1.0, 1 - blur(landf, 4))
shelf_wide = smoothstep(0.5, 1.0, 1 - inland_mid)
shelf = shelf_near + (shelf_wide - shelf_near) * smoothstep(0.35, 0.65, noise(70, 3, 611))
elev_sea = -0.0012 - depth * shelf ** 1.4
LAND_MIN = 0.012
land_min = 0.0058 + 0.0062 * smoothstep(0.45, 0.72, noise(50, 3, 612))
soft_land = blur(landf, 2.2)
t_coast = smoothstep(0.15, 0.85, soft_land)
elev = (np.maximum(elev_land, land_min) * t_coast + np.minimum(elev_sea, -0.0008) * (1 - t_coast)).astype(np.float32)

RIVER_PATHS = [(rv, meander(rv["pts"], 500 + zlib.crc32(rv["name"].encode("utf-8")) % 100000, 0.1 + 0.02 * rv["width"])) for rv in geo["rivers"]]


def to_geo(x, y):
    return x / (PPD * LON_FACTOR) + LON_MIN, LAT_MAX - y / PPD


def extend_mouth(path, others, reach=60):
    P = np.array([to_px(a, b) for a, b in path], np.float64)
    end = P[-1]
    if not (0 <= end[0] < W and 0 <= end[1] < H):
        return path
    k = max(1, min(len(P) - 1, 4))
    dirv = end - P[-1 - k]
    dirv /= max(np.hypot(*dirv), 1e-6)
    x, y = int(round(end[0])), int(round(end[1]))
    x0, y0 = max(0, x - reach), max(0, y - reach)
    ys, xs = np.nonzero(elev[y0:min(H, y + reach + 1), x0:min(W, x + reach + 1)] < -0.0004)
    cands = []
    if len(xs):
        pts = np.stack([xs + x0, ys + y0], 1).astype(np.float64)
        d = np.hypot(*(pts - end).T) - 0.6 * ((pts - end) @ dirv)
        i = int(d.argmin())
        cands.append((float(np.hypot(*(pts[i] - end))), pts[i], True))
    for o in others:
        d = np.hypot(*(o - end).T)
        i = int(d.argmin())
        if d[i] > 1.0:
            cands.append((float(d[i]), o[i], False))
    if not cands:
        return path
    dist, target, water = min(cands, key=lambda c: c[0])
    if dist > reach:
        return path
    if dist < 1.0 and water:
        tail = end + dirv[None, :] * np.arange(1.0, 9.0)[:, None]
        return [to_geo(a, b) for a, b in np.vstack([P, tail])]
    ctrl = end + dirv * dist * 0.45
    n = max(3, int(dist / 0.8))
    t = np.linspace(0, 1, n + 1)[1:, None]
    ext = (1 - t) ** 2 * end + 2 * (1 - t) * t * ctrl + t * t * target
    if water:
        tail = target - (ctrl if dist > 1 else end)
        tail /= max(np.hypot(*tail), 1e-6)
        ext = np.vstack([ext, target + tail[None, :] * np.arange(1.0, 9.0)[:, None]])
    P = np.vstack([P, ext])
    return [to_geo(a, b) for a, b in P]


_px_paths = [np.array([to_px(a, b) for a, b in path]) for _, path in RIVER_PATHS]
RIVER_PATHS = [(rv, extend_mouth(path, [q for j, q in enumerate(_px_paths) if j != i])) for i, (rv, path) in enumerate(RIVER_PATHS)]


def extend_source(path, reach=90, band=120):
    P = np.array([to_px(a, b) for a, b in path], np.float64)
    start = P[0]
    if not (0 <= start[0] < KW and 0 <= start[1] < KH):
        return path
    k = max(1, min(len(P) - 1, 4))
    dirv = start - P[k]
    dirv /= max(np.hypot(*dirv), 1e-6)
    x, y = int(round(start[0])), int(round(start[1]))
    x0, y0 = max(0, x - reach), max(0, y - reach)
    ys, xs = np.nonzero(elev[y0:min(H, y + reach + 1), x0:min(W, x + reach + 1)] < -0.0004)
    xs, ys = xs + x0, ys + y0
    ocean = (KW - xs < band) | (KH - ys < band)
    if not ocean.any():
        return path
    pts = np.stack([xs[ocean], ys[ocean]], 1).astype(np.float64)
    d = np.hypot(*(pts - start).T)
    i = int(d.argmin())
    if d[i] > reach:
        return path
    target = pts[i]
    ctrl = start + dirv * d[i] * 0.45
    n = max(3, int(d[i] / 0.8))
    t = np.linspace(0, 1, n + 1)[1:, None]
    ext = (1 - t) ** 2 * start + 2 * (1 - t) * t * ctrl + t * t * target
    tail = target - ctrl
    tail /= max(np.hypot(*tail), 1e-6)
    ext = np.vstack([ext, target + tail[None, :] * np.arange(1.0, 9.0)[:, None]])
    return [to_geo(a, b) for a, b in np.vstack([ext[::-1], P])]


RIVER_PATHS = [(rv, extend_source(path)) for rv, path in RIVER_PATHS]


SEA_E = 0.15 / 42.0
RIVER_BED = SEA_E - 0.05
RIVER_BANK = LAND_MIN
RIVER_TOP = 0.12


def carve_valley(elev, path, width):
    P = np.array([to_px(a, b) for a, b in path], np.float64)
    seg = np.hypot(*np.diff(P, axis=0).T)
    L = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.arange(0.0, L[-1], 0.75)
    P = np.stack([np.interp(t, L, P[:, 0]), np.interp(t, L, P[:, 1])], 1)
    smooth = fblur(elev, 2.0)
    xi = np.clip(P[:, 0].round().astype(int), 0, W - 1)
    yi = np.clip(P[:, 1].round().astype(int), 0, H - 1)
    h = smooth[yi, xi]
    low = np.nonzero(h <= RIVER_TOP)[0]
    if len(low) == 0:
        return elev, P[:0]
    P, h = P[low[0]:], h[low[0]:]
    n = len(P)
    grow = np.clip(np.arange(n) * 0.75 / 40.0, 0.0, 1.0)
    out = elev.copy()
    for (x, y), hh, g in zip(P, h, grow):
        core = (1.4 + 0.6 * width) * (0.55 + 0.45 * g)
        chan_r = core * 1.5
        cut = max(0.0, float(hh) - RIVER_BANK)
        reach = chan_r + 3.0 + min(10.0, cut * 300.0)
        R = int(np.ceil(reach))
        x0, x1 = max(0, int(x) - R), min(W, int(x) + R + 2)
        y0, y1 = max(0, int(y) - R), min(H, int(y) + R + 2)
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx - x, yy - y)
        orig = elev[y0:y1, x0:x1]
        valley = orig - np.maximum(orig - RIVER_BANK, 0.0) * (1.0 - smoothstep(chan_r, reach, d))
        chan = np.where(d < chan_r, RIVER_BED + (RIVER_BANK - RIVER_BED) * smoothstep(0.0, chan_r, d), np.inf)
        out[y0:y1, x0:x1] = np.minimum(out[y0:y1, x0:x1], np.minimum(valley, chan))
    return out, P


RIVER_LINES = []
for rv, path in RIVER_PATHS:
    carved, line = carve_valley(elev, path, rv["width"])
    elev = np.minimum(elev, carved)
    if len(line) > 1:
        RIVER_LINES.append((rv, line))
elev = elev.astype(np.float32)

water = elev < SEA_E
pond = Image.fromarray((water * 255).astype(np.uint8)).copy()
core = np.asarray(pond.filter(ImageFilter.MinFilter(5))) == 255
for _, line in RIVER_LINES:
    ri = np.clip(line.round().astype(int), [0, 0], [W - 1, H - 1])
    core[ri[:, 1], ri[:, 0]] |= water[ri[:, 1], ri[:, 0]]
for y0, x0 in np.concatenate([np.argwhere(core | (lake_mask & water))[::37], np.argwhere(lake_mask & water)[::3]]):
    if pond.getpixel((int(x0), int(y0))) == 255:
        ImageDraw.floodfill(pond, (int(x0), int(y0)), 128)
spurious = np.asarray(pond) == 255
elev = np.where(spurious, LAND_MIN, elev).astype(np.float32)
log(f"filled puddles: {int(spurious.sum())} px")
json.dump({"rivers": [{"name": rv["name"], "width": rv["width"], "pts": [round(float(v), 2) for xy in line for v in xy]} for rv, line in RIVER_LINES
                      if any(float(x) < KW and float(y) < KH for x, y in line)]},
          open(os.path.join(OUT, "rivers.json"), "w", encoding="utf-8"), ensure_ascii=False)
log("elevation done")

DESERTS = [(8, 21.5, 26, 8.2), (20, 28.5, 9, 3.6), (33.2, 26, 2.2, 5), (33.9, 29.9, 1.2, 1.1), (46.5, 23.5, 11, 7), (40.5, 32.3, 4.2, 2.5),
           (56, 32.3, 4.3, 3.2), (62, 27.8, 4.2, 2.4), (60, 39.8, 6, 2.8), (64.5, 42.6, 4, 2.4), (56, 43.7, 3, 1.7), (83.3, 39.2, 6.3, 2.2),
           (104, 42.5, 9, 3), (103.5, 39.8, 4, 1.8), (71.3, 26.8, 3, 2.6)]
STEPPES = [(41, 48.3, 13, 4.3), (66, 48.8, 17, 4.6), (104, 47.3, 15, 4.3), (121, 45, 3, 4), (20.3, 47, 2.2, 1.2), (35, 39, 5.5, 1.7)]


def blob_score(blobs, lon, lat, edge):
    best = np.full(lon.shape, -9, np.float32)
    for cx, cy, rx, ry in blobs:
        s = 1 - np.sqrt(((lon - cx) / rx) ** 2 + ((lat - cy) / ry) ** 2)
        best = np.maximum(best, s)
    return best + (edge - 0.5) * 0.7


n1 = noise(300, 2, 11)
n2 = noise(300, 2, 12)
edge = noise(25, 3, 13)
forest_n = noise(55, 4, 14)
dither = rng.random((H, W)).astype(np.float32)
lon = LON + (n1 - 0.5) * 3 + (edge - 0.5) * 1.8
lat = LAT + (n2 - 0.5) * 2 + (edge - 0.5) * 1.2

B = {"sea": 0, "grass": 1, "forest": 2, "taiga": 3, "steppe": 4, "dry": 5, "desert": 6, "tundra": 7, "snow": 8, "jungle": 9, "farm": 10}
biome = np.full((H, W), -1, np.int16)


def assign(mask, name):
    sel = (biome < 0) & mask
    biome[sel] = B[name]


assign(lat > 70.3, "snow")
assign(lat > 66.8, "tundra")
ds = blob_score(DESERTS, lon, lat, edge)
assign((ds > 0) | ((ds > -0.07) & (dither < (ds + 0.07) / 0.07 * 0.5)), "desert")
st = blob_score(STEPPES, lon, lat, edge)
steppe_zone = (st > 0) | ((st > -0.06) & (dither < (st + 0.06) / 0.06 * 0.5))
assign(steppe_zone & (lat > 52.5) & (lon < 60) & (forest_n > 0.55), "forest")
assign(steppe_zone, "steppe")
assign((lon < 31) & (lat > 63.5), "taiga")
assign((lat > 58.3) & (lon > 8) & (forest_n > 0.35), "taiga")
assign((lat > 58.3) & (lon > 8), "grass")
assign((lon > 58) & (lat > 55.5), "taiga")
assign((lon > 85) & (lat > 51) & (forest_n > 0.3), "taiga")
assign((lon > 85) & (lat > 51), "steppe")
assign((lat < 30) & (lon > 66) & (forest_n > 0.3), "jungle")
assign((lat < 30) & (lon > 66), "grass")
china = (lon >= 100) & (lat < 41)
assign(china & (lat < 33) & (forest_n > 0.35), "jungle")
assign(china & (lat < 33), "grass")
assign(china & (forest_n > 0.62), "forest")
assign(china, "grass")
assign((lon > 123) & (lat > 38), "forest")
med = (lat < 43.5) & (lat > 12) & (lon < 72)
assign(med & (lon < 30) & (forest_n > 0.62), "forest")
assign(med, "dry")
eu = (lon < 60) & (lat >= 43.5)
thr = np.where((lon > 28) & (lat > 51), 0.42, 0.56)
assign(eu & (forest_n > thr), "forest")
assign(eu, "grass")
assign((lat > 50) & (forest_n > 0.45), "taiga")
assign(lat > 50, "steppe")
assign(np.ones((H, W), bool), "dry")
biome[~land] = B["sea"]

FIELD_R = 10.0
gy_e, gx_e = np.gradient(elev * 42.0)
flat_low = land & (elev * 42.0 < 6.0) & (np.hypot(gx_e, gy_e) < 0.35)
patches = noise(5, 2, 41)
fields = np.zeros((H, W), bool)
for fname in sorted(os.listdir(os.path.join(OUT, "factions"))):
    if not fname.endswith(".json"):
        continue
    for v in json.load(open(os.path.join(OUT, "factions", fname), encoding="utf-8")).get("villages", []):
        vx = (v["lon"] - LON_MIN) * PPD * LON_FACTOR
        vy = (LAT_MAX - v["lat"]) * PPD
        x0, x1 = max(0, int(vx - FIELD_R) - 1), min(W, int(vx + FIELD_R) + 2)
        y0, y1 = max(0, int(vy - FIELD_R) - 1), min(H, int(vy + FIELD_R) + 2)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx - vx, yy - vy) / FIELD_R
        fields[y0:y1, x0:x1] |= d < 0.45 + (patches[y0:y1, x0:x1] - 0.5) * 1.1
fields &= flat_low & np.isin(biome, [B["grass"], B["forest"], B["steppe"], B["dry"], B["taiga"]])
biome[fields] = B["farm"]
log("biomes done: " + ", ".join(f"{k} {np.mean(biome == v) * 100:.1f}%" for k, v in B.items()))


def hexrgb(h):
    return np.array([(h >> 16) & 255, (h >> 8) & 255, h & 255], np.float32) / 255.0


PAL = {
    "grass": [0x6b9a3f, 0x5c8a36, 0x7eaa4a], "farm": [0x8ba84a, 0x7c9a40, 0xb9ad58], "forest": [0x4d7b32, 0x41702b, 0x588638],
    "taiga": [0x4b6a44, 0x3f5e3a, 0x55744d], "steppe": [0xa6a55b, 0x979651, 0xb6b36a], "dry": [0x9ca155, 0x8c924a, 0xabaa62],
    "desert": [0xdcb56d, 0xd0a860, 0xe6c47f], "tundra": [0x8d9a82, 0x7f8c75, 0x9ba790], "snow": [0xe9eef2, 0xd8e0e8, 0xf6f8fa],
    "jungle": [0x3d7733, 0x336a2c, 0x468439],
}


def up(arr, mode=Image.BILINEAR):
    if arr.dtype == bool or arr.dtype == np.int16:
        img = Image.fromarray(arr.astype(np.uint8))
        return np.asarray(img.resize((CW, CH), Image.NEAREST))
    img = Image.fromarray(arr.astype(np.float32), mode="F")
    return np.asarray(img.resize((CW, CH), mode), np.float32)


bio_c = up(biome)
elev_c = up(elev)
nf = noise(10, 3, 31, CW, CH)
nm = noise(60, 3, 32, CW, CH)
tmix = np.clip(nf * 0.6 + nm * 0.4, 0, 1)[..., None]
col = np.zeros((CH, CW, 3), np.float32)
wsum = np.zeros((CH, CW), np.float32)
for name, idx in B.items():
    if name == "sea":
        continue
    m = biome == idx
    if not m.any():
        continue
    w = up(blur(m.astype(np.float32), 1.1))
    a, dark, light = (hexrgb(c) for c in PAL[name])
    c = np.where(tmix < 0.5, dark + (a - dark) * (tmix * 2), a + (light - a) * ((tmix - 0.5) * 2))
    col += c * w[..., None]
    wsum += w
col /= np.maximum(wsum, 1e-4)[..., None]
del tmix, wsum

if (bio_c == B["desert"]).any():
    dunes = (np.sin(np.mgrid[0:CH, 0:CW][1] * 0.09 + nm * 18) * 0.5 + 0.5) * 0.06
    col[bio_c == B["desert"]] += dunes[bio_c == B["desert"]][:, None]

lat_c = LAT_MAX - np.mgrid[0:CH, 0:CW][0].astype(np.float32) / (PPD * CS)
rock_t = smoothstep(ROCK_HEIGHT[0] / 42.0, ROCK_HEIGHT[1] / 42.0, elev_c) * (bio_c != B["sea"])
rock = hexrgb(0x8a7f6d) * (0.9 + nf[..., None] * 0.2)
col = col * (1 - rock_t[..., None]) + rock * rock_t[..., None]
snowline = 0.88 - np.clip(lat_c - 28, 0, 42) * 0.005
snow_t = smoothstep(snowline, snowline + 0.08, elev_c + (nf - 0.5) * 0.05) * (bio_c != B["sea"])
col = col * (1 - snow_t[..., None]) + hexrgb(0xeef2f6) * snow_t[..., None]

near_c = up(inland_near)
beach_t = smoothstep(0.62, 0.5, near_c) * (bio_c != B["sea"]) * (elev_c < 0.03) * (bio_c != B["snow"]) * (bio_c != B["tundra"])
col = col * (1 - beach_t[..., None] * 0.8) + hexrgb(0xd8c890) * beach_t[..., None] * 0.8

sea = bio_c == B["sea"]
depth_c = np.clip(-elev_c / 0.12, 0, 1)
sea_col = hexrgb(0x4585b0) + (hexrgb(0x19304f) - hexrgb(0x4585b0)) * (depth_c[..., None] ** 0.7) + (nf[..., None] - 0.5) * 0.03
sea_w = np.clip(up(blur((biome == B["sea"]).astype(np.float32), 0.8)), 0, 1)[..., None]
col = col * (1 - sea_w) + sea_col * sea_w
del sea_col, sea_w

river_c = Image.new("L", (CW, CH), 0)
rd = ImageDraw.Draw(river_c)
for rv, line in RIVER_LINES:
    pts = [(float(x) * CS, float(y) * CS) for x, y in line]
    rd.line(pts, fill=255, width=int((2.8 + 1.2 * rv["width"]) * CS) + 2, joint="curve")
riv = np.asarray(river_c.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255.0 * (~sea)[..., None]
col = col * (1 - riv * 0.6) + hexrgb(0x3a4636) * riv * 0.6

shade = 1 - blur(np.clip(1 - inland_mid, 0, 1), 2) * 0
col = np.clip(col, 0, 1)
Image.fromarray((col[:KH * CS, :KW * CS] * 255).astype(np.uint8)).save(os.path.join(OUT, "color.png"), optimize=True)
log("color.png saved")
del col

SPLAT = [("grass",), ("forest", "jungle"), ("taiga",), ("farm",), ("steppe", "dry"), ("desert",), ("tundra",), ("snow",)]
snowline_h = 0.88 - np.clip(LAT - 28, 0, 42) * 0.005
snow_h = smoothstep(snowline_h, snowline_h + 0.08, elev) * land
chans = [blur(np.isin(biome, [B[n] for n in names]).astype(np.float32), 0.9) for names in SPLAT]
chans = [c * (1 - snow_h) for c in chans[:7]] + [np.maximum(chans[7], snow_h)]
spl = np.stack(chans, -1)
spl /= np.maximum(spl.sum(-1, keepdims=True), 1e-4)
spl *= land[..., None]
for k, part in enumerate((spl[..., :4], spl[..., 4:])):
    Image.fromarray((np.clip(part[:KH, :KW], 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"splat{k}.png"), optimize=True)
del spl, chans
log("splat maps saved")

MESH_STEP = 2
coarse = Image.fromarray(elev[::MESH_STEP, ::MESH_STEP].astype(np.float32), mode="F").resize((CW, CH), Image.BILINEAR)
fine = Image.fromarray(elev.astype(np.float32), mode="F").resize((CW, CH), Image.BICUBIC)
crag = smoothstep(0.08, 0.4, elev_c) * (bio_c != B["sea"])
rel = (noise(5, 3, 41, CW, CH) - 0.5) * (0.0025 + 0.012 * crag) + (noise(1.6, 2, 42, CW, CH) - 0.5) * 0.0012 * (bio_c != B["sea"])
detail_h = (np.asarray(fine, np.float32) - np.asarray(coarse, np.float32) + rel) * 42.0
del coarse, fine, rel, crag
unit = 1.0 / CS
gx = np.zeros_like(detail_h)
gz = np.zeros_like(detail_h)
gx[:, 1:-1] = (detail_h[:, 2:] - detail_h[:, :-2]) / (2 * unit)
gz[1:-1, :] = -(detail_h[2:, :] - detail_h[:-2, :]) / (2 * unit)
relief = np.stack([np.clip(gx / 4 + 0.5, 0, 1), np.clip(gz / 4 + 0.5, 0, 1), np.full_like(gx, 1.0)], -1)
Image.fromarray((relief[:KH * CS, :KW * CS] * 255).astype(np.uint8)).save(os.path.join(OUT, "relief.png"), optimize=True)
del relief, gx, gz, detail_h
log("relief.png saved")

HMIN, HMAX = -0.12, 1.0
enc = np.clip((elev - HMIN) / (HMAX - HMIN), 0, 1)
(enc[:KH, :KW] * 65535).astype("<u2").tofile(os.path.join(OUT, "height.r16"))
Image.fromarray(biome[:KH, :KW].astype(np.uint8)).save(os.path.join(OUT, "biome.png"), optimize=True)
meta = {
    "width": KW, "height": KH, "fullWidth": W, "fullHeight": H, "colorScale": CS,
    "lonMin": LON_MIN, "lonMax": KEEP_LON_MAX, "latMin": KEEP_LAT_MIN, "latMax": LAT_MAX, "pxPerDegLat": PPD, "lonFactor": LON_FACTOR,
    "heightMin": HMIN, "heightMax": HMAX, "rockHeight": list(ROCK_HEIGHT),
    "biomes": {k: v for k, v in B.items()},
}
json.dump(meta, open(os.path.join(OUT, "world.json"), "w"), indent=1)
log(f"done: height.r16 {KW}x{KH}, biome.png, world.json; max elev {elev.max():.2f}, min {elev.min():.3f}")
