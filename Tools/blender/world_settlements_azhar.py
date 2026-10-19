import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldAzhar"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())

M["sand"] = mat("env_sandstone", (0.85, 0.66, 0.43), 0.9)
M["sand_dark"] = mat("env_sandstone_dark", (0.68, 0.5, 0.32), 0.9)
M["ivory"] = mat("env_ivory", (0.93, 0.86, 0.71), 0.85)
M["green"] = mat("env_tile_green", (0.05, 0.36, 0.2), 0.35)
M["palm"] = mat("env_palm", (0.24, 0.46, 0.17), 0.9)
M["cypress"] = mat("env_cypress", (0.1, 0.27, 0.13), 0.9)
M["trunk"] = mat("env_palm_trunk", (0.47, 0.35, 0.22), 0.9)
M["paving"] = mat("env_paving", (0.78, 0.72, 0.6), 0.9)
M["hedge"] = mat("env_hedge", (0.2, 0.38, 0.15), 0.9)
M["cloth"] = mat("env_felt", (0.92, 0.88, 0.78), 0.95)
M["rocky"] = mat("env_rock_hill", (0.55, 0.45, 0.34), 1.0)
mat("env_flag", (0.06, 0.34, 0.2), 0.8)


def local(c, rz):
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0))
    return lambda x, y, z=0.0: base + rot @ Vector((x, y, z))


def box_m(mx, m):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=mx)
    return put("box", bm, m, False)


def palm(c, h, seed=0):
    rr = random.Random(seed)
    x, y, z = c
    lean = Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), 0.0)) * h * 0.08
    top = Vector((x, y, z + h)) + lean
    log((x, y, z), (x + lean.x * 0.5, y + lean.y * 0.5, z + h * 0.5), h * 0.035, "trunk", 6)
    log((x + lean.x * 0.5, y + lean.y * 0.5, z + h * 0.5), top, h * 0.03, "trunk", 6)
    for k in range(7):
        a = k / 7 * math.tau + rr.uniform(-0.2, 0.2)
        mx = Matrix.Translation(top) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(0.5, 4, "Y") @ Matrix.Translation((h * 0.2, 0, 0)) @ Matrix.Diagonal((h * 0.42, h * 0.09, h * 0.015, 1.0))
        box_m(mx, "palm")


def cypress(c, h):
    x, y, z = c
    lathe([(0.0, 0.0), (0.12, 0.03), (0.15, 0.3), (0.1, 0.75), (0.0, 1.0)], (x, y, z), h, "cypress", 8)


def tent(c, r, m="cloth"):
    x, y, z = c
    cone((x, y, z), r, r, r * 0.6, m, 10)
    cone((x, y, z + r * 0.6), r * 1.05, 0.0, r * 0.8, m, 10)
    log((x, y, z + r * 1.3), (x, y, z + r * 1.7), r * 0.05, "log_dark", 5)


DOME = [(0.0, 0.0), (1.0, 0.0), (1.04, 0.25), (0.98, 0.56), (0.8, 0.86), (0.5, 1.1), (0.16, 1.28), (0.0, 1.34)]


def dome(c, r, drum_h, m="green", drum="ivory"):
    x, y, z = c
    cone((x, y, z), r * 1.02, r * 1.02, drum_h, drum, 16)
    for i in range(8):
        a = i / 8 * math.tau
        box((x + math.cos(a) * r * 1.03, y + math.sin(a) * r * 1.03, z + drum_h * 0.55), (r * 0.12, r * 0.1, drum_h * 0.5), "window", a)
    cone((x, y, z + drum_h * 0.92), r * 1.06, r * 1.06, drum_h * 0.1, "green" if m != "green" else "gold", 16)
    lathe(DOME, (x, y, z + drum_h), r, m, 16)
    top = z + drum_h + r * 1.34
    box((x, y, top + r * 0.2), (r * 0.06, r * 0.06, r * 0.4), "gold")
    cone((x, y, top + r * 0.42), r * 0.1, r * 0.1, r * 0.04, "gold", 8)
    return top + r * 0.45


