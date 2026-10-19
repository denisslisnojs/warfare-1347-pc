import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

SCENE = "WorldHero"
KIT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347\Tools\blender\world_kit.py"
exec(compile(open(KIT, encoding="utf-8").read(), KIT, "exec"), globals())

M.update({
    "bay": mat("env_hide_bay", (0.45, 0.27, 0.15), 0.85),
    "mane": mat("env_hide_dark", (0.14, 0.1, 0.08), 0.9),
    "hoof": mat("env_hoof", (0.18, 0.16, 0.15), 0.6),
    "leather": mat("env_leather", (0.33, 0.2, 0.11), 0.7),
    "mail": mat("env_mail", (0.52, 0.54, 0.57), 0.45, 0.6),
    "steel": mat("env_steel", (0.68, 0.7, 0.73), 0.35, 0.8),
    "skin": mat("env_skin", (0.87, 0.68, 0.55), 0.6),
    "flag_trim": mat("env_flag_trim", (0.9, 0.85, 0.7), 0.8),
    "beam": mat("env_beam", (0.36, 0.23, 0.13), 0.85),
    "black": mat("env_black", (0.05, 0.05, 0.05), 0.4),
})


def blob(c, s, m, sub=2, rough=0.0, seed=1):
    rr = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        n = v.co.normalized()
        k = 1.0 + rr.uniform(-rough, rough)
        v.co = Vector((n.x * s[0] * k, n.y * s[1] * k, n.z * s[2] * k))
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return put("blob", bm, m, True)


