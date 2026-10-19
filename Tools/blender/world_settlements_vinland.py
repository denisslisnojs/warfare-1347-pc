import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldVinland"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())
TOWN_BUDGET = 1000
NORSE = {"lime": "grey", "dark": "grey_dark", "plank": "wood", "beige": "wood_ochre"}

M["wood"] = mat("env_wood_dark_vin", (0.3, 0.22, 0.15), 0.9)
M["wood_red"] = mat("env_wood_red", (0.48, 0.17, 0.12), 0.9)
M["wood_ochre"] = mat("env_wood_ochre", (0.7, 0.52, 0.28), 0.9)
M["wood_white"] = mat("env_wood_white", (0.86, 0.84, 0.78), 0.9)
M["turf"] = mat("env_roof_turf", (0.3, 0.38, 0.19), 1.0)
M["grey"] = mat("env_stone_grey_vin", (0.6, 0.6, 0.58), 0.9)
M["grey_dark"] = mat("env_stone_grey_dark", (0.44, 0.45, 0.45), 0.9)
M["slate"] = mat("env_roof_slate_vin", (0.24, 0.26, 0.3), 0.8)
M["rocky"] = mat("env_rock_hill_vin", (0.42, 0.42, 0.41), 1.0)
M["sail"] = mat("env_felt_vin", (0.88, 0.86, 0.8), 0.95)
M["shield"] = mat("env_flag_trim", (0.84, 0.87, 0.92), 0.6)
M["fire"] = mat("env_fire", (0.95, 0.55, 0.15), 0.8)
M["paving"] = mat("env_paving_vin", (0.6, 0.58, 0.54), 0.9)
mat("env_flag", (0.1, 0.18, 0.38), 0.8)


def local(c, rz):
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0))
    return lambda x, y, z=0.0: base + rot @ Vector((x, y, z))


def house(c, w, d, h, rz, wall="wood", roof="roof", steep=0.75, budget=TOWN_BUDGET):
    name = "House_2" if h > 0.27 else rnd.choice(("House_1", "House_1", "House_2", "Blacksmith"))
    building(name, c, rz, w / 0.64 * 1.1, roof, budget, wall, NORSE)


def longhouse(c, length, w, rz, roof="turf", wall="wood"):
    L = local(c, rz)
    h = w * 0.55
    box(L(0, 0, h / 2), (length, w, h), wall, rz)
    gable(L(0, 0, h), length, w, w * 0.62, roof, rz, 0.06, 0.05)
    gable_end(L(0, 0, h), length, w, w * 0.62, wall, rz)
    box(L(0, -w / 2 - 0.005, h * 0.4), (w * 0.3, 0.02, h * 0.7), "log_dark", rz)
    for sx in (-1, 1):
        q = L(sx * (length / 2 + 0.02), 0, h + w * 0.55)
        log((q.x, q.y, q.z), (q.x, q.y, q.z + w * 0.22), 0.012, "log_dark", 4)


def houses(n, rmin, rmax, avoid, seed, center=(0.0, 0.0), walls=("wood", "wood", "wood_red", "wood_ochre"), roofs=("roof", "roof", "turf"), ymin=-99.0, budget=TOWN_BUDGET):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 5000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r
        if y < ymin or any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < 0.48 for p in placed):
            continue
        placed.append((x, y))
        house((x, y, 0.0), rr.uniform(0.36, 0.52), rr.uniform(0.26, 0.34), rr.uniform(0.2, 0.3), a + math.pi / 2 + rr.uniform(-0.15, 0.15), rr.choice(walls), rr.choice(roofs), budget=budget)
    return placed


