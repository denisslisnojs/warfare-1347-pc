import bpy, bmesh, math, os
from mathutils import Vector

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
SRC = os.path.join(ROOT, "Tools", "blender", "chibi_style_test.py")
OUT = os.path.join(ROOT, "docs", "style", "5-body-variants.png")

code = open(SRC, encoding="utf-8").read().split("figs = [")[0].replace('"Chibi"', '"BodyVariants"')
ns = {}
exec(compile(code, SRC, "exec"), ns)
scn, coll, M = ns["scn"], ns["coll"], ns["M"]
mat, finish, apply_all, subsurf = ns["mat"], ns["finish"], ns["apply_all"], ns["subsurf"]
sphere, cyl, box, join, heater = ns["sphere"], ns["cyl"], ns["box"], ns["join"], ns["heater_shield"]
M["hair"] = mat("bv_hair", (0.33, 0.22, 0.13), 0.8)
M["plume"] = mat("bv_plume", (0.92, 0.94, 0.98), 0.7)
M["blue"] = mat("bv_blue", (0.1, 0.24, 0.72), 0.7)
M["boots"] = mat("bv_boots", (0.22, 0.14, 0.09), 0.7)

VARIANTS = [
    ("1", dict(leg=0.42, torso=0.42, neck=0.05, head=0.42, sw=0.2, hw=0.1, arm=0.42, thigh=0.1, calf=0.085, upper=0.085, fore=0.065, hand=0.078, pelvis=0.2, belly=0.215, chest=0.215, neckr=0.12, foot=0.09, face="chibi")),
    ("2", dict(leg=0.6, torso=0.58, neck=0.09, head=0.23, sw=0.29, hw=0.13, arm=0.64, thigh=0.115, calf=0.095, upper=0.09, fore=0.085, hand=0.1, pelvis=0.18, belly=0.2, chest=0.25, neckr=0.105, foot=0.13, face="hero")),
    ("3", dict(leg=0.84, torso=0.56, neck=0.07, head=0.135, sw=0.2, hw=0.1, arm=0.7, thigh=0.095, calf=0.072, upper=0.068, fore=0.058, hand=0.06, pelvis=0.16, belly=0.15, chest=0.18, neckr=0.06, foot=0.11, face="real")),
]