def minaret(c, r, h):
    x, y, z = c
    cone((x, y, z), r * 1.3, r * 1.3, h * 0.12, "sand", 8, math.pi / 8, False)
    cone((x, y, z + h * 0.12), r, r * 0.86, h * 0.68, "ivory", 8, math.pi / 8, False)
    for t in (0.35, 0.6):
        cone((x, y, z + h * t), r * (1 - 0.14 * t) * 1.03, r * (1 - 0.14 * t) * 1.03, h * 0.035, "green", 8, math.pi / 8, False)
    cone((x, y, z + h * 0.8), r * 1.35, r * 1.35, h * 0.04, "sand", 8, math.pi / 8, False)
    cone((x, y, z + h * 0.84), r * 0.75, r * 0.7, h * 0.12, "ivory", 8, math.pi / 8, False)
    lathe(DOME, (x, y, z + h * 0.96), r * 0.72, "green", 10)
    box((x, y, z + h * 0.96 + r * 1.1), (r * 0.08, r * 0.08, r * 0.6), "gold")
    return z + h + r * 1.3


def iwan(c, w, h, rz, m="sand"):
    L = local(c, rz)
    box(L(0, 0, h / 2), (w, w * 0.32, h), m, rz)
    box(L(0, -w * 0.165, h * 0.4), (w * 0.52, 0.02, h * 0.62), "window", rz)
    pyramid(L(0, -w * 0.165, h * 0.71), w * 0.52, h * 0.14, "window", 4, rz)
    for sx in (-1, 1):
        box(L(sx * w * 0.36, -w * 0.168, h * 0.48), (w * 0.08, 0.02, h * 0.9), "green", rz)
    box(L(0, -w * 0.168, h * 0.93), (w * 0.8, 0.02, h * 0.08), "green", rz)
    for k in range(5):
        box(L(-w * 0.4 + k * w * 0.2, 0, h + 0.05), (w * 0.1, w * 0.3, 0.1), m, rz)


def wall(a, b, h, center, z0=0.0, m="sand", t=0.28):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d, n = outward(a, b, center)
    rz = math.atan2(d.y, d.x)
    length = (b - a).length
    mid = (a + b) / 2
    box((mid.x, mid.y, z0 + h / 2), (length, t, h), m, rz)
    box((mid.x + n.x * t * 0.48, mid.y + n.y * t * 0.48, z0 + h * 0.86), (length, 0.03, 0.04), "green", rz)
    k = max(2, int(length / 0.2))
    for i in range(k):
        q = a.lerp(b, (i + 0.5) / k) + n * (t / 2 - 0.05)
        box((q.x, q.y, z0 + h + 0.05), (0.1, 0.08, 0.1), m, rz)
        box((q.x, q.y, z0 + h + 0.13), (0.05, 0.08, 0.06), m, rz)


def tower(c, r, h, m="sand", cap="crenel"):
    x, y, z = c
    cone((x, y, z), r * 1.12, r * 0.95, h, m, 12)
    cone((x, y, z + h * 0.7), r * 1.02, r * 1.02, h * 0.05, "green", 12)
    for i in range(2):
        a = i * 2.6 + 0.5
        box((x + math.cos(a) * r, y + math.sin(a) * r, z + h * 0.5), (r * 0.12, r * 0.12, r * 0.3), "window", a)
    cone((x, y, z + h), r * 1.06, r * 1.06, r * 0.2, m, 12)
    top = z + h + r * 0.2
    if cap == "dome":
        lathe(DOME, (x, y, top), r * 0.8, "green", 12)
        return top + r * 1.07
    for i in range(10):
        a = i / 10 * math.tau
        box((x + math.cos(a) * r, y + math.sin(a) * r, top + r * 0.1), (r * 0.2, r * 0.16, r * 0.2), m, a)
    return top + r * 0.2


def ring_walls(pts, h, center, z0, tr, m, gates=()):
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        wall(a + dd * tr * 0.8, b - dd * tr * 0.8, h, center, z0, m)
    for i, p in enumerate(pts):
        if i in gates:
            prev, nxt = Vector(pts[i - 1]), Vector(pts[(i + 1) % len(pts)])
            t = (nxt - prev).normalized()
            n = Vector((-t.y, t.x))
            if n.dot(Vector(p) - Vector(center)) < 0:
                n = -n
            iwan((p[0], p[1], z0), tr * 3.4, h * 1.75, math.atan2(n.y, n.x) - math.pi / 2, m)
        else:
            tower((p[0], p[1], z0), tr, h * 1.3, m)


