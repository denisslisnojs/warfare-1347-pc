import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldVarden"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())
M["beam"] = M["log"]
M["plank"] = mat("env_plank", (0.56, 0.41, 0.26), 0.85)
TOWN_BUDGET = 1000
LOGS = {"grey": "log_dark", "lime": "log", "dark": "log_dark", "plank": "log"}


def srub(c, w, d, h, r, rz=0.0, mats=("log", "log_dark")):
    step = r * 1.85
    n = max(1, int(h / step))
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector(c)
    m = rnd.choice(mats)
    for i in range(n):
        z = r + i * step
        for sy in (-1, 1):
            log(base + rot @ Vector((-w / 2 - r * 1.5, sy * d / 2, z)), base + rot @ Vector((w / 2 + r * 1.5, sy * d / 2, z)), r, m)
        for sx in (-1, 1):
            log(base + rot @ Vector((sx * w / 2, -d / 2 - r * 1.5, z + step / 2)), base + rot @ Vector((sx * w / 2, d / 2 + r * 1.5, z + step / 2)), r, m)
    box((c[0], c[1], c[2] + n * step / 2), (w * 0.98, d * 0.98, n * step), m, rz)
    return c[2] + n * step + step / 2


def wood_tower(c, w, h, rz=0.0, lookout=False, roof="roof"):
    top = srub(c, w, w, h, w * 0.11, rz)
    ct = srub((c[0], c[1], top), w * 1.26, w * 1.26, w * 0.42, w * 0.08, rz, ("log_old",))
    for k in range(4):
        a = rz + k * math.pi / 2
        v = Vector((math.cos(a), math.sin(a), 0)) * (w * 0.63 + w * 0.09)
        box((c[0] + v.x, c[1] + v.y, top + w * 0.22), (w * 0.2, w * 0.2, w * 0.16), "window", a)
    pyramid((c[0], c[1], ct), w * 1.55, w * 1.45, roof, 4, rz)
    apex = ct + w * 1.45
    if lookout:
        box((c[0], c[1], ct + w * 1.3), (w * 0.24, w * 0.24, w * 0.34), "plank", rz)
        pyramid((c[0], c[1], ct + w * 1.47), w * 0.36, w * 0.5, roof, 4, rz)
        apex = ct + w * 1.97
    return apex


def stone_tower(c, r, h, round_=True, roof="roof_green", spire="gold"):
    if round_:
        cone(c, r, r * 0.94, h, "stone", 12)
        cone((c[0], c[1], c[2] + h), r * 1.08, r * 1.08, r * 0.18, "stone", 12)
        cone((c[0], c[1], c[2] + h + r * 0.18), r * 1.12, 0.0, r * 2.3, roof, 12, 0.0, False)
    else:
        box((c[0], c[1], c[2] + h / 2), (r * 2, r * 2, h), "stone")
        box((c[0], c[1], c[2] + h + r * 0.09), (r * 2.2, r * 2.2, r * 0.18), "stone")
        pyramid((c[0], c[1], c[2] + h + r * 0.18), r * 2.25, r * 2.3, roof)
    apex = c[2] + h + r * 2.48
    box((c[0], c[1], apex + r * 0.25), (r * 0.08, r * 0.08, r * 0.5), spire)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        box((c[0] + math.cos(a) * r * 0.98, c[1] + math.sin(a) * r * 0.98, c[2] + h * 0.6), (r * 0.18, r * 0.18, r * 0.36), "window", a)
    return apex + r * 0.5


