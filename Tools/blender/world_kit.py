import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
OUT = os.path.join(ROOT, "Assets", "Art", "Environment", "World")
SRC = os.path.join(ROOT, "Tools", "blender", "env_props.py")
SCENE = globals().get("SCENE", "WorldKit")
code = open(SRC, encoding="utf-8").read().split("props = [")[0].replace('scenes.get("Environment") or bpy.data.scenes.new("Environment")', f'scenes.get("{SCENE}") or bpy.data.scenes.new("{SCENE}")')
ns = {}
exec(compile(code, SRC, "exec"), ns)
mat, coll, scn = ns["mat"], ns["coll"], ns["scn"]
os.makedirs(OUT, exist_ok=True)

M = {
    "log": mat("env_log", (0.5, 0.35, 0.21), 0.9),
    "log_dark": mat("env_log_dark", (0.38, 0.26, 0.16), 0.9),
    "log_old": mat("env_log_old", (0.45, 0.39, 0.32), 0.9),
    "plank": mat("env_plank", (0.56, 0.41, 0.26), 0.85),
    "roof": mat("env_roof_wood", (0.3, 0.24, 0.19), 0.9),
    "roof_green": mat("env_roof_green", (0.2, 0.36, 0.3), 0.6),
    "stone": mat("env_white_stone", (0.86, 0.84, 0.78), 0.85),
    "gold": mat("env_dome_gold", (0.92, 0.68, 0.26), 0.3, 0.8),
    "dome": mat("env_dome_dark", (0.13, 0.26, 0.29), 0.4, 0.3),
    "red": mat("env_trim_red", (0.55, 0.07, 0.07), 0.7),
    "white": mat("env_trim_white", (0.92, 0.9, 0.84), 0.7),
    "window": mat("env_window", (0.07, 0.07, 0.08), 0.4),
    "earth": mat("env_mound", (0.33, 0.4, 0.18), 1.0),
    "field": mat("env_field", (0.78, 0.66, 0.34), 0.95),
    "field_green": mat("env_field_green", (0.45, 0.55, 0.22), 0.95),
    "hay": mat("env_hay", (0.86, 0.72, 0.38), 0.95),
    "pine": mat("env_pine", (0.12, 0.27, 0.15), 0.9),
    "flag": mat("env_flag", (0.5, 0.06, 0.08), 0.8),
}
rnd = random.Random(1347)
parts = []


def put(name, bm, m, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.data.materials.append(M[m])
    for p in me.polygons:
        p.use_smooth = smooth
    parts.append(o)
    return o


def log(a, b, r, m="log", seg=6):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    mx = Matrix.Translation((a + b) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r * 0.96, depth=d.length, matrix=mx)
    for v in bm.verts:
        v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * r * 0.07
    return put("log", bm, m)


def box(c, s, m, rz=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=s, verts=bm.verts)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rz, 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return put("box", bm, m, False)


def cone(c, r1, r2, h, m, seg=12, rz=0.0, smooth=True):
    bm = bmesh.new()
    mx = Matrix.Translation((c[0], c[1], c[2] + h / 2)) @ Matrix.Rotation(rz, 4, "Z")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=mx)
    return put("cone", bm, m, smooth)


def pyramid(c, w, h, m, sides=4, rz=0.0):
    return cone(c, w / 2 / math.cos(math.pi / sides), 0.0, h, m, sides, math.pi / sides + rz, False)


def lathe(profile, c, s, m, seg=14):
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        n = seg if r > 1e-4 else 1
        rings.append([bm.verts.new((c[0] + math.cos(i / seg * math.tau) * r * s, c[1] + math.sin(i / seg * math.tau) * r * s, c[2] + h * s)) for i in range(n)])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            if len(r0) == 1:
                bm.faces.new((r0[0], r1[j], r1[i]))
            elif len(r1) == 1:
                bm.faces.new((r0[i], r0[j], r1[0]))
            else:
                bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put("lathe", bm, m)