def house(c, w, d, h, rz, m="sand", dome_top=False, wind=False):
    L = local(c, rz)
    box(L(0, 0, h / 2), (w, d, h), m, rz)
    box(L(0, 0, h + 0.03), (w * 1.02, d * 1.02, 0.06), "sand_dark" if m != "sand_dark" else "sand", rz)
    box(L(0, -d / 2 - 0.005, h * 0.3), (w * 0.18, 0.02, h * 0.5), "log_dark", rz)
    for x in (-0.28, 0.28):
        box(L(x * w, -d / 2 - 0.005, h * 0.68), (w * 0.1, 0.02, h * 0.14), "window", rz)
    if dome_top:
        q = L(w * 0.2, 0)
        lathe([(0.0, 0.0), (1.0, 0.0), (0.92, 0.45), (0.6, 0.85), (0.0, 1.0)], (q.x, q.y, q.z + h), min(w, d) * 0.3, "ivory", 10)
    if wind:
        q = L(-w * 0.28, d * 0.15)
        box((q.x, q.y, q.z + h + 0.12), (0.1, 0.1, 0.24), m, rz)
        for k in range(4):
            a = rz + k * math.pi / 2
            box((q.x + math.cos(a) * 0.05, q.y + math.sin(a) * 0.05, q.z + h + 0.18), (0.03, 0.03, 0.08), "window", a)


house = grouped(house)


def houses(n, rmin, rmax, avoid, seed, center=(0.0, 0.0), extra=0.25):
    rr = random.Random(seed)
    placed = []
    tries = 0
    while len(placed) < n and tries < 5000:
        tries += 1
        a = rr.uniform(0, math.tau)
        r = rr.uniform(rmin, rmax)
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r
        if any(math.dist((x, y), q) < qr for q, qr in avoid) or any(math.dist((x, y), p) < 0.48 for p in placed):
            continue
        placed.append((x, y))
        house((x, y, 0.0), rr.uniform(0.3, 0.46), rr.uniform(0.26, 0.4), rr.uniform(0.22, 0.4), a + rr.uniform(-0.15, 0.15),
              rr.choice(("sand", "sand", "ivory", "sand_dark")), rr.random() < extra * 0.5, rr.random() < extra)
    return placed


def canal(a, b, w=0.12):
    a, b = Vector(a), Vector(b)
    d = b - a
    mid = (a + b) / 2
    box((mid.x, mid.y, 0.01), (d.length, w + 0.06, 0.02), "paving", math.atan2(d.y, d.x))


def garden(c, s, rz=0.0):
    L = local(c, rz)
    q = L(0, 0)
    box((q.x, q.y, 0.012), (s, s, 0.024), "paving", rz)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = L(sx * s * 0.25, sy * s * 0.25)
            box((p.x, p.y, 0.05), (s * 0.4, s * 0.4, 0.08), "hedge", rz)
            cypress(L(sx * s * 0.45, sy * s * 0.45), s * 0.55)
    canal(L(-s * 0.5, 0), L(s * 0.5, 0), s * 0.06)
    canal(L(0, -s * 0.5), L(0, s * 0.5), s * 0.06)
    cone((q.x, q.y, 0.0), s * 0.09, s * 0.09, 0.06, "ivory", 12)


def mosque(c, s, rz):
    L = local(c, rz)
    box(L(0, 0, 0.32 * s), (1.2 * s, 1.0 * s, 0.64 * s), "ivory", rz)
    top = dome(L(0, 0.1 * s, 0.64 * s), 0.38 * s, 0.28 * s, "green")
    for sx in (-1, 1):
        q = L(sx * 0.42 * s, -0.25 * s, 0.64 * s)
        dome((q.x, q.y, q.z), 0.14 * s, 0.1 * s, "green")
    iwan(L(0, -0.58 * s), 0.6 * s, 1.0 * s, rz, "sand")
    q = L(0.68 * s, -0.55 * s)
    minaret((q.x, q.y, q.z), 0.07 * s, 1.75 * s)
    return top