def stave_church(c, s, rz):
    L = local(c, rz)
    box(L(0, 0, 0.16 * s), (0.62 * s, 0.42 * s, 0.32 * s), "wood", rz)
    gable(L(0, 0, 0.32 * s), 0.62 * s, 0.42 * s, 0.24 * s, "roof", rz, 0.05, 0.03)
    gable_end(L(0, 0, 0.32 * s), 0.62 * s, 0.42 * s, 0.24 * s, "wood", rz)
    box(L(0, 0, 0.52 * s), (0.3 * s, 0.3 * s, 0.4 * s), "wood", rz)
    pyramid(L(0, 0, 0.72 * s), 0.42 * s, 0.14 * s, "roof", 4, rz)
    box(L(0, 0, 0.9 * s), (0.18 * s, 0.18 * s, 0.22 * s), "wood", rz)
    top = cone(L(0, 0, 1.01 * s), 0.15 * s, 0.0, 0.42 * s, "roof", 6, rz, False)
    q = L(0, 0, 1.43 * s)
    box((q.x, q.y, q.z + 0.04 * s), (0.02 * s, 0.02 * s, 0.1 * s), "gold")
    for sx in (-1, 1):
        q = L(sx * 0.36 * s, 0, 0.56 * s)
        log((q.x, q.y, q.z), (q.x + math.cos(rz) * sx * 0.06 * s, q.y + math.sin(rz) * sx * 0.06 * s, q.z + 0.08 * s), 0.012 * s, "log_dark", 4)
    q = L(0.36 * s, 0)
    cone((q.x, q.y, 0.0), 0.14 * s, 0.14 * s, 0.24 * s, "wood", 8)
    cone((q.x, q.y, 0.24 * s), 0.17 * s, 0.0, 0.2 * s, "roof", 8, 0.0, False)
    return 1.5 * s


def stone_church(c, s, rz):
    L = local(c, rz)
    box(L(0, 0, 0.24 * s), (0.95 * s, 0.42 * s, 0.48 * s), "grey", rz)
    gable(L(0, 0, 0.48 * s), 0.95 * s, 0.42 * s, 0.28 * s, "slate", rz, 0.04, 0.03)
    gable_end(L(0, 0, 0.48 * s), 0.95 * s, 0.42 * s, 0.28 * s, "grey", rz)
    for k in range(3):
        q = L((k - 1) * 0.26 * s, -0.215 * s, 0.26 * s)
        box((q.x, q.y, q.z), (0.06 * s, 0.02, 0.2 * s), "window", rz)
    q = L(0.52 * s, 0)
    cone((q.x, q.y, 0.0), 0.2 * s, 0.2 * s, 0.38 * s, "grey", 10)
    cone((q.x, q.y, 0.38 * s), 0.22 * s, 0.0, 0.18 * s, "slate", 10, 0.0, False)
    t = L(-0.6 * s, 0)
    box((t.x, t.y, 0.5 * s), (0.32 * s, 0.32 * s, 1.0 * s), "grey", rz)
    box((t.x, t.y, 0.82 * s), (0.34 * s, 0.34 * s, 0.03 * s), "grey_dark", rz)
    for k in range(2):
        a = rz + k * math.pi / 2
        box((t.x + math.cos(a) * 0.165 * s, t.y + math.sin(a) * 0.165 * s, 0.86 * s), (0.06 * s, 0.06 * s, 0.1 * s), "window", a)
    pyramid((t.x, t.y, 1.0 * s), 0.36 * s, 0.62 * s, "slate", 4, rz)
    q = (t.x, t.y, 1.62 * s)
    box((q[0], q[1], q[2] + 0.05 * s), (0.02 * s, 0.02 * s, 0.12 * s), "gold")
    return 1.7 * s


def great_hall(c, s, rz):
    L = local(c, rz)
    longhouse(L(0, 0), 1.3 * s, 0.5 * s, rz, "roof", "wood")
    q = L(0, -0.45 * s)
    box((q.x, q.y, 0.012), (1.0 * s, 0.35 * s, 0.024), "plank", rz)
    for k in range(5):
        p = L((k - 2) * 0.24 * s, -0.27 * s)
        log((p.x, p.y, 0.0), (p.x, p.y, 0.22 * s), 0.018 * s, "log_dark", 5)
    p = L(0.75 * s, 0.1 * s)
    flag((p.x, p.y, 0.0), 0.9 * s, 0.4)


