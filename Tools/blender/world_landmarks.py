import bpy, bmesh, math, os, random
from mathutils import Matrix, Vector

SCENE = "WorldLandmarks" if bpy.context.window else bpy.context.scene.name
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
kit = open(KIT, encoding="utf-8").read()
if not bpy.context.window:
    kit = kit.replace('exec(compile(code, SRC, "exec"), ns)', 'exec(compile(code.replace("bpy.context.window.scene = scn", "pass"), SRC, "exec"), ns)')
exec(compile(kit, KIT, "exec"), globals())

PACKS = os.path.join(ROOT, "ArtSource", "packs")


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in o.users_collection:
            c.objects.unlink(o)
        coll.objects.link(o)
    return [o for o in new if o.type == "MESH"]


def bake_world(o):
    me = o.data.copy()
    me.transform(o.matrix_world)
    fresh = bpy.data.objects.new(o.name + "_clean", me)
    coll.objects.link(fresh)
    bpy.data.objects.remove(o, do_unlink=True)
    return fresh


def face_colors(o):
    me = o.data
    uv = me.uv_layers.active.data
    cache = {}
    out = []
    for p in me.polygons:
        m = me.materials[p.material_index]
        img = next((n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None) if m and m.use_nodes else None
        if img is None:
            out.append(Vector((0.5, 0.5, 0.5)))
            continue
        if img.name not in cache:
            cache[img.name] = (img.size[0], img.size[1], img.pixels[:])
        w, h, px = cache[img.name]
        pts = [uv[l].uv for l in p.loop_indices]
        c = Vector((sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)))
        acc = Vector((0.0, 0.0, 0.0))
        samples = pts + [c, c, c]
        for q in samples:
            x = int((q[0] % 1.0) * (w - 1))
            y = int((q[1] % 1.0) * (h - 1))
            i = (y * w + x) * 4
            acc += Vector(px[i:i + 3])
        out.append(acc / len(samples))
    return out


def kmeans(cols, k, seed=3):
    rnd = random.Random(seed)
    centers = [cols[i].copy() for i in rnd.sample(range(len(cols)), k)]
    label = [0] * len(cols)
    for _ in range(12):
        for i, c in enumerate(cols):
            label[i] = min(range(k), key=lambda j: (c - centers[j]).length_squared)
        for j in range(k):
            members = [cols[i] for i in range(len(cols)) if label[i] == j]
            if members:
                centers[j] = sum(members, Vector((0, 0, 0))) / len(members)
    return label, centers


def role(c):
    r, g, b = c
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    sat = max(c) - min(c)
    if sat < 0.06:
        return "env_stone_grey" if lum < 0.55 else "env_wall_light"
    if r > b + 0.08 and lum < 0.35:
        return "env_beam"
    if r > b + 0.08 and lum < 0.55:
        return "env_wood"
    return "env_plaster"


def restyle(o, k, override=None):
    cols = face_colors(o)
    label, centers = kmeans(cols, k)
    me = o.data
    me.materials.clear()
    names = []
    for j, c in enumerate(centers):
        name = (override or {}).get(j) or role(c)
        tone = Vector((c[0] ** 0.9, c[1] ** 0.9, c[2] ** 0.9))
        m = mat(f"{name}_{o.name}_{j}", tuple(tone), 0.9)
        me.materials.append(m)
        names.append((name, tuple(round(x, 2) for x in c), sum(1 for l in label if l == j)))
    for p, l in zip(me.polygons, label):
        p.material_index = l
    for a in list(me.uv_layers):
        me.uv_layers.remove(a)
    return names


def ground(o, height):
    vs = o.data.vertices
    zs = [v.co.z for v in vs]
    z0, z1 = min(zs), max(zs)
    foot = [v.co for v in vs if v.co.z < z0 + (z1 - z0) * 0.03]
    cx = sum(v.x for v in foot) / len(foot)
    cy = sum(v.y for v in foot) / len(foot)
    s = height / (z1 - z0)
    return cx, cy, z0, s


