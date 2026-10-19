import bpy, math
from mathutils import Vector

ROWS = globals().get("ROWS")
OUTFILE = globals().get("OUTFILE")
scn = bpy.context.window.scene
coll = scn.collection
for o in list(scn.objects):
    if o.name.startswith(("PV_", "PVText")):
        bpy.data.objects.remove(o, do_unlink=True)


def flat_mat(name, rgb, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


font = bpy.data.fonts.load(r"C:\Windows\Fonts\arialbd.ttf", check_existing=True)
text_mat = flat_mat("PV_text", (0.95, 0.93, 0.86), 0.6)
y = 0.0
width = 0.0
for spacing, row in ROWS:
    x0 = -spacing * (len(row) - 1) / 2
    for i, (name, label) in enumerate(row):
        o = scn.objects[name]
        o.location = (x0 + i * spacing, y, 0)
        o.rotation_euler = (0, 0, 0)
        cu = bpy.data.curves.new("PVText_" + name, "FONT")
        cu.body = label
        cu.font = font
        cu.size = 0.75
        cu.align_x = "CENTER"
        cu.extrude = 0.02
        t = bpy.data.objects.new("PVText_" + name, cu)
        coll.objects.link(t)
        t.location = (x0 + i * spacing, y - spacing * 0.5, 0.02)
        t.data.materials.append(text_mat)
        width = max(width, spacing * len(row))
    y += spacing * 1.15
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y / 2 - 3, -0.01))
g = bpy.context.active_object
g.name = "PV_ground"
g.scale = (width + 12, y + 14, 1)
g.data.materials.append(flat_mat("PV_grass", (0.27, 0.38, 0.16), 1.0))
world = bpy.data.worlds.get("PV_sky") or bpy.data.worlds.new("PV_sky")
world.use_nodes = True
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
sky = nt.nodes.new("ShaderNodeTexSky")
try:
    sky.sun_disc = False
    sky.sun_elevation = math.radians(25)
except AttributeError:
    pass
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.25
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(sky.outputs[0], bg.inputs[0])
nt.links.new(bg.outputs[0], out.inputs[0])
scn.world = world
ld = bpy.data.lights.new("PV_sun", "SUN")
ld.energy = 4.0
ld.angle = math.radians(3)
ld.color = (1.0, 0.88, 0.72)
sun = bpy.data.objects.new("PV_sun", ld)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(-125))
cd = bpy.data.cameras.new("PV_cam")
cd.type = "ORTHO"
cd.ortho_scale = width + 2
cam = bpy.data.objects.new("PV_cam", cd)
coll.objects.link(cam)
target = Vector((0, y / 2 - 3.5, 0))
pitch = math.radians(52)
cam.location = target + Vector((0, -math.cos(pitch), math.sin(pitch))) * 80
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scn.camera = cam
try:
    scn.render.engine = "CYCLES"
except TypeError:
    pass
scn.cycles.samples = 48
scn.cycles.use_denoising = True
scn.render.resolution_x = 2000
scn.render.resolution_y = int(2000 * (y + 4) * math.sin(pitch) / (width + 2)) + 120
scn.view_settings.view_transform = "AgX"
try:
    scn.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
scn.render.filepath = OUTFILE
bpy.ops.render.render(write_still=True)
print("rendered", OUTFILE, scn.render.resolution_x, scn.render.resolution_y)
