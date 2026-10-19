import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldVallerois"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())

M["lime"] = mat("env_limestone", (0.86, 0.81, 0.68), 0.85)
M["grey"] = mat("env_stone_grey", (0.6, 0.58, 0.55), 0.9)
M["slate"] = mat("env_slate", (0.27, 0.31, 0.39), 0.55)
M["tile"] = mat("env_roof_tile", (0.62, 0.3, 0.2), 0.8)
M["plaster"] = mat("env_plaster", (0.93, 0.89, 0.79), 0.9)
M["beam"] = mat("env_beam_dark", (0.3, 0.2, 0.13), 0.85)
M["leaf"] = mat("env_leaf_round", (0.26, 0.46, 0.18), 0.9)
M["vine"] = mat("env_vine", (0.22, 0.38, 0.14), 0.9)
M["soil"] = mat("env_soil", (0.48, 0.38, 0.25), 1.0)
M["paving"] = mat("env_paving", (0.74, 0.7, 0.62), 0.9)
M["hedge"] = mat("env_hedge", (0.2, 0.36, 0.15), 0.9)
mat("env_flag", (0.14, 0.28, 0.78), 0.8)
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())
TOWN_BUDGET = 1000


def local(c, rz):
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0))
    return lambda x, y, z=0.0: base + rot @ Vector((x, y, z))


def box_m(mx, m):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=mx)
    return put("box", bm, m, False)


def tree(c, h):
    x, y, z = c
    log((x, y, z), (x, y, z + h * 0.5), h * 0.05, "log_dark", 5)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=h * 0.33, matrix=Matrix.Translation((x, y, z + h * 0.66)))
    for v in bm.verts:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 1))) * h * 0.05
    put("tree", bm, "leaf", False)


def rock(c, r):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((1.0, 0.8, 0.6, 1.0)))
    for v in bm.verts:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * r * 0.2
    put("rock", bm, "grey", False)


def ftower(c, r, h, roof="slate", m="lime", flag_h=0.0):
    x, y, z = c
    cone((x, y, z), r * 1.07, r, h, m, 14)
    cone((x, y, z + h), r * 1.15, r * 1.15, r * 0.3, m, 14)
    for i in range(3):
        a = i / 3 * math.tau + 0.5
        box((x + math.cos(a) * r * 1.01, y + math.sin(a) * r * 1.01, z + h * (0.45 + 0.2 * i)), (r * 0.12, r * 0.12, r * 0.34), "window", a)
    if roof:
        cone((x, y, z + h + r * 0.3), r * 1.22, 0.0, r * 2.7, roof, 14)
        apex = z + h + r * 3.0
        box((x, y, apex + r * 0.15), (r * 0.06, r * 0.06, r * 0.5), "gold")
    else:
        for i in range(10):
            a = i / 10 * math.tau
            box((x + math.cos(a) * r * 1.05, y + math.sin(a) * r * 1.05, z + h + r * 0.4), (r * 0.22, r * 0.18, r * 0.2), m, a)
        apex = z + h + r * 0.5
    if flag_h:
        flag((x, y, apex - r * 0.2), flag_h)
    return apex


def keep(c, w, h, rz=0.0, m="lime", roof="slate", turrets=True, flag_h=0.0):
    L = local(c, rz)
    z0 = L(0, 0).z
    box(L(0, 0, h / 2), (w, w, h), m, rz)
    for k in range(4):
        a = rz + k * math.pi / 2
        for zz in (0.45, 0.72):
            box(L(0, 0, h * zz) + Vector((math.cos(a), math.sin(a), 0)) * w * 0.51, (w * 0.08, w * 0.08, w * 0.18), "window", a)
    if roof:
        pyramid(L(0, 0, h), w * 1.04, w * 0.95, roof, 4, rz)
        apex = z0 + h + w * 0.95
    else:
        n = 5
        for sx in (-1, 1):
            for i in range(n):
                t = (i + 0.5) / n - 0.5
                box(L(t * w, sx * w * 0.47, h + w * 0.07), (w * 0.11, w * 0.08, w * 0.14), m, rz)
                box(L(sx * w * 0.47, t * w, h + w * 0.07), (w * 0.08, w * 0.11, w * 0.14), m, rz)
        apex = z0 + h + w * 0.14
    if turrets:
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = L(sx * w * 0.5, sy * w * 0.5, h - w * 0.28)
            ftower((q.x, q.y, q.z), w * 0.12, w * 0.3, roof or "slate", m)
    if flag_h:
        q = L(0, 0)
        flag((q.x, q.y, apex - w * 0.08), flag_h)
    return apex


