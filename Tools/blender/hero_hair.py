import bpy, os, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_base as hb

HEAD_C = np.array([0.0, -0.03, 1.60])
FACE_C = np.array([0.0, -0.01, 1.53])
UNDER_C = np.array([0.0, -0.13, 1.36])
SINK = -0.002
FULL = None
KEPT = set()
VERT_FACE = {}


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def visible(bvh, lo, hi, step=0.004, count=100):
    seen = set()
    ctr = (lo + hi) / 2
    size = np.linalg.norm(hi - lo)
    n = int(size / step)
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(count * 2):
        z = 1 - (k + 0.5) / count
        if z < -0.5:
            break
        rr = math.sqrt(max(0.0, 1 - z * z))
        d = Vector((rr * math.cos(golden * k), rr * math.sin(golden * k), z))
        t = d.orthogonal().normalized()
        b = d.cross(t)
        o = Vector(ctr) + d * 0.3
        for i in range(n):
            for j in range(n):
                q = o + t * ((i / n - 0.5) * size) + b * ((j / n - 0.5) * size)
                idx = bvh.ray_cast(q, -d, 0.6)[2]
                if idx is not None:
                    seen.add(idx)
    return seen


def outer_bvh(body):
    V = hb.coords(body)
    lo, hi = np.array([-0.14, -0.22, 1.36]), np.array([0.14, 0.06, 1.62])
    seen = visible(hb.body_bvh(body), lo, hi)
    polys, ids = [], []
    for p in body.data.polygons:
        c = V[list(p.vertices)].mean(0)
        if np.all(c > lo) and np.all(c < hi) and p.index not in seen:
            continue
        polys.append(tuple(p.vertices))
        ids.append(p.index)
    print("inner polys", len(body.data.polygons) - len(ids))
    global FULL, KEPT, VERT_FACE
    FULL = hb.body_bvh(body)
    KEPT = set(ids)
    VERT_FACE = {}
    for p in body.data.polygons:
        for v in p.vertices:
            VERT_FACE.setdefault(v, p.index)
    return BVHTree.FromPolygons([tuple(v) for v in V], polys), ids


def frame(axis):
    a = unit(axis)
    f = np.array([0.0, -1.0, 0.0]) - a * a[1] * -1.0
    f = unit(f) if np.linalg.norm(f) > 1e-6 else np.array([0.0, 0.0, 1.0])
    return a, f, np.cross(a, f)


def grid(bvh, ids, centre, axis, theta_max, nt, na, outside=False):
    a, f, s = frame(axis)
    th = np.radians(np.linspace(1.0, theta_max, nt))
    al = np.linspace(0.0, 2 * math.pi, na, endpoint=False)
    T, A = np.meshgrid(th, al, indexing="ij")
    D = np.cos(T)[..., None] * a + np.sin(T)[..., None] * (np.cos(A)[..., None] * f + np.sin(A)[..., None] * s)
    Dt = -np.sin(T)[..., None] * a + np.cos(T)[..., None] * (np.cos(A)[..., None] * f + np.sin(A)[..., None] * s)
    P = np.zeros_like(D)
    poly = np.full(T.shape, -1)
    for i in range(nt):
        for j in range(na):
            hit, _, idx, dist = bvh.ray_cast(Vector(centre), Vector(D[i, j]), 0.4)
            if hit is not None:
                idx = ids[idx]
            if not outside and FULL is not None and (hit is None or dist > 0.2):
                hit, _, idx, _ = FULL.ray_cast(Vector(centre), Vector(D[i, j]), 0.2)
            if hit is not None:
                P[i, j] = hit
                poly[i, j] = idx
    return {"P": P, "D": -D if outside else D, "Dt": Dt, "T": T, "A": A, "poly": poly, "outside": outside}


def head_coords(P):
    q = P - HEAD_C
    phi = np.degrees(np.abs(np.arctan2(q[..., 0], -q[..., 1])))
    return phi, P[..., 2]


def line(phi, keys):
    xs, zs = zip(*keys)
    return np.interp(phi, xs, zs)


