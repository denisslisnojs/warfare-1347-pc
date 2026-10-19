import bpy, math, os, random
from mathutils import Vector

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
SRC = os.path.join(ROOT, "Tools", "blender", "env_props.py")
OUT = os.path.join(ROOT, "Assets", "Art", "Environment", "World")
os.makedirs(OUT, exist_ok=True)

code = open(SRC, encoding="utf-8").read().split("props = [")[0].replace('"Environment"', '"WorldSettlements"')
ns = {}
exec(compile(code, SRC, "exec"), ns)
mat, box, cyl, sphere, prism, gable, join = ns["mat"], ns["box"], ns["cyl"], ns["sphere"], ns["prism"], ns["gable"], ns["join"]
M = ns["M"]
M["roof_red"] = mat("env_roof_red", (0.62, 0.26, 0.18))
M["roof_slate"] = mat("env_roof_slate", (0.32, 0.36, 0.42))
M["flag"] = mat("env_flag", (0.15, 0.3, 0.8))
M["field"] = mat("env_field", (0.78, 0.66, 0.34), 0.95)
M["wall_light"] = mat("env_wall_light", (0.82, 0.8, 0.74), 0.9)


def bake(o, loc, rotz):
    o.location = loc
    o.rotation_euler = (0, 0, rotz)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def mini_house(x, y, s, rot, roof="roof_red", rnd=None):
    body = box((0, 0, 0.35 * s), (1.0 * s, 0.8 * s, 0.7 * s), "wall", 0.03 * s)
    top = prism("r", 1.0 * s, 0.8 * s, 0.55 * s, 0.12 * s, 0.1 * s, roof, 0.68 * s)
    for o in (body, top):
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return [bake(body, (x, y, 0), rot), bake(top, (x, y, 0), rot)]


def flag(x, y, h):
    return [cyl((x, y, 0), (x, y, h), 0.04, 0.035, "wood", 8), box((x + 0.32, y, h - 0.25), (0.6, 0.04, 0.4), "flag", 0.01)]


def tower(x, y, r, h, roof="roof_slate"):
    return [cyl((x, y, 0), (x, y, h), r, r * 0.95, "wall_light", 16, bevel=0.03), cyl((x, y, h), (x, y, h + r * 1.6), r * 1.18, 0.02, roof, 16)]


def wall_ring(r, h, n, gate=True):
    p = []
    for i in range(n):
        a0, a1 = i / n * math.tau, (i + 1) / n * math.tau
        a, b = Vector((math.cos(a0) * r, math.sin(a0) * r, 0)), Vector((math.cos(a1) * r, math.sin(a1) * r, 0))
        mid = (a + b) / 2
        length = (b - a).length
        o = box((0, 0, h / 2), (length, 0.25, h), "wall_light", 0.03)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        p.append(bake(o, (mid.x, mid.y, 0), math.atan2(b.y - a.y, b.x - a.x)))
        p += tower(a.x, a.y, 0.32, h * 1.45)
    return p


def town():
    rnd = random.Random(11)
    p = wall_ring(3.2, 0.9, 7)
    for i in range(16):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.6, 2.5)
        p += mini_house(math.cos(a) * r, math.sin(a) * r, rnd.uniform(0.7, 1.0), rnd.uniform(0, math.tau), "roof_red" if i % 3 else "roof_slate")
    p.append(box((0.3, -0.2, 0.7), (1.6, 0.8, 1.4), "wall_light", 0.04))
    p.append(prism("nave", 1.6, 0.8, 0.6, 0.1, 0.1, "roof_slate", 1.4))
    p += tower(-0.65, -0.2, 0.3, 2.3)
    p += flag(-0.65, -0.2, 3.6)
    return join("WorldTown", p)


def castle():
    p = []
    for x, y in ((-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)):
        p += tower(x, y, 0.38, 1.6)
    for (ax, ay), (bx, by) in (((-1.3, -1.3), (1.3, -1.3)), ((1.3, -1.3), (1.3, 1.3)), ((1.3, 1.3), (-1.3, 1.3)), ((-1.3, 1.3), (-1.3, -1.3))):
        mx, my = (ax + bx) / 2, (ay + by) / 2
        o = box((mx, my, 0.55), (abs(bx - ax) + 0.25, abs(by - ay) + 0.25, 1.1), "wall_light", 0.03)
        p.append(o)
    p.append(box((0.2, 0.2, 1.2), (1.2, 1.2, 2.4), "wall_light", 0.05))
    for x, y in ((-0.3, -0.3), (0.7, -0.3), (0.7, 0.7), (-0.3, 0.7)):
        p.append(box((x, y, 2.5), (0.25, 0.25, 0.25), "wall_light", 0.02))
    p += flag(0.2, 0.2, 3.6)
    return join("WorldCastle", p)


def village():
    rnd = random.Random(5)
    p = []
    for i in range(5):
        a = i / 5 * math.tau + rnd.uniform(-0.3, 0.3)
        r = rnd.uniform(0.6, 1.3)
        p += mini_house(math.cos(a) * r, math.sin(a) * r, rnd.uniform(0.6, 0.85), rnd.uniform(0, math.tau), "thatch")
    f = box((2.0, 0.4, 0.03), (1.6, 1.2, 0.06), "field", 0.0)
    p.append(f)
    p.append(sphere((1.7, -0.9, 0.0), 0.35, "hay", (1, 1, 1.3), 12))
    p += flag(0.1, 0.1, 1.6)
    return join("WorldVillage", p)


for o, name in ((town(), "WorldTown.fbx"), (castle(), "WorldCastle.fbx"), (village(), "WorldVillage.fbx")):
    ns["export"](o, os.path.join(OUT, name))
print("ok")