PALETTE = {
    "env_roof_wood": (0.42, 0.3, 0.2),
    "env_stone": (0.56, 0.53, 0.48),
    "env_plaster": (0.86, 0.8, 0.66),
    "env_beam": (0.36, 0.24, 0.15),
    "env_plank": (0.55, 0.42, 0.28),
}


def by_shape(o, height, roof_from=0.68, base_to=0.12):
    cols = face_colors(o)
    label, centers = kmeans(cols, 4)
    dark = min(range(4), key=lambda j: centers[j].length)
    me = o.data
    me.materials.clear()
    names = list(PALETTE)
    for n in names:
        me.materials.append(mat(f"{n}_{o.name}", PALETTE[n], 0.9))
    for p, l in zip(me.polygons, label):
        z = p.center.z / height
        if z > 0.8 or z > roof_from and abs(p.normal.z) > 0.25:
            r = "env_roof_wood"
        elif z < base_to:
            r = "env_stone"
        elif l == dark:
            r = "env_beam"
        else:
            r = "env_plaster"
        p.material_index = names.index(r)
    for a in list(me.uv_layers):
        me.uv_layers.remove(a)
    return {n: sum(1 for p in me.polygons if p.material_index == i) for i, n in enumerate(names)}


def blades_style(o):
    cols = face_colors(o)
    label, centers = kmeans(cols, 2)
    dark = min(range(2), key=lambda j: centers[j].length)
    me = o.data
    me.materials.clear()
    me.materials.append(mat(f"env_beam_{o.name}", PALETTE["env_beam"], 0.9))
    me.materials.append(mat(f"env_plank_{o.name}", PALETTE["env_plank"], 0.9))
    for p, l in zip(me.polygons, label):
        p.material_index = 0 if l == dark else 1
    for a in list(me.uv_layers):
        me.uv_layers.remove(a)


def windmill():
    parts = load(os.path.join(PACKS, "windmill", "windmill.fbx"))
    o = bake_world(parts[0])
    for x in list(coll.objects):
        if x is not o:
            bpy.data.objects.remove(x, do_unlink=True)
    cx, cy, z0, s = ground(o, 3.2)
    for v in o.data.vertices:
        v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - z0) * s))
    bm = bmesh.new()
    bm.from_mesh(o.data)
    blade_faces = [f for f in bm.faces if f.material_index == 1]
    hub = sum((f.calc_center_median() for f in blade_faces), Vector()) / max(len(blade_faces), 1)
    bm.free()
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    o.active_material_index = 1
    bpy.ops.object.material_slot_select()
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    blades = next(x for x in bpy.context.selected_objects if x is not o)
    tower_info = by_shape(o, max(v.co.z for v in o.data.vertices))
    blades_style(blades)
    blade_info = len(blades.data.polygons)
    for v in blades.data.vertices:
        v.co -= hub
    blades.location = hub
    blades.parent = o
    blades.matrix_parent_inverse = Matrix.Identity(4)
    o.name = o.data.name = "WorldLandmark_windmill"
    blades.name = blades.data.name = "Blades"
    return o, blades, tower_info, blade_info, hub


def append_blend(path):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    out = []
    for o in dst.objects:
        if o is not None and o.type == "MESH":
            coll.objects.link(o)
            out.append(o)
    bpy.context.view_layer.update()
    return out