def hashf(k, seed):
    k = np.asarray(k, dtype=np.int64)
    x = (k * 374761393 + seed * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return (x & 0xFFFF) / 65535.0


def locks(coord, count, seed, depth):
    s = coord * count
    k = np.floor(s)
    u = s - k - 0.5
    prof = (1 - depth) + depth * np.sqrt(np.clip(1 - (2 * u) ** 2, 0, 1))
    return k, prof


def rim(x, width):
    return np.where(x > 0, np.clip(x / width, 0, 1) ** 0.5, 0.0)


HAIRLINE = [(0, 1.672), (28, 1.668), (50, 1.652), (68, 1.62), (78, 1.565), (86, 1.565), (92, 1.622), (108, 1.618), (122, 1.565), (140, 1.54), (180, 1.525)]


def face_coords(P):
    q = P - HEAD_C
    phi = np.degrees(np.abs(np.arctan2(q[..., 0], -q[..., 1])))
    return phi, P[..., 2], P[..., 0]


BEARD_TOP = [(0, 1.472), (10, 1.474), (17, 1.49), (24, 1.515), (40, 1.53), (62, 1.545), (90, 1.565)]
BEARD_LOW = [(0, 1.37), (40, 1.372), (70, 1.395), (90, 1.46)]


def beard_mask(phi, z, P):
    top = line(phi, BEARD_TOP)
    low = line(phi, BEARD_LOW)
    return np.minimum(np.minimum(top - z, z - low), (88 - phi) * 0.001)


MOUSTACHE_TOP = [(0, 1.505), (12, 1.505), (19, 1.5), (26, 1.49)]


def build_mesh(name, g, t, drop, body, centre):
    nt, na = t.shape
    valid = g["poly"] >= 0
    out = g["P"] + g["D"] * t[..., None]
    if drop is not None:
        out[..., 2] -= drop
    idx = np.full(t.shape, -1)
    verts, faces = [], []
    keep = np.zeros(t.shape, dtype=bool)
    quads = []
    for i in range(nt - 1):
        for j in range(na):
            jj = (j + 1) % na
            q = [(i, j), (i + 1, j), (i + 1, jj), (i, jj)]
            if all(valid[c] for c in q) and any(t[c] > 0 for c in q) and max(np.linalg.norm(g["P"][q[k]] - g["P"][q[k - 1]]) for k in range(4)) < 0.03:
                quads.append((i, j))
                for c in q:
                    keep[c] = True
    for i in range(nt):
        for j in range(na):
            if keep[i, j]:
                idx[i, j] = len(verts)
                verts.append(tuple(out[i, j]))
    for i, j in quads:
        jj = (j + 1) % na
        faces.append((idx[i, j], idx[i, jj], idx[i + 1, jj], idx[i + 1, j]))
    V = np.array(verts)
    sign = sum(np.dot(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]), V[f[0]] - centre) for f in faces[::50])
    if (sign < 0) != g.get("outside", False):
        faces = [f[::-1] for f in faces]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(hb.material("Hair"))
    for p in me.polygons:
        p.use_smooth = True
    src = [(g["P"][i, j], g["poly"][i, j]) for i in range(nt) for j in range(na) if keep[i, j]]
    return o, src


def skin_weights(o, body, W):
    names = [g.name for g in body.vertex_groups]
    M = np.zeros((len(body.data.vertices), len(names)))
    for v in body.data.vertices:
        for ge in v.groups:
            M[v.index, ge.group] = ge.weight
    o.vertex_groups.clear()
    groups = [o.vertex_groups.new(name=n) for n in names]
    for i, (vs, w) in enumerate(W):
        row = (M[vs] * w[:, None]).sum(0)
        for gi in np.nonzero(row > 1e-4)[0]:
            groups[gi].add([i], float(row[gi]), "REPLACE")


def follow(o, src, body):
    B = hb.coords(body)
    P = hb.coords(o)
    W = []
    for p, poly in src:
        vs = list(body.data.polygons[poly].vertices)
        d = np.linalg.norm(B[vs] - p, axis=1) + 1e-5
        w = 1 / d
        W.append((vs, w / w.sum()))
    skin_weights(o, body, W)
    keys = body.data.shape_keys
    if keys is None:
        return
    shapes = {}
    for kb in keys.key_blocks[1:]:
        K = np.empty(len(B) * 3)
        kb.data.foreach_get("co", K)
        delta = K.reshape(-1, 3) - B
        shapes[kb.name] = P + np.array([(delta[vs] * w[:, None]).sum(0) for vs, w in W])
    hb.add_keys(o, shapes)