def wall(a, b, h, center, z0=0.0, m="grey", t=0.24):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, z0 + h / 2), (length, t, h), m, rz)
    k = max(2, int(length / 0.2))
    for i in range(k):
        q = a.lerp(b, (i + 0.5) / k) + n * (t / 2 - 0.05)
        box((q.x, q.y, z0 + h + 0.05), (0.1, 0.08, 0.1), m, rz)


def tower(c, s, h, m="grey", rz=0.0, cap="roof"):
    x, y, z = c
    box((x, y, z + h / 2), (s, s, h), m, rz)
    box((x, y, z + h * 0.8), (s * 1.08, s * 1.08, h * 0.05), "grey_dark", rz)
    for k in range(2):
        a = rz + k * math.pi / 2
        box((x + math.cos(a) * s * 0.51, y + math.sin(a) * s * 0.51, z + h * 0.62), (s * 0.1, s * 0.1, s * 0.2), "window", a)
    if cap == "roof":
        pyramid((x, y, z + h), s * 1.14, s * 1.05, "slate", 4, rz)
        return z + h + s * 1.05
    if cap == "beacon":
        box((x, y, z + h + 0.04), (s * 1.1, s * 1.1, 0.08), m, rz)
        cone((x, y, z + h + 0.08), s * 0.28, s * 0.34, s * 0.16, "log_dark", 8)
        cone((x, y, z + h + 0.24 * s), s * 0.26, 0.0, s * 0.42, "fire", 7, 0.0, False)
        return z + h + s * 0.66
    for u, v in ((-0.35, -0.42), (0.35, -0.42), (-0.35, 0.42), (0.35, 0.42), (-0.42, 0.0), (0.42, 0.0), (0.0, -0.42), (0.0, 0.42)):
        q = local((x, y, z), rz)(u * s, v * s)
        box((q.x, q.y, z + h + 0.06), (s * 0.18, s * 0.18, 0.12), m, rz)
    return z + h + 0.12


def keep(c, s, h, rz=0.0):
    x, y, z = c
    box((x, y, z + h / 2), (s, s * 0.85, h), "grey", rz)
    for k in (0.4, 0.7):
        for j in range(2):
            a = rz + j * math.pi / 2
            box((x + math.cos(a) * s * 0.44, y + math.sin(a) * s * 0.44, z + h * k), (s * 0.08, s * 0.08, s * 0.16), "window", a)
    gable((x, y, z + h), s, s * 0.85, s * 0.55, "slate", rz, 0.04, 0.04)
    gable_end((x, y, z + h), s, s * 0.85, s * 0.55, "grey", rz)
    for sx in (-1, 1):
        q = local((x, y, z), rz)(sx * s * 0.5, -s * 0.42)
        cone((q.x, q.y, z + h * 0.6), s * 0.12, s * 0.12, h * 0.5, "grey", 8)
        cone((q.x, q.y, z + h * 1.1), s * 0.14, 0.0, s * 0.42, "slate", 8, 0.0, False)
    return z + h + s * 0.55


def ring_walls(pts, h, center, z0, ts, m="grey", gates=(), cap="roof"):
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        wall(a + dd * ts * 0.6, b - dd * ts * 0.6, h, center, z0, m)
    for i, p in enumerate(pts):
        t = Vector(pts[(i + 1) % len(pts)]) - Vector(pts[i - 1])
        rz = math.atan2(t.y, t.x)
        if i in gates:
            L = local((p[0], p[1], z0), rz)
            box(L(0, 0, h * 0.7), (ts * 1.7, ts * 1.1, h * 1.4), m, rz)
            box(L(0, -ts * 0.56, h * 0.35), (ts * 0.7, 0.02, h * 0.6), "log_dark", rz)
            gable(L(0, 0, h * 1.4), ts * 1.7, ts * 1.1, ts * 0.8, "slate", rz, 0.03, 0.03)
            gable_end(L(0, 0, h * 1.4), ts * 1.7, ts * 1.1, ts * 0.8, m, rz)
        else:
            tower((p[0], p[1], z0), ts, h * 1.3, m, rz, cap)


