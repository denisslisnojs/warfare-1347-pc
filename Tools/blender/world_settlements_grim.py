import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldGrim"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())
TOWN_BUDGET = 1000

M["lime"] = mat("env_limestone_grim", (0.86, 0.81, 0.7), 0.85)
M["brick"] = mat("env_brick_grim", (0.6, 0.29, 0.19), 0.9)
M["tile"] = mat("env_roof_red_grim", (0.7, 0.3, 0.18), 0.85)
M["lead"] = mat("env_roof_slate_lead", (0.47, 0.5, 0.53), 0.5)
M["plaster"] = mat("env_plaster_grim", (0.93, 0.89, 0.8), 0.95)
M["ochre"] = mat("env_wall_ochre", (0.86, 0.7, 0.5), 0.95)
M["redstone"] = mat("env_stone_red", (0.64, 0.34, 0.26), 0.9)
M["marble"] = mat("env_white_stone_grim", (0.94, 0.92, 0.87), 0.6)
M["cypress"] = mat("env_cypress_grim", (0.1, 0.26, 0.13), 0.9)
M["olive"] = mat("env_olive", (0.27, 0.36, 0.18), 0.9)
M["vine"] = mat("env_vine", (0.3, 0.43, 0.16), 0.9)
M["paving"] = mat("env_paving_grim", (0.76, 0.71, 0.62), 0.9)
M["rocky"] = mat("env_rock_hill_grim", (0.45, 0.41, 0.36), 1.0)
M["cloth"] = mat("env_felt_grim", (0.9, 0.86, 0.78), 0.95)
M["awning"] = mat("env_flag_awning", (0.4, 0.14, 0.46), 0.8)
mat("env_flag", (0.4, 0.14, 0.46), 0.8)


def local(c, rz):
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0))
    return lambda x, y, z=0.0: base + rot @ Vector((x, y, z))


def cypress(c, h):
    x, y, z = c
    lathe([(0.0, 0.0), (0.11, 0.03), (0.14, 0.3), (0.09, 0.75), (0.0, 1.0)], (x, y, z), h, "cypress", 8)


def olive(c, s, seed=0):
    rr = random.Random(seed)
    x, y, z = c
    log((x, y, z), (x + rr.uniform(-0.03, 0.03), y, z + s * 0.35), s * 0.05, "log_dark", 5)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s * 0.28, matrix=Matrix.Translation((x, y, z + s * 0.48)) @ Matrix.Diagonal((1.25, 1.1, 0.75, 1.0)))
    for v in bm.verts:
        v.co += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1))) * s * 0.04
    put("olive", bm, "olive", False)


DOME = [(0.0, 0.0), (1.0, 0.0), (0.98, 0.3), (0.88, 0.58), (0.68, 0.82), (0.38, 0.97), (0.0, 1.02)]


def dome(c, r, drum_h, m="lead", drum="lime", cross=True):
    x, y, z = c
    cone((x, y, z), r * 1.04, r * 1.04, drum_h, drum, 12, 0.0, False)
    for i in range(12):
        a = (i + 0.5) / 12 * math.tau
        box((x + math.cos(a) * r * 1.05, y + math.sin(a) * r * 1.05, z + drum_h * 0.55), (r * 0.1, r * 0.12, drum_h * 0.5), "window", a)
    cone((x, y, z + drum_h * 0.9), r * 1.1, r * 1.1, drum_h * 0.12, "brick", 12)
    lathe(DOME, (x, y, z + drum_h), r, m, 14)
    top = z + drum_h + r * 1.02
    if cross:
        box((x, y, top + r * 0.25), (r * 0.06, r * 0.06, r * 0.5), "gold")
        box((x, y, top + r * 0.36), (r * 0.24, r * 0.06, r * 0.06), "gold")
    return top + r * 0.5


def bands(c, size, h, rz, m="brick", n=2):
    for k in range(n):
        z = c[2] + h * (0.3 + 0.38 * k)
        box((c[0], c[1], z), (size[0] * 1.02, size[1] * 1.02, h * 0.05), m, rz)


