import json, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "maps", "village_fields.json")
HALF_X, HALF_Z = 120.0, 80.0
rnd = random.Random(1347)

CROPS = {
    "wheat": [0.80, 0.70, 0.38],
    "barley": [0.73, 0.68, 0.42],
    "plowed": [0.47, 0.37, 0.26],
    "meadow": [0.40, 0.56, 0.27],
    "flax": [0.47, 0.58, 0.34],
}
props, patches = [], []


def prop(pid, x, z, rot=None, scale=1.0):
    props.append({"id": pid, "x": round(x, 2), "z": round(z, 2), "rot": round(rnd.uniform(0, 360) if rot is None else rot, 1), "scale": round(scale, 2)})


def patch(kind, x, z, w, h, rot=0.0, layer=0):
    patches.append({"kind": kind if isinstance(kind, str) else "road", "color": CROPS[kind] if isinstance(kind, str) else kind, "x": round(x, 2), "z": round(z, 2), "w": round(w, 2), "h": round(h, 2), "rot": round(rot, 1), "layer": layer})


def spaced(n, x0, x1, z0, z1, gap, taken):
    out = []
    tries = 0
    while len(out) < n and tries < n * 40:
        tries += 1
        x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
        if all((x - a) ** 2 + (z - b) ** 2 >= gap * gap for a, b in taken + out):
            out.append((x, z))
    taken.extend(out)
    return out


x = -HALF_X
kinds = ["meadow", "wheat", "plowed", "barley", "meadow", "flax", "wheat", "plowed"]
i = 0
while x < HALF_X - 5:
    w = min(rnd.uniform(26, 44), HALF_X - x)
    z = -HALF_Z
    while z < HALF_Z - 5:
        h = min(rnd.uniform(30, 60), HALF_Z - z)
        kind = kinds[(i * 3 + int(z)) % len(kinds)] if rnd.random() < 0.8 else "meadow"
        patch(kind, x + w / 2, z + h / 2, w - rnd.uniform(1.5, 3.5), h - rnd.uniform(1.5, 3.5), rnd.uniform(-2.5, 2.5))
        z += h
        i += 1
    x += w

road = []
z = -HALF_Z - 30
while z < HALF_Z + 40:
    road.append((8 * math.sin(z / 37.0) + 4, z))
    z += 6
for (x0, z0), (x1, z1) in zip(road, road[1:]):
    ang = math.degrees(math.atan2(x1 - x0, z1 - z0))
    patch([0.55, 0.45, 0.31], (x0 + x1) / 2, (z0 + z1) / 2, 5.0, math.hypot(x1 - x0, z1 - z0) + 1.0, ang, layer=1)

taken = []
village = (6.0, 118.0)
prop("Well", *village, rot=0)
taken.append(village)
for k in range(10):
    for _ in range(60):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(13, 30)
        hx, hz = village[0] + math.cos(a) * r, village[1] + math.sin(a) * r * 0.75
        if hz < HALF_Z + 12 or any((hx - p) ** 2 + (hz - q) ** 2 < 11 ** 2 for p, q in taken):
            continue
        face = math.degrees(math.atan2(village[0] - hx, village[1] - hz))
        prop("House_Long" if k % 3 == 0 else "House_Small", hx, hz, face + 180 + rnd.uniform(-12, 12), rnd.uniform(0.95, 1.1))
        taken.append((hx, hz))
        break

for gx0, gz, length in ((-30, HALF_Z + 8, 70), (-36, HALF_Z + 26, 24), (40, HALF_Z + 30, 30)):
    for s in range(int(length / 2)):
        prop("Fence", gx0 + s * 2.0, gz + rnd.uniform(-0.1, 0.1), 0 + rnd.uniform(-3, 3))
for _ in range(9):
    prop("Haystack", rnd.uniform(-60, 70), rnd.uniform(HALF_Z + 3, HALF_Z + 14), scale=rnd.uniform(0.9, 1.2))
prop("Cart", village[0] + 9, village[1] - 9, 35)
prop("Cart", village[0] - 26, village[1] - 14, 160)
for x, z in spaced(18, -70, 80, HALF_Z + 30, HALF_Z + 70, 7, taken):
    prop(rnd.choice(["Tree_Round", "Tree_Round_Big", "Bush"]), x, z, scale=rnd.uniform(0.9, 1.2))

for x, z in spaced(260, -190, 190, -HALF_Z - 70, -HALF_Z - 9, 4.6, taken):
    edge = z > -HALF_Z - 18
    pid = "Bush" if edge and rnd.random() < 0.5 else rnd.choice(["Tree_Pine", "Tree_Pine", "Tree_Round", "Tree_Round_Big"])
    prop(pid, x, z, scale=rnd.uniform(0.85, 1.25))

for side in (-1, 1):
    for x, z in spaced(40, HALF_X + 10, HALF_X + 70, -HALF_Z - 10, HALF_Z + 40, 6, taken):
        prop(rnd.choice(["Tree_Round", "Tree_Round_Big", "Tree_Pine", "Bush", "Rock"]), side * x, z, scale=rnd.uniform(0.85, 1.3))

for x, z in spaced(25, -HALF_X - 30, HALF_X + 30, -HALF_Z - 8, HALF_Z + 8, 9, taken):
    if abs(x) > HALF_X + 3 or abs(z) > HALF_Z + 3:
        prop("Rock", x, z, scale=rnd.uniform(0.7, 1.6))

for k in range(22):
    a = k / 22 * math.tau + rnd.uniform(-0.1, 0.1)
    r = rnd.uniform(260, 330)
    prop("Hill", math.cos(a) * r * 1.2, math.sin(a) * r, scale=rnd.uniform(1.4, 2.6))

data = {
    "name": "Поля у деревни",
    "ground": [0.36, 0.5, 0.24],
    "field": [0.43, 0.56, 0.27],
    "sun": {"pitch": 34, "yaw": -42, "intensity": 1.7, "color": [1.0, 0.9, 0.76]},
    "ambientSky": [0.62, 0.68, 0.78],
    "ambientEquator": [0.52, 0.53, 0.46],
    "ambientGround": [0.26, 0.25, 0.2],
    "fogColor": [0.76, 0.8, 0.82],
    "fogStart": 90,
    "fogEnd": 430,
    "patches": patches,
    "props": props,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("patches", len(patches), "props", len(props))