def wall_wood(a, b, h, center, z0=0.0, r=0.065):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    step = r * 1.85
    k = max(2, int(h / step))
    for i in range(k):
        z = z0 + r + i * step
        log(a + n * 0.14 + Vector((0, 0, z - z0)), b + n * 0.14 + Vector((0, 0, z - z0)), r, rnd.choice(("log", "log_dark")))
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x - n.x * 0.04, mid.y - n.y * 0.04, z0 + k * step / 2), (length, 0.3, k * step), "log_dark", rz)
    box((mid.x + n.x * 0.16, mid.y + n.y * 0.16, z0 + k * step + 0.12), (length, 0.05, 0.24), "plank", rz)
    for i in range(max(1, int(length / 0.45))):
        q = a.lerp(b, (i + 0.5) / max(1, int(length / 0.45))) + n * 0.19
        box((q.x, q.y, z0 + k * step + 0.13), (0.07, 0.02, 0.09), "window", rz)
    gable((mid.x, mid.y, z0 + k * step + 0.24), length, 0.42, 0.18, "roof", rz, 0.04)


def wall_stone(a, b, h, center, z0=0.0):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, z0 + h / 2), (length, 0.26, h), "stone", rz)
    m = max(2, int(length / 0.2))
    for i in range(m):
        q = a.lerp(b, (i + 0.5) / m) + n * 0.09
        box((q.x, q.y, z0 + h + 0.07), (0.1, 0.08, 0.14), "stone", rz)
    gable((mid.x - n.x * 0.05, mid.y - n.y * 0.05, z0 + h), length, 0.16, 0.08, "roof_green", rz, 0.02, 0.02)


ONION = [(0.0, 0.0), (0.66, 0.0), (0.9, 0.2), (1.0, 0.48), (0.95, 0.76), (0.75, 1.02), (0.48, 1.28), (0.22, 1.52), (0.07, 1.78), (0.0, 1.98)]


def onion(c, r, m, drum=0.9, drum_m="stone"):
    x, y, z = c
    cone((x, y, z), r * 0.72, r * 0.72, r * drum, drum_m, 12)
    for i in range(6):
        a = i / 6 * math.tau
        box((x + math.cos(a) * r * 0.73, y + math.sin(a) * r * 0.73, z + r * drum * 0.55), (r * 0.12, r * 0.12, r * 0.4), "window", a)
    lathe(ONION, (x, y, z + r * drum), r, m)
    top = z + r * drum + r * 1.98
    box((x, y, top + r * 0.35), (r * 0.08, r * 0.08, r * 0.7), "gold")
    box((x, y, top + r * 0.48), (r * 0.42, r * 0.07, r * 0.07), "gold")
    return top + r * 0.7


def cathedral(c, s, domes="five", center="gold", side="dome"):
    x, y, z = c
    box((x, y, z + 0.65 * s), (1.2 * s, 1.2 * s, 1.3 * s), "stone")
    box((x, y - 0.78 * s, z + 0.45 * s), (0.7 * s, 0.36 * s, 0.9 * s), "stone")
    for side_i in range(4):
        a = side_i * math.pi / 2
        for k in (-1, 0, 1):
            v = Vector((math.cos(a) * 0.6 * s, math.sin(a) * 0.6 * s, 0)) + Vector((-math.sin(a), math.cos(a), 0)) * k * 0.4 * s
            bm = bmesh.new()
            mx = Matrix.Translation((x + v.x, y + v.y, z + 1.3 * s)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
            bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.2 * s, radius2=0.2 * s, depth=0.06 * s, matrix=mx)
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z + 1.3 * s), plane_no=(0, 0, 1), clear_inner=True)
            put("zakomara", bm, "stone", True)
            if side_i != 3:
                box((x + v.x * 1.02, y + v.y * 1.02, z + 0.8 * s), (0.09 * s, 0.09 * s, 0.3 * s), "window", a)
    box((x, y, z + 1.37 * s), (1.12 * s, 1.12 * s, 0.14 * s), "stone")
    top = onion((x, y, z + 1.44 * s), 0.3 * s, center, 1.3)
    if domes == "five":
        for dx, dy in ((-0.38, -0.38), (0.38, -0.38), (0.38, 0.38), (-0.38, 0.38)):
            onion((x + dx * s, y + dy * s, z + 1.44 * s), 0.17 * s, side, 1.1)
    return top


