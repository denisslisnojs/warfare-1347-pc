import bpy, math, os
from mathutils import Matrix, Vector

SCENE = "WorldShips" if bpy.context.window else bpy.context.scene.name
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
kit = open(KIT, encoding="utf-8").read()
if not bpy.context.window:
    kit = kit.replace('exec(compile(code, SRC, "exec"), ns)', 'exec(compile(code.replace("bpy.context.window.scene = scn", "pass"), SRC, "exec"), ns)')
exec(compile(kit, KIT, "exec"), globals())

BOATS = os.path.join(ROOT, "ArtSource", "packs", "boats")
ROLE = {
    "DarkWood": "env_beam",
    "Wood": "env_plank",
    "LightWood": "env_wood",
    "Fabric": "env_sail",
    "Sail": "env_sail",
    "White": "env_sail",
    "C5B99A": "env_sail",
    "Red": "env_flag",
    "DarkRed": "env_flag",
    "Steel": "env_iron",
}
SHIPS = [
    ("BoatWSail.fbx", "boat", 0.5),
    ("Viking boat.fbx", "longship", 1.0),
    ("Sail ship.fbx", "cog", 1.05),
    ("Sail ship.fbx", "galley", 1.05),
    ("Sail ship.fbx", "dhow", 1.05),
]


def build(fname, kind, length):
    for x in list(coll.objects):
        bpy.data.objects.remove(x, do_unlink=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(BOATS, fname))
    parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    bpy.context.view_layer.update()
    clean = []
    for o in parts:
        me = o.data.copy()
        me.transform(o.matrix_world)
        names = [ROLE.get(m.name.split(".")[0], "env_plank") if m else "env_plank" for m in me.materials]
        cols = [tuple(next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value[:3]) if m and m.use_nodes else (0.5, 0.4, 0.3) for m in me.materials]
        idx = [p.material_index for p in me.polygons]
        me.materials.clear()
        for r, c in zip(names, cols):
            me.materials.append(mat(f"{r}_{kind}_{len(me.materials)}", c, 0.9))
        for p, i in zip(me.polygons, idx):
            p.material_index = i
        for a in list(me.uv_layers):
            me.uv_layers.remove(a)
        n = bpy.data.objects.new(o.name + "_c", me)
        coll.objects.link(n)
        clean.append(n)
    for o in parts:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in clean:
        o.select_set(True)
    bpy.context.view_layer.objects.active = clean[0]
    if len(clean) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.data.transform(Matrix.Rotation(math.pi / 2, 4, "Z"))
    vs = o.data.vertices
    xs = [v.co.x for v in vs]; ys = [v.co.y for v in vs]; zs = [v.co.z for v in vs]
    cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    s = length / (max(xs) - min(xs))
    for v in vs:
        v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - z0) * s))
    o.name = o.data.name = "WorldShip_" + kind
    bake_ao(o, 0.3, 16)
    ns["export"](o, os.path.join(OUT, o.name + ".fbx"))
    o.data.calc_loop_triangles()
    print("SHIP", o.name, len(o.data.loop_triangles), tuple(round(d, 2) for d in o.dimensions), sorted({m.name for m in o.data.materials}))


for fname, kind, length in SHIPS:
    build(fname, kind, length)