def church(c, s, rz, dome_m="lead", wall_m="lime"):
    L = local(c, rz)
    h = 0.55 * s
    box(L(0, 0, h / 2), (0.9 * s, 0.9 * s, h), wall_m, rz)
    bands(L(0, 0), (0.9 * s, 0.9 * s), h, rz)
    for ax, ay, ln in ((1, 0, 0.42), (-1, 0, 0.32), (0, 1, 0.32), (0, -1, 0.32)):
        w = 0.42 * s
        q = L(ax * (0.45 + ln / 2) * s, ay * (0.45 + ln / 2) * s)
        sx, sy = (ln * s, w) if ax else (w, ln * s)
        box((q.x, q.y, h * 0.42), (sx, sy, h * 0.84), wall_m, rz)
        gable((q.x, q.y, h * 0.84), sx if ax else sy, w, 0.16 * s, "tile", rz + (0 if ax else math.pi / 2), 0.03, 0.03)
    q = L(0.95 * s, 0)
    cone((q.x, q.y, 0), 0.2 * s, 0.2 * s, h * 0.7, wall_m, 10)
    lathe([(0.0, 0.0), (1.0, 0.0), (0.7, 0.6), (0.0, 0.8)], (q.x, q.y, h * 0.7), 0.2 * s, "tile", 10)
    for k in range(3):
        p = L(-0.68 * s, (k - 1) * 0.12 * s, h * 0.45)
        box((p.x, p.y, p.z), (0.02, 0.06 * s, 0.22 * s), "window", rz)
    return dome(L(0, 0, h), 0.3 * s, 0.24 * s, dome_m)


def great_church(c, s, rz):
    L = local(c, rz)
    h = 0.6 * s
    box(L(0, 0, h / 2), (1.5 * s, 1.3 * s, h), "lime", rz)
    bands(L(0, 0), (1.5 * s, 1.3 * s), h, rz, n=3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = L(sx * 0.62 * s, sy * 0.52 * s)
            box((q.x, q.y, h * 0.62), (0.26 * s, 0.26 * s, h * 1.24), "lime", rz)
            pyramid((q.x, q.y, h * 1.24), 0.28 * s, 0.1 * s, "lead", 4, rz)
    for sx in (-1, 1):
        q = L(sx * 0.42 * s, 0, h)
        lathe(DOME, (q.x, q.y, q.z), 0.36 * s, "lead", 12)
    top = dome(L(0, 0, h), 0.56 * s, 0.22 * s, "gold", "lime")
    q = L(0.82 * s, 0)
    cone((q.x, q.y, 0), 0.32 * s, 0.32 * s, h * 0.75, "lime", 12)
    lathe(DOME, (q.x, q.y, h * 0.75), 0.32 * s, "lead", 12)
    return top


def wall(a, b, h, center, z0=0.0, m="lime", t=0.26, band=True):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, z0 + h / 2), (length, t, h), m, rz)
    if band:
        for k in (0.35, 0.7):
            box((mid.x + n.x * t * 0.02, mid.y + n.y * t * 0.02, z0 + h * k), (length, t * 1.06, h * 0.07), "brick", rz)
    k = max(2, int(length / 0.2))
    for i in range(k):
        q = a.lerp(b, (i + 0.5) / k) + n * (t / 2 - 0.05)
        box((q.x, q.y, z0 + h + 0.05), (0.1, 0.08, 0.1), m, rz)


def tower(c, s, h, m="lime", rz=0.0, cap="crenel"):
    x, y, z = c
    box((x, y, z + h / 2), (s, s, h), m, rz)
    bands((x, y, z), (s, s), h, rz, n=3)
    for k in range(2):
        a = rz + k * math.pi / 2
        box((x + math.cos(a) * s * 0.51, y + math.sin(a) * s * 0.51, z + h * 0.78), (s * 0.12, s * 0.12, s * 0.22), "window", a)
    if cap == "roof":
        pyramid((x, y, z + h), s * 1.12, s * 0.55, "tile", 4, rz)
        return z + h + s * 0.55
    if cap == "cone":
        cone((x, y, z + h), s * 0.68, 0.0, s * 0.8, "tile", 8, 0.0, False)
        return z + h + s * 0.8
    L = local((x, y, z), rz)
    for u, v in ((-0.35, -0.42), (0.35, -0.42), (-0.35, 0.42), (0.35, 0.42), (-0.42, 0.0), (0.42, 0.0), (0.0, -0.42), (0.0, 0.42)):
        q = L(u * s, v * s)
        box((q.x, q.y, z + h + 0.06), (s * 0.18, s * 0.18, 0.12), m, rz)
    return z + h + 0.12


def round_tower(c, r, h, m="lime", cap="crenel"):
    x, y, z = c
    cone((x, y, z), r * 1.08, r * 0.96, h, m, 12)
    for k in (0.35, 0.7):
        cone((x, y, z + h * k), r * (1.06 - 0.12 * k), r * (1.06 - 0.12 * k), h * 0.06, "brick", 12)
    if cap == "cone":
        cone((x, y, z + h), r * 1.05, 0.0, r * 1.3, "tile", 12)
        return z + h + r * 1.3
    for i in range(8):
        a = i / 8 * math.tau
        box((x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, z + h + 0.06), (r * 0.3, r * 0.22, 0.12), m, a)
    return z + h + 0.12