REF = os.path.join(hb.ROOT, "ArtSource", "reference", "hair")
FITTED = [
    ("Hair_Tousled", "DummyHair.fbx", "Hair", "Dummy", (0.0, -0.01, 0.065), 1.3, None),
    ("Hair_Long", "Hair_Male_013.fbx", "Hair_013_Mesh1.001", "Stylized_hair_man_Pack_01.025", (0.0, -0.28, 1.53), 0.4, 1.43),
]


def ray_len(bvh, c, u):
    hit = bvh.ray_cast(Vector(c), Vector(u), 1.0)[0]
    if hit is None:
        hit = bvh.find_nearest(Vector(c) + Vector(u) * 0.1)[0]
    return (Vector(hit) - Vector(c)).length


def fit(name, file, hair_name, head_name, centre, scale, cut, bvh, ids):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REF, file))
    new = [o for o in bpy.data.objects if o not in before]
    src, head = bpy.data.objects[hair_name], bpy.data.objects[head_name]
    H = np.array([head.matrix_world @ v.co for v in head.data.vertices])
    sb = BVHTree.FromPolygons([tuple(v) for v in H], [tuple(p.vertices) for p in head.data.polygons])
    c = np.array(centre)
    P = np.array([src.matrix_world @ v.co for v in src.data.vertices])
    out, roots = [], []
    for p in P:
        r = np.linalg.norm(p - c)
        u = (p - c) / r
        h = r - ray_len(sb, c, u)
        rt = ray_len(bvh, HEAD_C, u)
        q = HEAD_C + u * (rt + h * scale)
        if cut is not None and q[2] < cut:
            q[2] = cut
        out.append(q)
        hit, _, idx, _ = bvh.ray_cast(Vector(HEAD_C), Vector(u), 1.0)
        if hit is None:
            hit, _, idx, _ = bvh.find_nearest(Vector(HEAD_C) + Vector(u) * rt)
        roots.append((np.array(hit), ids[idx]))
    me = bpy.data.meshes.new(name)
    polys = [tuple(p.vertices) for p in src.data.polygons]
    if cut is not None:
        under = np.array([q[2] <= cut + 1e-6 for q in out])
        polys = [f for f in polys if not under[list(f)].all()]
    me.from_pydata([tuple(v) for v in out], [], polys)
    me.validate()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(hb.material("Hair"))
    for p in me.polygons:
        p.use_smooth = True
    for x in new:
        bpy.data.objects.remove(x)
    return o, roots


DOWN = np.array([0.0, 0.0, -1.0])
FWD = np.array([0.0, -1.0, 0.0])


def flat(v, n):
    v = v - n * np.dot(v, n)
    l = np.linalg.norm(v)
    return v / l if l > 1e-9 else v


def trace(bvh, C, root, d, L, steps, h0, h1, hug, gravity, lift, stop, extra=None):
    pts = [root]
    p = root.copy()
    for i in range(1, steps + 1):
        t = i / steps
        d = unit(d + DOWN * gravity * t)
        q = p + d * L / steps
        r = np.linalg.norm(q - C)
        u = (q - C) / r
        hit = bvh.ray_cast(Vector(C), Vector(u), 1.0)[0]
        near = hit is not None and (Vector(hit) - Vector(q)).length < (0.03 if extra is not None else 0.05)
        if extra is not None and not near:
            break
        if near:
            target = (Vector(hit) - Vector(C)).length + h0 + (h1 - h0) * t + lift * t * t
            if extra is not None:
                target += float(extra(np.array(hit)))
            r = target if r < target else r + (target - r) * hug
            q = C + u * r
        if stop is not None and stop(q):
            break
        d = unit(q - p)
        p = q
        pts.append(q)
    return np.array(pts)


