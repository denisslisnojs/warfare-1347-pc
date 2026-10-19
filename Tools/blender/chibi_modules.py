import bpy, os
from mathutils import Vector

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
RIG = os.path.join(ROOT, "Tools", "blender", "chibi_rig.py")
CHAR_OUT = os.path.join(ROOT, "Assets", "Art", "Characters")
EQUIP_OUT = os.path.join(ROOT, "Assets", "Art", "Equipment")
BLEND = os.path.join(ROOT, "ArtSource", "chibi_modules.blend")
os.makedirs(EQUIP_OUT, exist_ok=True)

code = open(RIG, encoding="utf-8").read()
code = code.split("base, base_arm, _ = build_base()")[0].replace('"ChibiRig"', '"ChibiModules"')
code = code.replace('code = code.split("figs = [")[0].replace(\'"Chibi"\', \'"ChibiRig"\')', 'code = code.split("figs = [")[0].replace(\'"Chibi"\', \'"ChibiModules"\')')
rig = {"__file__": RIG}
exec(compile(code, RIG, "exec"), rig)
ns = rig["ns"]
coll = rig["coll"]
HEAD_Z, HEAD_R = rig["HEAD_Z"], rig["HEAD_R"]


def build_soldier(cloth="blue", trim="gold"):
    body, pts = ns["skin_body"]("Chibi_Soldier", 0, "trousers")
    ns["dress"](body, pts, "trousers", "metal")
    arm = rig["make_armature"]("Chibi_Soldier", pts)
    rig["skin_auto"](body, arm)
    head = ns["head"]("so")
    helm = [ns["cap"]("so", "metal", r=HEAD_R * 1.08, cut=0.08),
            ns["cyl"]("so_brim", (0, 0, HEAD_Z + 0.05), (0, 0, HEAD_Z + 0.08), HEAD_R * 1.34, HEAD_R * 1.28, "metal", verts=40)]
    tunic = ns["tunic"]("so", cloth, trim)
    rig["apply_tf"](head + helm + tunic)
    rig["rigid"](head + helm, "Head")
    bpy.ops.object.select_all(action="DESELECT")
    for o in tunic:
        o.select_set(True)
    bpy.context.view_layer.objects.active = tunic[0]
    bpy.ops.object.join()
    tunic_obj = bpy.context.active_object
    rig["skin_auto"](tunic_obj, arm)
    tunic_obj.modifiers.clear()
    tunic_obj.parent = None
    return rig["merge"]("Chibi_Soldier", body, head + helm + [tunic_obj], arm), arm


def join_static(name, parts):
    rig["apply_tf"](parts)
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


def sword():
    parts = [
        ns["cyl"]("sw_grip", (0, 0, -0.1), (0, 0, 0.05), 0.026, 0.026, "leather", verts=12),
        ns["sphere"]("sw_pommel", (0, 0, -0.12), 0.04, "gold", (1, 1, 1), 16),
        ns["box"]("sw_guard", (0, 0, 0.065), (0.26, 0.045, 0.04), "gold", 0.01),
        ns["box"]("sw_blade", (0, 0, 0.43), (0.075, 0.018, 0.7), "metal", 0.006),
        ns["cyl"]("sw_tip", (0, 0, 0.78), (0, 0, 0.88), 0.037, 0.002, "metal", verts=4),
    ]
    return join_static("Sword", parts)


def round_shield():
    parts = ns["round_shield"]("rs", (0, -0.05, 0), 0.34, "blue", "white", "gold")
    parts.append(ns["box"]("rs_strap", (0, 0.0, 0), (0.05, 0.03, 0.2), "leather", 0.005))
    return join_static("Shield_Round", parts)


def spear():
    parts = [
        ns["cyl"]("sp_shaft", (0, 0, -0.65), (0, 0, 1.3), 0.024, 0.021, "wood", verts=10),
        ns["cyl"]("sp_tip", (0, 0, 1.3), (0, 0, 1.55), 0.055, 0.002, "metal", verts=8),
        ns["cyl"]("sp_socket", (0, 0, 1.25), (0, 0, 1.32), 0.03, 0.03, "metal", verts=10),
    ]
    return join_static("Spear", parts)


def export_static(obj, filename):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(EQUIP_OUT, filename),
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
    )


soldier, soldier_arm = build_soldier()
rig["export"](soldier_arm, soldier, "Chibi_Soldier.fbx")

items = [(sword(), "Sword.fbx"), (round_shield(), "Shield_Round.fbx"), (spear(), "Spear.fbx")]
for i, (o, fname) in enumerate(items):
    export_static(o, fname)
    o.location = (1.0 + i * 0.8, 0, 1.0)

bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)
print("exported", [f for _, f in items], "soldier verts", len(soldier.data.vertices))
