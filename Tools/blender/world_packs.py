import bpy, bmesh, math, os, sys
from mathutils import Matrix, Vector

SCENE = "WorldPacks" if bpy.context.window else bpy.context.scene.name
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
kit = open(KIT, encoding="utf-8").read()
if not bpy.context.window:
    kit = kit.replace('exec(compile(code, SRC, "exec"), ns)', 'exec(compile(code.replace("bpy.context.window.scene = scn", "pass"), SRC, "exec"), ns)')
exec(compile(kit, KIT, "exec"), globals())

PACKS = os.path.join(ROOT, "ArtSource", "packs")
TREES = os.path.join(PACKS, "LowPoly_Tree_Collection_01_fbx.FBX")
ROCKS = os.path.join(PACKS, "Rocks_series_02.fbx")

M.update({
    "bark": mat("env_bark", (0.34, 0.25, 0.17), 0.95),
    "bark_pine": mat("env_bark_pine", (0.46, 0.29, 0.17), 0.95),
    "deadwood": mat("env_bark_dead", (0.5, 0.45, 0.4), 0.95),
    "oak": mat("env_leaf_oak", (0.25, 0.43, 0.15), 0.85),
    "birch": mat("env_leaf_birch", (0.45, 0.6, 0.22), 0.85),
    "bush": mat("env_leaf_bush", (0.33, 0.43, 0.17), 0.9),
    "spruce": mat("env_needle_spruce", (0.11, 0.26, 0.15), 0.9),
    "pine": mat("env_needle_pine", (0.18, 0.34, 0.16), 0.9),
    "cypress": mat("env_leaf_cypress", (0.17, 0.3, 0.14), 0.9),
    "lightleaf": mat("env_leaf_light", (0.3, 0.45, 0.17), 0.85),
    "rock": mat("env_rock", (0.56, 0.53, 0.49), 0.95),
    "rock_moss": mat("env_rock_moss", (0.42, 0.47, 0.32), 0.95),
})

GROUPS = {
    "broad": (["122", "131", "132", "134", "70", "65", "193"], "oak", "bark", 1.3, 0.4),
    "light": (["141", "143", "77", "79"], "lightleaf", "bark", 1.35, 0.4),
    "young": (["73", "81"], "oak", "bark", 0.75, 0.45),
    "bush": (["97", "98", "99"], "bush", "bark", 0.45, 0.45),
    "spruce": (["90", "91", "92", "94"], "spruce", "bark_pine", 1.4, 0.4),
    "pine": (["86", "88", "89", "93"], "pine", "bark_pine", 1.4, 0.45),
    "youngfir": (["31", "153"], "spruce", "bark_pine", 0.75, 0.5),
    "cypress": (["95", "96"], "cypress", "bark", 1.3, 0.45),
    "dead": (["85", "173", "176", "178"], "deadwood", "deadwood", 1.15, 0.6),
}
ROCK_PICK = ["Rocks_01", "Rocks_011", "Rocks_016", "Rocks_022", "Rocks_027", "Rocks_033", "Rocks_038", "Rocks_045"]
MOSSY = {"Rocks_016", "Rocks_033", "Rocks_045"}


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.name not in coll.objects:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
    return {o.name: o for o in new if o.type == "MESH"}


def tris(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def lay_flat(o):
    best = None
    for rot in (Matrix.Identity(4), Matrix.Rotation(math.pi / 2, 4, "X"), Matrix.Rotation(math.pi / 2, 4, "Y")):
        zs = [(rot @ v.co).z for v in o.data.vertices]
        h = max(zs) - min(zs)
        if best is None or h < best[0]:
            best = (h, rot)
    o.data.transform(best[1])


def prepare(src, name, height, flat=False, radius=None):
    o = src.copy()
    o.data = src.data.copy()
    coll.objects.link(o)
    o.data.transform(o.matrix_world)
    o.matrix_world = o.matrix_world.__class__.Identity(4)
    if flat:
        lay_flat(o)
    vs = [v.co for v in o.data.vertices]
    z0 = min(v.z for v in vs)
    z1 = max(v.z for v in vs)
    foot = [v for v in vs if v.z < z0 + (z1 - z0) * 0.04]
    cx = sum(v.x for v in foot) / len(foot)
    cy = sum(v.y for v in foot) / len(foot)
    s = height / max(z1 - z0, 1e-4)
    if radius:
        s = radius / max(max(math.hypot(v.x - cx, v.y - cy) for v in vs), 1e-4)
    for v in o.data.vertices:
        v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - z0) * s))
    o.name = name
    o.data.name = name
    return o


def paint_tree(o, leaf, bark):
    me = o.data
    uv = me.uv_layers.active
    me.materials.clear()
    me.materials.append(M[bark])
    if leaf != bark:
        me.materials.append(M[leaf])
    for p in me.polygons:
        v = sum(uv.data[l].uv[1] for l in p.loop_indices) / p.loop_total
        p.material_index = 0 if leaf == bark or v >= 0.85 or v < 0.69 else 1


def paint_rock(o, mossy):
    me = o.data
    me.materials.clear()
    me.materials.append(M["rock"])
    if mossy:
        me.materials.append(M["rock_moss"])
        for p in me.polygons:
            p.material_index = 1 if p.normal.z > 0.72 else 0


def decimate(o, ratio):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)


def lod_copy(o, ratio):
    c = o.copy()
    c.data = o.data.copy()
    coll.objects.link(c)
    c.name = o.name + "_lod"
    decimate(c, ratio)
    if tris(c) > tris(o) * 0.7:
        bpy.data.objects.remove(c, do_unlink=True)
        return None
    return c


def finish_mesh(o):
    for a in list(o.data.uv_layers):
        o.data.uv_layers.remove(a)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


for o in list(coll.objects):
    bpy.data.objects.remove(o, do_unlink=True)

models = []
trees = load(TREES)
for group, (ids, leaf, bark, height, ratio) in GROUPS.items():
    for i in ids:
        o = prepare(trees[i], f"WorldTree_p_{group}_{i}", height)
        paint_tree(o, leaf, bark)
        finish_mesh(o)
        models.append(o)
        lod = lod_copy(o, ratio)
        if lod:
            models.append(lod)
for o in trees.values():
    bpy.data.objects.remove(o, do_unlink=True)

rocks = load(ROCKS)
for i, rid in enumerate(ROCK_PICK):
    o = prepare(rocks[rid], f"WorldTree_p_rock_{i + 1}", 1.0, True, 0.36)
    finish_mesh(o)
    decimate(o, 320 / max(tris(o), 1))
    paint_rock(o, rid in MOSSY)
    models.append(o)
    lod = lod_copy(o, 0.3)
    if lod:
        models.append(lod)
for o in rocks.values():
    bpy.data.objects.remove(o, do_unlink=True)

result = []
for o in models:
    bake_ao(o, 0.35, 16)
    ns["export"](o, os.path.join(OUT, o.name + ".fbx"))
    vs = o.data.vertices
    result.append((o.name, tris(o), round(max(v.co.z for v in vs), 2), round(max(math.hypot(v.co.x, v.co.y) for v in vs), 2)))
for i, o in enumerate(models):
    o.location = ((i % 12) * 2.0, (i // 12) * 2.2, 0)
for r in result:
    print("M", *r)