def limb(a, b, r1, r2, m, seg=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    mx = Matrix.Translation((a + b) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=d.length, matrix=mx)
    return put("limb", bm, m, True)


def cloth(x0, x1, z0, z1, y, m, wave=0.02, nu=10, nv=3, offset=0.0, v0=0.0, v1=1.0):
    pts = []
    bm = bmesh.new()
    rows = []
    for i in range(nu + 1):
        u = i / nu
        x = x0 + (x1 - x0) * u
        dy = math.sin(u * math.pi * 2.2) * wave * u
        col = []
        for j in range(nv + 1):
            v = v0 + (v1 - v0) * j / nv
            z = z0 + (z1 - z0) * v - u * 0.02
            col.append(bm.verts.new((x, y + dy + offset, z)))
        rows.append(col)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    back = bm.copy()
    bmesh.ops.reverse_faces(back, faces=back.faces[:])
    if offset:
        bmesh.ops.translate(back, vec=(0, -2 * offset, 0), verts=back.verts)
    put("cloth", bm, m, True)
    put("cloth_back", back, m, True)


def group(name, origin=(0, 0, 0)):
    o = finish(name)
    bpy.context.scene.cursor.location = origin
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.context.scene.cursor.location = (0, 0, 0)
    return o


def horse():
    out = []
    blob((0, 0, 0.36), (0.25, 0.1, 0.11), "bay", 2, 0.03, 21)
    blob((0.16, 0, 0.37), (0.11, 0.095, 0.11), "bay", 2, 0.02, 22)
    blob((-0.16, 0, 0.385), (0.12, 0.1, 0.11), "bay", 2, 0.02, 23)
    limb((0.2, 0, 0.42), (0.31, 0, 0.6), 0.06, 0.042, "bay", 10)
    blob((0.34, 0, 0.63), (0.06, 0.048, 0.05), "bay", 2, 0.0, 24)
    blob((0.405, 0, 0.585), (0.062, 0.037, 0.04), "bay", 2, 0.0, 25)
    for sy in (1, -1):
        cone((0.325, sy * 0.026, 0.665), 0.013, 0.003, 0.045, "bay", 6)
        blob((0.37, sy * 0.036, 0.635), (0.008, 0.006, 0.008), "black", 1, 0.0, 26)
        log((0.42, sy * 0.034, 0.59), (0.12, sy * 0.045, 0.53), 0.0045, "leather", 4)
    limb((0.19, 0, 0.475), (0.325, 0, 0.67), 0.02, 0.012, "mane", 6)
    blob((-0.275, 0, 0.445), (0.035, 0.03, 0.03), "mane", 1, 0.0, 27)
    limb((-0.28, 0, 0.445), (-0.335, 0, 0.35), 0.03, 0.034, "mane", 8)
    limb((-0.335, 0, 0.35), (-0.35, 0, 0.2), 0.034, 0.012, "mane", 8)
    box((-0.01, 0, 0.455), (0.23, 0.205, 0.014), "flag")
    for sy in (1, -1):
        box((-0.01, sy * 0.104, 0.39), (0.21, 0.012, 0.13), "flag")
        box((-0.01, sy * 0.1055, 0.333), (0.21, 0.012, 0.022), "flag_trim")
    box((-0.01, 0, 0.47), (0.15, 0.17, 0.03), "leather")
    box((-0.085, 0, 0.495), (0.025, 0.14, 0.045), "leather")
    box((0.065, 0, 0.49), (0.022, 0.1, 0.035), "leather")
    out.append(group("Body"))
    for name, x, y in (("LegFL", 0.17, 0.06), ("LegFR", 0.17, -0.06), ("LegBL", -0.17, 0.06), ("LegBR", -0.17, -0.06)):
        dx = 0.012 if x > 0 else -0.022
        limb((x, y, 0.36), (x + dx, y, 0.17), 0.036, 0.024, "bay", 8)
        limb((x + dx, y, 0.17), (x, y, 0.035), 0.021, 0.017, "bay", 8)
        cone((x, y, 0), 0.025, 0.02, 0.04, "hoof", 8)
        out.append(group(name, (x, y, 0.36)))
    return out


def rider():
    blob((0.0, 0, 0.6), (0.065, 0.08, 0.1), "mail", 2, 0.0, 31)
    blob((0.006, 0, 0.572), (0.071, 0.086, 0.083), "flag", 2, 0.0, 32)
    cone((-0.004, 0, 0.47), 0.1, 0.074, 0.07, "flag", 12)
    cone((0.0, 0, 0.528), 0.079, 0.079, 0.016, "leather", 12)
    for sy in (1, -1):
        limb((0.0, sy * 0.058, 0.505), (0.078, sy * 0.115, 0.455), 0.03, 0.026, "mail", 8)
        limb((0.078, sy * 0.115, 0.455), (0.05, sy * 0.122, 0.33), 0.025, 0.02, "mail", 8)
        blob((0.065, sy * 0.122, 0.317), (0.036, 0.021, 0.019), "leather", 1, 0.0, 33)
        blob((0.0, sy * 0.083, 0.662), (0.036, 0.036, 0.032), "mail", 1, 0.0, 34)
    limb((0.0, 0.09, 0.655), (0.05, 0.1, 0.585), 0.024, 0.021, "mail", 8)
    limb((0.05, 0.1, 0.585), (0.12, 0.05, 0.552), 0.02, 0.018, "mail", 8)
    blob((0.126, 0.046, 0.55), (0.021, 0.019, 0.019), "leather", 1, 0.0, 35)
    limb((0.0, -0.09, 0.655), (0.035, -0.125, 0.592), 0.024, 0.021, "mail", 8)
    limb((0.035, -0.125, 0.592), (0.058, -0.13, 0.638), 0.02, 0.018, "mail", 8)
    blob((0.062, -0.13, 0.645), (0.021, 0.021, 0.022), "leather", 1, 0.0, 36)
    limb((0.0, 0, 0.66), (0.0, 0, 0.72), 0.032, 0.029, "skin", 8)
    return [group("Rider")]


def head():
    blob((0.006, 0, 0.775), (0.068, 0.066, 0.072), "skin", 2, 0.0, 41)
    for sy in (1, -1):
        blob((0.069, sy * 0.023, 0.777), (0.008, 0.009, 0.01), "black", 1, 0.0, 42)
    lathe([(0.0, 0.142), (0.026, 0.132), (0.052, 0.106), (0.07, 0.07), (0.077, 0.034), (0.078, 0.0), (0.0, 0.0)], (0.0, 0, 0.79), 1.0, "steel", 16)
    box((0.074, 0, 0.777), (0.012, 0.012, 0.04), "steel")
    cone((0.0, 0, 0.675), 0.064, 0.05, 0.055, "mail", 12)
    return [group("Head")]


def shield():
    outline = [(-0.065, 0.075), (0.065, 0.075), (0.065, 0.012), (0.046, -0.048), (0.0, -0.092), (-0.046, -0.048), (-0.065, 0.012)]
    cx, cy, cz = -0.02, 0.136, 0.56

    def plate(m, y0, pts):
        bm = bmesh.new()
        front = [bm.verts.new((cx + u, cy + y0 - (u * u) * 1.6, cz + v)) for u, v in pts]
        back = [bm.verts.new((cx + u, cy + y0 - 0.012 - (u * u) * 1.6, cz + v)) for u, v in pts]
        bm.faces.new(front[::-1])
        bm.faces.new(back)
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((front[i], front[j], back[j], back[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return put("shield", bm, m, False)

    plate("flag", 0.0, outline)
    plate("flag_trim", 0.003, [(-0.064, 0.074), (0.064, 0.074), (0.064, 0.046), (-0.064, 0.046)])
    return [group("Shield")]


def banner():
    limb((0.062, -0.13, 0.4), (0.062, -0.13, 1.32), 0.0085, 0.007, "beam", 6)
    cone((0.062, -0.13, 1.32), 0.015, 0.0, 0.045, "gold", 8)
    pole = group("Pole")
    cloth(0.055, -0.25, 1.12, 1.29, -0.13, "flag", 0.022, 10, 3)
    cloth(0.055, -0.25, 1.12, 1.29, -0.13, "flag_trim", 0.022, 10, 1, 0.0018, 0.4, 0.6)
    flag = group("Flag", (0.062, -0.13, 1.2))
    return [pole, flag]


def export_group(objs, name):
    for o in objs:
        bake_ao(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, name + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
    )
    return (name, [o.name for o in objs], sum(len(o.data.polygons) for o in objs))


report = []
for name, fn in (("WorldHero_Mount_horse", horse), ("WorldHero_Body_mail", rider), ("WorldHero_Head_bascinet", head), ("WorldHero_Shield_heater", shield), ("WorldHero_Banner_standard", banner)):
    report.append(export_group(fn(), name))
print(report)
