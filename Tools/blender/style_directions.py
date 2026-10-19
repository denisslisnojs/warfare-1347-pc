import bpy, math, os
from mathutils import Vector

OUT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\docs\style"
os.makedirs(OUT, exist_ok=True)

scn = bpy.data.scenes.get("StyleTest") or bpy.data.scenes.new("StyleTest")
bpy.context.window.scene = scn
for o in list(scn.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scn.collection


def mat(name, rgb, rough=0.6, metal=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    return m


def palette(prefix, cloth, trim, gloss):
    r = 0.28 if gloss else 1.0
    c = 0.6 if gloss else 0.0
    return {
        "cloth": mat(prefix + "cloth", cloth, 0.75 * r + (0 if gloss else 0), 0, c),
        "trim": mat(prefix + "trim", trim, 0.5 * r, 0, c),
        "skin": mat(prefix + "skin", (0.86, 0.62, 0.48), 0.6 * r, 0, c),
        "metal": mat(prefix + "metal", (0.72, 0.74, 0.78), 0.35, 0.9, c),
        "dark": mat(prefix + "dark", (0.25, 0.25, 0.28), 0.4, 0.8, c),
        "leather": mat(prefix + "leather", (0.32, 0.2, 0.12), 0.7 * r, 0, c),
        "trousers": mat(prefix + "trousers", (0.22, 0.2, 0.18), 0.85 * r, 0, c),
        "wood": mat(prefix + "wood", (0.45, 0.3, 0.16), 0.7 * r, 0, c),
        "eye": mat(prefix + "eye", (0.04, 0.04, 0.05), 0.3, 0, c),
        "base": mat(prefix + "base", (0.07, 0.07, 0.06), 0.4, 0, c),
        "flock": mat(prefix + "flock", (0.3, 0.42, 0.16), 0.95, 0, 0),
    }


class Builder:
    def __init__(self, P, M):
        self.P, self.M, self.parts = P, M, []
        self.seg = P["seg"]

    def done(self, o, m):
        o.data.materials.append(self.M[m])
        self.parts.append(o)
        return o

    def sphere(self, loc, r, m, sc=(1, 1, 1)):
        seg = self.seg
        bpy.ops.mesh.primitive_uv_sphere_add(segments=max(8, seg), ring_count=max(6, seg // 2), radius=1, location=loc)
        o = bpy.context.active_object
        o.scale = (r * sc[0], r * sc[1], r * sc[2])
        return self.done(o, m)

    def cone(self, a, b, r1, r2, m, sy=1.0, verts=None):
        a, b = Vector(a), Vector(b)
        d = b - a
        bpy.ops.mesh.primitive_cone_add(vertices=verts or max(8, self.seg), radius1=r1, radius2=r2, depth=d.length, location=(a + b) / 2)
        o = bpy.context.active_object
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        o.scale = (1, sy, 1)
        return self.done(o, m)

    def limb(self, a, b, r1, r2, m):
        self.cone(a, b, r1, r2, m)
        self.sphere(a, r1, m)
        self.sphere(b, r2, m)

    def box(self, loc, size, m, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
        o = bpy.context.active_object
        o.scale = size
        return self.done(o, m)

    def build(self, name):
        P = self.P
        w, lr, ar = P["shoulder"], P["legR"], P["armR"]
        boot = 0.09
        hipZ = P["leg"] + boot
        for s in (-1, 1):
            x = s * w * 0.21
            self.limb((x, 0, boot + lr * 0.6), (x, 0, hipZ), lr * 0.92, lr * 1.08, "trousers")
            self.box((x, -lr * 0.55, boot * 0.75), (lr * 2.3, lr * 3.6, boot * 1.5), "leather")
        tz0, tz1 = hipZ - 0.06, hipZ + P["torso"]
        self.cone((0, 0, tz0), (0, 0, tz1), w * 0.5 * P["taper"], w * 0.5, "cloth", sy=0.66)
        self.cone((0, 0, hipZ + 0.02), (0, 0, hipZ - P["leg"] * 0.42), w * 0.5 * P["taper"] * 0.98, w * 0.5 * P["taper"] * 1.12, "cloth", sy=0.7)
        self.cone((0, 0, hipZ - 0.04), (0, 0, hipZ + 0.06), w * 0.5 * P["taper"] * 1.04, w * 0.5 * P["taper"] * 1.04, "leather", sy=0.7)
        mid = (tz0 + tz1) / 2
        self.box((0, -w * 0.33 * (0.9 + 0.1 * P["taper"]), mid), (w * 0.16, 0.03, (tz1 - tz0) * 0.85), "trim")
        self.box((0, -w * 0.34, mid + (tz1 - tz0) * 0.12), (w * 0.5, 0.03, w * 0.12), "trim")

        h = P["head"]
        self.cone((0, 0, tz1 - 0.02), (0, 0, tz1 + 0.06), h * 0.2, h * 0.18, "skin")
        hc = tz1 + 0.04 + h * 0.5
        self.sphere((0, 0, hc), h * 0.5, "skin", (1, 0.95, 1.03))
        for s in (-1, 1):
            self.sphere((s * h * 0.17, -h * 0.45, hc + h * 0.0), h * 0.06, "eye", (1, 0.5, 1.2))
        hb = hc + h * 0.08
        self.cone((0, 0, hb), (0, 0, hb + h * 0.62), h * 0.55, 0.008, "metal")
        self.cone((0, 0, hb - h * 0.05), (0, 0, hb + h * 0.06), h * 0.56, h * 0.56, "dark")
        self.box((0, -h * 0.55, hb - h * 0.16), (h * 0.08, h * 0.05, h * 0.36), "metal")

        shz = tz1 - ar * 1.1
        sx = w * 0.5 + ar * 0.25
        L = P["armLen"]
        hr = ar * P["hand"]
        rs = (sx, 0, shz)
        re = (sx + 0.06, 0.02, shz - L * 0.52)
        rh = (sx + 0.04, -0.26, shz - L * 0.5)
        self.limb(rs, re, ar, ar * 0.9, "metal")
        self.limb(re, rh, ar * 0.9, ar * 0.8, "metal")
        self.sphere(rh, hr, "skin")
        ls = (-sx, 0, shz)
        le = (-sx - 0.06, -0.08, shz - L * 0.5)
        lh = (-sx + 0.06, -0.3, shz - L * 0.6)
        self.limb(ls, le, ar, ar * 0.9, "metal")
        self.limb(le, lh, ar * 0.9, ar * 0.8, "metal")
        self.sphere(lh, hr, "skin")
        if P["pads"]:
            for s, c in ((1, rs), (-1, ls)):
                self.sphere(c, ar * 1.55, "cloth", (1.1, 1, 0.8))

        sr = P["shieldR"]
        sc = Vector((-sx - 0.06, -0.4, shz - L * 0.55))
        sv = 2 * max(8, self.seg)
        self.cone(sc + Vector((0, 0.04, 0)), sc, sr * 1.07, sr * 1.07, "trim", verts=sv)
        self.cone(sc, sc + Vector((0, -0.035, 0)), sr, sr, "cloth", verts=sv)
        self.box(sc + Vector((0, -0.04, 0)), (sr * 0.2, 0.02, sr * 1.9), "trim")
        self.box(sc + Vector((0, -0.04, 0)), (sr * 1.9, 0.02, sr * 0.2), "trim")
        self.sphere(sc + Vector((0, -0.05, 0)), sr * 0.18, "metal", (1, 0.6, 1))

        top = hc + h * 0.5 + 0.75
        self.cone((rh[0], rh[1], 0.05), (rh[0], rh[1], top), 0.024, 0.022, "wood", verts=8)
        self.cone((rh[0], rh[1], top), (rh[0], rh[1], top + 0.24), 0.05, 0.003, "metal", verts=6)

        if P.get("base"):
            self.cone((0, 0, -0.08), (0, 0, 0.0), 0.62, 0.6, "base", verts=48)
            self.cone((0, 0, -0.005), (0, 0, 0.012), 0.58, 0.58, "flock", verts=48)

        bpy.ops.object.select_all(action="DESELECT")
        for o in self.parts:
            o.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.join()
        o = bpy.context.active_object
        o.name = name
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        if P["flat"]:
            bpy.ops.object.shade_flat()
        else:
            try:
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
            except Exception:
                bpy.ops.object.shade_smooth()
        return o


VARIANTS = [
    ("1", dict(head=0.66, torso=0.5, leg=0.4, shoulder=0.62, armLen=0.5, legR=0.11, armR=0.085, hand=1.35, shieldR=0.44, taper=0.95, pads=False, seg=24, flat=False), False),
    ("2", dict(head=0.42, torso=0.64, leg=0.66, shoulder=0.72, armLen=0.72, legR=0.11, armR=0.092, hand=1.3, shieldR=0.42, taper=0.72, pads=True, seg=24, flat=False), False),
    ("3", dict(head=0.27, torso=0.6, leg=0.88, shoulder=0.48, armLen=0.72, legR=0.07, armR=0.055, hand=1.25, shieldR=0.36, taper=0.82, pads=False, seg=6, flat=True), False),
    ("4", dict(head=0.36, torso=0.62, leg=0.72, shoulder=0.62, armLen=0.72, legR=0.1, armR=0.08, hand=1.3, shieldR=0.4, taper=0.78, pads=True, seg=24, flat=False, base=True), True),
]

BLUE = ((0.12, 0.3, 0.78), (0.95, 0.76, 0.22))
RED = ((0.72, 0.1, 0.09), (0.94, 0.92, 0.86))

models = {}
for key, P, gloss in VARIANTS:
    for side, (cloth, trim) in (("blue", BLUE), ("red", RED)):
        M = palette(f"v{key}_{side}_", cloth, trim, gloss)
        models[(key, side)] = Builder(P, M).build(f"V{key}_{side}")

ground_m = mat("ground", (0.27, 0.4, 0.16), 1.0)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
g = bpy.context.active_object
g.name = "Ground"
g.data.materials.append(ground_m)

world = bpy.data.worlds.get("StyleWorld") or bpy.data.worlds.new("StyleWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.62, 0.72, 0.86, 1)
bg.inputs[1].default_value = 0.55
scn.world = world

sun_data = bpy.data.lights.new("StyleSun", "SUN")
sun_data.energy = 4.5
sun_data.angle = math.radians(8)
sun = bpy.data.objects.new("StyleSun", sun_data)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(-35))

label_m = mat("label", (1, 1, 1), 0.5)


def label(text, loc, size, rot):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.active_object
    t.data.body = text
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.materials.append(label_m)
    return t


def place(src, loc, rotz=0.0):
    o = src.copy()
    coll.objects.link(o)
    o.location = loc
    o.rotation_euler = (0, 0, rotz)
    return o


xs = [-2.7, -0.9, 0.9, 2.7]
for i, (key, P, gloss) in enumerate(VARIANTS):
    o = models[(key, "blue")]
    o.location = (xs[i], 60, 0)
    label(key, (xs[i], 60, 2.7), 0.4, (math.radians(90), 0, 0))
for o in [models[(k, "red")] for k, _, _ in VARIANTS]:
    o.location = (0, -500, 0)

cam1_d = bpy.data.cameras.new("CamClose")
cam1_d.lens = 48
cam1 = bpy.data.objects.new("CamClose", cam1_d)
coll.objects.link(cam1)
cam1.location = (0.3, 49.0, 1.9)
direction = Vector((0, 60, 1.2)) - cam1.location
cam1.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

bx = [-18, -6, 6, 18]
for i, (key, P, gloss) in enumerate(VARIANTS):
    spacing = 1.6 if not P.get("base") else 1.35
    for r in range(3):
        for c in range(4):
            x = bx[i] + (c - 1.5) * spacing
            place(models[(key, "blue")], (x, -10 - r * spacing, 0))
            place(models[(key, "red")], (x, -3 + r * spacing, 0), math.pi)
    label(key, (bx[i], 1.5, 4.0), 2.2, (math.radians(55), 0, 0))

cam2_d = bpy.data.cameras.new("CamBattle")
cam2_d.lens = 28
cam2 = bpy.data.objects.new("CamBattle", cam2_d)
coll.objects.link(cam2)
cam2.location = (0, -36, 26)
direction = Vector((0, -6.5, 0)) - cam2.location
cam2.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

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
scn.view_settings.look = "None"
try:
    scn.eevee.use_gtao = True
except Exception:
    pass
try:
    scn.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
except Exception:
    pass
scn.render.image_settings.file_format = "PNG"

for cam, fname in ((cam1, "1-closeup.png"), (cam2, "2-battle.png")):
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)

scn.camera = cam1
print("engine", scn.render.engine, "objects", len(scn.objects))
