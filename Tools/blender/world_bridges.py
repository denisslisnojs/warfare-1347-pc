import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

SCENE = "WorldBridges"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())

M.update({
    "bridge_stone": mat("env_stone_grey", (0.62, 0.6, 0.55), 0.9),
    "bridge_plank": mat("env_plank", (0.56, 0.41, 0.26), 0.85),
    "bridge_beam": mat("env_beam", (0.36, 0.23, 0.13), 0.85),
})

for o in list(coll.objects):
    bpy.data.objects.remove(o, do_unlink=True)


def stone_bridge():
    box((0, 0, 0.2), (1.0, 0.36, 0.07), "bridge_stone")
    for sy in (-1, 1):
        box((0, sy * 0.165, 0.27), (1.0, 0.03, 0.08), "bridge_stone")
    for x in (-0.47, -0.16, 0.16, 0.47):
        box((x, 0, -0.05), (0.09, 0.3, 0.46), "bridge_stone")
    for x0, x1 in ((-0.47, -0.16), (-0.16, 0.16), (0.16, 0.47)):
        cx = (x0 + x1) / 2
        span = x1 - x0
        for k in range(5):
            t = (k + 0.5) / 5
            ang = math.pi * t
            z = 0.04 + math.sin(ang) * 0.1
            box((x0 + span * t, 0, z + 0.06), (span / 5 + 0.01, 0.32, 0.04), "bridge_stone")


def wood_bridge():
    box((0, 0, 0.18), (1.0, 0.3, 0.035), "bridge_plank")
    for x in (-0.42, -0.14, 0.14, 0.42):
        for sy in (-1, 1):
            log((x, sy * 0.12, -0.25), (x, sy * 0.12, 0.17), 0.018, "bridge_beam", 5)
            log((x, sy * 0.13, 0.17), (x, sy * 0.13, 0.3), 0.012, "bridge_beam", 5)
    for sy in (-1, 1):
        log((-0.5, sy * 0.13, 0.29), (0.5, sy * 0.13, 0.29), 0.01, "bridge_beam", 5)


stone_bridge()
a = finish("WorldBridge_stone")
wood_bridge()
b = finish("WorldBridge_wood")
print(export_all([a, b]))