def ribbon(pts, C, W, arch, verts, faces):
    n = len(pts)
    if n < 3:
        return 0
    T = np.gradient(pts, axis=0)
    base = len(verts)
    for i, p in enumerate(pts):
        t = i / (n - 1)
        Ti = unit(T[i])
        N = flat(unit(p - C), Ti)
        S = unit(np.cross(Ti, N))
        w = max(W * (1 - t ** 1.6) * min(1.0, (t + 0.2) / 0.35), 0.0004)
        verts += [p - S * w / 2 - N * w * 0.12, p + N * w * arch, p + S * w / 2 - N * w * 0.12]
    for i in range(n - 1):
        a, b = base + 3 * i, base + 3 * (i + 1)
        faces += [(a, a + 1, b + 1, b), (a + 1, a + 2, b + 2, b + 1)]
    return 3 * n


def grow(name, g, bvh, ids, C, mask, flow, layers, seed, cap, body, stop=None, extra=None, spread=0.12, below=None):
    rng = np.random.default_rng(seed)
    m = mask(g["P"])
    ok = (g["poly"] >= 0) & (m > 0)
    if callable(cap):
        tc, dc = cap(g["P"], m)
    else:
        tc, dc = np.where(m > 0, cap * np.clip(m / 0.006, 0, 1), SINK), None
    under, src0 = build_mesh(name + "_cap", g, tc, dc, body, C)
    cand = np.argwhere(ok)
    wgt = np.sin(g["T"][ok]) + 0.05
    wgt = wgt / wgt.sum()
    verts = [tuple(v.co) for v in under.data.vertices]
    faces = [tuple(p.vertices) for p in under.data.polygons]
    src = list(src0)
    bpy.data.objects.remove(under)
    if below is not None and callable(cap):
        mb = mask(below["P"])
        tb, _ = cap(below["P"], mb)
        extra_cap, srcb = build_mesh(name + "_under", below, tb, None, body, UNDER_C)
        base = len(verts)
        verts += [tuple(v.co) for v in extra_cap.data.vertices]
        faces += [tuple(i + base for i in p.vertices) for p in extra_cap.data.polygons]
        src += list(srcb)
        bpy.data.objects.remove(extra_cap)
    for count, h0, h1, W, L, hug, gravity, lift, arch in layers:
        for k in rng.choice(len(cand), size=count, p=wgt):
            i, j = cand[k]
            P0, D = g["P"][i, j], g["D"][i, j]
            d = flat(flow(P0, D, g["Dt"][i, j]), D)
            ang = rng.normal(0, spread)
            d = unit(d * math.cos(ang) + np.cross(D, d) * math.sin(ang))
            pts = trace(bvh, C, P0 - D * 0.001, d, L * rng.uniform(0.75, 1.25), 7, h0, h1, hug, gravity, lift * rng.uniform(0, 1.5), stop, extra)
            added = ribbon(pts, C, W * rng.uniform(0.75, 1.25), arch, verts, faces)
            src += [(P0, ids_of(g, i, j))] * added
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(hb.material("Hair"))
    for p in me.polygons:
        p.use_smooth = True
    return o, src


def ids_of(g, i, j):
    return g["poly"][i, j]


def scalp_mask(P):
    phi, z = head_coords(P)
    return z - line(phi, HAIRLINE)


def meridian(P, D, Dt):
    return Dt


def beard_flow(P, D, Dt):
    return unit(DOWN + FWD * 0.35)


def moustache_flow(P, D, Dt):
    return unit(np.array([np.sign(P[0]) * 0.9, 0.0, -0.45]))


def moustache_mask(P):
    phi, z, xx = face_coords(P)
    low = line(phi, [(0, 1.494), (18, 1.488), (26, 1.485)])
    return np.minimum(np.minimum(np.minimum(line(phi, MOUSTACHE_TOP) - z, z - low), (28 - phi) * 0.001), np.abs(xx) - 0.006)


def bowl_cut(P):
    phi, z = head_coords(P)
    return z - line(phi, [(0, 1.64), (45, 1.638), (75, 1.625), (100, 1.62), (180, 1.595)])


def bowl_stop(q):
    return bowl_cut(q) < 0


def side_mask(P):
    phi, z = head_coords(P)
    top = line(phi, [(0, 1.5), (78, 1.5), (82, 1.62), (100, 1.66), (130, 1.70), (180, 1.71)])
    return np.minimum(scalp_mask(P), top - z)