def cwall(a, b, h, center, z0=0.0, m="lime", t=0.28):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, z0 + h / 2), (length, t, h), m, rz)
    k = max(2, int(length / 0.19))
    for i in range(k):
        q = a.lerp(b, (i + 0.5) / k) + n * (t / 2 - 0.04)
        box((q.x, q.y, z0 + h + 0.06), (0.09, 0.08, 0.12), m, rz)


def gatehouse(c, rz, s=1.0, m="lime", roof="slate", flag_h=0.0):
    L = local(c, rz)
    for sx in (-1, 1):
        q = L(sx * 0.3 * s, 0)
        ftower((q.x, q.y, q.z), 0.19 * s, 0.95 * s, roof, m)
    box(L(0, 0, 0.42 * s), (0.42 * s, 0.42 * s, 0.84 * s), m, rz)
    gable(L(0, 0, 0.84 * s), 0.42 * s, 0.42 * s, 0.3 * s, roof or "slate", rz + math.pi / 2, 0.03)
    for sy in (-1, 1):
        box(L(0, sy * 0.215 * s, 0.17 * s), (0.18 * s, 0.02 * s, 0.32 * s), "window", rz)
    if flag_h:
        q = L(0.3 * s, 0)
        flag((q.x, q.y, q.z + 0.95 * s + 0.19 * s * 3.0), flag_h)


def fr_ring(pts, h, center, z0, tower, gates=(), m="lime"):
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        d = (b - a).normalized()
        ca = 0.32 if i in gates else 0.12
        cb = 0.32 if (i + 1) % len(pts) in gates else 0.12
        cwall(a + d * ca, b - d * cb, h, center, z0, m)
    for i, p in enumerate(pts):
        if i in gates:
            prev, nxt = Vector(pts[i - 1]), Vector(pts[(i + 1) % len(pts)])
            t = (nxt - prev).normalized()
            gatehouse((p[0], p[1], z0), math.atan2(t.y, t.x), 0.95, m)
        else:
            tower((p[0], p[1], z0))


def house(c, s, rz, roof="tile", tall=1.0, timber=True):
    name = "Inn" if tall >= 1.8 else "House_2" if tall >= 1.4 else rnd.choice(("House_1", "House_1", "House_2", "Blacksmith"))
    building(name, c, rz, s * 0.85, roof, TOWN_BUDGET, None if timber else "lime")
    return (c[2] if len(c) > 2 else 0.0) + s


def church(c, s, rz, roof="slate"):
    L = local(c, rz)
    box(L(0.15 * s, 0, 0.4 * s), (1.1 * s, 0.5 * s, 0.8 * s), "lime", rz)
    gable(L(0.15 * s, 0, 0.8 * s), 1.1 * s, 0.5 * s, 0.4 * s, roof, rz, 0.04)
    q = L(0.7 * s, 0)
    cone((q.x, q.y, q.z), 0.25 * s, 0.25 * s, 0.7 * s, "lime", 10)
    cone((q.x, q.y, q.z + 0.7 * s), 0.27 * s, 0.0, 0.35 * s, roof, 10)
    box(L(-0.55 * s, 0, 0.75 * s), (0.36 * s, 0.36 * s, 1.5 * s), "lime", rz)
    for k in range(4):
        a = rz + k * math.pi / 2
        box(L(-0.55 * s, 0, 1.25 * s) + Vector((math.cos(a), math.sin(a), 0)) * 0.185 * s, (0.08 * s, 0.08 * s, 0.2 * s), "window", a)
    pyramid(L(-0.55 * s, 0, 1.5 * s), 0.4 * s, 1.0 * s, roof, 8, rz)
    tip = L(-0.55 * s, 0, 2.5 * s)
    box((tip.x, tip.y, tip.z + 0.08 * s), (0.03 * s, 0.03 * s, 0.2 * s), "gold")
    return tip.z