def skeleton(P, drop):
    s = math.radians(drop)
    hz = P["leg"]
    top = hz + P["torso"]
    pts = {
        "pelvis": ((0, 0, hz + 0.03), P["pelvis"]),
        "belly": ((0, 0, hz + P["torso"] * 0.38), P["belly"]),
        "chest": ((0, 0, hz + P["torso"] * 0.72), P["chest"]),
        "neckbase": ((0, 0, top - 0.03), P["neckr"] * 1.25),
        "neck": ((0, 0, top + P["neck"] * 0.8), P["neckr"]),
    }
    edges = [("pelvis", "belly"), ("belly", "chest"), ("chest", "neckbase"), ("neckbase", "neck")]
    for side, sx in (("L", 1), ("R", -1)):
        hip = Vector((sx * P["hw"], 0, hz))
        pts[f"hip{side}"] = (tuple(hip), P["thigh"])
        pts[f"knee{side}"] = ((sx * P["hw"] * 1.05, 0, hz * 0.52), P["calf"] * 1.05)
        pts[f"ankle{side}"] = ((sx * P["hw"] * 1.08, 0, P["foot"] * 0.9), P["calf"] * 0.85)
        pts[f"toe{side}"] = ((sx * P["hw"] * 1.08, -P["foot"] * 1.3, P["foot"] * 0.55), P["calf"] * 0.85)
        sh = Vector((sx * P["sw"], 0, top - P["upper"] * 1.2))
        d = Vector((sx * math.cos(s), 0, -math.sin(s)))
        pts[f"shoulder{side}"] = (tuple(sh), P["upper"])
        pts[f"elbow{side}"] = (tuple(sh + d * P["arm"] * 0.46), P["fore"])
        pts[f"wrist{side}"] = (tuple(sh + d * P["arm"] * 0.86), P["fore"] * 0.85)
        pts[f"hand{side}"] = (tuple(sh + d * P["arm"]), P["hand"])
        edges += [("pelvis", f"hip{side}"), (f"hip{side}", f"knee{side}"), (f"knee{side}", f"ankle{side}"), (f"ankle{side}", f"toe{side}"),
                  ("chest", f"shoulder{side}"), (f"shoulder{side}", f"elbow{side}"), (f"elbow{side}", f"wrist{side}"), (f"wrist{side}", f"hand{side}")]
    names = list(pts)
    me = bpy.data.meshes.new("bv_body")
    me.from_pydata([pts[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in edges], [])
    o = bpy.data.objects.new("bv_body", me)
    coll.objects.link(o)
    mod = o.modifiers.new("Skin", "SKIN")
    mod.use_smooth_shade = True
    sv = me.skin_vertices[0].data
    for i, n in enumerate(names):
        r = pts[n][1]
        sv[i].radius = (r, r * (0.8 if n in ("pelvis", "belly", "chest") else 1.0))
        sv[i].use_root = n == "pelvis"
    subsurf(o, 2)
    apply_all(o)
    finish(o, "skin")
    return o, pts


def head(P):
    hz = P["leg"] + P["torso"] + P["neck"]
    r = P["head"]
    cz = hz + r * (0.92 if P["face"] == "chibi" else 0.96)
    parts = [sphere("bv_head", (0, 0, cz), r, "skin", (1.03, 0.98, 0.94) if P["face"] == "chibi" else (0.9, 0.95, 1.12))]
    ey = -r * (0.93 if P["face"] == "chibi" else 0.86)
    ex = r * (0.33 if P["face"] == "chibi" else 0.3)
    es = r * (0.115 if P["face"] == "chibi" else 0.075)
    for sx in (1, -1):
        parts.append(sphere("bv_eye", (sx * ex, ey, cz - r * 0.04), es, "eye", (0.85, 0.45, 1.1), 16))
    if P["face"] != "chibi":
        parts.append(sphere("bv_nose", (0, ey - r * 0.08, cz - r * 0.2), r * 0.13, "skin", (0.8, 1.0, 1.1), 16))
        for sx in (1, -1):
            parts.append(box("bv_brow", (sx * ex, ey - r * 0.02, cz + r * 0.13), (r * 0.26, r * 0.06, r * 0.06), "hair", r * 0.02))
    return parts, cz


def fuse(body, head_obj, zj, r, voxel=0.009):
    bpy.ops.object.select_all(action="DESELECT")
    for o in (body, head_obj):
        o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    rm = body.modifiers.new("Remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    rm.use_smooth_shade = True
    apply_all(body)
    vg = body.vertex_groups.new(name="blend")
    for v in body.data.vertices:
        co = v.co
        radial = math.hypot(co.x, co.y)
        w = math.exp(-((co.z - zj) / (r * 0.38)) ** 2) * (1.0 if radial < r * 1.1 else 0.0)
        if w > 0.01:
            vg.add([v.index], w, "REPLACE")
    sm = body.modifiers.new("Blend", "SMOOTH")
    sm.factor = 1.0
    sm.iterations = 30
    sm.vertex_group = "blend"
    apply_all(body)
    sm2 = body.modifiers.new("Soft", "SMOOTH")
    sm2.factor = 0.4
    sm2.iterations = 3
    apply_all(body)
    body.data.materials.clear()
    body.data.materials.append(M["skin"])
    finish(body, "skin")
    return body


def hair(P, cz):
    r = P["head"]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r * 1.06, location=(0, r * 0.05, cz + r * 0.05))
    o = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < r * 0.05 and v.co.y < r * 0.3], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    return finish(o, "hair")


def dress(body, pts, P):
    me = body.data
    for k in ("trousers", "metal", "boots"):
        me.materials.append(M[k])
    hands = [Vector(pts["handL"][0]), Vector(pts["handR"][0])]
    hz = P["leg"]
    for poly in me.polygons:
        c = poly.center
        if c.z < P["foot"] * 1.6:
            poly.material_index = 3
        elif c.z < hz:
            poly.material_index = 1
        elif c.z < hz + P["torso"] + P["neck"] * 0.5 and min((c - h).length for h in hands) > P["hand"] * 1.3:
            poly.material_index = 2