def wood_church(c, s, rz=0.0, dome="dome"):
    x, y, z = c
    cone((x, y, z), 0.42 * s, 0.42 * s, 0.75 * s, "log", 8, rz, False)
    cone((x, y, z + 0.75 * s), 0.5 * s, 0.5 * s, 0.06 * s, "plank", 8, rz, False)
    pyramid((x, y, z + 0.81 * s), 0.9 * s, 1.15 * s, "roof", 8, rz)
    top = onion((x, y, z + 1.86 * s), 0.1 * s, dome, 0.6, "plank")
    v = Matrix.Rotation(rz, 3, "Z") @ Vector((0, -0.62 * s, 0))
    srub((x + v.x, y + v.y, z), 0.5 * s, 0.42 * s, 0.42 * s, 0.05 * s, rz)
    gable((x + v.x, y + v.y, z + 0.45 * s), 0.5 * s, 0.42 * s, 0.3 * s, "roof", rz + math.pi / 2, 0.05)
    return top


def izba(c, s, rz, tall=1.0, budget=TOWN_BUDGET):
    name = "House_2" if tall > 1.1 else rnd.choice(("House_1", "House_1", "House_2", "Blacksmith"))
    building(name, c, rz, s * 1.05, "roof", budget, "log_dark", LOGS)
    return c[2] + s


def terem(c, s, rz, flag_h=0.0):
    x, y, z = c
    rot = Matrix.Rotation(rz, 3, "Z")
    top = srub(c, 1.1 * s, 0.85 * s, 1.0 * s, 0.065 * s, rz)
    for dx in (-0.28, 0.12):
        for zz in (0.35, 0.75):
            v = rot @ Vector((dx * s, -0.45 * s, zz * s))
            box((x + v.x, y + v.y, z + v.z), (0.15 * s, 0.03 * s, 0.2 * s), "window", rz)
            box((x + v.x, y + v.y, z + v.z + 0.13 * s), (0.22 * s, 0.04 * s, 0.05 * s), "red", rz)
    gable((x, y, top), 0.85 * s, 1.1 * s, 0.8 * s, "roof", rz + math.pi / 2, 0.12 * s)
    gable_end((x, y, top), 0.85 * s, 1.1 * s, 0.8 * s, "red", rz + math.pi / 2)
    v = rot @ Vector((0.82 * s, 0.0, 0))
    t2 = srub((x + v.x, y + v.y, z), 0.45 * s, 0.45 * s, 1.35 * s, 0.055 * s, rz)
    pyramid((x + v.x, y + v.y, t2), 0.66 * s, 0.8 * s, "roof", 8, rz)
    if flag_h:
        flag((x + v.x, y + v.y, t2 + 0.7 * s), flag_h)
    return t2 + 0.8 * s


def palace(c, s, rz, flag_h=0.0):
    x, y, z = c
    rot = Matrix.Rotation(rz, 3, "Z")
    terem(c, s, rz, flag_h)
    v = rot @ Vector((-0.95 * s, 0.25 * s, 0))
    top = srub((x + v.x, y + v.y, z), 0.7 * s, 0.7 * s, 1.5 * s, 0.06 * s, rz)
    cone((x + v.x, y + v.y, top), 0.34 * s, 0.34 * s, 0.2 * s, "log_old", 8, rz, False)
    lathe([(0.0, 0.0), (0.4, 0.0), (0.42, 0.25), (0.3, 0.6), (0.0, 0.85)], (x + v.x, y + v.y, top + 0.2 * s), s, "roof", 8)
    return top + 1.05 * s


def bell_tower(c, s):
    x, y, z = c
    box((x, y, z + 0.5 * s), (0.5 * s, 0.5 * s, 1.0 * s), "stone")
    cone((x, y, z + 1.0 * s), 0.22 * s, 0.2 * s, 0.6 * s, "stone", 8, math.pi / 8, False)
    for i in range(8):
        a = i / 8 * math.tau + math.pi / 8
        box((x + math.cos(a) * 0.2 * s, y + math.sin(a) * 0.2 * s, z + 1.3 * s), (0.06 * s, 0.06 * s, 0.2 * s), "window", a)
    pyramid((x, y, z + 1.6 * s), 0.48 * s, 0.8 * s, "roof_green", 8)
    return onion((x, y, z + 2.38 * s), 0.07 * s, "gold", 0.4)