def gable(c, length, width, h, m, rz=0.0, over=0.08, thick=0.04):
    hl, hw = length / 2 + over, width / 2 + over
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((-hl, -hw, 0), (hl, -hw, 0), (hl, 0, h), (-hl, 0, h), (-hl, hw, 0), (hl, hw, 0))]
    bm.faces.new((v[0], v[1], v[2], v[3]))
    bm.faces.new((v[3], v[2], v[5], v[4]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rz, 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return put("roof", bm, m, False)


def gable_end(c, length, width, h, m, rz=0.0):
    hl, hw = length / 2, width / 2
    bm = bmesh.new()
    for sx in (-1, 1):
        v = [bm.verts.new(p) for p in ((sx * hl, -hw, 0), (sx * hl, hw, 0), (sx * hl, 0, h))]
        bm.faces.new(v)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rz, 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return put("gable", bm, m, False)


def outward(a, b, center):
    d = (b - a).normalized()
    n = Vector((-d.y, d.x, 0))
    mid = (a + b) / 2
    if n.dot(mid - Vector((center[0], center[1], mid.z))) < 0:
        n = -n
    return d, n


def palisade(a, b, h, z0=0.0, spacing=0.15, thick=0.08):
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    n = max(2, int((b - a).length / spacing))
    d = (b - a).normalized()
    off = Vector((d.y, -d.x, 0)) * thick
    bm = bmesh.new()
    for i in range(n):
        p0, p1 = a.lerp(b, (i + 0.06) / n), a.lerp(b, (i + 0.94) / n)
        hh = h * rnd.uniform(0.95, 1.05)
        prof = [p0, p1, p1 + Vector((0, 0, hh * 0.84)), a.lerp(b, (i + 0.5) / n) + Vector((0, 0, hh)), p0 + Vector((0, 0, hh * 0.84))]
        f = bm.faces.new([bm.verts.new(q - off / 2) for q in prof])
        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        bmesh.ops.translate(bm, vec=off, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put("palisade", bm, "log_old", False)


def ring(r, n, jitter, seed, phase=0.0):
    rr = random.Random(seed)
    return [(math.cos(phase + i / n * math.tau) * r * rr.uniform(1 - jitter, 1 + jitter), math.sin(phase + i / n * math.tau) * r * rr.uniform(1 - jitter, 1 + jitter)) for i in range(n)]


def mound(c, r, h):
    cone((c[0], c[1], -0.05), r + 0.45, r - 0.05, h + 0.05, "earth", 28)
    return h


def flag(c, h, w=0.55):
    x, y, z = c
    log((x, y, z), (x, y, z + h), 0.022, "plank", 6)
    bm = bmesh.new()
    vs = []
    for i in range(7):
        for j in range(3):
            u = i / 6
            vs.append(bm.verts.new((x + 0.02 + u * w, y + math.sin(u * 4.5) * 0.05 * u, z + h - 0.04 - j * w * 0.3 - u * 0.05)))
    for i in range(6):
        for j in range(2):
            bm.faces.new((vs[i * 3 + j], vs[(i + 1) * 3 + j], vs[(i + 1) * 3 + j + 1], vs[i * 3 + j + 1]))
    bm2 = bm.copy()
    bmesh.ops.reverse_faces(bm2, faces=bm2.faces[:])
    put("flag", bm, "flag", True)
    put("flag_back", bm2, "flag", True)


def pine(c, h):
    x, y, z = c
    log((x, y, z), (x, y, z + h * 0.3), h * 0.04, "log_dark", 5)
    for k in range(3):
        rr = h * (0.27 - k * 0.06)
        cone((x, y, z + h * (0.2 + k * 0.22)), rr, 0.0, h * (0.5 - k * 0.06), "pine", 7, rnd.uniform(0, 1), False)


def field(c, w, d, rz, m="field"):
    box((c[0], c[1], 0.015), (w, d, 0.03), m, rz)
    for i in range(int(d / 0.12)):
        v = Matrix.Rotation(rz, 3, "Z") @ Vector((0, -d / 2 + (i + 0.5) * d / int(d / 0.12), 0))
        box((c[0] + v.x, c[1] + v.y, 0.035), (w * 0.96, 0.025, 0.012), "hay" if m == "field" else "pine", rz)


def haystack(c, s=1.0):
    cone((c[0], c[1], 0), 0.16 * s, 0.0, 0.42 * s, "hay", 9)
    cone((c[0], c[1], 0), 0.17 * s, 0.15 * s, 0.14 * s, "hay", 9)


GROUP = [0]


def grouped(fn):
    def wrapper(*args, **kwargs):
        n0 = len(parts)
        out = fn(*args, **kwargs)
        GROUP[0] += 1
        for o in parts[n0:]:
            o["grp"] = GROUP[0]
        return out
    return wrapper


def join_parts(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for p in objs:
        p.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return o


def finish(name):
    global parts
    groups = {}
    for p in parts:
        groups.setdefault(p.get("grp", 0), []).append(p)
    core = groups.pop(0, None) or groups.pop(min(groups))
    o = join_parts(core, name)
    for i, k in enumerate(sorted(groups)):
        c = join_parts(groups[k], f"{name}_b{i}")
        c.parent = o
    parts = []
    return o


def bake_ao(o, distance=0.7, samples=24):
    scn = bpy.context.scene
    try:
        scn.render.engine = "CYCLES"
    except TypeError:
        pass
    scn.cycles.samples = samples
    scn.render.bake.target = "VERTEX_COLORS"
    if scn.world is None:
        scn.world = bpy.data.worlds.get("KitWorld") or bpy.data.worlds.new("KitWorld")
    scn.world.light_settings.distance = distance
    me = o.data
    attr = me.color_attributes.get("AO") or me.color_attributes.new("AO", "BYTE_COLOR", "CORNER")
    me.color_attributes.active_color = attr
    others = [x for x in scn.objects if x is not o and x.type == "MESH" and not x.hide_render]
    for x in others:
        x.hide_render = True
    bpy.ops.mesh.primitive_plane_add(size=60, location=(o.location.x, o.location.y, -0.002))
    ground = bpy.context.active_object
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.bake(type="AO")
    bpy.data.objects.remove(ground, do_unlink=True)
    for x in others:
        x.hide_render = False


def export_all(models):
    for o in models:
        bake_ao(o)
        ns["export"](o, os.path.join(OUT, o.name + ".fbx"))
    return [(o.name, len(o.data.polygons), round(max(math.hypot(v.co.x, v.co.y) for v in o.data.vertices), 2)) for o in models]
