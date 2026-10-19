import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldKhordan"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())

M["adobe"] = mat("env_adobe", (0.83, 0.6, 0.36), 0.95)
M["adobe_dark"] = mat("env_adobe_dark", (0.68, 0.43, 0.26), 0.95)
M["brick"] = mat("env_brick", (0.68, 0.34, 0.22), 0.9)
M["turq"] = mat("env_tile_turq", (0.08, 0.55, 0.58), 0.4)
M["felt"] = mat("env_felt", (0.9, 0.86, 0.76), 0.95)
M["felt_dark"] = mat("env_felt_dark", (0.6, 0.48, 0.36), 0.95)
M["black"] = mat("env_black", (0.07, 0.07, 0.07), 0.8)
M["grey"] = mat("env_stone_grey", (0.6, 0.58, 0.55), 0.9)
M["rocky"] = mat("env_rock_hill", (0.42, 0.39, 0.32), 1.0)
M["leaf"] = mat("env_leaf_round", (0.26, 0.46, 0.18), 0.9)
M["paving"] = mat("env_paving", (0.74, 0.7, 0.62), 0.9)
mat("env_flag", (0.05, 0.42, 0.45), 0.8)


def local(c, rz):
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0))
    return lambda x, y, z=0.0: base + rot @ Vector((x, y, z))


def yurt(c, r, rz=0.0, roof="felt", wall="felt"):
    x, y, z = c
    lathe([(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.97, 0.56)], (x, y, z), r, wall, 14)
    lathe([(0.97, 0.56), (0.62, 0.82), (0.24, 1.0), (0.0, 1.04)], (x, y, z), r, roof, 14)
    cone((x, y, z + r * 0.98), r * 0.2, r * 0.18, r * 0.1, "black", 10)
    L = local(c, rz)
    box(L(0, -r * 0.98, r * 0.24), (r * 0.36, r * 0.06, r * 0.46), "turq", rz)
    for k in range(6):
        a = k / 6 * math.tau + 0.3
        box((x + math.cos(a) * r * 1.0, y + math.sin(a) * r * 1.0, z + r * 0.36), (r * 0.06, r * 0.06, r * 0.08), "black", a)


yurt = grouped(yurt)


def house(c, w, d, h, rz, m="adobe", dome=False, porch=False):
    L = local(c, rz)
    wood = m == "plank"
    box(L(0, 0, h / 2), (w, d, h), m, rz)
    box(L(0, 0, h + 0.025), (w * 1.02, d * 1.02, 0.05), "log_dark" if wood else "adobe_dark", rz)
    box(L(0, -d / 2 - 0.005, h * 0.3), (w * 0.2, 0.02, h * 0.55), "log_dark" if not wood else "black", rz)
    box(L(w * 0.28, -d / 2 - 0.005, h * 0.62), (w * 0.12, 0.02, h * 0.16), "black", rz)
    if not wood:
        n = max(2, int(w / 0.1))
        for k in range(n):
            x = -w / 2 + (k + 0.5) * w / n
            for sy in (-1, 1):
                log(L(x, sy * (d / 2 - 0.02), h * 0.86), L(x, sy * (d / 2 + 0.06), h * 0.86), 0.013, "log_dark", 5)
    else:
        for x in (-w / 2, w / 2):
            for sy in (-1, 1):
                log(L(x, sy * d / 2, 0.0), L(x, sy * d / 2, h), 0.02, "log_dark", 5)
    if porch:
        for sx in (-1, 1):
            log(L(sx * w * 0.38, -d / 2 - 0.15, 0.0), L(sx * w * 0.38, -d / 2 - 0.15, h * 0.78), 0.016, "log_dark", 5)
        box(L(0, -d / 2 - 0.08, h * 0.79), (w * 0.86, 0.2, 0.025), "plank", rz)
    if dome:
        q = L(w * 0.15, d * 0.1)
        lathe([(0.0, 0.0), (1.0, 0.0), (0.92, 0.45), (0.6, 0.85), (0.0, 1.0)], (q.x, q.y, q.z + h), min(w, d) * 0.3, "adobe_dark", 10)


DOME = [(0.0, 0.0), (1.0, 0.0), (1.02, 0.22), (0.96, 0.52), (0.78, 0.84), (0.48, 1.06), (0.14, 1.2), (0.0, 1.24)]


house = grouped(house)