def cathedral(c, s, rz, towers=2):
    L = local(c, rz)
    box(L(0, 0, 0.55 * s), (2.0 * s, 0.7 * s, 1.1 * s), "lime", rz)
    gable(L(0, 0, 1.1 * s), 2.0 * s, 0.7 * s, 0.55 * s, "slate", rz, 0.04)
    box(L(0.4 * s, 0, 0.5 * s), (0.6 * s, 1.3 * s, 1.0 * s), "lime", rz)
    gable(L(0.4 * s, 0, 1.0 * s), 1.3 * s, 0.6 * s, 0.5 * s, "slate", rz + math.pi / 2, 0.04)
    q = L(1.0 * s, 0)
    cone((q.x, q.y, q.z), 0.35 * s, 0.35 * s, 0.95 * s, "lime", 12)
    cone((q.x, q.y, q.z + 0.95 * s), 0.38 * s, 0.0, 0.45 * s, "slate", 12)
    for x in (-0.75, -0.35, 0.0, 0.75):
        for sy in (-1, 1):
            box(L(x * s, sy * 0.42 * s, 0.4 * s), (0.08 * s, 0.14 * s, 0.8 * s), "lime", rz)
            box(L(x * s + 0.2 * s, sy * 0.36 * s, 0.6 * s), (0.08 * s, 0.02 * s, 0.38 * s), "window", rz)
    if towers == 2:
        for sy in (-1, 1):
            box(L(-1.0 * s, sy * 0.24 * s, 0.95 * s), (0.36 * s, 0.36 * s, 1.9 * s), "lime", rz)
            pyramid(L(-1.0 * s, sy * 0.24 * s, 1.9 * s), 0.34 * s, 0.75 * s, "slate", 8, rz)
        box(L(-1.19 * s, 0, 0.8 * s), (0.02 * s, 0.2 * s, 0.2 * s), "window", rz)
        box(L(-1.19 * s, 0, 0.3 * s), (0.02 * s, 0.14 * s, 0.32 * s), "window", rz)
    else:
        box(L(-1.0 * s, 0, 1.0 * s), (0.45 * s, 0.45 * s, 2.0 * s), "lime", rz)
        pyramid(L(-1.0 * s, 0, 2.0 * s), 0.45 * s, 1.3 * s, "slate", 8, rz)
        box(L(-1.23 * s, 0, 0.35 * s), (0.02 * s, 0.16 * s, 0.36 * s), "window", rz)
    q = L(0.4 * s, 0, 1.5 * s)
    pyramid((q.x, q.y, q.z), 0.2 * s, 1.0 * s, "slate", 8, rz)
    box((q.x, q.y, q.z + 1.05 * s), (0.03 * s, 0.03 * s, 0.18 * s), "gold")


def palace(c, s, rz, flag_h=0.0):
    L = local(c, rz)
    box(L(0, 0, 0.42 * s), (1.4 * s, 0.55 * s, 0.84 * s), "lime", rz)
    gable(L(0, 0, 0.84 * s), 1.4 * s, 0.55 * s, 0.62 * s, "slate", rz, 0.04)
    for x in (-0.45, 0.0, 0.45):
        box(L(x * s, -0.2 * s, 1.0 * s), (0.14 * s, 0.12 * s, 0.16 * s), "lime", rz)
        box(L(x * s, -0.265 * s, 1.0 * s), (0.08 * s, 0.01 * s, 0.09 * s), "window", rz)
        for zz in (0.25, 0.6):
            box(L(x * s + 0.22 * s, -0.28 * s, zz * s), (0.08 * s, 0.02 * s, 0.14 * s), "window", rz)
    for x in (-0.35, 0.35):
        box(L(x * s, 0.1 * s, 1.35 * s), (0.08 * s, 0.08 * s, 0.4 * s), "lime", rz)
    apex = 0.0
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        q = L(sx * 0.72 * s, sy * 0.3 * s)
        apex = max(apex, ftower((q.x, q.y, q.z), 0.19 * s, 1.0 * s, "slate", "lime", flag_h if (sx, sy) == (1, -1) else 0.0))
    return apex


def windmill(c, s, rz):
    L = local(c, rz)
    q = L(0, 0)
    cone((q.x, q.y, q.z), 0.2 * s, 0.15 * s, 0.75 * s, "plaster", 10)
    cone((q.x, q.y, q.z + 0.75 * s), 0.18 * s, 0.0, 0.25 * s, "roof", 10)
    box(L(0, -0.16 * s, 0.12 * s), (0.08 * s, 0.02 * s, 0.16 * s), "window", rz)
    hub = Vector((0, -0.2 * s, 0.68 * s))
    for i in range(4):
        a = i * math.pi / 2 + 0.35
        u = Vector((math.cos(a), 0, math.sin(a)))
        mx = Matrix.Translation(q) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Translation(hub + u * 0.3 * s) @ Matrix.Rotation(-a, 4, "Y") @ Matrix.Diagonal((0.6 * s, 0.015 * s, 0.1 * s, 1.0))
        box_m(mx, "plank")