def scatter_izbas(n, rmin, rmax, avoid, seed, s=(0.62, 0.8), tall=(1.0, 1.0, 1.3), budget=TOWN_BUDGET):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 4000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = math.cos(a) * r, math.sin(a) * r
        if any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < 0.62 for p in placed):
            continue
        placed.append((x, y))
        izba((x, y, 0.0), rr.uniform(*s), a + math.pi / 2 + rr.uniform(-0.25, 0.25), rr.choice(tall), budget)
    return placed


def ring_walls(pts, h, center, kind, z0=0.0, tower=None, gate=0):
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        va, vb = Vector(a), Vector(b)
        d = (vb - va).normalized() * 0.3
        a2, b2 = (va + d), (vb - d)
        if kind == "wood":
            wall_wood(a2, b2, h, center, z0)
        elif kind == "stone":
            wall_stone(a2, b2, h, center, z0)
        else:
            palisade(a2, b2, h, z0)
    tops = []
    for i, p in enumerate(pts):
        tops.append(tower((p[0], p[1], z0), i == gate, math.atan2(p[1] - center[1], p[0] - center[0])))
    return tops


def capital():
    outer = ring(3.75, 10, 0.05, 31, 0.2)
    ring_walls(outer, 0.6, (0, 0), "wood", 0.0, lambda c, g, rz: wood_tower(c, 0.58 if g else 0.44, 1.05 if g else 0.85, rz, g), 0)
    dc = (0.25, 0.35)
    z = mound(dc, 1.75, 0.32)
    inner = [(dc[0] + x, dc[1] + y) for x, y in ring(1.5, 7, 0.0, 1, 0.3)]
    ring_walls(inner, 0.62, dc, "stone", z, lambda c, g, rz: stone_tower(c, 0.2 if g else 0.16, 0.95 if g else 0.78, not g), 0)
    cathedral((dc[0] + 0.35, dc[1] + 0.3, z), 0.95, "five", "gold", "gold")
    palace((dc[0] - 0.45, dc[1] - 0.55, z), 0.8, 0.35, 0.7)
    bell_tower((dc[0] + 0.85, dc[1] - 0.75, z), 0.75)
    cathedral((dc[0] - 0.75, dc[1] + 0.75, z), 0.5, "one", "dome")
    marks = [((-2.35, 1.35), 0.9), ((2.0, -2.15), 0.85), ((-1.0, -2.65), 0.7), ((2.55, 1.0), 0.6)]
    terem((-2.35, 1.35, 0.0), 0.65, 1.2)
    terem((2.0, -2.15, 0.0), 0.6, -0.6)
    wood_church((-1.0, -2.65, 0.0), 0.75, 0.3)
    cathedral((2.55, 1.0, 0.0), 0.45, "one", "dome")
    scatter_izbas(30, 2.3, 3.1, [(dc, 2.35)] + marks, 7)
    flag((outer[0][0], outer[0][1], 2.1), 0.6)
    return finish("WorldTown_varden_capital")


def large():
    outer = ring(3.15, 8, 0.06, 12, 0.5)
    ring_walls(outer, 0.85, (0, 0), "palisade", 0.0, lambda c, g, rz: wood_tower(c, 0.5 if g else 0.4, 0.95 if g else 0.75, rz, g), 0)
    dc = (0.2, 0.25)
    z = mound(dc, 1.4, 0.26)
    inner = [(dc[0] + x, dc[1] + y) for x, y in ring(1.2, 5, 0.0, 2, 0.1)]
    ring_walls(inner, 0.55, dc, "wood", z, lambda c, g, rz: wood_tower(c, 0.42 if g else 0.34, 0.9 if g else 0.7, rz, g), 0)
    cathedral((dc[0] + 0.25, dc[1] + 0.25, z), 0.8, "five", "gold", "dome")
    terem((dc[0] - 0.45, dc[1] - 0.35, z), 0.6, 0.2, 0.6)
    wood_church((-1.9, -1.6, 0.0), 0.65, 0.5)
    scatter_izbas(20, 1.95, 2.5, [(dc, 2.0), ((-1.9, -1.6), 0.7)], 9)
    return finish("WorldTown_varden_large")


