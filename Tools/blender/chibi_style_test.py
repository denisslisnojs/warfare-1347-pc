import bpy, bmesh, math, os
from mathutils import Vector

OUT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\docs\style"
os.makedirs(OUT, exist_ok=True)

scn = bpy.data.scenes.get("Chibi") or bpy.data.scenes.new("Chibi")
bpy.context.window.scene = scn
for o in list(scn.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scn.collection


def mat(name, rgb, rough=0.65, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M = {
    "skin": mat("c_skin", (0.88, 0.64, 0.48), 0.7),
    "eye": mat("c_eye", (0.03, 0.03, 0.035), 0.3),
    "blue": mat("c_blue", (0.1, 0.22, 0.85), 0.7),
    "red": mat("c_red", (0.78, 0.1, 0.08), 0.7),
    "gold": mat("c_gold", (0.95, 0.74, 0.18), 0.45),
    "white": mat("c_white", (0.93, 0.91, 0.86), 0.7),
    "brown": mat("c_brown", (0.5, 0.33, 0.18), 0.8),
    "straw": mat("c_straw", (0.78, 0.62, 0.33), 0.85),
    "leather": mat("c_leather", (0.3, 0.18, 0.1), 0.75),
    "metal": mat("c_metal", (0.7, 0.72, 0.76), 0.35, 0.9),
    "dark": mat("c_dark", (0.2, 0.2, 0.22), 0.4, 0.7),
    "wood": mat("c_wood", (0.48, 0.31, 0.15), 0.75),
    "trousers": mat("c_trousers", (0.3, 0.24, 0.18), 0.85),
}

HEAD_R = 0.42
HEAD_Z = 1.26


def finish(o, m, smooth=True):
    o.data.materials.clear()
    o.data.materials.append(M[m])
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    if smooth:
        bpy.ops.object.shade_smooth()
    return o


def apply_all(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    return o


def subsurf(o, levels=2):
    mod = o.modifiers.new("Sub", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    return o


def skin_body(name, arm_drop, legs_m):
    s = math.radians(arm_drop)
    pts = {
        "pelvis": ((0, 0, 0.52), 0.2),
        "belly": ((0, 0, 0.66), 0.215),
        "chest": ((0, 0, 0.8), 0.215),
        "neck": ((0, 0, 0.9), 0.12),
    }
    edges = [("pelvis", "belly"), ("belly", "chest"), ("chest", "neck")]
    for side, sx in (("L", 1), ("R", -1)):
        pts[f"hip{side}"] = ((sx * 0.1, 0, 0.44), 0.1)
        pts[f"knee{side}"] = ((sx * 0.115, 0, 0.26), 0.088)
        pts[f"ankle{side}"] = ((sx * 0.12, 0, 0.09), 0.085)
        pts[f"toe{side}"] = ((sx * 0.12, -0.09, 0.06), 0.08)
        edges += [("pelvis", f"hip{side}"), (f"hip{side}", f"knee{side}"), (f"knee{side}", f"ankle{side}"), (f"ankle{side}", f"toe{side}")]
        sh = Vector((sx * 0.2, 0, 0.84))
        d = Vector((sx * math.cos(s), 0, -math.sin(s)))
        pts[f"shoulder{side}"] = (tuple(sh), 0.085)
        pts[f"elbow{side}"] = (tuple(sh + d * 0.2), 0.065)
        pts[f"wrist{side}"] = (tuple(sh + d * 0.34), 0.058)
        pts[f"hand{side}"] = (tuple(sh + d * 0.42), 0.078)
        edges += [("chest", f"shoulder{side}"), (f"shoulder{side}", f"elbow{side}"), (f"elbow{side}", f"wrist{side}"), (f"wrist{side}", f"hand{side}")]
    names = list(pts)
    me = bpy.data.meshes.new(name + "_skin")
    me.from_pydata([pts[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in edges], [])
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    mod = o.modifiers.new("Skin", "SKIN")
    mod.use_smooth_shade = True
    sv = me.skin_vertices[0].data
    for i, n in enumerate(names):
        r = pts[n][1]
        sv[i].radius = (r, r)
        sv[i].use_root = n == "pelvis"
    subsurf(o, 2)
    apply_all(o)
    finish(o, "skin")
    return o, pts


def sphere(name, loc, r, m, sc=(1, 1, 1), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = sc
    return finish(o, m)


def head(prefix):
    h = sphere(prefix + "_head", (0, 0, HEAD_Z), HEAD_R, "skin", (1.04, 0.98, 0.94))
    eyes = []
    for sx in (1, -1):
        e = sphere(prefix + "_eye", (sx * 0.14, -HEAD_R * 0.93, HEAD_Z - 0.02), 0.048, "eye", (0.85, 0.45, 1.1), 16)
        eyes.append(e)
    return [h] + eyes


def cap(prefix, m, r=HEAD_R * 1.07, cut=-0.08, sc=(1.04, 1.0, 0.95), z=HEAD_Z + 0.02):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=(0, 0, z))
    o = bpy.context.active_object
    o.name = prefix + "_cap"
    bm = bmesh.new()
    bm.from_mesh(o.data)
    kill = [v for v in bm.verts if v.co.z < cut * r]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    mod = o.modifiers.new("Solid", "SOLIDIFY")
    mod.thickness = 0.03
    o.scale = sc
    apply_all(o)
    return finish(o, m)


def cyl(name, a, b, r1, r2, m, sy=1.0, verts=32, sub=0):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.scale = (1, sy, 1)
    if sub:
        bev = o.modifiers.new("Bevel", "BEVEL")
        bev.width = min(r1, r2, d.length) * 0.25
        bev.segments = 3
        apply_all(o)
    return finish(o, m)


def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    if bevel:
        bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        apply_all(o)
    return finish(o, m)


def tunic(prefix, m, trim):
    parts = [
        cyl(prefix + "_tunic", (0, 0, 0.36), (0, 0, 0.9), 0.27, 0.23, m, sy=0.82, sub=1),
        cyl(prefix + "_belt", (0, 0, 0.55), (0, 0, 0.61), 0.255, 0.255, "leather", sy=0.84),
    ]
    if trim:
        parts.append(box(prefix + "_crossV", (0, -0.235, 0.72), (0.06, 0.03, 0.26), trim, 0.01))
        parts.append(box(prefix + "_crossH", (0, -0.235, 0.76), (0.2, 0.03, 0.06), trim, 0.01))
    return parts


def round_shield(prefix, center, r, face, rim, emblem):
    c = Vector(center)
    parts = [
        cyl(prefix + "_rim", c + Vector((0, 0.03, 0)), c, r * 1.06, r * 1.06, rim, verts=48),
        cyl(prefix + "_face", c, c + Vector((0, -0.03, 0)), r, r, face, verts=48),
        sphere(prefix + "_boss", tuple(c + Vector((0, -0.04, 0))), r * 0.2, "metal", (1, 0.55, 1), 24),
    ]
    if emblem:
        parts.append(box(prefix + "_e1", tuple(c + Vector((0, -0.035, 0))), (r * 0.22, 0.015, r * 1.85), emblem, 0.005))
        parts.append(box(prefix + "_e2", tuple(c + Vector((0, -0.035, 0))), (r * 1.85, 0.015, r * 0.22), emblem, 0.005))
    return parts


def heater_shield(prefix, center, w, h, face, emblem):
    pts = [(-w, h), (w, h), (w, h * 0.25), (w * 0.88, -h * 0.2), (w * 0.62, -h * 0.6), (w * 0.3, -h * 0.86), (0, -h), (-w * 0.3, -h * 0.86), (-w * 0.62, -h * 0.6), (-w * 0.88, -h * 0.2), (-w, h * 0.25)]
    me = bpy.data.meshes.new(prefix + "_heater")
    me.from_pydata([(x, 0, z) for x, z in pts], [], [list(range(len(pts)))])
    o = bpy.data.objects.new(prefix + "_heater", me)
    coll.objects.link(o)
    o.location = center
    s = o.modifiers.new("Solid", "SOLIDIFY")
    s.thickness = 0.05
    s.offset = 0.0
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = 0.015
    b.segments = 2
    apply_all(o)
    finish(o, face, smooth=False)
    c = Vector(center)
    parts = [o]
    if emblem:
        parts.append(box(prefix + "_band", tuple(c + Vector((0, -0.04, h * 0.15))), (w * 1.7, 0.015, h * 0.22), emblem, 0.005))
        parts.append(box(prefix + "_pale", tuple(c + Vector((0, -0.04, -h * 0.05))), (w * 0.3, 0.015, h * 1.5), emblem, 0.005))
    return parts


def spear(prefix, x, y, top, m_tip="metal"):
    return [
        cyl(prefix + "_shaft", (x, y, 0.03), (x, y, top), 0.022, 0.02, "wood", verts=10),
        cyl(prefix + "_tip", (x, y, top), (x, y, top + 0.22), 0.05, 0.002, m_tip, verts=8),
    ]


def join(name, parts, loc=(0, 0, 0)):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.location = loc
    return o


def dress(body, pts, legs_m, sleeve_m):
    me = body.data
    me.materials.append(M[legs_m])
    if sleeve_m:
        me.materials.append(M[sleeve_m])
    hands = [Vector(pts["handL"][0]), Vector(pts["handR"][0])]
    for poly in me.polygons:
        c = poly.center
        if c.z < 0.4:
            poly.material_index = 1
        elif sleeve_m and c.z < 0.88 and min((c - h).length for h in hands) > 0.1:
            poly.material_index = 2


def hand_pos(pts, side):
    return Vector(pts[f"hand{side}"][0])


def base_figure():
    body, pts = skin_body("Base_body", 0, "skin")
    return join("Base", [body] + head("base"))


def militia(cloth):
    body, pts = skin_body("Mil_body", 62, "trousers")
    dress(body, pts, "trousers", cloth)
    parts = [body] + head("mil") + tunic("mil", cloth, None)
    parts.append(cap("mil", "straw", cut=0.05))
    hr = hand_pos(pts, "R")
    parts += [cyl("mil_fork", (hr.x, hr.y - 0.02, 0.03), (hr.x, hr.y - 0.02, 1.85), 0.022, 0.02, "wood", verts=10)]
    for dx in (-0.06, 0, 0.06):
        parts.append(cyl("mil_tine", (hr.x + dx, hr.y - 0.02, 1.85), (hr.x + dx, hr.y - 0.02, 2.08), 0.012, 0.004, "dark", verts=6))
    parts.append(box("mil_forkbar", (hr.x, hr.y - 0.02, 1.85), (0.15, 0.02, 0.02), "dark"))
    return join("Militia", parts)


def spearman(cloth, trim, side_name):
    body, pts = skin_body("Sp_body", 62, "trousers")
    dress(body, pts, "trousers", "metal")
    parts = [body] + head("sp") + tunic("sp", cloth, trim)
    parts.append(cap("sp", "metal", r=HEAD_R * 1.08, cut=0.08))
    parts.append(cyl("sp_brim", (0, 0, HEAD_Z + 0.05), (0, 0, HEAD_Z + 0.08), HEAD_R * 1.34, HEAD_R * 1.28, "metal", verts=40))
    hr = hand_pos(pts, "R")
    hl = hand_pos(pts, "L")
    parts += spear("sp", hr.x, hr.y - 0.02, 2.15)
    parts += round_shield("sp", (hl.x + 0.05, -0.2, hl.z + 0.12), 0.34, cloth, "white" if trim == "gold" else "gold", trim)
    return join("Spearman_" + side_name, parts)


def knight(cloth, emblem, side_name):
    body, pts = skin_body("Kn_body", 62, "metal")
    body.data.materials.clear()
    body.data.materials.append(M["metal"])
    parts = [body]
    for sx in (1, -1):
        parts.append(sphere("kn_eyeslot", (sx * 0.14, -HEAD_R * 1.02, HEAD_Z - 0.02), 0.05, "eye", (0.9, 0.3, 0.6), 16))
    parts.append(cyl("kn_helm", (0, 0, HEAD_Z - HEAD_R * 0.95), (0, 0, HEAD_Z + HEAD_R * 0.9), HEAD_R * 1.04, HEAD_R * 0.98, "metal", verts=40, sub=1))
    parts.append(box("kn_slit", (0, -HEAD_R * 1.03, HEAD_Z - 0.02), (0.5, 0.03, 0.05), "dark", 0.01))
    parts.append(box("kn_crossV", (0, -HEAD_R * 1.03, HEAD_Z - 0.16), (0.06, 0.03, 0.22), emblem, 0.01))
    parts += tunic("kn", cloth, None)
    parts.append(cyl("kn_pauldL", (0.22, 0, 0.84), (0.22, 0, 0.9), 0.12, 0.09, "metal", verts=24, sub=1))
    parts.append(cyl("kn_pauldR", (-0.22, 0, 0.84), (-0.22, 0, 0.9), 0.12, 0.09, "metal", verts=24, sub=1))
    hr = hand_pos(pts, "R")
    hl = hand_pos(pts, "L")
    parts.append(cyl("kn_blade", (hr.x, hr.y - 0.05, hr.z), (hr.x, hr.y - 0.05, hr.z + 0.85), 0.035, 0.012, "metal", verts=4))
    parts.append(box("kn_guard", (hr.x, hr.y - 0.05, hr.z + 0.05), (0.2, 0.04, 0.04), "gold", 0.01))
    parts += heater_shield("kn", (hl.x + 0.05, -0.22, hl.z + 0.12), 0.27, 0.36, cloth, emblem)
    return join("Knight_" + side_name, parts)


figs = [
    base_figure(),
    militia("brown"),
    spearman("blue", "gold", "blue"),
    knight("blue", "gold", "blue"),
]
xs = [-2.4, -0.8, 0.8, 2.4]
for f, x in zip(figs, xs):
    f.location = (x, 0, 0)

red_sp = spearman("red", "white", "red")
red_kn = knight("red", "white", "red")
blue_sp, blue_kn = figs[2], figs[3]
for o in (red_sp, red_kn):
    o.location = (0, -500, 0)

ground_m = mat("c_ground", (0.36, 0.52, 0.22), 1.0)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
g = bpy.context.active_object
g.name = "Ground"
g.data.materials.append(ground_m)

world = bpy.data.worlds.get("ChibiWorld") or bpy.data.worlds.new("ChibiWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.66, 0.76, 0.9, 1)
bg.inputs[1].default_value = 0.5
scn.world = world

sun_d = bpy.data.lights.new("ChibiSun", "SUN")
sun_d.energy = 3.4
sun_d.angle = math.radians(10)
sun = bpy.data.objects.new("ChibiSun", sun_d)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))


def camera(name, lens, loc, target):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    o = bpy.data.objects.new(name, d)
    coll.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


cam_close = camera("ChibiClose", 50, (0.2, -9.5, 2.0), (0, 0, 1.0))


def place(src, loc, rotz=0.0):
    o = src.copy()
    coll.objects.link(o)
    o.location = loc
    o.rotation_euler = (0, 0, rotz)
    return o


BX = 40.0
for r in range(3):
    for c in range(6):
        place(blue_sp, (BX - 5 + (c - 2.5) * 1.5, -r * 1.5, 0))
        place(red_sp, (BX - 5 + (c - 2.5) * 1.5, 6 + r * 1.5, 0), math.pi)
for r in range(2):
    for c in range(4):
        place(blue_kn, (BX + 6 + (c - 1.5) * 1.9, -1 - r * 1.9, 0))
        place(red_kn, (BX + 6 + (c - 1.5) * 1.9, 7 + r * 1.9, 0), math.pi)
cam_battle = camera("ChibiBattle", 30, (BX, -22, 17), (BX, 3, 0))

for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scn.render.engine = eng
        break
    except TypeError:
        continue
scn.render.resolution_x = 1600
scn.render.resolution_y = 900
scn.render.resolution_percentage = 100
try:
    scn.eevee.taa_render_samples = 48
except Exception:
    pass
scn.view_settings.view_transform = "Standard"
scn.render.image_settings.file_format = "PNG"

for cam, fname in ((cam_close, "3-chibi-closeup.png"), (cam_battle, "4-chibi-battle.png")):
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)
scn.camera = cam_close
print("ok", len(scn.objects), sum(len(f.data.polygons) for f in figs))