def dome(c, r, drum_h, m="turq", drum="brick"):
    x, y, z = c
    cone((x, y, z), r * 1.02, r * 1.02, drum_h, drum, 14)
    for i in range(8):
        a = i / 8 * math.tau
        box((x + math.cos(a) * r * 1.03, y + math.sin(a) * r * 1.03, z + drum_h * 0.55), (r * 0.1, r * 0.1, drum_h * 0.4), "black", a)
    lathe(DOME, (x, y, z + drum_h), r, m, 16)
    box((x, y, z + drum_h + r * 1.24 + r * 0.15), (r * 0.06, r * 0.06, r * 0.3), "gold")
    return z + drum_h + r * 1.5


def minaret(c, r, h):
    x, y, z = c
    cone((x, y, z), r * 1.15, r * 0.85, h, "brick", 10)
    cone((x, y, z + h * 0.72), r * 1.35, r * 1.35, h * 0.05, "turq", 10)
    cone((x, y, z + h), r * 1.1, r * 1.1, h * 0.06, "brick", 10)
    lathe(DOME, (x, y, z + h * 1.06), r * 0.9, "turq", 10)
    return z + h * 1.06 + r * 1.1


def portal(c, w, h, rz, m="brick"):
    L = local(c, rz)
    box(L(0, 0, h / 2), (w, w * 0.35, h), m, rz)
    box(L(0, -w * 0.18, h * 0.42), (w * 0.5, 0.02, h * 0.7), "black", rz)
    box(L(0, -w * 0.18, h * 0.84), (w * 0.62, 0.02, h * 0.06), "turq", rz)
    for sx in (-1, 1):
        box(L(sx * w * 0.115, -w * 0.19, h * 0.24), (w * 0.21, 0.025, h * 0.46), "plank", rz)
    for sx in (-1, 1):
        q = L(sx * w * 0.5, 0)
        cone((q.x, q.y, q.z), w * 0.09, w * 0.08, h * 1.08, "turq", 8)


def bastion(c, r, h, m="adobe"):
    x, y, z = c
    cone((x, y, z), r * 1.15, r * 0.92, h, m, 12)
    cone((x, y, z + h), r * 0.96, r * 0.96, r * 0.22, "adobe_dark" if m == "adobe" else m, 12)
    for i in range(8):
        a = i / 8 * math.tau
        box((x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, z + h + r * 0.3), (r * 0.22, r * 0.18, r * 0.2), m, a)
    return z + h + r * 0.4


def mud_wall(a, b, h, center, z0=0.0, m="adobe", t=0.3):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, z0 + h / 2), (length, t, h), m, rz)
    box((mid.x - n.x * t * 0.05, mid.y - n.y * t * 0.05, z0 + h * 0.12), (length, t * 1.25, h * 0.24), m, rz)
    k = max(2, int(length / 0.22))
    for i in range(k):
        q = a.lerp(b, (i + 0.5) / k) + n * (t / 2 - 0.05)
        cone((q.x, q.y, z0 + h), 0.055, 0.03, 0.14, m, 6, rz, False)


def walled(pts, h, center, z0, tower_r, m, gates=()):
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        mud_wall(a + dd * tower_r * 0.8, b - dd * tower_r * 0.8, h, center, z0, m)
    for i, p in enumerate(pts):
        if i in gates:
            prev, nxt = Vector(pts[i - 1]), Vector(pts[(i + 1) % len(pts)])
            t = (nxt - prev).normalized()
            n = Vector((-t.y, t.x))
            if n.dot(Vector(p) - Vector(center)) < 0:
                n = -n
            portal((p[0], p[1], z0), tower_r * 3.2, h * 1.7, math.atan2(n.y, n.x) - math.pi / 2, "brick")
        else:
            bastion((p[0], p[1], z0), tower_r, h * 1.25, m)


def watch_tower(c, w, h, rz=0.0):
    x, y, z = c
    L = local(c, rz)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        q = L(sx * w / 2, sy * w / 2)
        log((q.x, q.y, z), (q.x * 0.98 + x * 0.02, q.y * 0.98 + y * 0.02, z + h), w * 0.07, "log_dark", 6)
    box(L(0, 0, h * 0.55), (w * 1.02, w * 0.04, w * 0.04), "log", rz)
    box(L(0, 0, h), (w * 1.2, w * 1.2, w * 0.08), "plank", rz)
    box(L(0, 0, h + w * 0.26), (w * 1.08, w * 1.08, w * 0.44), "log_old", rz)
    for k in range(4):
        a = rz + k * math.pi / 2
        box(L(0, 0, h + w * 0.3) + Vector((math.cos(a), math.sin(a), 0)) * w * 0.55, (w * 0.22, w * 0.22, w * 0.14), "black", a)
    pyramid(L(0, 0, h + w * 0.48), w * 1.3, w * 0.75, "roof", 4, rz)
    return z + h + w * 1.23