def plaza(c, w, d, rz):
    box((c[0], c[1], 0.012), (w, d, 0.024), "paving", rz)


def scatter_houses(n, rmin, rmax, avoid, seed, s=(0.6, 0.78), center=(0.0, 0.0)):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 5000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r
        if any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < 0.58 for p in placed):
            continue
        placed.append((x, y))
        house((x, y, 0.0), rr.uniform(*s), a + math.pi / 2 + rr.uniform(-0.2, 0.2), rr.choice(("tile", "tile", "slate")), rr.choice((1.0, 1.0, 1.4, 1.7)), rr.random() < 0.7)
    return placed


def capital():
    outer = ring(3.75, 12, 0.03, 44, 0.1)
    fr_ring(outer, 0.75, (0, 0), 0.0, lambda c: ftower(c, 0.24, 1.05), gates=(0, 4, 8))
    cc = (0.75, 0.95)
    z = mound(cc, 1.25, 0.3)
    inner = [(cc[0] + x, cc[1] + y) for x, y in ring(1.05, 6, 0.0, 3, 0.25)]
    fr_ring(inner, 0.7, cc, z, lambda c: ftower(c, 0.2, 1.05, "slate", "lime"), gates=(3,))
    palace((cc[0] - 0.1, cc[1] - 0.25, z), 0.75, 0.2, 0.7)
    keep((cc[0] + 0.35, cc[1] + 0.45, z), 0.55, 1.55, 0.2, "lime", "slate", True, 0.7)
    cathedral((-1.05, -0.35, 0.0), 0.95, 0.15, 2)
    plaza((0.55, -1.35), 1.2, 0.8, 0.1)
    for i, (x, y) in enumerate(((-0.05, -1.35), (0.55, -1.9), (1.2, -1.2))):
        house((x, y, 0.0), 0.8, 0.1 + i * math.pi / 2, "slate", 1.8, True)
    avoid = [(cc, 1.9), ((-1.05, -0.35), 1.3), ((0.55, -1.35), 1.0), ((-2.2, 1.6), 0.85)]
    scatter_houses(36, 1.2, 3.25, avoid, 5)
    church((-2.2, 1.6, 0.0), 0.6, 0.9)
    return finish("WorldTown_vallerois_capital")


def large():
    outer = ring(3.05, 9, 0.04, 17, 0.35)
    fr_ring(outer, 0.65, (0, 0), 0.0, lambda c: ftower(c, 0.21, 0.9), gates=(0, 5))
    keep((0.9, 0.85, 0.0), 0.6, 1.45, 0.3, "lime", "slate", True, 0.65)
    cathedral((-0.6, -0.1, 0.0), 0.72, -0.2, 1)
    plaza((0.45, -0.95), 0.9, 0.6, 0.2)
    house((0.45, -1.45, 0.0), 0.75, 0.2, "slate", 1.8, True)
    avoid = [((0.9, 0.85), 0.75), ((-0.6, -0.1), 1.05), ((-1.35, -0.25), 0.5), ((0.45, -0.95), 0.75), ((0.45, -1.45), 0.4)]
    scatter_houses(26, 0.6, 2.6, avoid, 8)
    return finish("WorldTown_vallerois_large")


def medium():
    pts = ring(1.85, 6, 0.05, 23, 0.6)
    fr_ring(pts, 0.55, (0, 0), 0.0, lambda c: ftower(c, 0.19, 0.75), gates=(0,))
    keep((0.45, 0.45, 0.0), 0.5, 1.25, 0.5, "lime", "slate", False, 0.55)
    church((-0.45, -0.35, 0.0), 0.62, 0.4)
    scatter_houses(7, 0.4, 1.4, [((0.45, 0.45), 0.6), ((-0.45, -0.35), 0.75), ((-0.78, -0.6), 0.45)], 31)
    scatter_houses(10, 2.25, 2.85, [((2.0, -1.9), 0.9)], 37)
    field((2.0, -1.9, 0.0), 1.0, 0.7, -0.6)
    windmill((-2.3, 1.7, 0.0), 0.95, 0.4)
    field((-1.7, 2.3, 0.0), 0.8, 0.55, 0.9, "field_green")
    return finish("WorldTown_vallerois_medium")