def ring_palisade(pts):
    for i in range(len(pts)):
        palisade(pts[i], pts[(i + 1) % len(pts)], 0.42)
    for p in pts[::2]:
        x, y = p
        box((x, y, 0.3), (0.26, 0.26, 0.6), "log_old", 0.0)
        pyramid((x, y, 0.6), 0.34, 0.22, "roof", 4, 0.0)


def close_south(a, b, h, ts):
    a, b = Vector(a), Vector(b)
    mid = (a + b) / 2
    dd = (b - a).normalized()
    wall(a + dd * 0.18, mid - dd * 0.32, h, (0, 0), 0.0)
    wall(mid + dd * 0.32, b - dd * 0.18, h, (0, 0), 0.0)
    for sx in (-1, 1):
        q = mid + dd * sx * 0.3
        tower((q.x, q.y, 0.0), ts, h + 0.25, "grey", 0.0, "crenel")


def market_square(c, rz):
    box((c[0], c[1], 0.012), (1.0, 0.6, 0.024), "paving", rz)
    prop("MarketStand_1", (c[0] - 0.25, c[1], 0.0), rz, 1.0)
    prop("MarketStand_2", (c[0] + 0.25, c[1] + 0.05, 0.0), rz + 0.3, 1.0)
    prop("Well", (c[0], c[1] - 0.2, 0.0), 0.0, 0.9)


def wharf_row(x0, y, n, step=0.36, seed=0):
    rr = random.Random(seed)
    for k in range(n):
        house((x0 + k * step, y, 0.0), 0.3, 0.5, rr.uniform(0.34, 0.46), math.pi / 2, rr.choice(("wood_red", "wood_ochre", "wood_white", "wood")), "roof", 0.95)


def drying_rack(c, rz):
    L = local(c, rz)
    for sx in (-1, 1):
        a = L(sx * 0.18, 0)
        log((a.x, a.y, 0.0), (a.x, a.y, 0.26), 0.012, "log_old", 4)
    a, b = L(-0.2, 0, 0.25), L(0.2, 0, 0.25)
    log(a, b, 0.01, "log_old", 4)
    for k in range(4):
        q = L(-0.13 + k * 0.087, 0, 0.18)
        box((q.x, q.y, q.z), (0.03, 0.03, 0.12), "hay", rz)