def static_landmark(name, parts, width, roles, tris=None):
    clean = [bake_world(o) for o in parts]
    bpy.ops.object.select_all(action="DESELECT")
    for o in clean:
        me = o.data
        names = [roles.get(m.name.split(".")[0], roles.get("*", "env_stone")) if m else "env_stone" for m in me.materials]
        before = [p.material_index for p in me.polygons]
        me.materials.clear()
        for r in sorted(set(names)):
            me.materials.append(mat(f"{r}_{name}", PALETTE.get(r, (0.6, 0.58, 0.54)), 0.9))
        order = sorted(set(names))
        idx = [order.index(r) for r in names] if names else [0]
        for p, mi in zip(me.polygons, before):
            p.material_index = idx[mi] if mi < len(idx) else 0
        for a in list(me.uv_layers):
            me.uv_layers.remove(a)
        o.select_set(True)
    bpy.context.view_layer.objects.active = clean[0]
    if len(clean) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    zs = [v.co.z for v in o.data.vertices]
    zmin, zspan = min(zs), max(zs) - min(zs)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    grey = next((i for i, m in enumerate(o.data.materials) if m.name.startswith("env_stone_grey")), -1)
    floor = [f for f in bm.faces if f.material_index == grey and f.calc_center_median().z < zmin + zspan * 0.08]
    if floor:
        bmesh.ops.delete(bm, geom=floor, context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    if tris:
        me = o.data
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        if n > tris:
            mod = o.modifiers.new("dec", "DECIMATE")
            mod.ratio = tris / n
            bpy.ops.object.modifier_apply(modifier=mod.name)
    vs = o.data.vertices
    xs = [v.co.x for v in vs]; ys = [v.co.y for v in vs]; zs = [v.co.z for v in vs]
    cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    sc = width / max(max(xs) - min(xs), max(ys) - min(ys))
    for v in vs:
        v.co = Vector(((v.co.x - cx) * sc, (v.co.y - cy) * sc, (v.co.z - z0) * sc))
    o.name = o.data.name = name
    return o


def export_one(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for x in objs:
        x.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, objs[0].name + ".fbx"), use_selection=True, object_types={"MESH"}, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", bake_space_transform=True, mesh_smooth_type="FACE")


PALETTE.update({"env_stone_grey": (0.4, 0.38, 0.35), "env_stone_old": (0.46, 0.44, 0.39)})

for x in list(coll.objects):
    bpy.data.objects.remove(x, do_unlink=True)
RUINS = os.path.join(PACKS, "ruins")
house_parts = [o for o in load(os.path.join(RUINS, "ruined_house.fbx")) if o.name.startswith("Cube")]
for x in list(coll.objects):
    if x not in house_parts:
        bpy.data.objects.remove(x, do_unlink=True)
for hp in house_parts:
    if hp.name.startswith("Cube.028"):
        for m in hp.data.materials:
            m.name = "Beams"
house = static_landmark("WorldLandmark_ruined_house", house_parts, 2.4, {"Beams": "env_beam", "*": "env_stone"})
bake_ao(house, 0.4, 16)
export_one([house])
print("HOUSE", len(house.data.polygons), round(max(v.co.z for v in house.data.vertices), 2))
bpy.data.objects.remove(house, do_unlink=True)

for fname, name, width, tris in (("castle_ruins.blend", "WorldLandmark_castle_ruins", 7.5, 4000), ("castle_wall.blend", "WorldLandmark_castle_wall", 4.5, 2200)):
    parts = append_blend(os.path.join(RUINS, fname))
    o = static_landmark(name, parts, width, {"Wall": "env_stone_old", "Walls": "env_stone_old", "Material": "env_stone_grey"}, tris)
    bake_ao(o, 0.6, 16)
    export_one([o])
    o.data.calc_loop_triangles()
    print("RUIN", name, len(o.data.loop_triangles), round(max(v.co.z for v in o.data.vertices), 2))
    bpy.data.objects.remove(o, do_unlink=True)

tower, blades, ti, bi, hub = windmill()
for x in (tower, blades):
    bake_ao(x, 0.5, 16)
bpy.ops.object.select_all(action="DESELECT")
tower.select_set(True)
blades.select_set(True)
bpy.context.view_layer.objects.active = tower
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, tower.name + ".fbx"), use_selection=True, object_types={"MESH"}, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", bake_space_transform=True, mesh_smooth_type="FACE")
print("TOWER", ti)
print("BLADES", bi)
print("HUB", tuple(round(v, 2) for v in hub), "HEIGHT", round(max(v.co.z for v in tower.data.vertices), 2), "TRIS", len(tower.data.polygons), len(blades.data.polygons))