def gate(c, w, h, rz, m="lime"):
    L = local(c, rz)
    box(L(0, 0, h / 2), (w, w * 0.45, h), m, rz)
    bands(L(0, 0, 0), (w, w * 0.45), h, rz)
    box(L(0, -w * 0.23, h * 0.32), (w * 0.34, 0.02, h * 0.5), "window", rz)
    cone(L(0, -w * 0.23, h * 0.57), w * 0.17, w * 0.17, 0.02, "window", 10)
    for sx in (-1, 1):
        tower(L(sx * w * 0.6, 0), w * 0.42, h * 1.15, m, rz)


def ring_walls(pts, h, center, z0, ts, m, gates=(), round_=False):
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        wall(a + dd * ts * 0.6, b - dd * ts * 0.6, h, center, z0, m)
    for i, p in enumerate(pts):
        if i in gates:
            prev, nxt = Vector(pts[i - 1]), Vector(pts[(i + 1) % len(pts)])
            t = (nxt - prev).normalized()
            gate((p[0], p[1], z0), ts * 1.6, h * 1.35, math.atan2(t.y, t.x), m)
        elif round_:
            round_tower((p[0], p[1], z0), ts * 0.55, h * 1.3, m)
        else:
            t = Vector(pts[(i + 1) % len(pts)]) - Vector(pts[i - 1])
            tower((p[0], p[1], z0), ts, h * 1.3, m, math.atan2(t.y, t.x))


def house(c, w, d, h, rz, m="plaster", court=False, budget=TOWN_BUDGET):
    name = "House_2" if h > 0.33 else rnd.choice(("House_1", "House_1", "House_2", "Blacksmith"))
    building(name, c, rz, w / 0.64 * 1.1, "tile", budget, m, {"beam": m, "grey": "lime", "dark": "redstone", "plank": "log_dark"})
    if court:
        L = local(c, rz)
        q = L(0, d * 0.95)
        box((q.x, q.y, 0.1), (w, d * 0.5, 0.2), m, rz)


house = grouped(house)


def houses(n, rmin, rmax, avoid, seed, center=(0.0, 0.0), court=0.2, budget=TOWN_BUDGET):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 5000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r
        if any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < 0.46 for p in placed):
            continue
        placed.append((x, y))
        house((x, y, 0.0), rr.uniform(0.3, 0.46), rr.uniform(0.26, 0.38), rr.uniform(0.24, 0.4), a + math.pi / 2 + rr.uniform(-0.12, 0.12),
              rr.choice(("plaster", "plaster", "ochre", "lime")), rr.random() < court, budget)
    return placed


def colonnade(a, b, h, z0=0.0, step=0.16, roof=True, rz_roof=None):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d = b - a
    n = max(2, int(d.length / step))
    for i in range(n + 1):
        q = a.lerp(b, i / n)
        cone((q.x, q.y, z0), 0.035, 0.03, h, "marble", 6)
    mid = (a + b) / 2
    rz = math.atan2(d.y, d.x)
    box((mid.x, mid.y, z0 + h + 0.03), (d.length + 0.06, 0.12, 0.06), "marble", rz)
    if roof:
        gable((mid.x, mid.y, z0 + h + 0.06), d.length, 0.16, 0.08, "tile", rz, 0.03, 0.02)


def forum(c, s, rz):
    L = local(c, rz)
    q = L(0, 0)
    box((q.x, q.y, 0.012), (s, s * 0.75, 0.024), "paving", rz)
    for sy in (-1, 1):
        colonnade(L(-s * 0.45, sy * s * 0.33), L(s * 0.45, sy * s * 0.33), 0.3)
    cone((q.x, q.y, 0.0), 0.06, 0.05, 0.75, "marble", 8)
    box((q.x, q.y, 0.8), (0.1, 0.1, 0.1), "gold")


def aqueduct(a, b, h, tiers=2):
    a, b = Vector((a[0], a[1], 0.0)), Vector((b[0], b[1], 0.0))
    d = b - a
    rz = math.atan2(d.y, d.x)
    n = max(2, int(d.length / 0.32))
    for i in range(n + 1):
        q = a.lerp(b, i / n)
        box((q.x, q.y, h / 2), (0.09, 0.14, h), "lime", rz)
    mid = (a + b) / 2
    for t in range(tiers):
        z = h * (t + 1) / tiers
        box((mid.x, mid.y, z - 0.04), (d.length, 0.15, 0.08), "lime", rz)
        box((mid.x, mid.y, z - 0.09), (d.length, 0.155, 0.02), "brick", rz)
    box((mid.x, mid.y, h + 0.02), (d.length, 0.1, 0.04), "brick", rz)