def castle_grand():
    pts = ring(2.1, 7, 0.0, 1, 0.2)
    fr_ring(pts, 0.7, (0, 0), 0.0, lambda c: ftower(c, 0.24, 1.05), gates=(5,))
    palace((0.15, -0.25, 0.0), 0.85, 0.15)
    q = ftower((-0.75, 0.75, 0.0), 0.42, 1.85, "slate", "lime", 0.7)
    box((0.55, 0.85, 0.3), (0.9, 0.45, 0.6), "lime", 0.15)
    gable((0.55, 0.85, 0.6), 0.9, 0.45, 0.3, "slate", 0.15, 0.04)
    return finish("WorldCastle_vallerois_grand")


def castle_fortress():
    pts = [(-1.65, -1.55), (1.65, -1.55), (1.75, 1.55), (-1.6, 1.65)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        d = (b - a).normalized()
        cwall(a + d * 0.3, b - d * 0.3, 0.95, (0, 0), 0.0, "grey", 0.36)
    for i, p in enumerate(pts):
        keep((p[0], p[1], 0.0), 0.6, 1.25, 0.05, "grey", None, False)
    gatehouse((0.0, -1.55, 0.0), 0.0, 1.05, "grey", None)
    keep((0.2, 0.3, 0.0), 0.95, 1.9, 0.05, "grey", None, False, 0.75)
    for x, y, rz in ((-0.95, 0.75, 0.0), (1.0, -0.65, math.pi / 2)):
        box((x, y, 0.25), (1.0, 0.42, 0.5), "grey", rz)
        gable((x, y, 0.5), 1.0, 0.42, 0.22, "tile", rz, 0.04)
    return finish("WorldCastle_vallerois_fortress")


def castle_keep():
    z = mound((0.35, 0.3), 0.95, 0.5)
    keep((0.35, 0.3, z), 0.75, 1.5, 0.3, "lime", "slate", True, 0.65)
    pts = ring(1.75, 6, 0.06, 9, 0.3)
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        d = (b - a).normalized()
        cwall(a + d * 0.1, b - d * 0.1, 0.45, (0, 0), 0.0, "lime", 0.2)
    for p in pts[::2]:
        ftower((p[0], p[1], 0.0), 0.16, 0.6, "slate")
    house((-0.75, -0.6, 0.0), 0.75, 0.5, "tile", 1.0, False)
    house((0.3, -1.05, 0.0), 0.7, -0.2, "tile", 1.0, True)
    rr = random.Random(3)
    for i in range(8):
        a = rr.uniform(0, math.tau)
        r = rr.uniform(2.05, 2.6)
        tree((math.cos(a) * r, math.sin(a) * r, 0.0), rr.uniform(0.9, 1.3))
    return finish("WorldCastle_vallerois_keep")


def castle_moat():
    pts = [(-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)]
    fr_ring(pts, 0.75, (0, 0), 0.0, lambda c: ftower(c, 0.27, 1.1), gates=())
    gatehouse((0.0, -1.3, 0.0), 0.0, 1.0, "lime", "slate", 0.6)
    keep((0.2, 0.25, 0.0), 0.7, 1.45, 0.0, "lime", "slate", True)
    box((-0.6, 0.55, 0.22), (0.4, 0.95, 0.44), "lime", 0.0)
    gable((-0.6, 0.55, 0.44), 0.95, 0.4, 0.22, "tile", math.pi / 2, 0.04)
    return finish("WorldCastle_vallerois_moat")


def disc(c, rx, ry, m, seg=24):
    bm = bmesh.new()
    mid = bm.verts.new(c)
    rim = [bm.verts.new((c[0] + math.cos(i / seg * math.tau) * rx, c[1] + math.sin(i / seg * math.tau) * ry, c[2])) for i in range(seg)]
    for i in range(seg):
        bm.faces.new((mid, rim[i], rim[(i + 1) % seg]))
    put("disc", bm, m, True)


def dormer(c, rz, s=1.0):
    L = local(c, rz)
    box(L(0, 0, 0), (0.14 * s, 0.12 * s, 0.16 * s), "lime", rz)
    box(L(0, -0.065 * s, -0.01 * s), (0.08 * s, 0.01 * s, 0.09 * s), "window", rz)
    gable(L(0, 0, 0.08 * s), 0.12 * s, 0.14 * s, 0.1 * s, "slate", rz + math.pi / 2, 0.01)


def chimney(c, h):
    box((c[0], c[1], c[2] + h / 2), (0.08, 0.08, h), "lime")
    box((c[0], c[1], c[2] + h + 0.02), (0.11, 0.11, 0.04), "lime")


def castle_chateau():
    cy = 0.45
    box((0.0, cy, 0.52), (1.0, 0.9, 1.05), "lime")
    gable((0.0, cy, 1.05), 1.0, 0.9, 0.62, "slate", 0.0, 0.04)
    for zz in (0.3, 0.72):
        for x in (-0.25, 0.0, 0.25):
            box((x, cy - 0.455, zz), (0.08, 0.02, 0.15), "window")
    for x in (-0.28, 0.28):
        dormer((x, cy - 0.3, 1.18), 0.0)
    for x, y in ((-0.38, cy + 0.15), (0.38, cy + 0.15), (-0.2, cy - 0.1), (0.2, cy - 0.1)):
        chimney((x, y, 1.2), 0.55)
    cone((0.0, cy, 1.5), 0.17, 0.15, 0.42, "lime", 8, math.pi / 8, False)
    for i in range(8):
        a = i / 8 * math.tau + math.pi / 8
        box((math.cos(a) * 0.16, cy + math.sin(a) * 0.16, 1.72), (0.05, 0.05, 0.16), "window", a)
    cone((0.0, cy, 1.92), 0.2, 0.2, 0.06, "lime", 8, math.pi / 8, False)
    cone((0.0, cy, 1.98), 0.19, 0.0, 0.7, "slate", 8, math.pi / 8, False)
    box((0.0, cy, 2.75), (0.03, 0.03, 0.18), "gold")
    for sx in (-1, 1):
        for sy in (-1, 1):
            ftower((sx * 0.55, cy + sy * 0.47, 0.0), 0.25, 1.0, "slate", "lime", 0.6 if (sx, sy) == (1, 1) else 0.0)
        box((sx * 0.95, -0.55, 0.37), (0.4, 1.15, 0.75), "lime")
        gable((sx * 0.95, -0.55, 0.75), 1.15, 0.4, 0.42, "slate", math.pi / 2, 0.04)
        for y in (-0.25, -0.65, -1.0):
            dormer((sx * 0.95 - sx * 0.13, y, 0.86), -sx * math.pi / 2, 0.85)
            box((sx * 0.95 - sx * 0.205, y, 0.38), (0.02, 0.08, 0.15), "window")
        chimney((sx * 1.0, -0.4, 0.95), 0.35)
        ftower((sx * 0.95, -1.28, 0.0), 0.2, 0.85, "slate", "lime")
    plaza((0.0, -0.7), 1.4, 1.15, 0.0)
    box((0.0, -2.05, 0.012), (2.5, 1.2, 0.024), "paving", 0.0)
    cone((0.0, -2.05, 0.0), 0.24, 0.24, 0.07, "lime", 16)
    disc((0.0, -2.05, 0.072), 0.2, 0.2, "paving", 16)
    cone((0.0, -2.05, 0.0), 0.04, 0.03, 0.22, "lime", 8)
    for i in range(8):
        a = i / 8 * math.tau + math.pi / 8
        box((math.cos(a) * 0.48, -2.05 + math.sin(a) * 0.4, 0.05), (0.3, 0.1, 0.1), "hedge", a + math.pi / 2)
    for sx in (-1, 1):
        box((sx * 0.95, -2.05, 0.05), (0.42, 0.9, 0.1), "hedge", 0.0)
        cwall((sx * 1.25, -2.68), (sx * 0.2, -2.68), 0.14, (0.0, 0.0), 0.0, "lime", 0.1)
        ftower((sx * 1.3, -2.68, 0.0), 0.1, 0.32, "slate")
        for k in range(4):
            tree((sx * 1.75, -0.45 - k * 0.52, 0.0), 0.95)
    disc((0.0, 1.8, 0.02), 1.45, 0.5, "paving")
    for i in range(6):
        a = i / 6 * math.tau
        box((math.cos(a) * 0.85, 1.8 + math.sin(a) * 0.28, 0.06), (0.36, 0.12, 0.1), "hedge", a + math.pi / 2)
    cone((0.0, 1.8, 0.0), 0.2, 0.2, 0.08, "lime", 12)
    church((1.85, 0.9, 0.0), 0.38, -math.pi / 2)
    return finish("WorldCastle_vallerois_chateau")


ALL = {"capital": capital, "large": large, "medium": medium, "grand": castle_grand, "fortress": castle_fortress, "keep": castle_keep, "moat": castle_moat, "chateau": castle_chateau}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, len(o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