def tugh(c, h):
    x, y, z = c
    log((x, y, z), (x, y, z + h), 0.025, "log_dark", 6)
    cone((x, y, z + h), 0.05, 0.05, 0.02, "gold", 10)
    cone((x, y, z + h * 0.82), 0.09, 0.02, h * 0.18, "black", 8)


def corral(c, r, n=10):
    x, y, z = c
    for i in range(n):
        a0, a1 = i / n * math.tau, (i + 1) / n * math.tau
        p0 = Vector((x + math.cos(a0) * r, y + math.sin(a0) * r, z))
        p1 = Vector((x + math.cos(a1) * r, y + math.sin(a1) * r, z))
        log(p0, p0 + Vector((0, 0, 0.14)), 0.018, "log_dark", 5)
        log(p0 + Vector((0, 0, 0.11)), p1 + Vector((0, 0, 0.11)), 0.012, "log", 5)


def wagon(c, rz):
    L = local(c, rz)
    box(L(0, 0, 0.1), (0.32, 0.18, 0.08), "plank", rz)
    q = L(0, 0, 0.14)
    lathe([(0.0, 0.0), (0.12, 0.0), (0.11, 0.06), (0.0, 0.11)], (q.x, q.y, q.z), 1.0, "felt_dark", 8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = L(sx * 0.11, sy * 0.1, 0.06)
            bm = bmesh.new()
            mx = Matrix.Translation(q) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
            bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.06, radius2=0.06, depth=0.02, matrix=mx)
            put("wheel", bm, "log_dark", False)


def poplar(c, h):
    x, y, z = c
    log((x, y, z), (x, y, z + h * 0.25), h * 0.03, "log_dark", 5)
    lathe([(0.0, 0.0), (0.14, 0.05), (0.18, 0.35), (0.12, 0.75), (0.0, 1.0)], (x, y, z + h * 0.18), h, "leaf", 7)


def yurt_ring(n, rmin, rmax, avoid, seed, s=(0.2, 0.28)):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 4000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = math.cos(a) * r, math.sin(a) * r
        size = rr.uniform(*s)
        if any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < size * 2.6 for p in placed):
            continue
        placed.append((x, y))
        yurt((x, y, 0.0), size, a + math.pi / 2, rr.choice(("felt", "felt", "felt_dark")))
    return placed


def houses(n, rmin, rmax, avoid, seed, center=(0.0, 0.0), dome_chance=0.15):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 5000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r
        if any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < 0.5 for p in placed):
            continue
        placed.append((x, y))
        w, d = rr.uniform(0.32, 0.5), rr.uniform(0.28, 0.42)
        house((x, y, 0.0), w, d, rr.uniform(0.22, 0.36), a + rr.uniform(-0.2, 0.2), rr.choice(("adobe", "adobe", "adobe_dark", "plank")), rr.random() < dome_chance, rr.random() < 0.35)
    return placed


def palace(c, s, rz):
    L = local(c, rz)
    box(L(0, 0, 0.32 * s), (1.5 * s, 1.1 * s, 0.64 * s), "brick", rz)
    box(L(0, 0, 0.66 * s), (1.2 * s, 0.8 * s, 0.04 * s), "adobe_dark", rz)
    portal(L(0, -0.62 * s), 0.7 * s, 1.15 * s, rz)
    top = dome(L(0.1 * s, 0.1 * s, 0.64 * s), 0.38 * s, 0.32 * s)
    for sx in (-1, 1):
        q = L(sx * 0.6 * s, 0.38 * s, 0.64 * s)
        dome((q.x, q.y, q.z), 0.16 * s, 0.12 * s)
    for sx in (-1, 1):
        q = L(sx * 0.95 * s, -0.55 * s)
        minaret((q.x, q.y, q.z), 0.08 * s, 1.55 * s)
    return top