def hippodrome(c, length, width, rz):
    L = local(c, rz)
    hl, hw = length / 2, width / 2
    for sy in (-1, 1):
        q = L(0, sy * hw)
        box((q.x, q.y, 0.12), (length, 0.22, 0.24), "lime", rz)
        box((q.x, q.y, 0.25), (length, 0.24, 0.03), "brick", rz)
        colonnade(L(-hl, sy * (hw + 0.1)), L(hl, sy * (hw + 0.1)), 0.18, 0.24, 0.2, False)
    for k in range(9):
        a = -math.pi / 2 + k / 8 * math.pi
        q = L(hl + math.cos(a) * hw, math.sin(a) * hw)
        box((q.x, q.y, 0.12), (0.22, hw * 0.42, 0.24), "lime", rz + a)
    box(L(-hl, 0, 0.18), (0.22, width + 0.2, 0.36), "lime", rz)
    q = L(0, 0)
    box((q.x, q.y, 0.01), (length - 0.1, width - 0.25, 0.02), "paving", rz)
    box((q.x, q.y, 0.05), (length * 0.66, 0.1, 0.08), "marble", rz)
    for x in (-0.3, 0.3):
        p = L(x * length, 0)
        cone((p.x, p.y, 0.08), 0.06, 0.012, 0.6, "lime", 4)
    p = L(0, 0)
    cone((p.x, p.y, 0.08), 0.04, 0.035, 0.45, "brick", 8)


def palace(c, s, rz):
    L = local(c, rz)
    hw = 0.62 * s
    q = L(0, 0)
    box((q.x, q.y, 0.012), (hw * 2, hw * 2, 0.024), "paving", rz)
    for k in range(4):
        a = rz + k * math.pi / 2
        p = L(math.cos(k * math.pi / 2) * hw, math.sin(k * math.pi / 2) * hw)
        box((p.x, p.y, 0.22 * s), (0.28 * s, hw * 2.2, 0.44 * s), "plaster", a)
        bands((p.x, p.y, 0.0), (0.28 * s, hw * 2.2), 0.44 * s, a, n=1)
        gable((p.x, p.y, 0.44 * s), hw * 2.2, 0.28 * s, 0.14 * s, "tile", a + math.pi / 2, 0.04, 0.03)
        e = L(math.cos(k * math.pi / 2) * hw * 0.7, math.sin(k * math.pi / 2) * hw * 0.7)
        f = Vector((-math.sin(a), math.cos(a), 0)) * hw * 0.62
        colonnade(e - f, e + f, 0.22 * s, 0.0, 0.15, False)
    box((q.x, q.y, 0.04), (hw * 0.6, hw * 0.6, 0.06), "hedge" if "hedge" in M else "olive", rz)
    cone((q.x, q.y, 0.0), 0.08 * s, 0.08 * s, 0.1, "marble", 10)
    p = L(hw, hw)
    return tower((p.x, p.y, 0.0), 0.3 * s, 1.0 * s, "lime", rz, "roof")


def capital():
    outer = ring(3.55, 14, 0.0, 2, 0.2)
    ring_walls(outer, 0.62, (0, 0), 0.0, 0.3, "lime", gates=(0, 5, 9))
    inner = ring(3.1, 14, 0.0, 2, 0.2)
    for i in range(len(inner)):
        a, b = Vector(inner[i]), Vector(inner[(i + 1) % len(inner)])
        wall(a, b, 0.42, (0, 0), 0.0, "lime", 0.16)
    great_church((0.55, 0.65, 0.0), 0.95, 0.15)
    palace((-0.85, -0.55), 0.95, 0.15)
    hippodrome((0.75, -1.25), 2.0, 0.62, 0.15)
    forum((-1.0, 1.15), 0.8, 0.15)
    aqueduct((-3.3, 1.6), (-1.6, 1.0), 0.75)
    church((1.95, 0.6, 0.0), 0.45, 0.4)
    avoid = [((0.55, 0.65), 1.2), ((-0.85, -0.55), 0.95), ((0.75, -1.25), 1.2), ((-1.0, 1.15), 0.6), ((1.95, 0.6), 0.45), ((-2.45, 1.3), 0.4)]
    houses(30, 0.5, 2.85, avoid, 11, court=0.3)
    for k in range(8):
        a = k / 8 * math.tau + 0.2
        cypress((math.cos(a) * 2.9, math.sin(a) * 2.9, 0.0), 0.6)
    flag((0.55, 0.65, 2.0), 0.75)
    return finish("WorldTown_grim_capital")