def palace(c, s, rz, gold=True):
    L = local(c, rz)
    box(L(0, 0, 0.3 * s), (1.5 * s, 1.1 * s, 0.6 * s), "ivory", rz)
    box(L(0, 0, 0.62 * s), (1.54 * s, 1.14 * s, 0.04 * s), "green", rz)
    top = dome(L(0, 0.1 * s, 0.62 * s), 0.42 * s, 0.34 * s, "gold" if gold else "green")
    iwan(L(0, -0.6 * s), 0.75 * s, 1.15 * s, rz, "sand")
    for sx in (-1, 1):
        q = L(sx * 0.75 * s, 0.55 * s)
        tower((q.x, q.y, q.z), 0.16 * s, 0.9 * s, "ivory", "dome")
    return top


def library(c, s, rz):
    L = local(c, rz)
    box(L(0, 0, 0.25 * s), (1.6 * s, 0.55 * s, 0.5 * s), "ivory", rz)
    for k in range(3):
        q = L((k - 1) * 0.5 * s, 0, 0.5 * s)
        dome((q.x, q.y, q.z), 0.17 * s, 0.1 * s, "green")
    for k in range(6):
        q = L((k - 2.5) * 0.26 * s, -0.28 * s, 0.22 * s)
        box((q.x, q.y, q.z), (0.1 * s, 0.02, 0.26 * s), "window", rz)


def capital():
    outer = ring(3.85, 12, 0.0, 2, 0.13)
    ring_walls(outer, 0.62, (0, 0), 0.0, 0.2, "sand", gates=(0, 6))
    inner = ring(2.25, 8, 0.0, 3, 0.39)
    ring_walls(inner, 0.7, (0, 0), 0.0, 0.18, "ivory", gates=(1, 5))
    cone((0.15, 0.35, -0.02), 1.1, 0.95, 0.24, "sand_dark", 24)
    palace((0.15, 0.4, 0.22), 0.85, 0.0)
    library((-0.95, -0.65, 0.0), 0.75, 0.6)
    mosque((0.95, -0.85, 0.0), 0.75, -0.5)
    garden((-0.9, 0.95), 0.75, 0.3)
    canal((-3.7, 0.15), (3.7, -0.15))
    avoid = [((0.15, 0.4), 1.25), ((-0.95, -0.65), 0.8), ((0.95, -0.85), 0.75), ((-0.9, 0.95), 0.6)]
    houses(14, 0.7, 2.0, avoid, 11)
    houses(26, 2.55, 3.5, [], 13)
    for k in range(10):
        a = k / 10 * math.tau + 0.3
        palm((math.cos(a) * 2.42, math.sin(a) * 2.42, 0.0), 0.75, k)
    flag((0.15 + 0.75 * 0.85 * 0.0, 0.4, 2.0), 0.7)
    return finish("WorldTown_azhar_capital")


def large():
    pts = ring(2.95, 9, 0.03, 5, 0.2)
    ring_walls(pts, 0.6, (0, 0), 0.0, 0.18, "sand", gates=(0, 5))
    mosque((0.3, 0.35, 0.0), 0.8, 0.2)
    tower((-0.85, 0.85, 0.0), 0.3, 1.2, "ivory", "dome")
    flag((-0.85, 0.85, 1.6), 0.6)
    garden((-0.9, -0.6), 0.7, -0.3)
    canal((-2.6, 1.0), (2.6, 0.75))
    houses(24, 0.55, 2.5, [((0.3, 0.35), 0.95), ((-0.85, 0.85), 0.45), ((-0.9, -0.6), 0.55)], 21)
    for k in range(5):
        palm((3.2 + (k % 2) * 0.2, -0.8 + k * 0.4, 0.0), 0.7, k + 30)
    return finish("WorldTown_azhar_large")