def medium():
    dc = (0.0, 0.0)
    z = mound(dc, 1.3, 0.2)
    inner = ring(1.15, 5, 0.04, 5, 0.7)
    tops = ring_walls(inner, 0.5, dc, "wood", z, lambda c, g, rz: wood_tower(c, 0.4 if g else 0.32, 0.85 if g else 0.65, rz, g), 0)
    cathedral((0.25, 0.2, z), 0.65, "one", "gold")
    terem((-0.35, -0.3, z), 0.5, -0.4, 0.55)
    arc = [(math.cos(a) * 2.7, math.sin(a) * 2.7) for a in [math.radians(t) for t in range(200, 341, 28)]]
    for a, b in zip(arc, arc[1:]):
        palisade(a, b, 0.6)
    field((2.2, 1.6, 0.0), 0.9, 0.6, 0.6)
    scatter_izbas(14, 1.95, 2.35, [(dc, 1.95), ((2.2, 1.6), 0.75)], 13)
    return finish("WorldTown_varden_medium")


def castle_stone():
    pts = [(-1.5, -1.4), (1.5, -1.4), (1.6, 1.4), (-1.45, 1.5)]
    tops = ring_walls(pts, 0.85, (0, 0), "stone", 0.0, lambda c, g, rz: stone_tower(c, 0.3 if g else 0.26, 1.35 if g else 1.15, not g, "roof_green"), 0)
    stone_tower((0.0, -1.4, 0.0), 0.28, 1.45, False)
    cathedral((0.35, 0.4, 0.0), 0.55, "one", "gold")
    box((-0.6, 0.6, 0.25), (1.0, 0.45, 0.5), "stone", 0.0)
    gable((-0.6, 0.6, 0.5), 1.0, 0.45, 0.25, "roof_green", 0.0, 0.05)
    flag((pts[0][0], pts[0][1], tops[0] - 0.1), 0.65)
    return finish("WorldCastle_varden_stone")


def castle_mixed():
    z = mound((0, 0), 1.75, 0.3)
    pts = ring(1.5, 5, 0.05, 8, 0.6)
    def tw(c, g, rz):
        return stone_tower(c, 0.26, 1.15, True, "roof") if g or c[0] > 0.8 else wood_tower(c, 0.42, 0.85, rz, False)
    tops = ring_walls(pts, 0.6, (0, 0), "wood", z, tw, 0)
    terem((-0.25, -0.15, z), 0.6, 0.3)
    wood_church((0.6, 0.6, z), 0.55, 0.0)
    flag((pts[0][0], pts[0][1], tops[0] - 0.1), 0.6)
    return finish("WorldCastle_varden_mixed")


def castle_ostrog():
    pts = [(-1.35, -1.3), (1.35, -1.3), (1.35, 1.3), (-1.35, 1.3)]
    tops = ring_walls(pts, 0.9, (0, 0), "palisade", 0.0, lambda c, g, rz: wood_tower(c, 0.48, 0.95, rz, False), 9)
    wood_tower((0.0, -1.3, 0.0), 0.55, 1.05, 0.0, False)
    top = wood_tower((0.15, 0.2, 0.0), 0.72, 1.7, 0.0, True)
    izba((-0.7, 0.65, 0.0), 0.75, 0.0)
    izba((0.75, -0.55, 0.0), 0.7, math.pi / 2)
    izba((-0.75, -0.45, 0.0), 0.65, 0.1)
    flag((0.15, 0.2, top - 0.05), 0.65)
    return finish("WorldCastle_varden_ostrog")


