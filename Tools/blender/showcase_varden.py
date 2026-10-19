import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
OUT = os.path.join(ROOT, "docs", "style", "varden-showcase.png")

scn = bpy.data.scenes.get("VardenShowcase") or bpy.data.scenes.new("VardenShowcase")
bpy.context.window.scene = scn
for o in list(scn.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scn.collection
rnd = random.Random(1347)


def node_mat(name, build):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    build(nt, bsdf)
    return m


def ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    els[1].position, els[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p, c in stops[1:-1]:
        e = els.new(p)
        e.color = (*c, 1)
    nt.links.new(fac, r.inputs[0])
    return r


def coord(nt, scale=(1, 1, 1)):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    return mp.outputs[0]


def bump(nt, bsdf, height, strength):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    nt.links.new(height, b.inputs["Height"])
    nt.links.new(b.outputs[0], bsdf.inputs["Normal"])


def wood_builder(base, dark, grain_scale=(1, 1, 7)):
    def build(nt, bsdf):
        v = coord(nt, grain_scale)
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "RINGS"
        wave.inputs["Scale"].default_value = 2.2
        wave.inputs["Distortion"].default_value = 6.0
        wave.inputs["Detail"].default_value = 3.0
        nt.links.new(v, wave.inputs[0])
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 3.0
        nt.links.new(v, noise.inputs[0])
        mix = nt.nodes.new("ShaderNodeMath")
        mix.operation = "MULTIPLY_ADD"
        mix.inputs[1].default_value = 0.55
        nt.links.new(wave.outputs["Fac"], mix.inputs[0])
        nt.links.new(noise.outputs["Fac"], mix.inputs[2])
        r = ramp(nt, mix.outputs[0], [(0.25, dark), (0.65, base), (1.0, tuple(min(1, c * 1.25) for c in base))])
        nt.links.new(r.outputs[0], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.85
        bump(nt, bsdf, mix.outputs[0], 0.35)
    return build


def stone_builder(nt, bsdf):
    v = coord(nt, (2.5, 2.5, 2.5))
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 2.2
    nt.links.new(v, vor.inputs[0])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 12.0
    nt.links.new(v, noise.inputs[0])
    r = ramp(nt, noise.outputs["Fac"], [(0.3, (0.66, 0.63, 0.57)), (0.7, (0.84, 0.82, 0.76))])
    nt.links.new(r.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation = "LESS_THAN"
    edge.inputs[1].default_value = 0.04
    nt.links.new(vor.outputs["Distance"], edge.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(edge.outputs[0], inv.inputs[1])
    bump(nt, bsdf, inv.outputs[0], 0.25)


def shingle_builder(nt, bsdf):
    v = coord(nt, (1, 1, 1))
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 9.0
    brick.inputs["Mortar Size"].default_value = 0.012
    brick.inputs["Color1"].default_value = (0.36, 0.27, 0.19, 1)
    brick.inputs["Color2"].default_value = (0.26, 0.2, 0.15, 1)
    brick.inputs["Mortar"].default_value = (0.12, 0.09, 0.07, 1)
    brick.offset = 0.5
    brick.squash = 0.35
    nt.links.new(v, brick.inputs[0])
    nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bump(nt, bsdf, brick.outputs["Fac"], 0.5)


def ground_builder(nt, bsdf):
    v = coord(nt, (0.6, 0.6, 0.6))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 8.0
    nt.links.new(v, noise.inputs[0])
    r = ramp(nt, noise.outputs["Fac"], [(0.35, (0.22, 0.3, 0.08)), (0.55, (0.36, 0.42, 0.13)), (0.75, (0.5, 0.44, 0.2))])
    nt.links.new(r.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bump(nt, bsdf, noise.outputs["Fac"], 0.3)


def flat(rgb, rough=0.6, metal=0.0):
    def build(nt, bsdf):
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return build


M = {
    "log": node_mat("sc_log", wood_builder((0.5, 0.36, 0.22), (0.28, 0.19, 0.12))),
    "log_old": node_mat("sc_log_old", wood_builder((0.42, 0.36, 0.3), (0.22, 0.19, 0.16))),
    "plank": node_mat("sc_plank", wood_builder((0.55, 0.4, 0.25), (0.33, 0.22, 0.13), (1, 6, 1))),
    "shingle": node_mat("sc_shingle", shingle_builder),
    "stone": node_mat("sc_stone", stone_builder),
    "gold": node_mat("sc_gold", flat((0.95, 0.68, 0.28), 0.28, 1.0)),
    "dome": node_mat("sc_dome", flat((0.12, 0.24, 0.27), 0.35, 0.4)),
    "red": node_mat("sc_red", flat((0.5, 0.05, 0.06), 0.7)),
    "white": node_mat("sc_trim", flat((0.92, 0.9, 0.84), 0.6)),
    "dark": node_mat("sc_window", flat((0.05, 0.05, 0.06), 0.4)),
    "ground": node_mat("sc_ground", ground_builder),
    "silver": node_mat("sc_silver", flat((0.85, 0.86, 0.9), 0.4)),
    "pine": node_mat("sc_pine", flat((0.07, 0.17, 0.09), 0.9)),
}


def link(o, m, smooth=True):
    o.data.materials.clear()
    o.data.materials.append(M[m])
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def obj(name, bm, m, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return link(o, m, smooth)


def log(a, b, r, m="log", seg=10):
    a, b = Vector(a), Vector(b)
    bm = bmesh.new()
    d = b - a
    mat = Matrix.Translation((a + b) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r * 0.97, depth=d.length, matrix=mat)
    for v in bm.verts:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * r * 0.06
    return obj("log", bm, m)


def boxo(c, s, m, rz=0.0, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=s, verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES")
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rz, 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return obj("box", bm, m, smooth=False)


def lathe(profile, c, s, m, seg=32):
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        ring = []
        for i in range(seg if r > 1e-4 else 1):
            a = i / seg * math.tau
            ring.append(bm.verts.new((c[0] + math.cos(a) * r * s, c[1] + math.sin(a) * r * s, c[2] + h * s)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        r0, r1 = rings[k], rings[k + 1]
        if len(r0) == 1:
            for i in range(seg):
                bm.faces.new((r0[0], r1[(i + 1) % seg], r1[i]))
        elif len(r1) == 1:
            for i in range(seg):
                bm.faces.new((r0[i], r0[(i + 1) % seg], r1[0]))
        else:
            for i in range(seg):
                bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj("lathe", bm, m)


def pyramid(c, w, h, m, sides=4, rz=0.0):
    bm = bmesh.new()
    mat = Matrix.Translation((c[0], c[1], c[2] + h / 2)) @ Matrix.Rotation(math.pi / sides + rz, 4, "Z")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=w / 2 / math.cos(math.pi / sides), radius2=0, depth=h, matrix=mat)
    return obj("pyr", bm, m, smooth=False)


def gable_roof(c, length, width, h, m, rz=0.0, over=0.18, thick=0.06):
    hl, hw = length / 2 + over, width / 2 + over
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-hl, -hw, 0), (hl, -hw, 0), (hl, 0, h), (-hl, 0, h), (-hl, hw, 0), (hl, hw, 0))]
    bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
    bm.faces.new((vs[3], vs[2], vs[5], vs[4]))
    r = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rz, 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return obj("roof", bm, m, smooth=False)


def srub(c, w, d, h, r=0.11, rz=0.0, m="log"):
    p = []
    step = r * 1.85
    n = max(1, int(h / step))
    rot = Matrix.Rotation(rz, 3, "Z")
    for i in range(n):
        z = r + i * step
        for sy in (-1, 1):
            a, b = rot @ Vector((-w / 2 - r * 1.6, sy * d / 2, z)), rot @ Vector((w / 2 + r * 1.6, sy * d / 2, z))
            p.append(log(Vector(c) + a, Vector(c) + b, r, m))
        for sx in (-1, 1):
            a, b = rot @ Vector((sx * w / 2, -d / 2 - r * 1.6, z + step / 2)), rot @ Vector((sx * w / 2, d / 2 + r * 1.6, z + step / 2))
            p.append(log(Vector(c) + a, Vector(c) + b, r, m))
    return p, n * step + step / 2


def pine(x, y, z, h):
    p = [log((x, y, z), (x, y, z + h * 0.3), h * 0.035, "log_old", 8)]
    for k in range(4):
        t = k / 4
        bm = bmesh.new()
        rr = h * (0.26 - t * 0.05)
        mat = Matrix.Translation((x, y, z + h * (0.22 + t * 0.2) + h * 0.2))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=9, radius1=rr, radius2=0.0, depth=h * 0.42, matrix=mat)
        for v in bm.verts:
            v.co.x += rnd.uniform(-1, 1) * rr * 0.08
            v.co.y += rnd.uniform(-1, 1) * rr * 0.08
        p.append(obj("pine", bm, "pine", False))
    return p


def tower(c, w, h, rz=0.0):
    p, top = srub(c, w, w, h, 0.12, rz)
    cz = c[2] + top
    p += srub((c[0], c[1], cz), w * 1.25, w * 1.25, 0.75, 0.1, rz, "log_old")[0]
    p.append(boxo((c[0], c[1], cz + 0.84), (w * 1.45, w * 1.45, 0.06), "plank", rz))
    p.append(pyramid((c[0], c[1], cz + 0.87), w * 1.6, w * 1.7, "shingle", 4, rz))
    p.append(boxo((c[0], c[1], cz + 0.87 + w * 1.55), (0.14, 0.14, 0.4), "plank", rz))
    p.append(pyramid((c[0], c[1], cz + 0.87 + w * 1.55 + 0.4), 0.3, 0.6, "shingle", 4, rz))
    for k in range(4):
        a = rz + k * math.pi / 2
        v = Vector((math.cos(a), math.sin(a), 0)) * (w * 1.25 / 2 + 0.12)
        p.append(boxo((c[0] + v.x, c[1] + v.y, cz + 0.4), (0.3, 0.3, 0.28), "dark", a))
    return p, cz + 0.87 + w * 1.55 + 1.0


def wall(a, b, h, z0=0.0):
    a, b = Vector(a), Vector(b)
    d = b - a
    rz = math.atan2(d.y, d.x)
    c = (a + b) / 2
    p, top = srub((c.x, c.y, z0), d.length, 0.9, h, 0.1, rz, "log")
    rot = Matrix.Rotation(rz, 3, "Z")
    out = rot @ Vector((0, -0.45, 0))
    p.append(boxo((c.x + out.x, c.y + out.y, z0 + top + 0.35), (d.length + 0.2, 0.1, 0.7), "plank", rz))
    n = int(d.length / 0.6)
    for i in range(n):
        q = a.lerp(b, (i + 0.5) / n) + rot @ Vector((0, -0.51, 0))
        p.append(boxo((q.x, q.y, z0 + top + 0.42), (0.1, 0.04, 0.22), "dark", rz))
    roof = gable_roof((c.x, c.y, z0 + top + 0.7), d.length + 0.1, 1.1, 0.45, "shingle", rz, 0.08)
    p.append(roof)
    return p


def palisade(a, b, h):
    a, b = Vector(a), Vector(b)
    n = int((b - a).length / 0.24)
    p = []
    for i in range(n):
        q = a.lerp(b, (i + 0.5) / n)
        hh = h * rnd.uniform(0.9, 1.08)
        tilt = Vector((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), 1)).normalized()
        top = q + tilt * hh
        p.append(log(q, top, 0.11, "log_old", 8))
        bm = bmesh.new()
        mat = Matrix.Translation(top + tilt * 0.16) @ Vector((0, 0, 1)).rotation_difference(tilt).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.107, radius2=0.0, depth=0.32, matrix=mat)
        p.append(obj("tip", bm, "log_old"))
    return p


def church(c, s):
    p = []
    x, y, z = c
    p.append(boxo((x, y, z + 1.3 * s), (2.4 * s, 2.4 * s, 2.6 * s), "stone", 0.0, 0.03))
    p.append(boxo((x, y - 1.55 * s, z + 0.95 * s), (1.4 * s, 0.7 * s, 1.9 * s), "stone", 0.0, 0.03))
    for side in range(4):
        a = side * math.pi / 2
        for k in (-1, 0, 1):
            v = Vector((math.cos(a) * 1.2 * s, math.sin(a) * 1.2 * s, 0))
            t = Vector((-math.sin(a), math.cos(a), 0)) * k * 0.8 * s
            bm = bmesh.new()
            mat = Matrix.Translation((x + v.x + t.x, y + v.y + t.y, z + 2.6 * s)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
            bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.4 * s, radius2=0.4 * s, depth=0.12 * s, matrix=mat)
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z + 2.6 * s), plane_no=(0, 0, 1), clear_inner=True)
            p.append(obj("zakomara", bm, "stone", True))
            if side != 3:
                p.append(boxo((x + v.x * 1.01 + t.x, y + v.y * 1.01 + t.y, z + 1.6 * s), (0.18 * s, 0.18 * s, 0.6 * s), "dark", a))
    p.append(boxo((x, y, z + 2.75 * s), (2.3 * s, 2.3 * s, 0.3 * s), "stone"))
    ONION = [(0.0, 0.0), (0.66, 0.0), (0.9, 0.2), (1.0, 0.48), (0.95, 0.76), (0.75, 1.02), (0.48, 1.28), (0.22, 1.52), (0.07, 1.78), (0.0, 1.98)]
    for dx, dy, r, h, m in ((0, 0, 0.62, 1.3, "gold"), (-0.78, -0.78, 0.36, 0.8, "dome"), (0.78, -0.78, 0.36, 0.8, "dome"), (0.78, 0.78, 0.36, 0.8, "dome"), (-0.78, 0.78, 0.36, 0.8, "dome")):
        bx, by, bz = x + dx * s, y + dy * s, z + 2.9 * s
        p.append(lathe([(0.0, 0.0), (0.72, 0.0), (0.72, h), (0.0, h)], (bx, by, bz), r * s, "stone"))
        for i in range(8):
            a = i / 8 * math.tau
            p.append(boxo((bx + math.cos(a) * 0.73 * r * s, by + math.sin(a) * 0.73 * r * s, bz + h * 0.55 * r * s), (0.08 * r * s, 0.08 * r * s, 0.5 * r * s), "dark", a))
        top = bz + h * r * s
        p.append(lathe(ONION, (bx, by, top), r * s, m))
        cz = top + 1.98 * r * s
        p.append(boxo((bx, by, cz + 0.32 * r * s), (0.05 * s, 0.05 * s, 0.65 * r * s + 0.1), "gold"))
        p.append(boxo((bx, by, cz + 0.45 * r * s), (0.28 * r * s + 0.05, 0.04 * s, 0.04 * s), "gold"))
    return p


def terem(c, rz):
    p, top = srub(c, 2.2, 1.7, 2.0, 0.1, rz)
    x, y, z = c
    rot = Matrix.Rotation(rz, 3, "Z")
    for i, dx in enumerate((-0.6, 0.2)):
        for zz in (0.75, 1.55):
            v = rot @ Vector((dx, -0.88, zz))
            p.append(boxo((x + v.x, y + v.y, z + v.z), (0.32, 0.06, 0.42), "dark", rz))
            p.append(boxo((x + v.x, y + v.y - 0.01, z + v.z + 0.26), (0.46, 0.08, 0.1), "red", rz))
            p.append(boxo((x + v.x, y + v.y - 0.01, z + v.z - 0.25), (0.42, 0.08, 0.06), "white", rz))
    p.append(gable_roof((x, y, z + top), 1.7, 2.2, 1.6, "shingle", rz + math.pi / 2, 0.25, 0.08))
    v = rot @ Vector((1.65, 0.0, 0))
    q, t2 = srub((x + v.x, y + v.y, z), 0.9, 0.9, 2.6, 0.1, rz)
    p += q
    p.append(pyramid((x + v.x, y + v.y, z + t2), 1.3, 1.6, "shingle", 8, rz))
    return p


def flag(c, h):
    x, y, z = c
    p = [log((x, y, z), (x, y, z + h), 0.035, "plank", 8)]
    bm = bmesh.new()
    vs = []
    for i in range(9):
        for j in range(4):
            u = i / 8
            vs.append(bm.verts.new((x + 0.05 + u * 1.1, y + math.sin(u * 5) * 0.08 * u, z + h - 0.08 - j * 0.22 - u * 0.1)))
    for i in range(8):
        for j in range(3):
            bm.faces.new((vs[i * 4 + j], vs[(i + 1) * 4 + j], vs[(i + 1) * 4 + j + 1], vs[i * 4 + j + 1]))
    p.append(obj("flag", bm, "red"))
    return p


def ground():
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=120, y_segments=120, size=30)
    for v in bm.verts:
        r = math.hypot(v.co.x, v.co.y)
        t = min(1.0, max(0.0, (10.5 - r) / 2.5))
        v.co.z = 1.4 * t * t * (3 - 2 * t) + 0.08 * math.sin(v.co.x * 0.7) * math.cos(v.co.y * 0.5)
    o = obj("ground", bm, "ground")
    return o