def chin_mask(P):
    phi, z, xx = face_coords(P)
    return np.minimum(beard_mask(phi, z, P), (22 - phi) * 0.001)


def droop_flow(P, D, Dt):
    return unit(np.array([np.sign(P[0]) * 0.9, 0.0, -0.8]))


def chin(P):
    phi, z, xx = face_coords(P)
    return np.clip((1.5 - z) / 0.1, 0, 1) * np.clip(1 - phi / 75, 0, 1)


def thickness(base, extra):
    return lambda P: base + extra * chin(P) ** 1.3


def core(base, extra, drop):
    th = thickness(base, extra)
    return lambda P, m: (np.where(m > 0, th(P) * np.clip(m / 0.006, 0, 1), SINK), drop * chin(P) ** 1.5 * np.clip(m / 0.01, 0, 1))


def beard(P):
    return beard_mask(*face_coords(P)[:2], P)


HAIR = [(300, 0.001, 0.005, 0.028, 0.04, 0.95, 0.0, 0.0, 0.16), (180, 0.004, 0.008, 0.03, 0.045, 0.9, 0.0, 0.001, 0.18)]
GROWN = [
    ("Hair_Cropped", "head", scalp_mask, meridian, HAIR, 11, 0.004, None),
    ("Hair_Bowl", "head", bowl_cut, meridian, [
        (300, 0.002, 0.012, 0.034, 0.12, 0.8, 0.0, 0.0, 0.18),
        (200, 0.008, 0.018, 0.038, 0.12, 0.7, 0.0, 0.0, 0.2),
    ], 14, 0.006, bowl_stop),
    ("Hair_Balding", "head", side_mask, meridian, [
        (140, 0.001, 0.005, 0.026, 0.045, 0.85, 0.0, 0.002, 0.18),
        (90, 0.004, 0.009, 0.03, 0.05, 0.75, 0.0, 0.003, 0.2),
    ], 15, 0.004, None),
    ("Moustache_Short", "face", moustache_mask, moustache_flow, [
        (50, 0.002, 0.007, 0.02, 0.035, 0.6, 0.0, 0.002, 0.2),
        (30, 0.005, 0.011, 0.022, 0.04, 0.45, 0.0, 0.003, 0.22),
    ], 13, 0.004, None),
    ("Moustache_Droopy", "face", moustache_mask, droop_flow, [
        (50, 0.002, 0.008, 0.02, 0.06, 0.5, 0.4, 0.0, 0.2),
        (30, 0.005, 0.012, 0.022, 0.075, 0.35, 0.6, 0.0, 0.22),
    ], 19, 0.004, None),
]


STUBBLE_PNG = os.path.join(hb.ROOT, "Assets", "Resources", "Characters", "Hero_Skin_Stubble.png")
SKIN_COPY = os.path.join(hb.ROOT, "Assets", "Resources", "Characters", "Hero_Skin.png")