def large():
    pts = ring(2.85, 10, 0.03, 5, 0.2)
    ring_walls(pts, 0.58, (0, 0), 0.0, 0.28, "lime", gates=(0, 5))
    church((0.3, 0.35, 0.0), 0.8, 0.2)
    forum((-0.75, -0.7), 0.8, 0.3)
    aqueduct((-2.6, 1.4), (-0.6, 0.9), 0.6, 1)
    p = tower((-0.95, 0.95, 0.0), 0.36, 1.2, "lime", 0.2, "roof")
    flag((-0.95, 0.95, p), 0.6)
    houses(24, 0.55, 2.35, [((0.3, 0.35), 1.0), ((-0.75, -0.7), 0.55), ((-0.95, 0.95), 0.35), ((-1.5, 1.15), 0.35)], 21, court=0.25)
    for k in range(5):
        cypress((3.1 + (k % 2) * 0.2, -0.8 + k * 0.4, 0.0), 0.6)
    return finish("WorldTown_grim_large")


def medium():
    pts = ring(1.95, 8, 0.05, 6, 0.4)
    ring_walls(pts, 0.5, (0, 0), 0.0, 0.24, "lime", gates=(0,))
    church((0.2, 0.2, 0.0), 0.62, 0.4)
    flag((-0.7, -0.4, 0.0), 1.2)
    houses(10, 0.45, 1.5, [((0.2, 0.2), 0.75)], 31)
    houses(7, 2.3, 2.95, [((2.25, 1.45), 0.85)], 33)
    vineyard((2.25, 1.45), 1.1, 0.8, 0.5)
    for k in range(5):
        olive((-2.4 + k * 0.32, -2.0 + (k % 2) * 0.25, 0.0), 0.55, k)
    return finish("WorldTown_grim_medium")


def vineyard(c, w, d, rz):
    L = local(c, rz)
    q = L(0, 0)
    box((q.x, q.y, 0.012), (w, d, 0.024), "earth", rz)
    rows = int(d / 0.14)
    for i in range(rows):
        p = L(0, -d / 2 + (i + 0.5) * d / rows)
        box((p.x, p.y, 0.06), (w * 0.94, 0.05, 0.08), "vine", rz)


def rock(c, r, sc=(1.0, 1.0, 1.0), seed=0, m="rocky"):
    rr = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)))
    for v in bm.verts:
        v.co += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-0.5, 1.0))) * r * 0.16
    put("rock", bm, m, False)


def barracks(c, w, d, rz):
    L = local(c, rz)
    box(L(0, 0, 0.12), (w, d, 0.24), "plaster", rz)
    gable(L(0, 0, 0.24), w, d, 0.13, "tile", rz, 0.03, 0.03)