def castle_monastery():
    pts = [(-1.55, -1.45), (1.55, -1.45), (1.55, 1.45), (-1.55, 1.45)]
    tops = ring_walls(pts, 0.6, (0, 0), "stone", 0.0, lambda c, g, rz: stone_tower(c, 0.22, 0.85, True, "roof"), 9)
    stone_tower((0.0, -1.45, 0.0), 0.26, 1.05, False, "roof_green")
    cathedral((0.1, 0.25, 0.0), 0.85, "five", "gold", "gold")
    bell_tower((0.95, -0.65, 0.0), 0.8)
    box((-0.95, 0.15, 0.24), (0.45, 1.6, 0.48), "stone", 0.0)
    gable((-0.95, 0.15, 0.48), 1.6, 0.45, 0.24, "roof", math.pi / 2, 0.05)
    cathedral((0.9, 0.95, 0.0), 0.4, "one", "dome")
    flag((pts[0][0], pts[0][1], tops[0] - 0.1), 0.55)
    return finish("WorldCastle_varden_monastery")


def selo():
    wood_church((0.0, 0.0, 0.0), 0.75, 0.3)
    scatter_izbas(9, 0.95, 1.85, [((0.75, -0.45), 0.35)], 41, budget=BUDGET)
    prop("Well", (0.75, -0.45, 0.0), 0.3, 1.0)
    prop("Cart", (-0.75, -0.55, 0.0), 1.9, 1.0)
    field((2.1, 0.3, 0.0), 1.1, 1.0, 0.2)
    field((-1.4, -2.0, 0.0), 1.0, 0.7, 0.9, "field_green")
    for x, y in ((1.85, -0.85), (2.25, -0.75), (2.0, -1.2)):
        haystack((x, y), 1.0)
    flag((-0.5, 0.45, 0.0), 1.35)
    return finish("WorldVillage_varden_selo")


def village():
    scatter_izbas(6, 0.6, 1.4, [((-0.55, -0.5), 0.35)], 52, budget=BUDGET)
    prop("Well", (-0.55, -0.5, 0.0), 0.2, 1.0)
    prop("Hay", (1.45, -1.05, 0.0), 0.3, 1.0)
    building("Stable", (-1.25, 0.95, 0.0), 2.3, 0.95, "roof", BUDGET, "log_dark", LOGS)
    top = srub((0.15, -0.1, 0.0), 0.55, 0.45, 0.35, 0.06, 0.4, ("log_old",))
    gable((0.15, -0.1, top), 0.55, 0.45, 0.28, "roof", 0.4, 0.06)
    field((2.0, 0.4, 0.0), 1.2, 1.0, 0.15)
    for x, y in ((1.7, -0.75), (2.15, -0.7)):
        haystack((x, y), 1.0)
    flag((-0.3, 0.3, 0.0), 1.2)
    return finish("WorldVillage_varden_village")


def hamlet():
    scatter_izbas(4, 0.5, 1.05, [], 63, (0.6, 0.72), budget=BUDGET)
    prop("Bonfire", (0.05, 0.05, 0.0), 0.0, 1.0)
    rr = random.Random(5)
    for i in range(9):
        a = rr.uniform(0, math.tau)
        r = rr.uniform(1.35, 2.1)
        pine((math.cos(a) * r, math.sin(a) * r, 0.0), rr.uniform(0.9, 1.35))
    for i in range(4):
        log((0.9 + i * 0.0, -0.3 + i * 0.07, 0.05 + (i % 2) * 0.08), (1.35, -0.3 + i * 0.07, 0.05 + (i % 2) * 0.08), 0.05, "log_old", 6)
    flag((-0.25, 0.25, 0.0), 1.1)
    return finish("WorldVillage_varden_hamlet")


ALL = {"capital": capital, "large": large, "medium": medium, "stone": castle_stone, "mixed": castle_mixed, "ostrog": castle_ostrog, "monastery": castle_monastery, "selo": selo, "village": village, "hamlet": hamlet}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, len(o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