def bake_values(body, values, size):
    scn = bpy.context.scene
    me = body.data
    rgba = np.repeat(np.clip(values, 0, 1)[:, None], 4, axis=1)
    rgba[:, 3] = 1.0
    attr = me.color_attributes.new("Stubble", "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", rgba.astype(np.float32).ravel())
    img = bpy.data.images.new("StubbleMask", size, size, float_buffer=True)
    mat = bpy.data.materials.new("BakeStubble")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Stubble"
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(ca.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    nt.nodes.active = tex
    keep = list(me.materials)
    me.materials.clear()
    me.materials.append(mat)
    engine = scn.render.engine
    scn.render.engine = "CYCLES"
    scn.cycles.samples = 1
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.bake(type="EMIT", margin=8, use_clear=True)
    scn.render.engine = engine
    me.materials.clear()
    for m in keep:
        me.materials.append(m)
    bpy.data.materials.remove(mat)
    me.color_attributes.remove(me.color_attributes["Stubble"])
    px = np.array(img.pixels[:]).reshape(size, size, 4)[..., 0]
    bpy.data.images.remove(img)
    return px


def stubble_skin(body):
    V = hb.coords(body)
    phi, z, xx = face_coords(V)
    lip = np.minimum(np.minimum(1.514 - z, z - 1.488), (30 - phi) * 0.001)
    m = np.maximum(beard(V), lip)
    m = np.where((V[:, 1] < 0.02) & (V[:, 2] > 1.33), m, -1.0)
    dens = np.clip(m / 0.01 + 0.5, 0, 1)
    src = bpy.data.images.load(hb.SKIN_PNG)
    w, h = src.size
    skin = np.array(src.pixels[:]).reshape(h, w, 4)
    mask = bake_values(body, dens, w)
    rng = np.random.default_rng(9)
    dots = (rng.random((h, w)) < 0.42).astype(float)
    dots = 0.35 + 0.65 * dots
    k = (mask * dots * 0.62)[..., None]
    dark = np.array([0.16, 0.11, 0.08])
    out = skin.copy()
    out[..., :3] = skin[..., :3] * (1 - k) + dark * k
    os.makedirs(os.path.dirname(STUBBLE_PNG), exist_ok=True)
    for path, data in ((STUBBLE_PNG, out), (SKIN_COPY, skin)):
        img = bpy.data.images.new("tmp", w, h)
        img.pixels.foreach_set(data.astype(np.float32).ravel())
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
    print("stubble texture", int((mask > 0.5).sum()), "texels")


def carve(name, grids, mask, thick, drop, body, seed, grooves=30, depth=0.55):
    rng = np.random.default_rng(seed)
    mb = bpy.data.metaballs.new(name)
    mb.resolution = mb.render_resolution = 0.0035
    mb.threshold = 0.6
    VB = hb.coords(body)
    me0 = body.data
    Nv = np.array([v.normal[:] for v in me0.vertices])
    outer = np.zeros(len(VB), dtype=bool)
    for p in me0.polygons:
        if p.index in KEPT:
            outer[list(p.vertices)] = True
    m = mask(VB)
    ok = np.nonzero(outer & (m > 0) & (VB[:, 1] < 0.03) & (VB[:, 2] > 1.33))[0]
    for i in ok:
        P = VB[i]
        th = float(thick(P))
        r = min(th * 1.8, float(m[i]) * 0.8 + th * 0.8)
        el = mb.elements.new()
        el.co = Vector(P + Nv[i] * th * 0.3 - np.array([0, 0, 1.0]) * float(drop(P)))
        el.radius = max(r, 0.0065)
        el.stiffness = 2.0
    ob = bpy.data.objects.new(name + "_mb", mb)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    sm = o.modifiers.new("Smooth", "SMOOTH")
    sm.iterations = 12
    sm.factor = 0.6
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=sm.name)
    me = o.data
    me.update()
    V = hb.coords(o)
    N = np.array([v.normal[:] for v in me.vertices])
    phi, z, xx = face_coords(V)
    a = np.radians(phi) * np.sign(xx) * grooves / (2 * math.pi)
    a = a + 0.6 * np.sin(z * 55.0 + phi * 0.05)
    u = a - np.floor(a) - 0.5
    groove = 1 - np.sqrt(np.clip(1 - (2 * u) ** 2, 0, 1))
    hb.set_coords(o, V - N * (groove * depth * 0.008)[:, None])
    me.materials.clear()
    me.materials.append(hb.material("Hair"))
    for p in me.polygons:
        p.use_smooth = True
    full = hb.body_bvh(body)
    src = []
    for v in me.vertices:
        hit, _, idx, _ = full.find_nearest(v.co)
        src.append((np.array(hit), idx))
    inside = set(ok.tolist())
    cfaces = [tuple(p.vertices) for p in me0.polygons if p.index in KEPT and all(v in inside for v in p.vertices)]
    used = sorted({v for f in cfaces for v in f})
    remap = {v: k for k, v in enumerate(used)}
    cverts = [tuple(VB[v] + Nv[v] * 0.003) for v in used]
    csrc = [(VB[v], VERT_FACE[v]) for v in used]
    base = len(me.vertices)
    verts = [tuple(v.co) for v in me.vertices] + cverts
    faces = [tuple(p.vertices) for p in me.polygons] + [tuple(remap[v] + base for v in f) for f in cfaces]
    me2 = bpy.data.meshes.new(name)
    me2.from_pydata(verts, [], faces)
    me2.materials.append(hb.material("Hair"))
    for p in me2.polygons:
        p.use_smooth = True
    o.data = me2
    return o, src + list(csrc)