def armor(P, cz, pts):
    hz, top = P["leg"], P["leg"] + P["torso"]
    r = P["head"]
    parts = []
    bottom = hz - P["leg"] * 0.32
    parts.append(cyl("bv_coat", (0, 0, bottom), (0, 0, top + P["neck"] * 0.2), P["pelvis"] * 1.5, P["chest"] * 1.1, "blue", sy=0.8, sub=1))
    parts.append(cyl("bv_belt", (0, 0, hz + 0.02), (0, 0, hz + 0.02 + max(0.04, P["torso"] * 0.08)), P["belly"] * 1.17, P["belly"] * 1.17, "leather", sy=0.82))
    fy = -P["chest"] * 1.1 * 0.8 - 0.006
    mid = hz + P["torso"] * 0.6
    vh = P["torso"] * 0.55
    for sx in (1, -1):
        b = box("bv_v", (0, 0, 0), (P["chest"] * 0.16, 0.02, vh), "gold", 0.004)
        b.rotation_euler = (0, sx * math.radians(28), 0)
        bpy.ops.object.select_all(action="DESELECT")
        b.select_set(True)
        bpy.context.view_layer.objects.active = b
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        b.location = (sx * vh * 0.24, fy, mid)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        parts.append(b)
    parts.append(cyl("bv_aventail", (0, 0, top - 0.03), (0, 0, cz - r * 0.78), P["neckr"] * 1.75, P["neckr"] * 1.25, "metal", verts=32, sub=1))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r * 1.1, location=(0, 0, cz + r * 0.04))
    helm = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(helm.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -r * 0.1 * (1 if P["face"] != "chibi" else 0.3)], context="VERTS")
    bm.to_mesh(helm.data)
    bm.free()
    sol = helm.modifiers.new("S", "SOLIDIFY")
    sol.thickness = r * 0.06
    helm.scale = (1.0, 1.05, 1.08)
    apply_all(helm)
    parts.append(finish(helm, "metal"))
    parts.append(cyl("bv_brim", (0, 0, cz - r * 0.08), (0, 0, cz - r * 0.0), r * 1.14, r * 1.12, "gold", verts=40))
    parts.append(cyl("bv_plume", (0, r * 0.15, cz + r * 1.0), (0, r * 0.5, cz + r * 1.8), r * 0.22, r * 0.08, "plume", verts=12, sub=1))
    parts.append(cyl("bv_plume2", (0, r * 0.05, cz + r * 1.0), (0, r * 0.3, cz + r * 1.55), r * 0.2, r * 0.06, "blue", verts=12, sub=1))
    hl, hr = Vector(pts["handL"][0]), Vector(pts["handR"][0])
    sw_, sh_ = P["torso"] * 0.42, P["torso"] * 0.58
    parts += heater("bv_sh", (hl.x + 0.02, -P["chest"] * 1.15, hl.z + sh_ * 0.35), sw_, sh_, "blue", "gold")
    blade = P["arm"] * 1.25
    parts.append(cyl("bv_grip", (hr.x, hr.y - P["hand"] * 0.6, hr.z - P["hand"]), (hr.x, hr.y - P["hand"] * 0.6, hr.z + P["hand"]), P["hand"] * 0.3, P["hand"] * 0.3, "leather", verts=10))
    parts.append(box("bv_guard", (hr.x, hr.y - P["hand"] * 0.6, hr.z + P["hand"] * 1.1), (blade * 0.32, P["hand"] * 0.35, P["hand"] * 0.3), "gold", 0.005))
    parts.append(box("bv_blade", (hr.x, hr.y - P["hand"] * 0.6, hr.z + P["hand"] * 1.2 + blade * 0.5), (P["hand"] * 0.55, P["hand"] * 0.14, blade), "metal", 0.004))
    return parts


figures = []
def fused_body(P):
    body, pts = skeleton(P, 62)
    hp, cz = head(P)
    if P["face"] != "chibi":
        zj = P["leg"] + P["torso"] + P["neck"] * 0.9
        body = fuse(body, hp[0], zj, P["head"])
        hp = hp[1:]
    return body, pts, hp, cz


for key, P in VARIANTS:
    body, pts, hp, cz = fused_body(P)
    naked = join(f"Naked_{key}", [body] + hp + [hair(P, cz)])
    body2, pts2, hp2, cz2 = fused_body(P)
    dress(body2, pts2, P)
    dressed = join(f"Armored_{key}", [body2] + hp2 + armor(P, cz2, pts2))
    figures.append((key, naked, dressed))

x = -5.2
for key, naked, dressed in figures:
    naked.location = (x, 0, 0)
    dressed.location = (x + 1.15, 0, 0)
    bpy.ops.object.text_add(location=(x + 0.58, 0, 2.35), rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object
    t.data.body = key
    t.data.size = 0.42
    t.data.align_x = "CENTER"
    t.data.materials.append(M["white"])
    x += 3.6

ground = bpy.data.materials.get("c_ground") or mat("c_ground", (0.36, 0.52, 0.22), 1.0)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
g = bpy.context.active_object
g.data.materials.append(ground)
world = bpy.data.worlds.get("ChibiWorld") or bpy.data.worlds.new("ChibiWorld")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.66, 0.76, 0.9, 1)
bg.inputs[1].default_value = 0.5
scn.world = world
sun_d = bpy.data.lights.new("BVSun", "SUN")
sun_d.energy = 3.4
sun_d.angle = math.radians(10)
sun = bpy.data.objects.new("BVSun", sun_d)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
cam_d = bpy.data.cameras.new("BVCam")
cam_d.lens = 40
cam = bpy.data.objects.new("BVCam", cam_d)
coll.objects.link(cam)
cam.location = (-0.5, -11.5, 1.75)
cam.rotation_euler = (Vector((-0.5, 0, 1.05)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scn.camera = cam
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scn.render.engine = eng
        break
    except TypeError:
        continue
scn.render.resolution_x, scn.render.resolution_y = 1800, 900
scn.view_settings.view_transform = "Standard"
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("ok", [f[1].name for f in figures])