ground()
Z = 1.4
corners = [(-5.5, -4.5), (5.5, -4.5), (6.0, 4.5), (-5.0, 5.0)]
tops = []
for i in range(4):
    a, b = corners[i], corners[(i + 1) % 4]
    da = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized() * 1.0
    wall((a[0] + da.x, a[1] + da.y, 0), (b[0] - da.x, b[1] - da.y, 0), 1.6, 0.0)
    tops.append(tower((a[0], a[1], 0.0), 1.6, 3.6 if i == 0 else 2.8, math.atan2(b[1] - a[1], b[0] - a[0]))[1])
for o in [o for o in scn.objects if o.name != "ground"]:
    o.location.z += Z - 0.05
church((1.4, 1.0, Z), 1.0)
terem((-2.4, 1.6, Z), 0.05)
for i in range(7):
    x = -4.5 + i * 1.5
    y = -11.8 + rnd.uniform(-0.5, 0.5)
    rz = rnd.uniform(-0.25, 0.25)
    top = srub((x, y, 0.0), 1.0, 0.85, 0.85, 0.08, rz)[1]
    gable_roof((x, y, top), 1.0, 0.85, 0.7, "shingle", rz, 0.15, 0.05)
palisade((-8.0, -13.8, 0), (8.0, -13.8, 0), 1.6)
flag((-5.5, -4.5, tops[0] + Z - 0.05), 1.4)
for i in range(70):
    a = rnd.uniform(-0.35, math.tau - 1.9)
    r = rnd.uniform(13.0, 24.0)
    x, y = math.cos(a) * r + 2, math.sin(a) * r + 6
    if y < -9:
        continue
    pine(x, y, 0.0, rnd.uniform(2.6, 4.2))

