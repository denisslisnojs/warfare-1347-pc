import bpy, bmesh, math, os, random, sys
from mathutils import Vector, Matrix

SCENE = "WorldVillagePack"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())
PACKKIT = os.path.join(os.path.dirname(KIT), "world_pack_kit.py")
exec(compile(open(PACKKIT, encoding="utf-8").read(), PACKKIT, "exec"), globals())


def tree(c, h):
    x, y = c
    log((x, y, 0.0), (x, y, h * 0.5), h * 0.05, "log_dark", 5)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=h * 0.33, matrix=Matrix.Translation((x, y, h * 0.66)))
    for v in bm.verts:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 1))) * h * 0.05
    put("tree", bm, "leaf", False)


def village():
    building("Bell_Tower", (0.1, 0.2, 0.0), 0.35, 1.3, "slate")
    houses = [
        ("House_1", (-1.3, 0.75), 2.2, "tile"), ("House_2", (1.2, 1.25), 3.6, "tile"),
        ("Inn", (-0.2, -1.4), 0.1, "tile"), ("House_2", (1.65, -0.35), 4.9, "slate"),
        ("Blacksmith", (-1.75, -0.6), 1.3, "tile"), ("House_1", (0.1, 1.85), 3.3, "slate"),
        ("Stable", (1.45, -1.65), 5.6, "tile"), ("House_2", (-1.0, 1.9), 2.6, "tile"),
    ]
    rr = random.Random(61)
    for name, (x, y), rz, roof in houses:
        building(name, (x, y, 0.0), rz + rr.uniform(-0.15, 0.15), rr.uniform(0.92, 1.05), roof)
    prop("Well", (0.7, -0.45, 0.0), 0.4, 1.0)
    prop("Cart", (-0.75, -0.35, 0.0), 2.0, 1.0)
    prop("MarketStand_1", (0.3, -0.75, 0.0), 0.1, 1.0)
    field((2.75, 0.55, 0.0), 1.1, 1.0, 0.25)
    field((-1.4, -2.45, 0.0), 1.0, 0.7, 0.9, "field_green")
    for x, y in ((2.5, -0.85), (2.8, -0.6)):
        haystack((x, y), 0.9)
    prop("Hay", (2.35, -1.15, 0.0), 0.5, 1.0)
    for i in range(5):
        a = rr.uniform(0, math.tau)
        r = rr.uniform(2.4, 2.8)
        tree((math.cos(a) * r, math.sin(a) * r), rr.uniform(0.6, 0.8))
    flag((-0.5, 0.55, 0.0), 1.4)
    return finish("WorldVillage_vallerois_village")


def vines(c, w, d, rz, rows=6):
    rot = Matrix.Rotation(rz, 3, "Z")
    base = Vector((c[0], c[1], 0.0))
    box(base + Vector((0, 0, 0.015)), (w, d, 0.03), "soil", rz)
    for i in range(rows):
        y = -d / 2 + (i + 0.5) * d / rows
        box(base + rot @ Vector((0, y, 0.07)), (w * 0.94, 0.05, 0.09), "vine", rz)


def ring_trees(n, r0, r1, seed, h=(0.6, 0.8)):
    rr = random.Random(seed)
    for i in range(n):
        a = rr.uniform(0, math.tau)
        r = rr.uniform(r0, r1)
        tree((math.cos(a) * r, math.sin(a) * r), rr.uniform(*h))


def hamlet():
    building("House_1", (-0.55, 0.45, 0.0), 2.4, 1.0, "slate")
    building("House_2", (0.75, 0.6, 0.0), 3.9, 0.95, "tile")
    building("Stable", (0.35, -0.85, 0.0), 0.15, 0.95, "tile")
    building("House_1", (-0.85, -0.7, 0.0), 1.1, 0.9, "tile")
    prop("Well", (0.05, -0.05, 0.0), 0.3, 1.0)
    prop("Cart", (1.15, -0.35, 0.0), 1.2, 1.0)
    prop("Hay", (1.3, -1.0, 0.0), 0.4, 1.0)
    field((2.0, 0.25, 0.0), 1.0, 0.9, 0.3, "field_green")
    ring_trees(8, 1.6, 2.3, 81)
    return finish("WorldVillage_vallerois_hamlet")


def mill():
    building("Mill", (-1.1, 1.05, 0.0), 0.6, 1.5, "tile", 4500)
    building("House_2", (0.55, 0.35, 0.0), 3.4, 1.0, "tile")
    building("House_1", (1.35, -0.55, 0.0), 4.6, 0.95, "slate")
    building("Sawmill", (-0.35, -1.05, 0.0), 0.2, 0.95, "tile")
    building("House_1", (0.6, -1.5, 0.0), 5.8, 0.9, "tile")
    prop("Cart", (-0.2, 0.15, 0.0), 2.6, 1.0)
    prop("Well", (0.85, -0.6, 0.0), 0.2, 1.0)
    field((2.35, 0.75, 0.0), 1.2, 1.1, 0.1)
    field((0.9, -2.55, 0.0), 1.3, 0.75, -0.15)
    for x, y in ((2.1, -0.75), (2.45, -0.95), (2.75, -0.65)):
        haystack((x, y), 0.9)
    ring_trees(4, 2.3, 2.7, 71)
    flag((0.15, 0.55, 0.0), 1.3)
    return finish("WorldVillage_vallerois_mill")


def vineyard():
    building("Inn", (0.0, 0.2, 0.0), 0.2, 1.05, "slate")
    building("House_2", (-1.1, -0.5, 0.0), 0.9, 0.95, "tile")
    building("Stable", (-0.75, 1.15, 0.0), 2.8, 0.9, "tile")
    prop("Cart", (0.95, -0.55, 0.0), 0.4, 1.0)
    prop("MarketStand_2", (0.55, -0.95, 0.0), 0.2, 1.0)
    for i, (x, y, rz) in enumerate(((2.0, 0.6, 0.15), (1.75, -1.4, -0.2), (-0.9, -2.15, 0.4), (-2.15, 0.95, 1.2))):
        vines((x, y), 1.1, 0.95, rz, 6)
    ring_trees(3, 2.4, 2.8, 91)
    flag((0.55, -0.05, 0.0), 1.4)
    return finish("WorldVillage_vallerois_vineyard")


ALL = {"village": village, "hamlet": hamlet, "mill": mill, "vineyard": vineyard}
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(ALL)
models = [ALL[k]() for k in only]
if "--preview" in sys.argv:
    print("parts", [(o.name, sum(len(p.vertices) - 2 for p in o.data.polygons)) for o in models])
else:
    print("ok", pack_export(models))
