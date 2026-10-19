import bpy, os, math
from mathutils import Vector

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
SRC = os.path.join(ROOT, "Tools", "blender", "chibi_style_test.py")
OUT = os.path.join(ROOT, "Assets", "Art", "Characters")
BLEND = os.path.join(ROOT, "ArtSource", "chibi.blend")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.dirname(BLEND), exist_ok=True)

code = open(SRC, encoding="utf-8").read()
code = code.split("figs = [")[0].replace('"Chibi"', '"ChibiRig"')
ns = {}
exec(compile(code, SRC, "exec"), ns)
scn, coll, M = ns["scn"], ns["coll"], ns["M"]
HEAD_Z, HEAD_R = ns["HEAD_Z"], ns["HEAD_R"]


def bone_layout(pts):
    p = lambda n: Vector(pts[n][0])
    B = {}
    B["Hips"] = (Vector((0, 0, 0.5)), Vector((0, 0, 0.6)), None)
    B["Spine"] = (Vector((0, 0, 0.6)), Vector((0, 0, 0.7)), "Hips")
    B["Spine1"] = (Vector((0, 0, 0.7)), Vector((0, 0, 0.78)), "Spine")
    B["Spine2"] = (Vector((0, 0, 0.78)), Vector((0, 0, 0.86)), "Spine1")
    B["Neck"] = (Vector((0, 0, 0.86)), Vector((0, 0, 0.92)), "Spine2")
    B["Head"] = (Vector((0, 0, 0.92)), Vector((0, 0, HEAD_Z + HEAD_R)), "Neck")
    for side, s in (("Left", "L"), ("Right", "R")):
        sh = p(f"shoulder{s}")
        B[f"{side}Shoulder"] = (Vector((sh.x * 0.25, 0, sh.z)), sh, "Spine2")
        B[f"{side}Arm"] = (sh, p(f"elbow{s}"), f"{side}Shoulder")
        B[f"{side}ForeArm"] = (p(f"elbow{s}"), p(f"wrist{s}"), f"{side}Arm")
        hand_tip = p(f"hand{s}") + (p(f"hand{s}") - p(f"wrist{s}")).normalized() * 0.06
        B[f"{side}Hand"] = (p(f"wrist{s}"), hand_tip, f"{side}ForeArm")
        hip = p(f"hip{s}")
        B[f"{side}UpLeg"] = (hip, p(f"knee{s}"), "Hips")
        B[f"{side}Leg"] = (p(f"knee{s}"), p(f"ankle{s}"), f"{side}UpLeg")
        B[f"{side}Foot"] = (p(f"ankle{s}"), p(f"toe{s}"), f"{side}Leg")
        B[f"{side}ToeBase"] = (p(f"toe{s}"), p(f"toe{s}") + Vector((0, -0.07, 0)), f"{side}Foot")
    return B


def make_armature(name, pts):
    arm_data = bpy.data.armatures.new(name + "_rig")
    arm = bpy.data.objects.new(name + "_Armature", arm_data)
    coll.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    layout = bone_layout(pts)
    for bname, (head, tail, parent) in layout.items():
        b = eb.new(bname)
        b.head, b.tail = head, tail
        b.roll = 0
    for bname, (head, tail, parent) in layout.items():
        if parent:
            eb[bname].parent = eb[parent]
            eb[bname].use_connect = (eb[parent].tail - head).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    return arm


def skin_auto(mesh, arm):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


def rigid(objs, bone):
    for o in objs:
        vg = o.vertex_groups.new(name=bone)
        vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")


def merge(name, body, extras, arm):
    bpy.ops.object.select_all(action="DESELECT")
    for o in [body] + extras:
        o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = name
    body.parent = arm
    if not any(m.type == "ARMATURE" for m in body.modifiers):
        mod = body.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
    return body


def apply_tf(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def build_base():
    body, pts = ns["skin_body"]("Chibi_Base", 0, "skin")
    arm = make_armature("Chibi_Base", pts)
    skin_auto(body, arm)
    head = ns["head"]("base")
    apply_tf(head)
    rigid(head, "Head")
    return merge("Chibi_Base", body, head, arm), arm, pts


def build_spearman(cloth="blue", trim="gold"):
    body, pts = ns["skin_body"]("Chibi_Spearman", 0, "trousers")
    ns["dress"](body, pts, "trousers", "metal")
    arm = make_armature("Chibi_Spearman", pts)
    skin_auto(body, arm)
    head = ns["head"]("sp")
    helm = [ns["cap"]("sp", "metal", r=HEAD_R * 1.08, cut=0.08),
            ns["cyl"]("sp_brim", (0, 0, HEAD_Z + 0.05), (0, 0, HEAD_Z + 0.08), HEAD_R * 1.34, HEAD_R * 1.28, "metal", verts=40)]
    tunic = ns["tunic"]("sp", cloth, trim)
    hr = Vector(pts["handR"][0])
    hl = Vector(pts["handL"][0])
    spear = ns["spear"]("sp", hr.x, hr.y - 0.02, 1.9)
    for o in spear:
        o.location.z -= 0.75
    shield = ns["round_shield"]("sp", (hl.x, -0.12, hl.z), 0.34, cloth, "white" if trim == "gold" else "gold", trim)
    every = head + helm + tunic + spear + shield
    apply_tf(every)
    rigid(head + helm, "Head")
    rigid(spear, "RightHand")
    rigid(shield, "LeftHand")
    bpy.ops.object.select_all(action="DESELECT")
    for o in tunic:
        o.select_set(True)
    bpy.context.view_layer.objects.active = tunic[0]
    bpy.ops.object.join()
    tunic_obj = bpy.context.active_object
    skin_auto(tunic_obj, arm)
    tunic_obj.modifiers.clear()
    tunic_obj.parent = None
    return merge("Chibi_Spearman", body, head + helm + [tunic_obj] + spear + shield, arm), arm, pts


def export(arm, mesh, filename):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, filename),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=False,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
    )


base, base_arm, _ = build_base()
spear_mesh, spear_arm, _ = build_spearman()

export(base_arm, base, "Chibi_Base.fbx")
export(spear_arm, spear_mesh, "Chibi_Spearman.fbx")

base_arm.location.x = -1.2
spear_arm.location.x = 1.2
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)
print("groups", sorted(g.name for g in spear_mesh.vertex_groups)[:30], "verts", len(spear_mesh.data.vertices))