sky = bpy.data.worlds.get("ShowcaseSky") or bpy.data.worlds.new("ShowcaseSky")
sky.use_nodes = True
nt = sky.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
st = nt.nodes.new("ShaderNodeTexSky")
try:
    st.sky_type = "NISHITA"
except TypeError:
    pass
try:
    st.sun_elevation = math.radians(22)
    st.sun_rotation = math.radians(210)
    st.sun_disc = False
except AttributeError:
    pass
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.22
wo = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(st.outputs[0], bg.inputs[0])
nt.links.new(bg.outputs[0], wo.inputs[0])
scn.world = sky
sd = bpy.data.lights.new("ShowcaseSun", "SUN")
sd.energy = 4.2
sd.angle = math.radians(3)
sd.color = (1.0, 0.86, 0.68)
sun = bpy.data.objects.new("ShowcaseSun", sd)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(64), 0, math.radians(-118))
cd = bpy.data.cameras.new("ShowcaseCam")
cd.lens = 38
cam = bpy.data.objects.new("ShowcaseCam", cd)
coll.objects.link(cam)
target = Vector((0.3, -4.6, 1.6))
cam.location = Vector((6.5, -27.5, 12.0))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scn.camera = cam
try:
    scn.render.engine = "CYCLES"
except TypeError:
    pass
scn.cycles.samples = 64
scn.cycles.use_denoising = True
scn.render.resolution_x = 1600
scn.render.resolution_y = 1000
scn.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in scn.view_settings.bl_rna.properties["view_transform"].enum_items] else scn.view_settings.view_transform
try:
    scn.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
scn.view_settings.exposure = -0.4
scn.render.filepath = OUT
print("built", len(scn.objects))