def capital():
    pts = ring(2.2, 8, 0.0, 3, 0.39)
    walled(pts, 0.55, (0, 0), 0.0, 0.2, "brick", gates=(0, 4))
    palace((0.15, 0.25, 0.0), 0.95, 0.0)
    flag((0.95 * 0.95 + 0.15, -0.55 * 0.95 + 0.25, 1.6), 0.7)
    q = ring(1.0, 1, 0, 1, 2.4)[0]
    dome((-0.9, -0.85, 0.0), 0.26, 0.4)
    houses(26, 0.6, 1.9, [((0.15, 0.25), 1.15), ((-0.9, -0.85), 0.45)], 41)
    yurt_ring(34, 2.75, 3.95, [], 7)
    for k in range(4):
        a = k / 4 * math.tau + 0.6
        corral((math.cos(a) * 3.35, math.sin(a) * 3.35, 0.0), 0.3)
    for k in range(6):
        a = k / 6 * math.tau + 0.2
        tugh((math.cos(a) * 2.55, math.sin(a) * 2.55, 0.0), 0.9)
    return finish("WorldTown_khordan_capital")


def large():
    pts = ring(1.95, 7, 0.04, 5, 0.2)
    walled(pts, 0.5, (0, 0), 0.0, 0.18, "adobe", gates=(0,))
    box((0.2, 0.2, 0.28), (1.0, 0.8, 0.56), "brick", 0.3)
    top = dome((0.25, 0.25, 0.56), 0.3, 0.26)
    portal((0.05, -0.32, 0.0), 0.5, 0.85, 0.3)
    minaret((-0.55, 0.65, 0.0), 0.08, 1.4)
    flag((-0.55, 0.65, 1.55), 0.6)
    houses(18, 0.5, 1.65, [((0.2, 0.2), 0.85), ((-0.55, 0.65), 0.25)], 51)
    yurt_ring(12, 2.35, 3.1, [((2.3, -1.6), 0.8)], 9)
    field((2.3, -1.6, 0.0), 0.9, 0.6, -0.6, "field_green")
    corral((-2.6, -1.2, 0.0), 0.32)
    for i in range(3):
        poplar((1.9 + i * 0.25, 1.75 - i * 0.15, 0.0), 0.9)
    return finish("WorldTown_khordan_large")


def medium():
    pts = ring(1.45, 6, 0.06, 6, 0.5)
    walled(pts, 0.42, (0, 0), 0.0, 0.16, "adobe", gates=(0,))
    box((0.1, 0.15, 0.22), (0.6, 0.55, 0.44), "adobe_dark", 0.0)
    dome((0.1, 0.15, 0.44), 0.22, 0.18)
    tugh((-0.45, -0.35, 0.0), 1.0)
    flag((-0.45, 0.45, 0.0), 1.1)
    houses(9, 0.45, 1.15, [((0.1, 0.15), 0.55)], 61)
    yurt_ring(10, 1.85, 2.75, [((2.0, 1.4), 0.75)], 11)
    field((2.0, 1.4, 0.0), 0.9, 0.6, 0.5, "field_green")
    corral((-2.2, 0.9, 0.0), 0.3)
    for i in range(3):
        poplar((-1.7 + i * 0.22, -1.9, 0.0), 0.85)
    return finish("WorldTown_khordan_medium")


def rock(c, r, sc=(1.0, 1.0, 1.0), seed=0, m="rocky"):
    rr = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)))
    for v in bm.verts:
        v.co += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-0.5, 1.0))) * r * 0.16
    put("rock", bm, m, False)


def ridge(a, b, w, h, seed, m="rocky"):
    rr = random.Random(seed)
    a, b = Vector(a), Vector(b)
    n = max(3, int((b - a).length / (w * 0.6)))
    for i in range(n):
        p = a.lerp(b, (i + 0.5) / n)
        hh = h * (0.65 + 0.35 * math.sin(math.pi * (i + 0.5) / n)) * rr.uniform(0.85, 1.1)
        r = w * rr.uniform(0.45, 0.6)
        rock((p.x, p.y, 0.0), r, (1.0, 0.85, hh / r), seed * 31 + i, m)


