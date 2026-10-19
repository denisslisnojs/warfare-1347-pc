import bpy, bmesh, math, os, random
from mathutils import Vector

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
OUT = os.path.join(ROOT, "Assets", "Art", "Environment")
BLEND = os.path.join(ROOT, "ArtSource", "environment.blend")
os.makedirs(OUT, exist_ok=True)

scn = bpy.data.scenes.get("Environment") or bpy.data.scenes.new("Environment")
bpy.context.window.scene = scn
for o in list(scn.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scn.collection


def mat(name, rgb, rough=0.8, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M = {
    "wall": mat("env_wall", (0.93, 0.87, 0.74)),
    "beam": mat("env_beam", (0.36, 0.23, 0.13)),
    "thatch": mat("env_thatch", (0.8, 0.63, 0.3), 0.95),
    "thatch2": mat("env_thatch_dark", (0.66, 0.5, 0.24), 0.95),
    "stone": mat("env_stone", (0.58, 0.57, 0.55), 0.9),
    "stone_dark": mat("env_stone_dark", (0.42, 0.41, 0.4), 0.9),
    "wood": mat("env_wood", (0.52, 0.35, 0.18)),
    "glass": mat("env_window", (0.16, 0.18, 0.22), 0.3),
    "leaf": mat("env_leaf", (0.28, 0.52, 0.2)),
    "leaf2": mat("env_leaf_light", (0.38, 0.6, 0.24)),
    "pine": mat("env_pine", (0.17, 0.38, 0.2)),
    "bark": mat("env_bark", (0.4, 0.27, 0.16)),
    "hay": mat("env_hay", (0.86, 0.72, 0.38), 0.95),
    "hill": mat("env_hill", (0.36, 0.5, 0.24), 1.0),
    "water": mat("env_water", (0.22, 0.38, 0.55), 0.2),
}


def finish(o, m, smooth=True):
    o.data.materials.clear()
    o.data.materials.append(M[m])
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    if smooth:
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        except Exception:
            bpy.ops.object.shade_smooth()
    else:
        bpy.ops.object.shade_flat()
    return o


def apply_mods(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")


def box(loc, size, m, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        apply_mods(o)
    return finish(o, m)


def cyl(a, b, r1, r2, m, verts=24, bevel=0.0):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    if bevel:
        bv = o.modifiers.new("Bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 2
        apply_mods(o)
    return finish(o, m)


def sphere(loc, r, m, sc=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = sc
    return finish(o, m)


def blob(loc, r, m, seed, sc=(1, 1, 1), amount=0.12):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc)
    o = bpy.context.active_object
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co *= 1 + rnd.uniform(-amount, amount)
    o.scale = sc
    return finish(o, m)


def prism(name, length, width, height, overhang, thickness, m, z):
    hw = width / 2 + overhang
    hl = length / 2 + overhang
    verts = [(-hl, -hw, z), (hl, -hw, z), (hl, 0, z + height), (-hl, 0, z + height), (-hl, hw, z), (hl, hw, z)]
    faces = [(0, 1, 2, 3), (3, 2, 5, 4)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    s = o.modifiers.new("Solid", "SOLIDIFY")
    s.thickness = thickness
    s.offset = 1.0
    bv = o.modifiers.new("Bevel", "BEVEL")
    bv.width = 0.05
    bv.segments = 2
    apply_mods(o)
    return finish(o, m, smooth=False)


def gable(length, width, z, height, m):
    hw = width / 2
    hl = length / 2
    verts = [(-hl, -hw, z), (-hl, hw, z), (-hl, 0, z + height), (hl, -hw, z), (hl, hw, z), (hl, 0, z + height)]
    faces = [(0, 1, 2), (3, 5, 4)]
    me = bpy.data.meshes.new("gable")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("gable", me)
    coll.objects.link(o)
    s = o.modifiers.new("Solid", "SOLIDIFY")
    s.thickness = 0.12
    apply_mods(o)
    return finish(o, m, smooth=False)


def join(name, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return o


def house(name, L, W, H, roofH, seed):
    rnd = random.Random(seed)
    p = [box((0, 0, 0.2), (L + 0.3, W + 0.3, 0.4), "stone", 0.06)]
    p.append(box((0, 0, 0.4 + H / 2), (L, W, H), "wall", 0.06))
    for x in (-L / 2, L / 2):
        for y in (-W / 2, W / 2):
            p.append(box((x, y, 0.4 + H / 2), (0.22, 0.22, H + 0.05), "beam", 0.02))
    p.append(box((0, -W / 2 - 0.02, 0.4 + H - 0.1), (L + 0.1, 0.18, 0.18), "beam", 0.02))
    p.append(box((0, W / 2 + 0.02, 0.4 + H - 0.1), (L + 0.1, 0.18, 0.18), "beam", 0.02))
    p.append(box((0, -W / 2 - 0.02, 0.4 + H * 0.52), (L, 0.14, 0.14), "beam", 0.02))
    door_x = rnd.uniform(-L * 0.2, L * 0.2)
    p.append(box((door_x, -W / 2 - 0.03, 0.4 + 0.85), (0.9, 0.12, 1.7), "wood", 0.04))
    for wx in (-L * 0.32, L * 0.32):
        if abs(wx - door_x) < 1.0:
            continue
        p.append(box((wx, -W / 2 - 0.03, 0.4 + H * 0.62), (0.7, 0.1, 0.6), "glass", 0.02))
        p.append(box((wx, -W / 2 - 0.06, 0.4 + H * 0.62 - 0.36), (0.85, 0.12, 0.1), "beam", 0.02))
    p.append(gable(L, W, 0.4 + H, roofH, "wall"))
    p.append(prism(name + "_roof", L, W, roofH, 0.45, 0.32, "thatch", 0.4 + H - 0.05))
    p.append(box((L * 0.28, W * 0.18, 0.4 + H + roofH * 0.7), (0.5, 0.5, 1.4), "stone_dark", 0.05))
    return join(name, p)


def tree_round(name, seed, scale=1.0):
    rnd = random.Random(seed)
    s = scale
    p = [cyl((0, 0, 0), (0, 0, 2.4 * s), 0.28 * s, 0.18 * s, "bark", 12)]
    for i in range(3):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.3, 0.8) * s
        p.append(blob((math.cos(a) * r, math.sin(a) * r, (2.6 + rnd.uniform(0, 1.1)) * s), rnd.uniform(1.1, 1.5) * s, "leaf" if i % 2 == 0 else "leaf2", seed * 7 + i))
    return join(name, p)


def tree_pine(name, seed, scale=1.0):
    rnd = random.Random(seed)
    s = scale
    p = [cyl((0, 0, 0), (0, 0, 1.6 * s), 0.22 * s, 0.16 * s, "bark", 10)]
    z = 1.0 * s
    for i, (r, h) in enumerate(((1.7, 2.0), (1.35, 1.8), (0.95, 1.6))):
        p.append(cyl((0, 0, z), (0, 0, z + h * s), r * s * rnd.uniform(0.92, 1.08), 0.05, "pine", 10, bevel=0.08))
        z += h * s * 0.55
    return join(name, p)


def bush(name, seed):
    rnd = random.Random(seed)
    p = [blob((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0.45), rnd.uniform(0.5, 0.75), "leaf2" if i == 1 else "leaf", seed * 3 + i, (1, 1, 0.8)) for i in range(3)]
    return join(name, p)


def haystack(name):
    p = [sphere((0, 0, 0.0), 1.3, "hay", (1, 1, 1.25), 20)]
    bm = bmesh.new()
    bm.from_mesh(p[0].data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context="VERTS")
    bm.to_mesh(p[0].data)
    bm.free()
    p.append(cyl((0, 0, 1.45), (0, 0, 1.9), 0.06, 0.02, "wood", 6))
    return join(name, p)


def fence(name):
    p = []
    for x in (0.0, 2.0):
        p.append(box((x, 0, 0.55), (0.12, 0.12, 1.1), "wood", 0.02))
    for z in (0.45, 0.85):
        p.append(box((1.0, 0, z), (2.15, 0.06, 0.1), "wood", 0.015))
    return join(name, p)


def well(name):
    p = [cyl((0, 0, 0), (0, 0, 0.8), 0.85, 0.85, "stone", 24, bevel=0.06),
         cyl((0, 0, 0.75), (0, 0, 0.82), 0.62, 0.62, "water", 24)]
    for x in (-0.7, 0.7):
        p.append(box((x, 0, 1.3), (0.12, 0.12, 1.4), "wood", 0.02))
    p.append(box((0, 0, 1.75), (1.6, 0.08, 0.08), "wood", 0.01))
    p.append(prism(name + "_roof", 1.5, 1.4, 0.6, 0.15, 0.1, "thatch", 1.95))
    p.append(cyl((0, 0, 1.2), (0, 0, 1.45), 0.14, 0.17, "wood", 12))
    return join(name, p)


def cart(name):
    p = [box((0, 0, 0.75), (2.2, 1.2, 0.25), "wood", 0.03)]
    for y in (-0.6, 0.6):
        p.append(box((0, y, 1.0), (2.2, 0.08, 0.45), "wood", 0.02))
        w = cyl((0.2, y * 1.12, 0.48), (0.2, y * 1.12 + (0.12 if y > 0 else -0.12), 0.48), 0.48, 0.48, "beam", 16, bevel=0.03)
        p.append(w)
    for y in (-0.35, 0.35):
        p.append(box((-1.8, y, 0.65), (1.6, 0.08, 0.08), "wood", 0.01))
    p.append(sphere((0.2, 0, 1.15), 0.6, "hay", (1.4, 0.8, 0.5), 16))
    return join(name, p)


def rock(name, seed):
    return join(name, [blob((0, 0, 0.25), 0.7, "stone", seed, (1.3, 1.0, 0.7), 0.25)])


def hill(name, seed):
    return join(name, [blob((0, 0, -4.0), 30.0, "hill", seed, (1.0, 0.7, 0.32), 0.08)])


def export(o, fname):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, fname),
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
    )


props = [
    (house("House_Small", 4.2, 3.4, 2.4, 1.9, 1), "House_Small.fbx"),
    (house("House_Long", 6.5, 3.8, 2.3, 2.0, 2), "House_Long.fbx"),
    (tree_round("Tree_Round", 3), "Tree_Round.fbx"),
    (tree_round("Tree_Round_Big", 4, 1.35), "Tree_Round_Big.fbx"),
    (tree_pine("Tree_Pine", 5), "Tree_Pine.fbx"),
    (bush("Bush", 6), "Bush.fbx"),
    (haystack("Haystack"), "Haystack.fbx"),
    (fence("Fence"), "Fence.fbx"),
    (well("Well"), "Well.fbx"),
    (cart("Cart"), "Cart.fbx"),
    (rock("Rock", 7), "Rock.fbx"),
    (hill("Hill", 8), "Hill.fbx"),
]
x = 0.0
for o, fname in props:
    export(o, fname)
    o.location = (x, 0, 0)
    x += max(o.dimensions.x, 2) + 2 if o.name != "Hill" else 0
next(o for o, _ in props if o.name == "Hill").location = (0, 60, 0)
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)
print("exported", len(props))
