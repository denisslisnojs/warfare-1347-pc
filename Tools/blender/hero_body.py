import bpy, bmesh, math, os, sys
from mathutils import Vector

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
FBX = os.path.join(ROOT, "Assets", "Art", "Characters", "Hero_Base.fbx")
BLEND = os.path.join(ROOT, "ArtSource", "hero_body.blend")
SHOTS = os.path.join(ROOT, "ArtSource", "renders", "hero_body")
os.makedirs(SHOTS, exist_ok=True)

scn = bpy.context.scene
for o in list(scn.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scn.collection


def mat(name, rgb, rough=0.65, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M = {
    "skin": mat("hero_skin", (0.86, 0.62, 0.47), 0.7),
    "eye": mat("hero_eye", (0.04, 0.035, 0.035), 0.35),
    "hair": mat("hero_hair", (0.3, 0.19, 0.11), 0.85),
    "brow": mat("hero_brow", (0.24, 0.15, 0.09), 0.85),
    "linen": mat("hero_linen", (0.86, 0.81, 0.69), 0.9),
    "cord": mat("hero_cord", (0.52, 0.42, 0.3), 0.9),
}

P = dict(leg=0.6, torso=0.58, neck=0.09, head=0.23, sw=0.29, hw=0.13, arm=0.64)
HZ = P["leg"]
TOP = HZ + P["torso"]
CZ = TOP + P["neck"] + P["head"] * 0.96
R = P["head"]


def select(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def convert(o):
    select([o])
    bpy.ops.object.convert(target="MESH")
    return o


def apply_tf(o):
    select([o])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def skin_body():
    pts = {
        "pelvis": ((0, 0, HZ + 0.03), (0.18, 0.13)),
        "waist": ((0, 0, HZ + 0.19), (0.165, 0.12)),
        "belly": ((0, 0, HZ + 0.3), (0.19, 0.135)),
        "chest": ((0, 0, HZ + 0.44), (0.245, 0.16)),
        "upper": ((0, 0, TOP - 0.06), (0.215, 0.15)),
        "neckbase": ((0, 0, TOP - 0.01), (0.13, 0.12)),
        "neck": ((0, 0, TOP + P["neck"] * 0.85), (0.1, 0.1)),
    }
    edges = [("pelvis", "waist"), ("waist", "belly"), ("belly", "chest"), ("chest", "upper"), ("upper", "neckbase"), ("neckbase", "neck")]
    sz = TOP - 0.1
    for side, sx in (("L", 1), ("R", -1)):
        sh = P["sw"]
        pts[f"shoulder{side}"] = ((sx * sh, 0, sz), (0.1, 0.1))
        pts[f"elbow{side}"] = ((sx * (sh + 0.3), 0, sz), (0.075, 0.075))
        pts[f"wrist{side}"] = ((sx * (sh + 0.55), 0, sz), (0.065, 0.065))
        pts[f"hand{side}"] = ((sx * (sh + P["arm"]), 0, sz), (0.092, 0.092))
        pts[f"thumb{side}"] = ((sx * (sh + 0.6), -0.07, sz + 0.02), (0.04, 0.04))
        pts[f"thumbtip{side}"] = ((sx * (sh + 0.645), -0.11, sz + 0.03), (0.035, 0.035))
        pts[f"hip{side}"] = ((sx * P["hw"], 0, HZ), (0.125, 0.125))
        pts[f"thigh{side}"] = ((sx * P["hw"] * 1.03, 0, HZ * 0.74), (0.11, 0.11))
        pts[f"knee{side}"] = ((sx * P["hw"] * 1.05, 0, HZ * 0.5), (0.088, 0.088))
        pts[f"calf{side}"] = ((sx * P["hw"] * 1.07, 0.01, HZ * 0.33), (0.092, 0.092))
        pts[f"ankle{side}"] = ((sx * P["hw"] * 1.08, 0, 0.11), (0.07, 0.07))
        pts[f"toe{side}"] = ((sx * P["hw"] * 1.08, -0.17, 0.06), (0.07, 0.06))
        edges += [("upper", f"shoulder{side}"), (f"shoulder{side}", f"elbow{side}"), (f"elbow{side}", f"wrist{side}"), (f"wrist{side}", f"hand{side}"),
                  (f"wrist{side}", f"thumb{side}"), (f"thumb{side}", f"thumbtip{side}"),
                  ("pelvis", f"hip{side}"), (f"hip{side}", f"thigh{side}"), (f"thigh{side}", f"knee{side}"), (f"knee{side}", f"calf{side}"),
                  (f"calf{side}", f"ankle{side}"), (f"ankle{side}", f"toe{side}")]
    names = list(pts)
    me = bpy.data.meshes.new("hero_body")
    me.from_pydata([pts[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in edges], [])
    o = bpy.data.objects.new("hero_body", me)
    coll.objects.link(o)
    mod = o.modifiers.new("Skin", "SKIN")
    mod.use_smooth_shade = True
    sv = me.skin_vertices[0].data
    for i, n in enumerate(names):
        sv[i].radius = pts[n][1]
        sv[i].use_root = n == "pelvis"
    sub = o.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    convert(o)
    return o, {n: Vector(pts[n][0]) for n in names}


def sphere(name, loc, r, scale=(1, 1, 1), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    return apply_tf(o)


def box(name, loc, size, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    apply_tf(o)
    if bevel > 0:
        b = o.modifiers.new("B", "BEVEL")
        b.width = bevel
        b.segments = 3
        convert(o)
    return o


def head_parts():
    skull = sphere("hero_head", (0, 0, CZ), R, (0.9, 0.95, 1.12))
    jaw = sphere("hero_jaw", (0, -R * 0.12, CZ - R * 0.42), R * 0.62, (1.0, 0.95, 0.8))
    ears = [sphere("hero_ear", (sx * R * 0.86, R * 0.02, CZ - R * 0.04), R * 0.2, (0.45, 0.75, 1.0), 16) for sx in (1, -1)]
    return [skull, jaw] + ears


def face():
    ey = -R * 0.89
    ex = R * 0.3
    parts = []
    for sx in (1, -1):
        parts.append(sphere("hero_eye", (sx * ex, ey, CZ + R * 0.02), R * 0.085, (0.85, 0.45, 1.15), 16))
        b = box("hero_brow", (sx * ex, ey - R * 0.03, CZ + R * 0.2), (R * 0.3, R * 0.07, R * 0.07), R * 0.025)
        b.rotation_euler = (0, sx * math.radians(-6), 0)
        parts.append(apply_tf(b))
    nose = sphere("hero_nose", (0, ey - R * 0.1, CZ - R * 0.14), R * 0.13, (0.8, 1.0, 1.15), 16)
    return parts, nose


def fuse(objs, voxel):
    select(objs)
    bpy.ops.object.join()
    o = bpy.context.active_object
    rm = o.modifiers.new("Remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    rm.use_smooth_shade = True
    convert(o)
    vg = o.vertex_groups.new(name="blend")
    zj = TOP + P["neck"] * 0.9
    for v in o.data.vertices:
        w = math.exp(-((v.co.z - zj) / (R * 0.4)) ** 2) * (1.0 if math.hypot(v.co.x, v.co.y) < R * 1.1 else 0.0)
        if w > 0.01:
            vg.add([v.index], w, "REPLACE")
    sm = o.modifiers.new("Blend", "SMOOTH")
    sm.factor = 1.0
    sm.iterations = 25
    sm.vertex_group = "blend"
    convert(o)
    o.vertex_groups.clear()
    soft = o.modifiers.new("Soft", "SMOOTH")
    soft.factor = 0.4
    soft.iterations = 3
    convert(o)
    return o


def decimate(o, faces):
    ratio = min(1.0, faces / max(1, len(o.data.polygons)))
    d = o.modifiers.new("Dec", "DECIMATE")
    d.ratio = ratio
    convert(o)
    return o


def paint_underwear(o):
    o.data.materials.clear()
    for k in ("skin", "linen", "cord"):
        o.data.materials.append(M[k])
    lo, hi = HZ - 0.22, HZ + 0.12
    for poly in o.data.polygons:
        z = poly.center.z
        if hi - 0.035 <= z <= hi:
            poly.material_index = 2
        elif lo <= z < hi - 0.035:
            poly.material_index = 1
    for poly in o.data.polygons:
        poly.use_smooth = True


def hair():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=R * 1.07, location=(0, R * 0.06, CZ + R * 0.07))
    o = bpy.context.active_object
    o.name = "hero_hair"
    o.scale = (0.92, 0.97, 1.1)
    apply_tf(o)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    cut = [v for v in bm.verts if (v.co.z < CZ + R * 0.12 and v.co.y < -R * 0.2) or v.co.z < CZ - R * 0.5]
    bmesh.ops.delete(bm, geom=cut, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    sol = o.modifiers.new("S", "SOLIDIFY")
    sol.thickness = R * 0.05
    convert(o)
    return o


def bone_layout(p):
    B = {}
    B["Hips"] = (Vector((0, 0, HZ - 0.02)), Vector((0, 0, HZ + 0.1)), None)
    B["Spine"] = (Vector((0, 0, HZ + 0.1)), Vector((0, 0, HZ + 0.26)), "Hips")
    B["Spine1"] = (Vector((0, 0, HZ + 0.26)), Vector((0, 0, HZ + 0.4)), "Spine")
    B["Spine2"] = (Vector((0, 0, HZ + 0.4)), Vector((0, 0, TOP - 0.02)), "Spine1")
    B["Neck"] = (Vector((0, 0, TOP - 0.02)), Vector((0, 0, TOP + P["neck"])), "Spine2")
    B["Head"] = (Vector((0, 0, TOP + P["neck"])), Vector((0, 0, CZ + R * 1.12)), "Neck")
    for side, s in (("Left", "L"), ("Right", "R")):
        sh = p[f"shoulder{s}"]
        B[f"{side}Shoulder"] = (Vector((sh.x * 0.3, 0, sh.z + 0.02)), sh, "Spine2")
        B[f"{side}Arm"] = (sh, p[f"elbow{s}"], f"{side}Shoulder")
        B[f"{side}ForeArm"] = (p[f"elbow{s}"], p[f"wrist{s}"], f"{side}Arm")
        tip = p[f"hand{s}"] + (p[f"hand{s}"] - p[f"wrist{s}"]).normalized() * 0.08
        B[f"{side}Hand"] = (p[f"wrist{s}"], tip, f"{side}ForeArm")
        B[f"{side}UpLeg"] = (p[f"hip{s}"], p[f"knee{s}"], "Hips")
        B[f"{side}Leg"] = (p[f"knee{s}"], p[f"ankle{s}"], f"{side}UpLeg")
        B[f"{side}Foot"] = (p[f"ankle{s}"], p[f"toe{s}"], f"{side}Leg")
        B[f"{side}ToeBase"] = (p[f"toe{s}"], p[f"toe{s}"] + Vector((0, -0.08, 0)), f"{side}Foot")
    return B


def armature(p):
    data = bpy.data.armatures.new("Hero_Base_rig")
    arm = bpy.data.objects.new("Hero_Base_Armature", data)
    coll.objects.link(arm)
    select([arm])
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones
    layout = bone_layout(p)
    for name, (head, tail, parent) in layout.items():
        b = eb.new(name)
        b.head, b.tail = head, tail
        b.roll = 0
    for name, (head, tail, parent) in layout.items():
        if parent:
            eb[name].parent = eb[parent]
            eb[name].use_connect = (eb[parent].tail - head).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def rigid(o, bone):
    vg = o.vertex_groups.new(name=bone)
    vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")


body, pts = skin_body()
nose_parts, nose = face()
body = fuse([body] + head_parts(), 0.011)
decimate(body, 9000)
paint_underwear(body)
arm = armature(pts)
select([body, arm], arm)
bpy.ops.object.parent_set(type="ARMATURE_AUTO")

extras = []
for o in nose_parts:
    o.data.materials.clear()
    o.data.materials.append(M["eye"] if o.name.startswith("hero_eye") else M["brow"])
    extras.append(o)
nose.data.materials.clear()
nose.data.materials.append(M["skin"])
extras.append(nose)
h = hair()
h.data.materials.clear()
h.data.materials.append(M["hair"])
extras.append(h)
for o in extras:
    for poly in o.data.polygons:
        poly.use_smooth = True
    rigid(o, "Head")
select([body] + extras, body)
bpy.ops.object.join()
body.name = "Hero_Base"
body.parent = arm
if not any(m.type == "ARMATURE" for m in body.modifiers):
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = arm

select([arm, body], arm)
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, apply_scale_options="FBX_SCALE_ALL",
                         axis_forward="-Z", axis_up="Y", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False,
                         mesh_smooth_type="FACE", use_mesh_modifiers=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)
print("hero", len(body.data.vertices), "verts", len(body.data.polygons), "faces", "bones", len(arm.data.bones))

world = bpy.data.worlds.new("HeroWorld")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.62, 0.68, 0.76, 1)
bg.inputs[1].default_value = 0.65
scn.world = world
sun = bpy.data.objects.new("HeroSun", bpy.data.lights.new("HeroSun", "SUN"))
sun.data.energy = 3.2
sun.data.angle = math.radians(12)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-28))
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(mat("hero_ground", (0.33, 0.27, 0.2), 1.0))
cam = bpy.data.objects.new("HeroCam", bpy.data.cameras.new("HeroCam"))
coll.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.45
scn.camera = cam
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scn.render.engine = eng
        break
    except TypeError:
        continue
scn.render.resolution_x, scn.render.resolution_y = 1100, 1000
scn.view_settings.view_transform = "Standard"
target = Vector((0, 0, 0.98))
for name, yaw in (("front", 0), ("three_quarter", 35), ("side", 90), ("back", 180)):
    d = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0.12)).normalized()
    cam.location = target + d * 6
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = os.path.join(SHOTS, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("ok")