def capital():
    pts = [(-2.75, -1.55), (-2.85, 0.3), (-1.9, 2.1), (0.0, 2.75), (1.9, 2.1), (2.85, 0.3), (2.75, -1.55)]
    close_south(pts[-1], pts[0], 0.55, 0.3)
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        dd = (b - a).normalized()
        wall(a + dd * 0.18, b - dd * 0.18, 0.55, (0, 0), 0.0)
    for i, p in enumerate(pts):
        tower((p[0], p[1], 0.0), 0.3, 0.75, "grey", 0.0, "roof")
    cone((1.15, 1.05, -0.05), 0.95, 0.78, 0.42, "rocky", 18)
    z = 0.37
    inner = [(0.6, 0.5), (1.7, 0.5), (1.7, 1.6), (0.6, 1.6)]
    for i in range(4):
        a, b = Vector(inner[i]), Vector(inner[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.16, b - dd * 0.16, 0.5, (1.15, 1.05), z)
    for p in inner:
        tower((p[0], p[1], z), 0.26, 0.7, "grey", 0.0, "crenel")
    top = keep((1.15, 1.1, z), 0.6, 1.0)
    flag((1.15, 1.1, top), 0.6)
    stone_church((-1.0, 0.95, 0.0), 0.9, 0.3)
    great_hall((-0.4, -0.45, 0.0), 0.95, 0.0)
    wharf_row(-2.35, -1.2, 6, 0.36, 3)
    wharf_row(0.45, -1.2, 6, 0.36, 4)
    market_square((1.3, -0.6), 0.0)
    avoid = [((1.15, 1.05), 1.0), ((-1.0, 0.95), 0.85), ((-0.4, -0.45), 0.8), ((1.3, -0.6), 0.6)]
    houses(34, 0.4, 2.55, avoid, 5, ymin=-0.85)
    return finish("WorldTown_vinland_capital")


def large():
    pts = [(-2.3, -1.25), (-2.45, 0.6), (-1.3, 2.15), (0.5, 2.4), (2.1, 1.4), (2.4, -1.25)]
    close_south(pts[-1], pts[0], 0.5, 0.28)
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        dd = (b - a).normalized()
        wall(a + dd * 0.17, b - dd * 0.17, 0.5, (0, 0), 0.0)
    for p in pts:
        tower((p[0], p[1], 0.0), 0.28, 0.68, "grey", 0.0, "roof")
    stone_church((0.35, 0.7, 0.0), 0.8, -0.2)
    top = keep((-1.2, 1.0, 0.0), 0.5, 0.85, 0.3)
    flag((-1.2, 1.0, top), 0.55)
    wharf_row(-1.95, -0.95, 11, 0.37, 7)
    houses(24, 0.35, 2.05, [((0.35, 0.7), 0.8), ((-1.2, 1.0), 0.5)], 8, ymin=-0.6)
    return finish("WorldTown_vinland_large")


def medium():
    pts = ring(1.85, 9, 0.06, 7, 0.3)
    ring_palisade(pts)
    stave_church((0.35, 0.45, 0.0), 0.8, 0.4)
    great_hall((-0.55, -0.35, 0.0), 0.75, 0.3)
    houses(12, 0.4, 1.45, [((0.35, 0.45), 0.6), ((-0.55, -0.35), 0.7)], 9)
    houses(5, 2.15, 2.6, [((2.0, 1.3), 0.8)], 10, walls=("wood", "wood_red"), roofs=("turf",))
    field((2.0, 1.3, 0.0), 0.9, 0.7, 0.5, "field_green")
    for k in range(7):
        pine((-2.3 + k * 0.28, -1.9 + (k % 2) * 0.26, 0.0), 0.75)
    return finish("WorldTown_vinland_medium")


def market():
    pts = ring(2.55, 10, 0.03, 21, 0.25)
    ring_walls(pts, 0.5, (0, 0), 0.0, 0.27, "grey", gates=(0, 5), cap="roof")
    box((-0.2, -0.3, 0.012), (1.2, 0.9, 0.024), "paving", 0.2)
    for k in range(6):
        q = (-0.6 + (k % 3) * 0.4, -0.55 + (k // 3) * 0.5)
        box((q[0], q[1], 0.08), (0.22, 0.16, 0.02), "flag" if k % 2 else "sail", 0.2)
        for sx in (-1, 1):
            for sy in (-1, 1):
                log((q[0] + sx * 0.09, q[1] + sy * 0.06, 0.0), (q[0] + sx * 0.09, q[1] + sy * 0.06, 0.08), 0.008, "log_dark", 4)
    stone_church((0.75, 0.75, 0.0), 0.8, -0.3)
    great_hall((-0.9, 0.85, 0.0), 0.7, 0.4)
    houses(22, 0.6, 2.1, [((-0.2, -0.3), 0.75), ((0.75, 0.75), 0.8), ((-0.9, 0.85), 0.6)], 22)
    for (x, y, rz) in ((2.6, 1.6, 0.4), (-2.7, -1.4, 1.1)):
        field((x, y, 0.0), 0.9, 0.7, rz, "field_green")
    haystack((2.5, -1.9, 0.0))
    return finish("WorldTown_vinland_market")


def rock(c, r, sc=(1.0, 1.0, 1.0), seed=0, m="rocky"):
    rr = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)))
    for v in bm.verts:
        v.co += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-0.5, 1.0))) * r * 0.16
    put("rock", bm, m, False)