def medium():
    pts = ring(1.9, 7, 0.05, 6, 0.4)
    ring_walls(pts, 0.5, (0, 0), 0.0, 0.16, "sand", gates=(0,))
    mosque((0.2, 0.2, 0.0), 0.62, 0.4)
    flag((-0.7, -0.4, 0.0), 1.2)
    houses(10, 0.45, 1.45, [((0.2, 0.2), 0.75)], 31)
    houses(8, 2.25, 2.9, [((2.3, 1.5), 0.85)], 33)
    field((2.3, 1.5, 0.0), 1.0, 0.7, 0.5, "field_green")
    canal((1.5, 2.2), (3.0, 0.6))
    for k in range(6):
        palm((-2.4 + k * 0.28, -2.0 + (k % 2) * 0.25, 0.0), 0.7, k + 40)
    return finish("WorldTown_azhar_medium")


def rock(c, r, sc=(1.0, 1.0, 1.0), seed=0, m="rocky"):
    rr = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)))
    for v in bm.verts:
        v.co += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-0.5, 1.0))) * r * 0.16
    put("rock", bm, m, False)


def castle_desert():
    cone((0.0, 0.0, -0.05), 2.3, 1.9, 0.3, "sand_dark", 24)
    z = 0.25
    pts = [(-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.25, b - dd * 0.25, 0.85, (0, 0), z, "sand", 0.32)
    for p in pts:
        tower((p[0], p[1], z), 0.27, 1.15, "sand")
    iwan((0.0, -1.3, z), 0.7, 1.35, 0.0, "sand")
    box((0.2, 0.25, z + 0.6), (0.85, 0.85, 1.2), "sand_dark", 0.0)
    top = dome((0.2, 0.25, z + 1.2), 0.3, 0.2, "green")
    flag((0.6, 0.65, z + 1.2), 0.65)
    cone((-0.6, -0.5, z), 0.12, 0.12, 0.1, "ivory", 10)
    for x, y in ((-0.75, 0.55), (-0.55, 0.85)):
        palm((x, y, z), 0.65, int(x * 10))
    for x, y in ((-1.9, -0.6), (-1.8, 0.4), (1.95, -0.2)):
        tent((x, y, 0.0), 0.17)
    return finish("WorldCastle_azhar_desert")


def castle_rock():
    canal((-2.3, -1.55), (2.3, -1.15), 0.5)
    for c, r, sc, sd in (((0.0, 0.2, 0.3), 1.1, (1.2, 1.0, 0.95), 1), ((0.9, -0.3, 0.2), 0.7, (1.0, 0.9, 1.0), 2),
                          ((-0.9, 0.6, 0.2), 0.75, (1.0, 1.0, 0.9), 3), ((-0.3, -0.6, 0.15), 0.6, (1.1, 0.9, 0.9), 4)):
        rock(c, r, sc, sd)
    z = 1.15
    pts = [(-0.75, -0.35), (0.35, -0.6), (0.85, 0.15), (0.3, 0.8), (-0.65, 0.6)]
    for i in range(len(pts)):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % len(pts)])
        dd = (b - a).normalized()
        wall(a + dd * 0.14, b - dd * 0.14, 0.45, (0.0, 0.1), z, "sand", 0.22)
    for p in pts:
        tower((p[0], p[1], z), 0.15, 0.6, "sand")
    top = tower((0.05, 0.15, z), 0.27, 1.05, "ivory", "dome")
    flag((0.05, 0.15, top - 0.05), 0.6)
    for k in range(4):
        box((1.5 - k * 0.25, -0.9 + k * 0.28, 0.08 + k * 0.22), (0.3, 0.22, 0.16 + k * 0.44), "sand_dark", 0.6)
    return finish("WorldCastle_azhar_rock")