def tall_tower(c, r, h, m="brick", bands=2, crown="crenel"):
    x, y, z = c
    cone((x, y, z), r * 1.2, r * 0.86, h, m, 12)
    for i in range(bands):
        t = 0.42 + 0.26 * i
        rr = r * (1.2 - 0.34 * t) * 1.04
        cone((x, y, z + h * t), rr, rr, h * 0.045, "turq", 12)
    for i in range(3):
        a = i * 2.1 + 0.4
        box((x + math.cos(a) * r * 1.0, y + math.sin(a) * r * 1.0, z + h * 0.62), (r * 0.12, r * 0.12, r * 0.32), "black", a)
    cone((x, y, z + h), r * 1.04, r * 1.04, r * 0.24, m, 12)
    top = z + h + r * 0.24
    if crown == "crenel":
        for i in range(10):
            a = i / 10 * math.tau
            box((x + math.cos(a) * r * 0.98, y + math.sin(a) * r * 0.98, top + r * 0.1), (r * 0.2, r * 0.16, r * 0.2), m, a)
        return top + r * 0.2
    if crown == "flat":
        return top
    lathe(DOME, (x, y, top), r * 0.75, "turq", 12)
    return top + r * 0.93


def arcade(a, b, h, center, n, m="adobe"):
    a, b = Vector((a[0], a[1], 0.0)), Vector((b[0], b[1], 0.0))
    d, nrm = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, h / 2), (length, 0.34, h), m, rz)
    box((mid.x, mid.y, h + 0.04), (length, 0.37, 0.08), "adobe_dark", rz)
    for i in range(n):
        q = a.lerp(b, (i + 0.5) / n) - nrm * 0.172
        box((q.x, q.y, h * 0.36), (length / n * 0.55, 0.02, h * 0.52), "black", rz)
        box((q.x, q.y, h * 0.67), (length / n * 0.38, 0.021, h * 0.1), "black", rz)
        box((q.x - nrm.x * 0.002, q.y - nrm.y * 0.002, h * 0.74), (length / n * 0.62, 0.02, h * 0.03), "turq", rz)


def rampart(a, b, w, h):
    a, b = Vector((a[0], a[1], 0.0)), Vector((b[0], b[1], 0.0))
    d = (b - a).normalized()
    n = Vector((-d.y, d.x, 0.0))
    bm = bmesh.new()
    pts = [a - n * w / 2, b - n * w / 2, b + n * w / 2, a + n * w / 2,
           a - n * w * 0.16 + Vector((0, 0, h)), b - n * w * 0.16 + Vector((0, 0, h)), b + n * w * 0.16 + Vector((0, 0, h)), a + n * w * 0.16 + Vector((0, 0, h))]
    v = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)):
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put("rampart", bm, "earth", False)


def beacon(c, h):
    x, y, z = c
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        log((x + sx * 0.09, y + sy * 0.09, z), (x + sx * 0.04, y + sy * 0.04, z + h), 0.018, "log_dark", 5)
    cone((x, y, z + h), 0.09, 0.13, 0.1, "plank", 8)
    cone((x, y, z + h + 0.1), 0.08, 0.0, 0.16, "gold", 7)


def steps(a, b, w, z0, z1, n):
    a, b = Vector(a), Vector(b)
    d = b - a
    rz = math.atan2(d.y, d.x)
    for i in range(n):
        p = a.lerp(b, (i + 0.5) / n)
        z = z0 + (z1 - z0) * (i + 1) / n
        box((p.x, p.y, z / 2), (d.length / n * 1.05, w, z), "adobe_dark", rz)