def castle_royal():
    cone((0.0, 0.0, -0.05), 2.5, 2.0, 0.4, "rocky", 24)
    z = 0.35
    pts = [(-1.6, -1.35), (1.6, -1.35), (1.75, 0.2), (1.2, 1.55), (-1.2, 1.55), (-1.75, 0.2)]
    ring_walls(pts, 0.6, (0, 0), z, 0.32, "grey", gates=(0,), cap="roof")
    top = keep((0.25, 0.35, z), 0.85, 1.35, 0.1)
    flag((0.25, 0.35, top), 0.7)
    longhouse((-0.85, -0.45, z), 1.0, 0.36, 0.1, "slate", "grey")
    stone_church((-0.75, 0.75, z), 0.5, 0.1)
    house((1.0, -0.6, z), 0.5, 0.32, 0.28, 0.1, "wood", "roof")
    return finish("WorldCastle_vinland_royal")


def castle_cape():
    rock((0.3, 0.1, 0.25), 1.15, (1.35, 1.0, 0.8), 3)
    rock((-0.6, -0.6, 0.1), 0.6, (1.0, 1.0, 0.8), 4)
    z = 0.95
    pts = [(-0.9, -0.55), (0.75, -0.75), (1.25, 0.35), (0.4, 0.95), (-0.75, 0.6)]
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        wall(a + dd * 0.15, b - dd * 0.15, 0.45, (0.15, 0.1), z, "grey", 0.22)
    for p in pts:
        tower((p[0], p[1], z), 0.24, 0.6, "grey", 0.0, "crenel")
    top = keep((0.15, 0.1, z), 0.55, 0.9)
    flag((0.15, 0.1, top), 0.6)
    top = tower((1.25, 0.35, z + 0.6), 0.2, 0.4, "grey", 0.0, "beacon")
    house((-1.3, -1.25, 0.0), 0.46, 0.3, 0.26, 0.3, "wood_red", "turf")
    house((1.0, -1.35, 0.0), 0.44, 0.3, 0.24, -0.2, "wood", "roof")
    return finish("WorldCastle_vinland_cape")


def castle_fjord():
    for c, r, sc, sd in (((-1.45, 0.0, 0.2), 1.0, (0.85, 1.9, 1.3), 1), ((1.45, 0.2, 0.2), 0.95, (0.8, 1.8, 1.25), 2)):
        rock(c, r, sc, sd)
    z = 1.15
    pts = [(-1.85, -0.65), (-0.75, -0.7), (-0.7, 0.75), (-1.8, 0.7)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.14, b - dd * 0.14, 0.4, (-1.3, 0.0), z, "grey", 0.2)
    for p in pts:
        tower((p[0], p[1], z), 0.22, 0.55, "grey", 0.0, "roof")
    top = keep((-1.3, 0.0, z), 0.5, 0.85, math.pi / 2)
    flag((-1.3, 0.0, top), 0.6)
    tower((1.3, 0.3, z), 0.26, 0.5, "grey", 0.0, "beacon")
    box((0.0, 0.0, 0.012), (0.55, 4.4, 0.024), "paving", 0.0)
    for k in range(5):
        pine((1.7 + (k % 2) * 0.25, -1.9 + k * 0.32, 0.25), 0.7)
    return finish("WorldCastle_vinland_fjord")


