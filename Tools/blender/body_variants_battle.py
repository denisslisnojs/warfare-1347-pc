import bpy, math
from mathutils import Vector

scn = bpy.data.scenes["BodyVariants"]
bpy.context.window.scene = scn
coll = scn.collection
for o in list(scn.objects):
    if o.name.startswith("Copy_"):
        bpy.data.objects.remove(o, do_unlink=True)
labels = [o for o in scn.objects if o.type == "FONT"]
for t in labels:
    t.hide_render = True
for name in ("Naked_1", "Naked_2", "Naked_3"):
    scn.objects[name].hide_render = True
bx = {"1": -9.0, "2": 0.0, "3": 9.0}
for key, x0 in bx.items():
    src = scn.objects[f"Armored_{key}"]
    src.hide_render = True
    for r in range(3):
        for c in range(4):
            o = src.copy()
            o.name = f"Copy_{key}_{r}_{c}"
            coll.objects.link(o)
            o.hide_render = False
            o.location = (x0 + (c - 1.5) * 1.6, 40 + r * 1.6, 0)
            o.rotation_euler = (0, 0, 0)
cam = scn.objects["BVCam"]
old = bpy.data.objects.get("BVBattleCam")
if old: bpy.data.objects.remove(old, do_unlink=True)
d = bpy.data.cameras.new("BVBattleCam")
d.lens = 30
bc = bpy.data.objects.new("BVBattleCam", d)
coll.objects.link(bc)
target = Vector((0, 41.6, 0.6))
pitch = math.radians(54)
dist = 26.0
bc.location = target + Vector((0, -math.cos(pitch) * dist, math.sin(pitch) * dist))
bc.rotation_euler = (target - bc.location).to_track_quat("-Z", "Y").to_euler()
scn.camera = bc
scn.render.filepath = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\docs\style\6-body-variants-battle.png"
bpy.ops.render.render(write_still=True)
scn.camera = cam
for name in ("Naked_1", "Naked_2", "Naked_3", "Armored_1", "Armored_2", "Armored_3"):
    scn.objects[name].hide_render = False
for t in labels:
    t.hide_render = False
print("ok")