def push_out(o, bvh, below, gap=0.004):
    for v in o.data.vertices:
        if v.co.z > below:
            continue
        hit, n, _, _ = bvh.find_nearest(v.co)
        if hit is not None and (v.co - hit).dot(n) < gap:
            v.co = hit + n * gap


def ear_stop(q):
    phi, z = head_coords(q)
    return 80 < phi < 120 and 1.5 < z < 1.628


CARVED = [
    ("Beard_Short", beard, 0.0055, 0.003, 0.0, 21),
    ("Beard_Full", beard, 0.007, 0.016, 0.012, 22),
    ("Beard_Goatee", chin_mask, 0.006, 0.008, 0.006, 23),
]


def build(body, rig):
    bvh, ids = outer_bvh(body)
    grids = {
        "head": grid(bvh, ids, HEAD_C, (0.0, math.sin(math.radians(22)), math.cos(math.radians(22))), 128, 110, 220),
        "face": grid(bvh, ids, FACE_C, (0.0, -0.45, -0.89), 115, 110, 220),
        "under": grid(bvh, ids, UNDER_C, (0.0, 0.55, 0.83), 80, 70, 160, outside=True),
    }
    made = []
    full = hb.body_bvh(body)
    for name, file, hair_name, head_name, centre, scale, cut in FITTED:
        o, src = fit(name, file, hair_name, head_name, centre, scale, cut, bvh, ids)
        push_out(o, full, 1.5)
        follow(o, src, body)
        if rig is not None:
            hb.attach(o, rig)
        made.append(o)
        print(name, len(o.data.vertices), "verts")
    for entry in GROWN:
        name, kind, mask, flow, layers, seed, cap, stop = entry[:8]
        extra = entry[8] if len(entry) > 8 else None
        if kind == "head":
            stop = (lambda f: lambda q: ear_stop(q) or (f is not None and f(q)))(stop)
        elif extra is not None:
            stop = (lambda mk: lambda q: float(mk(q)) < -0.002)(mask)
        o, src = grow(name, grids[kind], bvh, ids, HEAD_C if kind == "head" else FACE_C, mask, flow, layers, seed, cap, body, stop, extra, 0.05 if extra is not None else 0.12, grids["under"] if extra is not None else None)
        follow(o, src, body)
        if rig is not None:
            hb.attach(o, rig)
        made.append(o)
        print(name, len(o.data.vertices), "verts")
    for name, mask, base, extra, drop, seed in CARVED:
        o, src = carve(name, [grids["face"], grids["under"]], mask, thickness(base, extra), lambda P, d=drop: d * chin(P) ** 1.5, body, seed)
        follow(o, src, body)
        if rig is not None:
            hb.attach(o, rig)
        made.append(o)
        print(name, len(o.data.vertices), "verts")
    stubble_skin(body)
    return made


def preview(made, out):
    hb.SHOTS = out
    others = [o for o in bpy.data.objects if o.type == "MESH" and o not in made]
    for m in made:
        for mat in m.data.materials:
            mat.use_backface_culling = True
    for o in made:
        for m in made:
            m.hide_render = m is not o
        hb.render(o.name, {
            "a": ((0.36, -0.78, 1.63), (0, -0.05, 1.56), None, (560, 560)),
            "b": ((-0.55, 0.75, 1.7), (0, -0.02, 1.58), None, (560, 560)),
            "c": ((0.75, -0.55, 1.3), (0, -0.05, 1.42), None, (560, 560)),
        })


def main():
    body = bpy.data.objects["Hero_Body"]
    rig = bpy.data.objects.get("Hero_Base_Armature")
    for k in body.data.shape_keys.key_blocks[1:]:
        k.value = 0.0
    for o in [o for o in bpy.data.objects if o.name.split("_")[0] in ("Hair", "Beard", "Moustache")]:
        bpy.data.objects.remove(o)
    made = build(body, rig)
    if hb.SHOTS:
        preview(made, hb.SHOTS)


if __name__ == "__main__":
    main()