def castle_naval():
    pts = [(-1.8, -0.95), (1.8, -0.95), (1.8, 1.35), (-1.8, 1.35)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        if i == 0:
            wall(a + dd * 0.2, Vector((-0.55, -0.95)), 0.55, (0, 0.2), 0.0)
            wall(Vector((0.55, -0.95)), b - dd * 0.2, 0.55, (0, 0.2), 0.0)
        else:
            wall(a + dd * 0.2, b - dd * 0.2, 0.55, (0, 0.2), 0.0)
    for p in pts:
        tower((p[0], p[1], 0.0), 0.32, 0.8, "grey", 0.0, "roof")
    for x in (-0.55, 0.55):
        tower((x, -0.95, 0.0), 0.26, 0.72, "grey", 0.0, "crenel")
    box((0.0, -0.45, 0.012), (1.0, 0.9, 0.024), "paving", 0.0)
    for x in (-1.0, 1.0):
        longhouse((x, 0.0, 0.0), 1.1, 0.42, math.pi / 2, "roof", "wood")
    top = keep((0.0, 0.75, 0.0), 0.6, 1.1)
    flag((0.0, 0.75, top), 0.65)
    house((-1.2, -1.55, 0.0), 0.46, 0.3, 0.26, 0.1, "wood_red", "turf")
    house((1.25, -1.6, 0.0), 0.44, 0.3, 0.24, -0.15, "wood_ochre", "roof")
    return finish("WorldCastle_vinland_naval")


def castle_border():
    cone((0.0, 0.0, -0.05), 2.2, 1.7, 0.3, "earth", 24)
    for side in (-1, 1):
        box((side * 2.1, -0.2, 0.15), (1.6, 0.4, 0.3), "earth", 0.0)
        palisade((side * 1.3, 0.0), (side * 2.9, 0.0), 0.36)
    z = 0.25
    pts = ring(1.25, 8, 0.0, 3, math.pi / 8)
    ring_walls(pts, 0.5, (0, 0), z, 0.26, "grey", gates=(6,), cap="crenel")
    top = keep((0.1, 0.15, z), 0.7, 1.25, 0.2)
    flag((0.1, 0.15, top), 0.65)
    house((-0.55, -0.35, z), 0.48, 0.3, 0.26, 0.2, "wood", "roof")
    house((0.6, -0.4, z), 0.42, 0.3, 0.24, -0.4, "wood_red", "roof")
    return finish("WorldCastle_vinland_border")


def castle_beacons():
    for k, x in enumerate((-1.75, 0.0, 1.75)):
        y = -0.8 + (0.25 if k == 1 else 0.0)
        rock((x, y + 0.1, 0.0), 0.55, (1.1, 1.0, 0.7), 10 + k)
        top = tower((x, y, 0.35), 0.4 if k == 1 else 0.32, 1.1 if k == 1 else 0.85, "grey", 0.0, "beacon")
        if k == 1:
            flag((x + 0.3, y, 0.35), 1.1)
    for x0, x1 in ((-1.45, -0.3), (0.3, 1.45)):
        wall((x0, -0.7), (x1, -0.6), 0.32, (0, 1), 0.3, "grey_dark", 0.16)
    longhouse((-0.6, 0.65, 0.0), 1.0, 0.38, 0.1)
    house((0.9, 0.7, 0.0), 0.44, 0.3, 0.25, 0.1)
    for k in range(4):
        pine((-1.9 + k * 0.32, 1.3, 0.0), 0.7)
    return finish("WorldCastle_vinland_beacons")


def village_fishing():
    for k in range(6):
        house((-1.7 + k * 0.66, -0.35 + (k % 2) * 0.32, 0.0), 0.44, 0.3, 0.24, 0.0, ("wood_red", "wood", "wood_ochre")[k % 3], ("roof", "turf")[k % 2], budget=BUDGET)
    for x in (-1.3, 0.0, 1.3):
        drying_rack((x, 0.55, 0.0), 0.0)
    for x in (-0.9, 0.9):
        drying_rack((x, -1.15, 0.0), 0.0)
    prop("Barrel", (0.35, -1.0, 0.0), 0.0, 1.0)
    prop("Crate", (0.6, -1.05, 0.0), 0.4, 1.0)
    prop("Cart", (-1.6, -1.1, 0.0), 0.3, 1.0)
    field((0.2, 1.6, 0.0), 1.6, 0.6, 0.0, "field_green")
    flag((2.0, 0.3, 0.0), 1.05)
    return finish("WorldVillage_vinland_fishing")


def village_farm():
    longhouse((0.0, 0.0, 0.0), 1.2, 0.4, 0.2)
    longhouse((-0.55, 0.75, 0.0), 0.9, 0.34, 1.4)
    longhouse((0.75, -0.75, 0.0), 0.8, 0.32, 0.9, "roof", "wood_red")
    field((2.0, 0.3, 0.0), 1.1, 1.0, 0.2, "field_green")
    field((-1.4, -1.9, 0.0), 1.0, 0.7, 0.9)
    haystack((1.3, 1.3, 0.0))
    haystack((1.55, 1.05, 0.0), 0.8)
    palisade((-1.2, -0.9), (1.4, -1.3), 0.22)
    for k in range(4):
        pine((-2.1 + k * 0.3, 0.9 + (k % 2) * 0.25, 0.0), 0.75)
    flag((0.6, 0.45, 0.0), 1.05)
    return finish("WorldVillage_vinland_farm")


def village_longhall():
    pts = ring(1.55, 8, 0.05, 11, 0.2)
    for i in range(len(pts)):
        if i != 0:
            palisade(pts[i], pts[(i + 1) % len(pts)], 0.36)
    great_hall((0.0, 0.1, 0.0), 1.0, 0.1)
    houses(4, 0.7, 1.15, [((0.0, 0.1), 0.85)], 12, budget=BUDGET)
    houses(4, 1.9, 2.5, [], 13, walls=("wood", "wood_red"), roofs=("turf",), budget=BUDGET)
    field((-2.0, -1.2, 0.0), 0.9, 0.7, 0.4)
    return finish("WorldVillage_vinland_longhall")


def village_forest():
    houses(6, 0.4, 1.3, [], 14, walls=("log", "log_dark", "wood"), roofs=("turf", "roof"), budget=BUDGET)
    longhouse((0.0, 0.0, 0.0), 0.7, 0.3, 0.5, "turf", "log")
    q = (0.9, -0.6)
    box((q[0], q[1], 0.15), (0.36, 0.3, 0.3), "grey_dark", 0.3)
    cone((q[0] + 0.1, q[1], 0.3), 0.05, 0.04, 0.3, "grey_dark", 6)
    for k in range(3):
        log((-1.6 + k * 0.12, -1.4, 0.03), (-0.9 + k * 0.12, -1.3, 0.03), 0.05, "log", 6)
    rr = random.Random(15)
    for k in range(14):
        a = rr.uniform(0, math.tau)
        r = rr.uniform(1.7, 2.6)
        pine((math.cos(a) * r, math.sin(a) * r, 0.0), rr.uniform(0.65, 0.95))
    flag((-0.5, 0.6, 0.0), 1.0)
    return finish("WorldVillage_vinland_forest")


def village_mountain():
    cone((0.0, 0.0, -0.05), 1.85, 1.2, 0.35, "rocky", 18)
    cone((0.1, 0.1, 0.25), 1.15, 0.7, 0.32, "turf", 16)
    rr = random.Random(16)
    for k in range(6):
        a = k / 6 * math.tau + 0.3
        r = 1.35 if k % 2 else 0.95
        z = 0.3 if r > 1.2 else 0.55
        house((math.cos(a) * r, math.sin(a) * r, z), 0.42, 0.3, 0.24, a + math.pi / 2, rr.choice(("wood", "wood_red")), rr.choice(("turf", "roof")), budget=BUDGET)
    stave_church((0.12, 0.12, 0.57), 0.65, 0.4)
    flag((-0.35, -0.25, 0.57), 0.8)
    for k in range(5):
        pine((-2.0 + k * 0.28, -1.5 + (k % 2) * 0.2, 0.0), 0.7)
    return finish("WorldVillage_vinland_mountain")


ALL = {"capital": capital, "large": large, "medium": medium, "market": market, "royal": castle_royal, "cape": castle_cape, "fjord": castle_fjord, "naval": castle_naval,
       "border": castle_border, "beacons": castle_beacons, "fishing": village_fishing, "farm": village_farm, "longhall": village_longhall, "forest": village_forest, "mountain": village_mountain}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, len(o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