def castle_citadel():
    outer = [(-2.0, -1.9), (0.0, -2.05), (2.0, -1.9), (2.05, 0.0), (2.0, 1.9), (0.0, 2.05), (-2.0, 1.9), (-2.05, 0.0)]
    ring_walls(outer, 0.5, (0, 0), 0.0, 0.28, "lime", gates=(1,))
    inner = [(-1.15, -1.05), (1.15, -1.05), (1.15, 1.1), (-1.15, 1.1)]
    for i in range(4):
        a, b = Vector(inner[i]), Vector(inner[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.2, b - dd * 0.2, 0.78, (0, 0), 0.0, "lime", 0.3)
    for p in inner:
        tower((p[0], p[1], 0.0), 0.36, 1.1, "lime")
    gate((0.0, -1.05, 0.0), 0.5, 1.0, 0.0)
    church((0.25, 0.3, 0.0), 0.6, 0.0, "gold")
    p = tower((-0.55, 0.45, 0.0), 0.42, 1.55, "lime", 0.0, "roof")
    flag((-0.55, 0.45, p), 0.7)
    for k in range(4):
        barracks((-1.55 + k * 1.03, -1.5, 0.0), 0.7, 0.26, 0.0)
    return finish("WorldCastle_grim_citadel")


def castle_fort():
    cone((0.0, 0.0, -0.05), 2.4, 1.9, 0.32, "rocky", 24)
    z = 0.27
    pts = [(-1.4, -1.0), (1.4, -1.0), (1.4, 1.0), (-1.4, 1.0)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.18, b - dd * 0.18, 0.62, (0, 0), z, "lime", 0.26)
    for p in pts:
        round_tower((p[0], p[1], z), 0.24, 0.85, "lime")
    for x in (-0.47, 0.47):
        round_tower((x, -1.0, z), 0.18, 0.75, "lime")
    gate((0.0, -1.0, z), 0.48, 0.92, 0.0)
    barracks((-0.55, 0.45, z), 1.0, 0.3, 0.0)
    barracks((0.55, 0.45, z), 1.0, 0.3, 0.0)
    box((0.0, -0.2, z + 0.25), (0.6, 0.45, 0.5), "plaster", 0.0)
    pyramid((0.0, -0.2, z + 0.5), 0.66, 0.22, "tile", 4, 0.0)
    flag((0.0, -0.2, z + 0.7), 0.7)
    return finish("WorldCastle_grim_fort")


def castle_camp():
    pts = [(-1.85, -1.4), (1.85, -1.4), (1.85, 1.4), (-1.85, 1.4)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.2, b - dd * 0.2, 0.42, (0, 0), 0.0, "lime", 0.2, False)
    for p in pts:
        tower((p[0], p[1], 0.0), 0.3, 0.7, "lime", 0.0, "roof")
    for x in (0.0,):
        gate((x, -1.4, 0.0), 0.44, 0.6, 0.0)
    box((0.0, 0.0, 0.012), (0.3, 2.5, 0.024), "paving", 0.0)
    box((0.0, 0.0, 0.012), (3.4, 0.3, 0.024), "paving", 0.0)
    for sx in (-1, 1):
        for k in range(3):
            barracks((sx * 1.0, -0.95 + k * 0.55 if k < 2 else 0.9, 0.0), 1.15, 0.28, 0.0)
    box((0.0, 0.75, 0.18), (0.7, 0.5, 0.36), "plaster", 0.0)
    gable((0.0, 0.75, 0.36), 0.7, 0.5, 0.18, "tile", 0.0, 0.04, 0.03)
    colonnade((-0.35, 0.45), (0.35, 0.45), 0.26, 0.0, 0.12, False)
    for x in (-0.25, 0.25):
        flag((x, 0.3, 0.0), 1.0, 0.35)
    for k in range(5):
        a = k / 5 * math.pi + 0.3
        q = (math.cos(a) * 2.3, -1.9 - math.sin(a) * 0.4)
        cone((q[0], q[1], 0.0), 0.16, 0.0, 0.26, "cloth", 4, 0.3, False)
    return finish("WorldCastle_grim_camp")


def castle_pass():
    for c, r, sc, sd in (((-1.55, 0.0, 0.25), 1.05, (0.9, 1.6, 1.3), 1), ((1.6, 0.1, 0.25), 1.0, (0.9, 1.6, 1.4), 2),
                          ((-1.9, 1.3, 0.1), 0.7, (1.0, 1.0, 1.0), 3), ((1.9, -1.3, 0.1), 0.65, (1.0, 1.0, 1.0), 4)):
        rock(c, r, sc, sd)
    wall((-0.95, 0.0), (-0.32, 0.0), 0.75, (0, 1.0), 0.0, "lime", 0.3)
    wall((0.32, 0.0), (0.95, 0.0), 0.75, (0, 1.0), 0.0, "lime", 0.3)
    gate((0.0, 0.0, 0.0), 0.5, 1.05, 0.0)
    for x in (-1.0, 1.0):
        tower((x, 0.0, 0.0), 0.34, 1.2, "lime")
    top = tower((-1.5, 0.15, 1.2), 0.36, 0.9, "lime", 0.3, "roof")
    flag((-1.5, 0.15, top), 0.6)
    tower((1.55, 0.1, 1.25), 0.28, 0.6, "lime", -0.2)
    box((0.0, 1.3, 0.012), (0.5, 1.6, 0.024), "paving", 0.0)
    box((0.0, -1.3, 0.012), (0.5, 1.6, 0.024), "paving", 0.0)
    barracks((0.55, 0.8, 0.0), 0.6, 0.3, math.pi / 2)
    return finish("WorldCastle_grim_pass")


def castle_towers():
    box((0.0, 0.0, 0.012), (4.4, 0.36, 0.024), "paving", 0.25)
    d = Vector((math.cos(0.25), math.sin(0.25), 0.0))
    n = Vector((-d.y, d.x, 0.0))
    for k, t in enumerate((-1.75, 0.0, 1.75)):
        q = d * t + n * 0.45
        top = tower((q.x, q.y, 0.0), 0.42 if k == 1 else 0.34, 1.35 if k == 1 else 1.0, "lime", 0.25, "roof")
        if k == 1:
            flag((q.x, q.y, top), 0.65)
    for t0, t1 in ((-1.55, -0.25), (0.25, 1.55)):
        a, b = d * t0 + n * 0.45, d * t1 + n * 0.45
        wall((a.x, a.y), (b.x, b.y), 0.4, (0, -1), 0.0, "lime", 0.18)
    for t in (-0.85, 0.9):
        q = d * t - n * 0.65
        barracks((q.x, q.y, 0.0), 0.55, 0.3, 0.25)
    for k in range(4):
        q = d * (-1.9 + k * 1.25) - n * 1.25
        cypress((q.x, q.y, 0.0), 0.6)
    return finish("WorldCastle_grim_towers")


def castle_red():
    cone((0.0, 0.0, -0.05), 2.1, 1.0, 0.6, "rocky", 18)
    rock((0.2, 0.15, 0.5), 0.75, (1.2, 1.05, 0.6), 7)
    z = 0.85
    pts = [(-1.0, -0.75), (0.25, -1.05), (1.1, -0.35), (0.95, 0.75), (-0.2, 1.05), (-1.1, 0.35)]
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        wall(a + dd * 0.14, b - dd * 0.14, 0.55, (0.0, 0.0), z - 0.15, "redstone", 0.24, False)
    for p in pts:
        round_tower((p[0], p[1], z - 0.15), 0.2, 0.8, "redstone")
    L = local((0.05, 0.1, z), 0.3)
    box(L(0, 0, 0.3), (0.62, 0.42, 0.6), "redstone", 0.3)
    gable(L(0, 0, 0.6), 0.62, 0.42, 0.18, "redstone", 0.3, 0.03, 0.03)
    cone(L(0, 0, 0.6), 0.16, 0.16, 0.35, "redstone", 8)
    cone(L(0, 0, 0.95), 0.2, 0.0, 0.3, "redstone", 8, 0.0, False)
    q = L(0, 0, 1.25)
    box((q.x, q.y, q.z + 0.1), (0.03, 0.03, 0.2), "gold")
    top = round_tower((-0.55, -0.25, z), 0.26, 1.1, "redstone", "cone")
    flag((-0.55, -0.25, top - 0.1), 0.6)
    for x, y in ((-1.6, -1.1), (1.5, 1.3), (1.7, -1.0)):
        house((x, y, 0.0), 0.36, 0.3, 0.26, x, "redstone")
    return finish("WorldCastle_grim_red")


def castle_gate():
    for c, r, sc, sd in (((0.1, 2.0, 0.2), 1.0, (1.8, 0.8, 1.1), 5), ((-1.4, 1.9, 0.1), 0.7, (1.0, 0.8, 0.9), 6)):
        rock(c, r, sc, sd)
    for x in (-0.65, 0.65):
        wall((x, -1.6), (x, 1.3), 0.6, (0.0, 0.0), 0.0, "lime", 0.24)
    for x in (-0.65, 0.65):
        for y in (-1.6, -0.6, 0.6):
            tower((x, y, 0.0), 0.3, 0.85, "lime")
    for y in (-0.15,):
        wall((-0.5, y), (0.5, y), 0.55, (0.0, 1.0), 0.0, "lime", 0.2)
    gate((0.0, -1.0, 0.0), 0.5, 0.95, 0.0)
    pts = [(-0.55, 1.05), (0.55, 1.05), (0.55, 1.75), (-0.55, 1.75)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.15, b - dd * 0.15, 0.5, (0.0, 1.4), 1.0, "lime", 0.2)
    top = tower((0.0, 1.4, 1.0), 0.42, 1.05, "lime", 0.0, "roof")
    flag((0.0, 1.4, top), 0.6)
    for y in (-0.6, 0.35):
        barracks((0.0, y, 0.0), 0.75, 0.26, 0.0)
    for x in (-1.5, 1.4):
        house((x, -0.8, 0.0), 0.38, 0.3, 0.26, 0.2)
    return finish("WorldCastle_grim_gate")


def chapel(c, s, rz):
    L = local(c, rz)
    box(L(0, 0, 0.18 * s), (0.5 * s, 0.36 * s, 0.36 * s), "plaster", rz)
    gable(L(0, 0, 0.36 * s), 0.5 * s, 0.36 * s, 0.12 * s, "tile", rz, 0.03, 0.03)
    return dome(L(0, 0, 0.42 * s), 0.12 * s, 0.1 * s, "lead", "plaster")


def village_farm():
    houses(7, 0.4, 1.3, [], 61, budget=BUDGET)
    chapel((0.0, 0.0, 0.0), 1.0, 0.3)
    field((2.0, 0.35, 0.0), 1.1, 1.0, 0.2, "field_green")
    field((-1.35, -2.0, 0.0), 1.0, 0.7, 0.9)
    haystack((1.3, -1.3, 0.0))
    haystack((1.55, -1.1, 0.0), 0.8)
    for k in range(4):
        olive((-1.9 + k * 0.32, 1.35 + (k % 2) * 0.2, 0.0), 0.55, k + 70)
    flag((-0.45, 0.4, 0.0), 1.1)
    return finish("WorldVillage_grim_farm")


def village_villa():
    L = local((0.0, 0.0, 0.0), 0.0)
    box((0.0, 0.0, 0.012), (1.3, 1.1, 0.024), "paving", 0.0)
    for (x, y, w, d, rz) in ((0.0, 0.62, 1.5, 0.36, 0.0), (-0.72, 0.0, 1.2, 0.34, math.pi / 2), (0.72, 0.0, 1.2, 0.34, math.pi / 2)):
        box((x, y, 0.16), (w, d, 0.32), "plaster", rz)
        bands((x, y, 0.0), (w, d), 0.32, rz, n=1)
        gable((x, y, 0.32), w, d, 0.13, "tile", rz, 0.04, 0.03)
    colonnade((-0.45, 0.35), (0.45, 0.35), 0.22, 0.0, 0.15, False)
    cone((0.0, -0.05, 0.0), 0.12, 0.12, 0.07, "marble", 10)
    box((0.0, -0.05, 0.075), (0.16, 0.16, 0.01), "marble", 0.0)
    for k in range(6):
        cypress((-1.3 + k * 0.52, -0.95, 0.0), 0.6)
    vineyard((1.9, 1.0), 1.0, 0.9, 0.3)
    field((-1.9, 1.0, 0.0), 1.0, 0.9, -0.3)
    houses(3, 1.6, 2.1, [((1.9, 1.0), 0.8), ((-1.9, 1.0), 0.8)], 81, budget=BUDGET)
    flag((0.0, 0.62, 0.42), 0.7)
    return finish("WorldVillage_grim_villa")


def village_vineyard():
    houses(5, 0.35, 1.0, [], 91, budget=BUDGET)
    box((0.15, -0.15, 0.17), (0.6, 0.4, 0.34), "lime", 0.2)
    gable((0.15, -0.15, 0.34), 0.6, 0.4, 0.14, "tile", 0.2, 0.04, 0.03)
    for (x, y, rz) in ((1.85, 0.2, 0.15), (-1.7, 0.6, -0.4), (0.1, -1.9, 1.3)):
        vineyard((x, y), 1.1, 1.0, rz)
    for k in range(5):
        cypress((-1.0 + k * 0.45, 1.65, 0.0), 0.62)
    chapel((-0.7, -0.75, 0.0), 0.9, 0.6)
    flag((0.6, 0.55, 0.0), 1.1)
    return finish("WorldVillage_grim_vineyard")


def village_coast():
    for k in range(6):
        house((-1.6 + k * 0.62, -0.5 + (k % 2) * 0.35, 0.0), 0.4, 0.32, 0.28, 0.0, "plaster" if k % 2 else "ochre", budget=BUDGET)
    chapel((0.3, 0.55, 0.0), 1.0, 0.0)
    box((0.0, -1.25, 0.012), (1.6, 0.6, 0.024), "paving", 0.0)
    prop("MarketStand_1", (-0.45, -1.25, 0.0), 0.0, 1.0)
    prop("MarketStand_2", (0.45, -1.2, 0.0), 0.2, 1.0)
    prop("Barrel", (0.0, -1.45, 0.0), 0.0, 1.0)
    prop("Cart", (1.4, -1.2, 0.0), 0.3, 1.0)
    for k in range(5):
        olive((-2.0 + k * 0.4, 1.0 + (k % 2) * 0.25, 0.0), 0.55, k + 80)
    vineyard((1.9, 1.15), 0.9, 0.7, 0.2)
    flag((1.9, 0.35, 0.0), 1.1)
    return finish("WorldVillage_grim_coast")


def village_hill():
    cone((0.0, 0.0, -0.05), 1.8, 1.2, 0.35, "rocky", 18)
    cone((0.1, 0.1, 0.25), 1.15, 0.7, 0.32, "rocky", 16)
    rr = random.Random(93)
    for k in range(6):
        a = k / 6 * math.tau + 0.3
        r = 1.35 if k % 2 else 0.95
        z = 0.3 if r > 1.2 else 0.55
        house((math.cos(a) * r, math.sin(a) * r, z), 0.38, 0.32, 0.3, a + math.pi / 2, rr.choice(("plaster", "lime", "ochre")), budget=BUDGET)
    top = chapel((0.12, 0.12, 0.57), 1.2, 0.4)
    flag((-0.3, -0.25, 0.57), 0.8)
    for k in range(4):
        cypress((-1.9 + k * 0.25, -1.4, 0.0), 0.62)
    return finish("WorldVillage_grim_hill")


ALL = {"capital": capital, "large": large, "medium": medium, "citadel": castle_citadel, "fort": castle_fort, "camp": castle_camp, "pass": castle_pass, "towers": castle_towers,
       "red": castle_red, "gate": castle_gate, "farm": village_farm, "villa": village_villa, "vineyard": village_vineyard, "coast": village_coast, "hill": village_hill}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, len(o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