def castle_fortress():
    cone((0.0, 0.0, -0.05), 2.7, 2.15, 0.33, "earth", 28)
    z1 = 0.28
    lower = ring(2.0, 8, 0.0, 1, math.pi / 8)
    walled(lower, 0.4, (0, 0), z1, 0.16, "adobe", gates=(5,))
    steps((lower[5][0] * 1.45, lower[5][1] * 1.45), (lower[5][0] * 1.08, lower[5][1] * 1.08), 0.32, 0.0, z1, 3)
    cone((0.1, 0.15, z1 - 0.02), 1.3, 1.02, 0.42, "earth", 22)
    z2 = z1 + 0.4
    pts = [(-0.68, -0.6), (0.82, -0.6), (0.82, 0.9), (-0.68, 0.9)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        mud_wall(a + dd * 0.25, b - dd * 0.25, 0.62, (0.07, 0.15), z2, "brick", 0.32)
    for p in pts:
        tall_tower((p[0], p[1], z2), 0.25, 0.95, "brick", 1)
    portal((0.07, -0.6, z2), 0.55, 0.95, 0.0)
    top = tall_tower((0.2, 0.3, z2), 0.33, 1.55, "brick", 2, "dome")
    flag((0.2, 0.3, top - 0.05), 0.75)
    for p in pts:
        tugh((p[0], p[1], z2 + 1.25), 0.45)
    house((-1.1, 0.75, z1), 0.8, 0.32, 0.32, 0.9, "adobe")
    house((1.25, 0.4, z1), 0.7, 0.32, 0.3, -1.2, "adobe")
    house((-0.95, -1.05, z1), 0.6, 0.3, 0.28, 0.6, "adobe_dark")
    for a in (0.6, 1.4, 2.3, 3.4, 4.2):
        yurt((math.cos(a) * 2.45, math.sin(a) * 2.45, 0.0), 0.2, a + math.pi / 2)
    return finish("WorldCastle_khordan_fortress")


def castle_gate():
    for sx in (-1, 1):
        ridge((sx * 0.75, -0.15 * sx), (sx * 2.5, 0.5 * sx), 1.2, 0.45, 3 + sx, "earth")
        ridge((sx * 0.85, -0.12 * sx), (sx * 2.4, 0.45 * sx), 0.8, 1.15, 7 + sx, "rocky")
    portal((0.0, 0.0, 0.0), 0.8, 1.6, 0.0)
    for sx in (-1, 1):
        tall_tower((sx * 0.55, 0.0, 0.0), 0.27, 1.35, "brick", 2)
        prev = (sx * 0.8, 0.0)
        for k, (x, y, z) in enumerate(((1.15, 0.1, 0.18), (1.5, 0.22, 0.42), (1.85, 0.33, 0.65))):
            q = (sx * x, sx * y)
            mud_wall(prev, q, 0.4, (0.0, 1.0), z * 0.6, "brick", 0.24)
            prev = q
        bastion((sx * 1.9, sx * 0.34, 0.66), 0.17, 0.5, "brick")
    for sx in (-1, 1):
        box((sx * 0.72, 1.05, 0.22), (0.26, 1.3, 0.44), "adobe", 0.0)
    arcade((-0.62, 1.7), (0.62, 1.7), 0.44, (0.0, 1.05), 4)
    for x, y in ((0.25, 1.2), (-0.2, 1.35), (0.3, 0.75)):
        box((x, y, 0.07), (0.18, 0.13, 0.14), "felt_dark", 0.4)
    box((0.0, -1.5, 0.012), (0.55, 2.2, 0.024), "paving", 0.0)
    wagon((0.15, -1.9, 0.0), math.pi / 2)
    for sx in (-1, 1):
        tugh((sx * 0.55, -0.45, 0.0), 1.05)
        flag((sx * 0.55, 0.0, 1.62), 0.55)
    return finish("WorldCastle_khordan_gate")


def castle_wall():
    line = [(-2.75, -0.35), (-1.4, 0.05), (0.0, 0.18), (1.4, 0.05), (2.75, -0.35)]
    h = 0.42
    for a, b in zip(line, line[1:]):
        rampart(a, b, 0.95, h)
        aa, bb = Vector(a), Vector(b)
        d = (bb - aa).normalized()
        n = Vector((-d.y, d.x))
        ma, mb = aa - n * 0.72, bb - n * 0.72
        mid = (ma + mb) / 2
        if a == (0.0, 0.18) or b == (0.0, 0.18):
            pa = aa.lerp(bb, 0.2 if b == (0.0, 0.18) else 0.8)
            palisade(a if b == (0.0, 0.18) else (pa.x, pa.y), (pa.x, pa.y) if b == (0.0, 0.18) else b, 0.5, h)
        else:
            palisade(a, b, 0.5, h)
    for x, y in ((-2.05, -0.15), (-0.7, 0.13), (0.7, 0.13), (2.05, -0.15)):
        watch_tower((x, y, h), 0.42, 0.85)
    for sx in (-1, 1):
        watch_tower((sx * 0.32, 0.18, h), 0.36, 1.05)
    box((0.0, 0.18, h + 0.95), (0.3, 0.12, 0.08), "log_dark", 0.0)
    flag((-0.32, 0.18, h + 1.4), 0.6)
    flag((0.32, 0.18, h + 1.4), 0.6)
    for x in (-2.6, 2.6):
        beacon((x, 0.2, 0.0), 1.25)
    for x, y in ((-1.2, 1.15), (-0.55, 1.35), (0.55, 1.3), (1.2, 1.1)):
        yurt((x, y, 0.0), 0.22, 0.2)
    corral((0.0, 1.55, 0.0), 0.32)
    wagon((1.85, 1.0, 0.0), 0.3)
    return finish("WorldCastle_khordan_wall")


def castle_mountain():
    cone((0.0, 0.0, -0.05), 2.6, 1.6, 0.42, "earth", 24)
    for c, r, sc, sd in (((0.0, 0.0, 0.45), 1.0, (1.15, 1.0, 0.95), 1), ((0.85, -0.55, 0.3), 0.62, (1.0, 0.9, 1.1), 2),
                          ((-0.8, 0.5, 0.32), 0.68, (1.0, 1.1, 1.0), 3), ((0.35, 0.9, 0.3), 0.55, (1.1, 0.9, 0.9), 4),
                          ((-0.55, -0.75, 0.25), 0.5, (1.0, 1.0, 0.9), 5)):
        rock(c, r, sc, sd, "rocky")
    z = 1.28
    pts = [(-0.7, -0.45), (0.25, -0.75), (0.85, -0.05), (0.45, 0.7), (-0.5, 0.6)]
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        mud_wall(a + dd * 0.15, b - dd * 0.15, 0.4, (0.05, 0.0), z, "grey", 0.22)
    for p in pts:
        tall_tower((p[0], p[1], z), 0.15, 0.55, "grey", 1)
    top = tall_tower((0.05, 0.05, z), 0.26, 1.05, "grey", 2, "dome")
    flag((0.05, 0.05, top - 0.05), 0.6)
    steps((1.9, -1.3), (1.0, -0.75), 0.22, 0.0, 0.7, 5)
    yurt((-1.8, -1.2, 0.0), 0.2, 0.4)
    corral((-1.6, 1.5, 0.0), 0.28)
    return finish("WorldCastle_khordan_mountain")


def castle_watch():
    tx, ty = -0.55, -0.25
    top = tall_tower((tx, ty, 0.0), 0.36, 1.45, "grey", 2, "flat")
    cone((tx, ty, 1.45 + 0.09), 0.5, 0.5, 0.06, "plank", 12)
    for i in range(6):
        a = i / 6 * math.tau
        log((tx + math.cos(a) * 0.44, ty + math.sin(a) * 0.44, 1.6), (tx + math.cos(a) * 0.44, ty + math.sin(a) * 0.44, 1.95), 0.02, "log_dark", 5)
    pyramid((tx, ty, 1.95), 1.0, 0.42, "roof", 8)
    beacon((tx, ty, 2.37), 0.25)
    flag((tx + 0.3, ty, 1.6), 0.7)
    yard = [(tx - 0.85, ty - 0.75), (tx + 0.7, ty - 0.75), (tx + 0.7, ty + 0.8), (tx - 0.85, ty + 0.8)]
    for i in range(4):
        a, b = yard[i], yard[(i + 1) % 4]
        if i == 0:
            mud_wall(a, (tx - 0.2, ty - 0.75), 0.28, (tx, ty), 0.0, "grey", 0.16)
            mud_wall((tx + 0.15, ty - 0.75), b, 0.28, (tx, ty), 0.0, "grey", 0.16)
        else:
            mud_wall(a, b, 0.28, (tx, ty), 0.0, "grey", 0.16)
    house((tx + 0.35, ty + 0.5, 0.0), 0.5, 0.28, 0.26, 0.0, "adobe_dark")
    cx, cy = 1.1, 0.95
    rock((cx, cy, 0.0), 0.2, (1.0, 0.85, 4.2), 9, "grey")
    for i in range(9):
        a = i / 9 * math.tau
        rock((cx + math.cos(a) * 0.72, cy + math.sin(a) * 0.72, 0.0), 0.11, (0.9, 0.7, 3.0 + (i % 3) * 0.5), 20 + i, "grey")
    yurt((-1.75, 0.95, 0.0), 0.22, 0.6)
    yurt((-1.2, 1.55, 0.0), 0.2, 1.2)
    corral((0.6, -1.75, 0.0), 0.3)
    return finish("WorldCastle_khordan_watch")


def castle_stavka():
    cone((0.0, 0.0, 0.0), 0.98, 0.92, 0.14, "plank", 18)
    box((0.0, -1.05, 0.05), (0.42, 0.3, 0.1), "plank", 0.0)
    yurt((0.0, 0.0, 0.14), 0.62, 0.0, "gold", "felt")
    for k in range(6):
        a = k / 6 * math.tau + 0.52
        yurt((math.cos(a) * 1.35, math.sin(a) * 1.35, 0.0), 0.28, a + math.pi / 2, "turq", "felt")
    for k in range(9):
        x = -0.8 + k * 0.2
        tugh((x, -1.45 - abs(x) * 0.25, 0.0), 1.15 if k == 4 else 0.95)
    yurt_ring(12, 1.8, 2.2, [((0.0, -1.9), 0.75)], 23, (0.19, 0.24))
    n = 20
    for i in range(n):
        a = i / n * math.tau
        if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.35:
            continue
        wagon((math.cos(a) * 2.6, math.sin(a) * 2.6, 0.0), a + math.pi / 2)
    for sx in (-1, 1):
        tugh((sx * 0.45, -2.6, 0.0), 1.2)
    flag((0.0, 0.0, 0.8), 0.8)
    return finish("WorldCastle_khordan_stavka")


def village_caravan():
    sq = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    for i in range(4):
        a, b = Vector(sq[i]), Vector(sq[(i + 1) % 4])
        d = (b - a).normalized()
        if i == 0:
            arcade(a + d * 0.12, Vector((-0.42, -1.0)), 0.5, (0.0, 0.0), 2)
            arcade(Vector((0.42, -1.0)), b - d * 0.12, 0.5, (0.0, 0.0), 2)
        else:
            arcade(a + d * 0.12, b - d * 0.12, 0.5, (0.0, 0.0), 5)
    for p in sq:
        tall_tower((p[0], p[1], 0.0), 0.16, 0.72, "adobe", 1)
    portal((0.0, -1.0, 0.0), 0.75, 0.95, 0.0)
    flag((0.0, -1.0, 0.95), 0.6)
    dome((0.0, 0.15, 0.0), 0.24, 0.14)
    cone((0.45, -0.35, 0.0), 0.09, 0.09, 0.08, "adobe_dark", 10)
    for x, y, rz in ((-0.45, 0.4, 0.3), (-0.55, 0.1, 1.1), (0.5, 0.45, 0.7), (-0.3, -0.45, 0.2)):
        box((x, y, 0.07), (0.17, 0.12, 0.14), "felt_dark", rz)
    for x, y in ((1.6, -0.7), (1.75, 0.25), (-1.65, -0.35)):
        cone((x, y, 0.0), 0.2, 0.0, 0.3, "felt", 8)
    wagon((0.7, -1.7, 0.0), 0.2)
    wagon((-0.65, -1.75, 0.0), -0.3)
    for i in range(5):
        poplar((-1.6 + i * 0.36, 1.65, 0.0), 0.95)
    return finish("WorldVillage_khordan_caravan")


def village_camp():
    yurt_ring(6, 0.5, 1.35, [], 31, (0.2, 0.27))
    corral((1.75, -0.6, 0.0), 0.42, 12)
    corral((-1.6, 1.0, 0.0), 0.32, 10)
    wagon((0.2, -1.6, 0.0), 0.4)
    wagon((-0.6, -1.5, 0.0), 1.2)
    tugh((0.0, 0.0, 0.0), 1.0)
    flag((0.25, 0.2, 0.0), 1.15)
    return finish("WorldVillage_khordan_camp")


def village_farm():
    houses(7, 0.4, 1.25, [], 71, (0.0, 0.0), 0.1)
    cone((0.0, 0.0, 0.0), 0.12, 0.12, 0.12, "adobe_dark", 10)
    field((2.0, 0.3, 0.0), 1.1, 1.0, 0.2)
    field((-1.3, -2.0, 0.0), 1.0, 0.7, 0.9, "field_green")
    for i in range(5):
        poplar((-1.9 + i * 0.22, 1.2 - i * 0.12, 0.0), 0.85)
    flag((-0.35, 0.3, 0.0), 1.1)
    return finish("WorldVillage_khordan_village")


ALL = {"capital": capital, "large": large, "medium": medium, "fortress": castle_fortress, "gate": castle_gate, "wall": castle_wall, "mountain": castle_mountain, "watch": castle_watch, "stavka": castle_stavka, "camp": village_camp, "farm": village_farm, "caravan": village_caravan}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, len(o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