def castle_frontier():
    outer = ring(2.15, 8, 0.0, 4, math.pi / 8)
    ring_walls(outer, 0.42, (0, 0), 0.0, 0.15, "sand_dark", gates=(6,))
    inner = [(-0.9, -0.85), (0.9, -0.85), (0.9, 0.9), (-0.9, 0.9)]
    for i in range(4):
        a, b = Vector(inner[i]), Vector(inner[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.24, b - dd * 0.24, 0.8, (0, 0), 0.0, "sand", 0.3)
    for p in inner:
        tower((p[0], p[1], 0.0), 0.25, 1.1, "sand")
    iwan((0.0, -0.85, 0.0), 0.6, 1.25, 0.0, "sand")
    top = tower((0.1, 0.15, 0.0), 0.32, 1.65, "ivory", "dome")
    flag((0.1, 0.15, top - 0.05), 0.7)
    for k in range(6):
        a = k / 6 * math.tau + 0.4
        tent((math.cos(a) * 1.45, math.sin(a) * 1.45, 0.0), 0.15, "cloth" if k % 2 else "hedge")
    for k in range(4):
        a = k / 4 * math.tau + 0.8
        flag((math.cos(a) * 1.1, math.sin(a) * 1.1, 0.0), 1.2, 0.4)
    return finish("WorldCastle_azhar_frontier")


def castle_tower():
    cone((0.0, 0.0, -0.05), 1.9, 0.9, 0.55, "rocky", 18)
    rock((0.2, 0.1, 0.45), 0.7, (1.1, 1.0, 0.7), 5)
    z = 0.85
    top = tower((0.1, 0.1, z), 0.36, 1.7, "sand")
    flag((0.1, 0.1, top - 0.05), 0.7)
    pts = [(-0.55, -0.45), (0.7, -0.45), (0.7, 0.6), (-0.55, 0.6)]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        wall(a, b, 0.3, (0.1, 0.1), z - 0.2, "sand_dark", 0.16)
    house((-1.3, -0.9, 0.0), 0.42, 0.34, 0.3, 0.4, "sand_dark")
    house((-1.55, 0.4, 0.0), 0.4, 0.32, 0.28, 1.1, "sand")
    cypress((1.4, -0.9, 0.0), 0.75)
    cypress((1.6, -0.6, 0.0), 0.65)
    return finish("WorldCastle_azhar_tower")


def castle_palace():
    pts = [(-1.75, -1.6), (1.75, -1.6), (1.75, 1.7), (-1.75, 1.7)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        if i == 0:
            wall(a + dd * 0.2, Vector((-0.45, -1.6)), 0.6, (0, 0), 0.0, "ivory", 0.24)
            wall(Vector((0.45, -1.6)), b - dd * 0.2, 0.6, (0, 0), 0.0, "ivory", 0.24)
        else:
            wall(a + dd * 0.2, b - dd * 0.2, 0.6, (0, 0), 0.0, "ivory", 0.24)
    for p in pts:
        tower((p[0], p[1], 0.0), 0.22, 0.85, "ivory", "dome")
    iwan((0.0, -1.6, 0.0), 0.75, 1.1, 0.0, "sand")
    flag((0.0, -1.6, 1.15), 0.6)
    palace((0.0, 0.85, 0.0), 0.8, 0.0)
    garden((0.0, -0.45), 1.6, 0.0)
    dome((1.1, 1.05, 0.0), 0.2, 0.25, "green", "sand")
    return finish("WorldCastle_azhar_palace")


def castle_ribat():
    pts = [(-1.15, -0.95), (1.15, -0.95), (1.15, 1.2), (-1.15, 1.2)]
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        dd = (b - a).normalized()
        wall(a + dd * 0.22, b - dd * 0.22, 0.7, (0, 0.1), 0.0, "sand", 0.3)
    for p in pts:
        tower((p[0], p[1], 0.0), 0.24, 0.95, "sand")
    iwan((0.0, 1.2, 0.0), 0.6, 1.05, math.pi, "sand")
    top = minaret((1.15, -0.95, 0.95), 0.12, 1.3)
    flag((-1.15, -0.95, 1.1), 0.6)
    dome((-0.2, 0.25, 0.0), 0.24, 0.35, "green")
    for x, y in ((-0.9, -1.75), (0.9, -1.8)):
        tent((x, y, 0.0), 0.2)
    prop("Cart", (0.0, -1.55, 0.0), 0.2, 1.0)
    prop("Barrel", (0.35, -1.45, 0.0), 0.0, 1.0)
    return finish("WorldCastle_azhar_ribat")


def village_oasis():
    cone((0.0, 0.0, 0.0), 0.68, 0.62, 0.03, "paving", 20)
    prop("Well", (0.0, 0.0, 0.03), 0.0, 1.2)
    prop("MarketStand_1", (0.4, -0.25, 0.03), 0.5, 0.9)
    for k in range(9):
        a = k / 9 * math.tau
        palm((math.cos(a) * 0.82, math.sin(a) * 0.7, 0.0), random.Random(k).uniform(0.7, 0.95), k)
    houses(5, 1.25, 2.0, [], 51, (0.0, 0.0), 0.3)
    for x, y in ((1.8, 0.9), (-1.9, -0.6), (0.3, -1.95)):
        tent((x, y, 0.0), 0.17)
    flag((0.95, -0.95, 0.0), 1.15)
    return finish("WorldVillage_azhar_oasis")


def village_farm():
    houses(7, 0.4, 1.25, [], 61, (0.0, 0.0), 0.3)
    dome((0.0, 0.0, 0.0), 0.16, 0.22, "green", "ivory")
    field((2.0, 0.35, 0.0), 1.1, 1.0, 0.2, "field_green")
    field((-1.35, -2.0, 0.0), 1.0, 0.7, 0.9)
    canal((1.4, -0.4), (1.4, 1.6))
    canal((-2.4, -1.4), (-0.3, -1.4))
    prop("Cart", (0.9, -0.8, 0.0), 0.6, 1.0)
    prop("Hay", (1.1, -1.05, 0.0), 0.2, 1.0)
    for k in range(4):
        palm((-1.9 + k * 0.3, 1.3 + (k % 2) * 0.2, 0.0), 0.75, k + 70)
    for k in range(3):
        cypress((0.9 + k * 0.2, -1.6, 0.0), 0.7)
    flag((-0.4, 0.35, 0.0), 1.1)
    return finish("WorldVillage_azhar_farm")


def village_coast():
    box((0.0, -1.0, 0.012), (3.9, 0.35, 0.024), "paving", 0.0)
    for k in range(6):
        house((-1.6 + k * 0.62, -0.4 + (k % 2) * 0.35, 0.0), 0.4, 0.32, 0.28, 0.0, "ivory" if k % 2 else "sand")
    prop("MarketStand_1", (-1.1, -1.05, 0.0), 0.0, 1.0)
    prop("MarketStand_2", (0.2, -1.0, 0.0), 0.0, 1.0)
    prop("Cart", (1.5, -1.1, 0.0), 0.3, 1.0)
    for x in (-0.35, 0.65):
        prop("Barrel", (x, -1.2, 0.0), 0.0, 1.0)
    for k in range(4):
        palm((-1.2 + k * 0.8, -1.75, 0.0), 0.75, k + 90)
    for x in (-0.5, 0.9):
        log((x, -1.05, 0.0), (x, -1.05, 0.35), 0.012, "log_dark", 5)
        box((x + 0.15, -1.05, 0.3), (0.3, 0.01, 0.12), "cloth", 0.0)
    for k in range(3):
        palm((-2.2 + k * 0.35, 0.9, 0.0), 0.75, k + 80)
    flag((1.9, 0.4, 0.0), 1.1)
    return finish("WorldVillage_azhar_coast")


def village_hill():
    cone((0.0, 0.0, -0.05), 1.8, 1.2, 0.35, "rocky", 18)
    cone((0.1, 0.1, 0.25), 1.15, 0.7, 0.32, "sand_dark", 16)
    rr = random.Random(91)
    for k in range(6):
        a = k / 6 * math.tau + 0.3
        r = 1.35 if k % 2 else 0.95
        z = 0.3 if r > 1.2 else 0.55
        house((math.cos(a) * r, math.sin(a) * r, z), 0.38, 0.32, 0.3, a + math.pi / 2, rr.choice(("sand", "sand_dark")))
    top = tower((0.15, 0.15, 0.57), 0.2, 0.75, "sand")
    flag((0.15, 0.15, top - 0.05), 0.55)
    for k in range(4):
        cypress((-1.9 + k * 0.25, -1.4, 0.0), 0.65)
    return finish("WorldVillage_azhar_hill")


ALL = {"capital": capital, "large": large, "medium": medium, "desert": castle_desert, "rock": castle_rock, "frontier": castle_frontier, "tower": castle_tower, "palace": castle_palace, "ribat": castle_ribat, "oasis": village_oasis, "farm": village_farm, "coast": village_coast, "hill": village_hill}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, len(o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
