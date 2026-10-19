import bpy, bmesh, os, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = r"C:\Users\ilana\Desktop\AI PROJECTS\Warfare1347"
SRC = os.path.join(ROOT, "ArtSource", "reference", "blender-studio", "human-base-meshes", "human_base_meshes_bundle.blend")
FBX = os.path.join(ROOT, "Assets", "Art", "Characters", "Hero_Base.fbx")
BLEND = os.path.join(ROOT, "ArtSource", "hero_base.blend")
EYE_PNG = os.path.join(ROOT, "Assets", "Art", "Characters", "Textures", "Hero_Eye.png")
SKIN_PNG = os.path.join(ROOT, "Assets", "Art", "Characters", "Textures", "Hero_Skin.png")
UV_TILES = {0: (0.0, 0.5), 1: (0.5, 0.5), 2: (0.0, 0.0), 4: (0.5, 0.0)}
SKIN_BASE = (0.965, 0.597, 0.397)
GPT_SKIN = os.path.join(ROOT, "ArtSource", "concept", "skin", "chatgpt_skin.png")
LOOKS = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "looks.json")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOTS = ARGS[0] if ARGS else None
HEIGHT = 1.75
BODY = "GEO-body_male_stylized"

SHAPE = {
    "Hips": (1.55, 1.0, 1.3),
    "Spine": (1.58, 1.0, 1.22),
    "Spine1": (1.56, 1.0, 1.3),
    "Spine2": (1.45, 1.0, 1.42),
    "Neck": (1.45, 1.0, 1.3),
    "Head": (1.15, 1.15, 1.15),
    "Shoulder": (1.3, 1.4, 1.3),
    "Arm": (1.45, 1.0, 1.45),
    "ForeArm": (1.4, 1.0, 1.4),
    "Hand": (1.4, 1.4, 1.4),
    "UpLeg": (1.75, 1.0, 1.75),
    "Leg": (1.8, 1.0, 1.8),
    "Foot": (1.55, 1.55, 1.55),
    "ToeBase": (1.55, 1.55, 1.55),
}

COLORS = {
    "Skin": ((0.80, 0.50, 0.33), 0.6),
    "Eyes": ((0.018, 0.012, 0.010), 0.25),
    "Linen": ((0.70, 0.62, 0.48), 0.9),
    "Cord": ((0.22, 0.13, 0.07), 0.8),
    "Hair": ((0.085, 0.048, 0.026), 0.75),
}


def coords(o):
    a = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def set_coords(o, V):
    o.data.vertices.foreach_set("co", np.ascontiguousarray(V).ravel())
    o.data.update()


def apply4(M, V):
    return V @ M[:3, :3].T + M[:3, 3]


def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    names = [BODY, BODY + ".eye.L", BODY + ".eye.R"]
    with bpy.data.libraries.load(SRC, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    scn = bpy.context.scene
    for o in dst.objects:
        scn.collection.objects.link(o)
    bpy.context.view_layer.update()
    objs = {o.name: o for o in dst.objects}
    mw = {n: o.matrix_world.copy() for n, o in objs.items()}
    for n, o in objs.items():
        o.parent = None
        o.data = o.data.copy()
        o.modifiers.clear()
        o.data.transform(mw[n])
        o.matrix_world = Matrix.Identity(4)
    return objs[BODY], [objs[BODY + ".eye.L"], objs[BODY + ".eye.R"]]


def normalize(body, eyes):
    V = coords(body)
    cx = (V[:, 0].min() + V[:, 0].max()) / 2
    V[:, 0] -= cx
    V[:, 2] -= V[:, 2].min()
    H = V[:, 2].max()
    feet = V[V[:, 2] < 0.03 * H]
    ank = V[np.abs(V[:, 2] - 0.09 * H) < 0.01 * H]
    ay = (ank[:, 1].min() + ank[:, 1].max()) / 2
    flip = (ay - feet[:, 1].min()) < (feet[:, 1].max() - ay)
    M = np.eye(4)
    M[0, 3] = -cx
    M[2, 3] = -coords(body)[:, 2].min()
    if flip:
        R = np.diag([-1.0, -1.0, 1.0, 1.0])
        M = R @ M
    V = apply4(M, coords(body))
    ank = V[np.abs(V[:, 2] - 0.09 * H) < 0.01 * H]
    M2 = np.eye(4)
    M2[1, 3] = -(ank[:, 1].min() + ank[:, 1].max()) / 2
    M = M2 @ M
    for o in [body] + eyes:
        set_coords(o, apply4(M, coords(o)))
    return coords(body)


def inner_run(xs, gap):
    xs = np.sort(xs)
    d = np.diff(xs)
    k = np.nonzero(d > gap)[0]
    if len(k):
        return xs[0], xs[k[0]], xs[k[0] + 1]
    return xs[0], xs[-1], None


def sl(V, z, tol):
    return V[np.abs(V[:, 2] - z) < tol]


def box_center(P):
    return (P.min(0) + P.max(0)) / 2


def edges(o):
    E = np.empty(len(o.data.edges) * 2, dtype=np.int64)
    o.data.edges.foreach_get("vertices", E)
    return E.reshape(-1, 2)


def arm_mask(V, E, H):
    mask = (V[:, 2] < 0.69 * H) & (V[:, 0] > 0)
    E = E[mask[E[:, 0]] & mask[E[:, 1]]]
    adj = [[] for _ in range(len(V))]
    for a, b in E:
        adj[a].append(b)
        adj[b].append(a)
    seed = int(np.argmax(np.where(mask, V[:, 0], -1e9)))
    seen = np.zeros(len(V), bool)
    seen[seed] = True
    stack = [seed]
    while stack:
        v = stack.pop()
        for w in adj[v]:
            if not seen[w]:
                seen[w] = True
                stack.append(w)
    print("arm verts", int(seen.sum()), "of", len(V))
    return seen


def joints(V, E):
    H = V[:, 2].max()
    L = V[V[:, 0] > 0]

    crotch = None
    for z in np.arange(0.52 * H, 0.30 * H, -0.002 * H):
        P = sl(V, z, 0.003 * H)
        if len(P) and np.abs(P[:, 0]).min() > 0.006 * H:
            crotch = z
            break

    def leg(z):
        P = sl(L, z, 0.004 * H)
        a, e, n = inner_run(P[:, 0], 0.012 * H)
        return P[P[:, 0] <= e]

    def narrowest(z0, z1):
        best = None
        for z in np.arange(z0, z1, 0.003 * H):
            P = leg(z)
            w = P[:, 0].max() - P[:, 0].min()
            if best is None or w < best[0]:
                best = (w, z, P)
        c = box_center(best[2])
        return np.array([c[0], c[1], best[1]])

    knee = narrowest(0.22 * H, 0.34 * H)
    ankle = narrowest(0.05 * H, 0.13 * H)
    th = box_center(leg(0.42 * H))
    hz = 0.5 * H
    k = (hz - knee[2]) / (0.42 * H - knee[2])
    hip = np.array([knee[0] + (th[0] - knee[0]) * k, knee[1] + (th[1] - knee[1]) * k, hz])
    foot = L[L[:, 2] < 0.04 * H]
    y0, y1 = foot[:, 1].min(), foot[:, 1].max()
    yb = y0 + 0.27 * (y1 - y0)
    fb = foot[np.abs(foot[:, 1] - yb) < 0.01 * H]
    ball = np.array([box_center(fb)[0], yb, 0.025 * H])
    toe = np.array([ball[0], y0, 0.02 * H])

    arm = V[arm_mask(V, E, H)]
    U = arm[(arm[:, 2] > 0.47 * H) & (arm[:, 2] < 0.68 * H)]
    c = U.mean(0)
    d = np.linalg.svd(U - c)[2][0]
    if d[2] > 0:
        d = -d
    sh = c + d * ((0.775 * H - c[2]) / d[2])
    T = (arm - sh) @ d
    tip_t = T.max()
    perp = arm - sh - np.outer(T, d)
    best = None
    for t in np.arange(tip_t - 0.16 * H, tip_t - 0.06 * H, 0.004 * H):
        m = np.abs(T - t) < 0.004 * H
        if m.sum() < 4:
            continue
        P = perp[m]
        r = np.linalg.norm(P - P.mean(0), axis=1).max()
        if best is None or r < best[0]:
            best = (r, t)
    wt = best[1]
    wrist = box_center(arm[np.abs(T - wt) < 0.006 * H])
    et = 0.56 * wt
    elbow = box_center(arm[np.abs(T - et) < 0.008 * H])
    tip = arm[T > tip_t - 0.012 * H].mean(0)

    def mid_y(z):
        P = sl(V, z, 0.006 * H)
        P = P[np.abs(P[:, 0]) < 0.02 * H]
        y0, y1 = P[:, 1].min(), P[:, 1].max()
        return (y0 + y1) / 2 + 0.1 * (y1 - y0)

    def spine(z):
        return np.array([0.0, mid_y(z), z])

    zs = {"Hips": hip[2], "Spine": 0.565 * H, "Spine1": 0.63 * H, "Spine2": 0.70 * H, "Neck": 0.815 * H, "Head": 0.865 * H}
    J = {}
    chain = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head"]
    for i, n in enumerate(chain):
        h = spine(zs[n])
        t = spine(zs[chain[i + 1]]) if i + 1 < len(chain) else np.array([0.0, h[1], H])
        J[n] = (h, t, chain[i - 1] if i else None)
    for side, s in (("Left", 1.0), ("Right", -1.0)):
        f = np.array([s, 1.0, 1.0])
        cl = np.array([0.025 * H * s, mid_y(0.80 * H) - 0.02 * H, 0.80 * H])
        J[side + "Shoulder"] = (cl, sh * f, "Spine2")
        J[side + "Arm"] = (sh * f, elbow * f, side + "Shoulder")
        J[side + "ForeArm"] = (elbow * f, wrist * f, side + "Arm")
        J[side + "Hand"] = (wrist * f, (wrist + 0.6 * (tip - wrist)) * f, side + "ForeArm")
        J[side + "UpLeg"] = (hip * f, knee * f, "Hips")
        J[side + "Leg"] = (knee * f, ankle * f, side + "UpLeg")
        J[side + "Foot"] = (ankle * f, ball * f, side + "Leg")
        J[side + "ToeBase"] = (ball * f, toe * f, side + "Foot")
    print("H", round(H, 3), "crotch", round(crotch / H, 3))
    for n in ("Hips", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase"):
        print("J", n, np.round(J[n][0] / H, 3), np.round(J[n][1] / H, 3))
    return J


def make_armature(name, J):
    data = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones
    for n, (h, t, p) in J.items():
        b = eb.new(n)
        b.head, b.tail = Vector(h), Vector(t)
        b.roll = 0
    for n, (h, t, p) in J.items():
        if p:
            eb[n].parent = eb[p]
            eb[n].use_connect = (Vector(J[p][1]) - Vector(h)).length < 1e-5
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def bind(mesh, arm):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


def weights(o, names, J):
    n = len(o.data.vertices)
    W = np.zeros((n, len(names)))
    idx = {g.index: names.index(g.name) for g in o.vertex_groups if g.name in names}
    for v in o.data.vertices:
        for g in v.groups:
            if g.group in idx:
                W[v.index, idx[g.group]] = g.weight
    s = W.sum(1)
    empty = s < 1e-6
    if empty.any():
        V = coords(o)[empty]
        dist = []
        for b in names:
            h, t = J[b][0], J[b][1]
            ab = t - h
            k = np.clip((V - h) @ ab / (ab @ ab), 0, 1)
            dist.append(np.linalg.norm(V - (h + np.outer(k, ab)), axis=1))
        nearest = np.argmin(np.array(dist), axis=0)
        W[np.nonzero(empty)[0], nearest] = 1.0
        s = W.sum(1)
    print("unweighted", int(empty.sum()))
    return W / s[:, None]


def shape_for(name):
    return SHAPE[name.replace("Left", "").replace("Right", "")]


def deformations(arm):
    D = {}
    order = []

    def walk(b):
        order.append(b)
        for c in b.children:
            walk(c)

    for b in arm.data.bones:
        if b.parent is None:
            walk(b)
    for b in order:
        R = np.array(b.matrix_local)
        rot = R[:3, :3]
        h = R[:3, 3]
        hn = h if b.parent is None else apply4(D[b.parent.name], h[None])[0]
        Lm = rot @ np.diag(shape_for(b.name)) @ rot.T
        M = np.eye(4)
        M[:3, :3] = Lm
        M[:3, 3] = hn - Lm @ h
        D[b.name] = M
    return D


def reshape(body, eyes, J, shapes):
    arm = make_armature("Fit", J)
    bind(body, arm)
    names = list(J.keys())
    W = weights(body, names, J)
    D = deformations(arm)
    V = coords(body)
    out = np.zeros_like(V)
    for i, n in enumerate(names):
        out += W[:, i:i + 1] * apply4(D[n], V)
    set_coords(body, out)
    for k, S in shapes.items():
        T = np.zeros_like(S)
        for i, n in enumerate(names):
            T += W[:, i:i + 1] * apply4(D[n], S)
        shapes[k] = T
    for e in eyes:
        set_coords(e, apply4(D["Head"], coords(e)))
    J2 = {n: (apply4(D[n], h[None])[0], apply4(D[n], t[None])[0], p) for n, (h, t, p) in J.items()}
    body.modifiers.clear()
    body.parent = None
    body.vertex_groups.clear()
    bpy.data.objects.remove(arm)
    zmin, zmax = out[:, 2].min(), out[:, 2].max()
    s = HEIGHT / (zmax - zmin)
    M = np.diag([s, s, s, 1.0])
    M[2, 3] = -zmin * s
    for o in [body] + eyes:
        set_coords(o, apply4(M, coords(o)))
    for k in shapes:
        shapes[k] = apply4(M, shapes[k])
    return {n: (apply4(M, h[None])[0], apply4(M, t[None])[0], p) for n, (h, t, p) in J2.items()}


def trim_lats(body, E, amount=0.16):
    V = coords(body)
    H = V[:, 2].max()
    flip = V * np.array([-1.0, 1.0, 1.0])
    arms = arm_mask(V, E, H) | arm_mask(flip, E, H)
    torso = ~arms & (V[:, 2] > 0.5 * H) & (V[:, 2] < 0.76 * H)
    z0, step = 0.5 * H, 0.01 * H
    bins = ((V[:, 2] - z0) / step).astype(int).clip(0, 26)
    hw = np.zeros(27)
    yc = np.zeros(27)
    dh = np.ones(27)
    for b in range(27):
        m = torso & (bins == b)
        if m.any():
            hw[b] = np.abs(V[m, 0]).max()
            yc[b] = (V[m, 1].min() + V[m, 1].max()) / 2
            dh[b] = (V[m, 1].max() - V[m, 1].min()) / 2
    r = np.abs(V[:, 0]) / np.maximum(hw[bins], 1e-6)
    side = smoothstep(0.6, 0.95, r)
    back = smoothstep(-0.35, 0.5, (V[:, 1] - yc[bins]) / dh[bins])
    band = np.exp(-((V[:, 2] - 0.635 * H) / (0.05 * H)) ** 2) * (1 - smoothstep(0.655 * H, 0.685 * H, V[:, 2]))
    w = side * back * band * torso
    for _ in range(8):
        acc = np.zeros(len(V))
        cnt = np.zeros(len(V))
        np.add.at(acc, E[:, 0], w[E[:, 1]])
        np.add.at(acc, E[:, 1], w[E[:, 0]])
        np.add.at(cnt, E[:, 0], 1)
        np.add.at(cnt, E[:, 1], 1)
        w = 0.5 * w + 0.5 * acc / np.maximum(cnt, 1)
    w *= torso
    V[:, 0] *= 1 - amount * w
    set_coords(body, V)


def blob(V, c, r):
    d = (V - np.asarray(c)) / np.asarray(r)
    return np.exp(-(d ** 2).sum(1))


def refine_face(body):
    V = coords(body)
    head = V[V[:, 2] > 0.84 * V[:, 2].max()]
    mid = head[np.abs(head[:, 0]) < 0.006]
    tip = mid[np.argmin(mid[:, 1])]
    alar = tip + (0, 0.018, -0.012)
    bridge = np.array([0, tip[1] + 0.035, tip[2] + 0.036])
    mouth = np.array([0, tip[1] + 0.015, tip[2] - 0.045])
    w = blob(V, alar, (0.05, 0.04, 0.024))
    V[:, 0] *= 1 - 0.3 * w
    w = blob(V, tip, (0.03, 0.03, 0.025))
    V[:, 0] *= 1 - 0.12 * w
    w = blob(V, bridge, (0.018, 0.03, 0.035))
    V[:, 1] -= 0.012 * w
    w = blob(V, mouth, (0.045, 0.03, 0.028))
    V[:, 1] += 0.013 * w
    V[:, 2] = mouth[2] + (V[:, 2] - mouth[2]) * (1 - 0.3 * w)
    set_coords(body, V)


def pack_uv(o):
    uv = np.empty(len(o.data.loops) * 2)
    o.data.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    t = np.floor(uv[:, 0]).astype(int)
    off = np.array([UV_TILES[int(k)] for k in t])
    uv[:, 0] -= t
    uv = uv * 0.5 + off
    o.data.uv_layers[0].data.foreach_set("uv", uv.astype(np.float32).ravel())


def face_shapes(body, eyes):
    V = coords(body)
    head = V[V[:, 2] > 0.84 * V[:, 2].max()]
    mid = head[np.abs(head[:, 0]) < 0.006]
    tip = mid[np.argmin(mid[:, 1])]
    ec = [(coords(e).min(0) + coords(e).max(0)) / 2 for e in eyes]
    er = (coords(eyes[0]).max(0) - coords(eyes[0]).min(0))[0] / 2
    keep = 1 - np.maximum.reduce([blob(V, c, (er * 1.15,) * 3) for c in ec])
    ez, ey = ec[0][2], ec[0][1]
    mz = tip[2] - 0.045
    sx = np.sign(V[:, 0])
    pair = lambda c, r: np.maximum(blob(V, (c[0], c[1], c[2]), r), blob(V, (-c[0], c[1], c[2]), r))
    front = smoothstep(ey + 0.09, ey + 0.03, V[:, 1])
    below = smoothstep(ez - 0.005, ez - 0.035, V[:, 2]) * smoothstep(mz - 0.12, mz - 0.07, V[:, 2])
    S = {}
    d = np.zeros_like(V)
    d[:, 0] = 0.11 * V[:, 0] * below * front * (np.abs(V[:, 0]) < 0.13)
    S["FaceWide"] = d
    w = pair((0.068, ey + 0.015, mz - 0.03), (0.045, 0.06, 0.035))
    d = np.zeros_like(V)
    d[:, 0] = 0.012 * sx * w
    d[:, 2] = -0.004 * w
    S["JawHeavy"] = d
    w = blob(V, (0, tip[1] + 0.025, tip[2] - 0.088), (0.032, 0.035, 0.028))
    d = np.zeros_like(V)
    d[:, 1] = -0.011 * w
    d[:, 2] = -0.007 * w
    S["ChinStrong"] = d
    w = pair((0.066, ey - 0.03, ez - 0.032), (0.028, 0.035, 0.022))
    d = np.zeros_like(V)
    d[:, 0] = 0.007 * sx * w
    d[:, 1] = -0.005 * w
    S["Cheekbones"] = d
    w = blob(V, tip + (0, 0.004, -0.004), (0.026, 0.03, 0.03))
    d = np.zeros_like(V)
    d[:, 1] = -0.006 * w
    d[:, 2] = -0.008 * w
    S["NoseLong"] = d
    w = blob(V, (0, tip[1] + 0.022, tip[2] + 0.022), (0.014, 0.02, 0.014))
    d = np.zeros_like(V)
    d[:, 1] = -0.007 * w
    S["NoseHump"] = d
    w = pair((ec[0][0], ey - 0.055, ez + 0.036), (0.034, 0.03, 0.017))
    d = np.zeros_like(V)
    d[:, 1] = -0.007 * w
    d[:, 2] = -0.003 * w
    S["BrowHeavy"] = d
    w = blob(V, (0, tip[1] + 0.015, mz), (0.028, 0.02, 0.012))
    d = np.zeros_like(V)
    d[:, 1] = -0.004 * w
    d[:, 2] = 0.45 * (V[:, 2] - mz) * w
    S["LipsFull"] = d
    gain = {"FaceWide": 2.0, "JawHeavy": 2.3, "ChinStrong": 2.0, "Cheekbones": 2.0, "NoseLong": 2.0, "NoseHump": 2.0, "BrowHeavy": 1.9, "LipsFull": 1.8}
    for k in S:
        S[k] *= gain[k]
        if k != "BrowHeavy":
            S[k] *= keep[:, None]
        S[k] = V + S[k]
    S.update(eye_shapes(body, eyes, V))
    return S


def eye_shapes(body, eyes, V):
    bvh = body_bvh(body)
    out = {k: np.zeros_like(V) for k in ("EyesNarrow", "EyesTilt", "EyesLong")}
    rings = []
    for e in eyes:
        c, R, oc, w, h = eye_opening(e, bvh)
        side = 1.0 if c[0] > 0 else -1.0
        a, b = w / 2, h / 2
        dx = V[:, 0] - oc[0]
        dz = V[:, 2] - oc[1]
        ell = np.sqrt((dx / a) ** 2 + (dz / b) ** 2)
        reg = (1 - smoothstep(1.1, 2.6, ell)) * (np.sign(V[:, 0]) == side) * smoothstep(c[1] + 0.3 * R, c[1] - 0.2 * R, V[:, 1])
        out["EyesNarrow"][:, 2] += -0.42 * dz * reg
        out["EyesTilt"][:, 2] += 0.32 * b * (side * dx / a) * reg
        out["EyesLong"][:, 0] += 0.16 * dx * reg
        rings.append((c, np.linalg.norm(coords(e) - c, axis=1).max(), reg))
    shapes = {}
    for k, d in out.items():
        P = V + d
        for c, R, reg in rings:
            m = reg > 0.001
            r0 = np.linalg.norm(V[m] - c, axis=1)
            r1 = np.linalg.norm(P[m] - c, axis=1)
            need = np.minimum(r0, R + 0.0006)
            fix = r1 < need
            idx = np.nonzero(m)[0][fix]
            P[idx] = c + (P[idx] - c) / r1[fix][:, None] * need[fix][:, None]
        shapes[k] = P
    return shapes


def add_keys(o, shapes):
    o.shape_key_add(name="Basis", from_mix=False)
    for name, S in shapes.items():
        k = o.shape_key_add(name=name, from_mix=False)
        k.data.foreach_set("co", np.ascontiguousarray(S, dtype=np.float32).ravel())
        k.slider_min = -1.0
        k.slider_max = 1.0
        k.value = 0.0


def follow_keys(o, body, shapes):
    B = coords(body)
    kd = KDTree(len(B))
    for i, p in enumerate(B):
        kd.insert(p, i)
    kd.balance()
    P = coords(o)
    idx = np.array([kd.find(p)[1] for p in P])
    add_keys(o, {k: P + (S[idx] - B[idx]) for k, S in shapes.items()})


def face_marks(body):
    V = coords(body)
    head = V[V[:, 2] > 0.84 * V[:, 2].max()]
    mid = head[np.abs(head[:, 0]) < 0.006]
    tip = mid[np.argmin(mid[:, 1])]
    ax = np.abs(V[:, 0])
    cheeks = np.maximum(blob(V, tip + (0.056, 0.045, -0.004), (0.03, 0.03, 0.024)), blob(V, tip + (-0.056, 0.045, -0.004), (0.03, 0.03, 0.024)))
    nose = blob(V, tip + (0, 0.008, 0.002), (0.024, 0.022, 0.026))
    lips = blob(V, tip + (0, 0.015, -0.045), (0.028, 0.02, 0.011))
    ears = smoothstep(0.098, 0.116, ax) * smoothstep(tip[2] - 0.05, tip[2] - 0.03, V[:, 2]) * (1 - smoothstep(tip[2] + 0.08, tip[2] + 0.1, V[:, 2])) * (V[:, 1] > tip[1] + 0.08)
    return {"blush": np.maximum.reduce([cheeks * 0.8, nose * 0.6, ears * 0.7]), "lips": lips, "face": np.maximum(cheeks, nose)}


def body_marks(body, J, bvh, marks):
    V = coords(body)
    names = [g.name for g in body.vertex_groups]
    hand = np.zeros(len(V))
    for v in body.data.vertices:
        for g in v.groups:
            if names[g.group].endswith("Hand"):
                hand[v.index] = max(hand[v.index], g.weight)
    blush = [marks["blush"], hand * 0.45]
    for side in ("Left", "Right"):
        k = J[side + "Leg"][0] + (0, -0.05, 0)
        blush.append(blob(V, k, (0.055, 0.04, 0.06)) * 0.5)
        e = J[side + "ForeArm"][0] + (0, 0.03, 0)
        blush.append(blob(V, e, (0.04, 0.035, 0.045)) * 0.35)
    nip = np.zeros(len(V))
    z = 0.725 * HEIGHT
    for sx in (1, -1):
        hit = bvh.ray_cast(Vector((sx * 0.105, -1.0, z)), Vector((0, 1, 0)), 2.0)[0]
        if hit is not None:
            nip = np.maximum(nip, blob(V, np.array(hit), (0.016, 0.016, 0.016)))
    return {"blush": np.maximum.reduce(blush), "lips": marks["lips"], "nipples": nip, "face": marks["face"]}


def to_linear(c):
    return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)


def vertex_uv(o):
    uv = np.empty(len(o.data.loops) * 2)
    o.data.uv_layers[0].data.foreach_get("uv", uv)
    lv = np.empty(len(o.data.loops), dtype=np.int64)
    o.data.loops.foreach_get("vertex_index", lv)
    out = np.zeros((len(o.data.vertices), 2))
    out[lv] = uv.reshape(-1, 2)
    return out


def gpt_palette(body, marks):
    img = bpy.data.images.load(GPT_SKIN)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[..., :3]
    uv = vertex_uv(body)
    x = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    y = np.clip((uv[:, 1] * h).astype(int), 0, h - 1)
    G = to_linear(px[y, x].astype(np.float64))
    bpy.data.images.remove(img)
    names = [g.name for g in body.vertex_groups]
    dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in body.data.vertices])
    plain = (marks["blush"] < 0.03) & (marks["lips"] < 0.03) & (marks["nipples"] < 0.03) & np.isin(dom, ["Spine", "Spine1", "Spine2", "LeftUpLeg", "RightUpLeg", "LeftArm", "RightArm"])
    base = np.median(G[plain], axis=0)
    ratio = lambda m: np.median(G[m] / base, axis=0)
    blush = ratio(marks["face"] > 0.6)
    lips = ratio(marks["lips"] > 0.6)
    ext = np.isin(dom, ["LeftHand", "RightHand", "LeftFoot", "RightFoot", "LeftToeBase", "RightToeBase"])
    lum = G @ np.array([0.2126, 0.7152, 0.0722])
    rel = np.ones(len(G))
    for grp in (["LeftHand"], ["RightHand"], ["LeftFoot", "LeftToeBase"], ["RightFoot", "RightToeBase"]):
        m = np.isin(dom, grp)
        rel[m] = lum[m] / np.median(lum[m])
    nails = smoothstep(1.04, 1.12, rel) * ext
    print("gpt base", np.round(base, 3), "blush", np.round(blush, 3), "lips", np.round(lips, 3), "nail verts", int((nails > 0.5).sum()))
    return {"base": base, "blush": blush, "lips": lips, "nails": nails, "nail_mult": np.median(G[nails > 0.5] / base, axis=0) if (nails > 0.5).any() else np.ones(3)}


def skin_colors(V, marks, pal):
    n = len(V)
    col = np.tile(pal["base"], (n, 1))
    wob = 1 + 0.03 * np.sin(V[:, 0] * 37 + V[:, 2] * 23) * np.sin(V[:, 1] * 31 - V[:, 2] * 17)
    col *= wob[:, None]
    blush = 1 - 1.25 * (1 - pal["blush"])
    for key, mult in (("blush", blush), ("lips", pal["lips"]), ("nipples", (0.78, 0.58, 0.52)), ("nails", pal["nail_mult"])):
        w = np.clip(marks[key], 0, 1)[:, None]
        col *= 1 - w * (1 - np.array(mult))
    return np.clip(col, 0, 1)


def bake_skin(body, marks):
    scn = bpy.context.scene
    me = body.data
    pal = gpt_palette(body, marks)
    marks["nails"] = pal["nails"]
    rgba = np.concatenate([skin_colors(coords(body), marks, pal), np.ones((len(me.vertices), 1))], axis=1)
    attr = me.color_attributes.new("Detail", "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", rgba.astype(np.float32).ravel())
    img = bpy.data.images.new("Hero_Skin", 2048, 2048)
    bake = bpy.data.materials.new("BakeSkin")
    bake.use_nodes = True
    nt = bake.node_tree
    nt.nodes.clear()
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Detail"
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(ca.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    nt.nodes.active = tex
    keep = list(me.materials)
    me.materials.clear()
    me.materials.append(bake)
    engine = scn.render.engine
    scn.render.engine = "CYCLES"
    scn.cycles.samples = 1
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.bake(type="EMIT", margin=12, use_clear=True)
    scn.render.engine = engine
    me.materials.clear()
    for m in keep:
        me.materials.append(m)
    bpy.data.materials.remove(bake)
    me.color_attributes.remove(me.color_attributes["Detail"])
    img.filepath_raw = SKIN_PNG
    img.file_format = "PNG"
    img.save()
    return img


def skin_material(img):
    m = bpy.data.materials.new("Skin")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    m.diffuse_color = (*SKIN_BASE, 1.0)
    return m


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def eye_texture(size=512, iris=0.46, pupil=0.16):
    y, x = np.mgrid[0:size, 0:size]
    u = (x + 0.5) / size * 2 - 1
    v = (y + 0.5) / size * 2 - 1
    r = np.sqrt(u * u + v * v)
    a = np.arctan2(v, u)
    rng = np.random.default_rng(7)
    fine = np.interp(a, np.linspace(-np.pi, np.pi, 241), rng.random(241))
    coarse = np.interp(a, np.linspace(-np.pi, np.pi, 41), rng.random(41))
    sclera = np.array([0.93, 0.91, 0.88]) * (1 - 0.18 * smoothstep(0.45, 1.0, r))[..., None]
    t = np.clip((r - pupil) / (iris - pupil), 0, 1)[..., None]
    inner = np.array([0.66, 0.47, 0.24])
    outer = np.array([0.36, 0.23, 0.12])
    ring = inner * (1 - t) + outer * t
    ring = ring * (0.78 + 0.44 * (0.6 * fine + 0.4 * coarse))[..., None]
    ring = ring * (1 - 0.6 * smoothstep(0.78, 1.0, t[..., 0]))[..., None]
    col = sclera
    m = (1 - smoothstep(iris - 0.015, iris + 0.015, r))[..., None]
    col = col * (1 - m) + ring * m
    m = (1 - smoothstep(pupil - 0.012, pupil + 0.012, r))[..., None]
    col = col * (1 - m) + np.array([0.02, 0.02, 0.025]) * m
    px = np.concatenate([np.clip(col, 0, 1), np.ones((size, size, 1))], axis=2)
    img = bpy.data.images.new("Hero_Eye", size, size)
    img.pixels.foreach_set(px.astype(np.float32).ravel())
    os.makedirs(os.path.dirname(EYE_PNG), exist_ok=True)
    img.filepath_raw = EYE_PNG
    img.file_format = "PNG"
    img.save()
    return img


def body_bvh(body):
    return BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons])


def eye_opening(o, bvh):
    E = coords(o)
    c = (E.min(0) + E.max(0)) / 2
    R = np.linalg.norm((E - c)[:, [0, 2]], axis=1).max()
    vis = np.array([p for p in E if p[1] < c[1] and bvh.ray_cast(Vector(p) + Vector((0, -1e-4, 0)), Vector((0, -1, 0)), 0.5)[0] is None])
    lo, hi = vis.min(0), vis.max(0)
    return c, R, np.array([(lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2]), hi[0] - lo[0], hi[2] - lo[2]


def eye_uv(o, bvh):
    c, R, oc, w, h = eye_opening(o, bvh)
    print("eye opening", np.round(oc - c[[0, 2]], 4), "w", round(w, 4), "h", round(h, 4))
    E = coords(o)
    loops = np.empty(len(o.data.loops), dtype=np.int64)
    o.data.loops.foreach_get("vertex_index", loops)
    P = E[loops]
    uv = np.stack([0.5 + (P[:, 0] - oc[0]) / (2 * R), 0.5 + (P[:, 2] - oc[1]) / (2 * R)], axis=1)
    o.data.uv_layers[0].data.foreach_set("uv", uv.astype(np.float32).ravel())
    return oc, w, h, R


def brows(body, bvh, openings):
    verts, faces = [], []
    nq, nt = 28, 6
    for oc, w, h, R in openings:
        s = 1.0 if oc[0] > 0 else -1.0
        x0 = abs(oc[0]) - 0.5 * w
        x1 = abs(oc[0]) + 0.62 * w
        base = len(verts)
        for i in range(nq):
            q = i / (nq - 1)
            zc = oc[1] + 0.5 * h + 0.42 * R + 0.16 * R * math.sin(math.pi * min(1.0, q / 0.75) * 0.5) - 0.1 * R * max(0.0, q - 0.75) / 0.25
            th = R * (0.34 - 0.2 * q) * min(1.0, (q + 0.03) / 0.12) ** 0.5 * min(1.0, (1.03 - q) / 0.3) ** 0.7
            for j in range(nt):
                t = j / (nt - 1) - 0.5
                x = s * (x0 + q * (x1 - x0))
                z = zc + t * th
                hit, n, _, _ = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 2.0)
                verts.append(hit + n * 0.0012)
        for i in range(nq - 1):
            for j in range(nt - 1):
                a = base + i * nt + j
                f = (a, a + nt, a + nt + 1, a + 1)
                faces.append(f if s > 0 else f[::-1])
    me = bpy.data.meshes.new("Hero_Brows")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("Hero_Brows", me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(material("Hair"))
    sol = o.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.0035
    sol.offset = 1.0
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=sol.name)
    return o


def fill_cornea(o):
    E = coords(o)
    c = (E.min(0) + E.max(0)) / 2
    d = E - c
    r = np.linalg.norm(d, axis=1)
    R = np.median(r)
    set_coords(o, c + d / r[:, None] * np.maximum(r, R)[:, None] * 0.975)
    print("cornea filled", int((r < R * 0.99).sum()))


def outward_eyes(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    E = coords(o)
    cs = [E[E[:, 0] > 0].mean(0), E[E[:, 0] < 0].mean(0)]
    flip = []
    for f in bm.faces:
        c = f.calc_center_median()
        e = cs[0] if c.x > 0 else cs[1]
        if f.normal.dot(c - Vector(e)) < 0:
            flip.append(f)
    bmesh.ops.reverse_faces(bm, faces=flip)
    bm.to_mesh(o.data)
    bm.free()
    print("eye faces flipped", len(flip))


def eye_material():
    m = bpy.data.materials.new("Eyes")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = eye_texture()
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.12
    m.diffuse_color = (0.9, 0.9, 0.9, 1.0)
    return m


def material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col, rough = COLORS[name]
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*col, 1.0)
    return m


def rigid(o, bone):
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name=bone)
    g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")


def attach(o, arm):
    o.parent = arm
    mod = o.modifiers.new("Armature", "ARMATURE")
    mod.object = arm


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def braies(body, J):
    H = HEIGHT
    top = J["Spine"][0][2] - 0.025 * H
    hip_z = J["LeftUpLeg"][0][2]
    knee_z = J["LeftLeg"][0][2]
    hem = knee_z + 0.35 * (hip_z - knee_z)
    allowed = {"Hips", "Spine", "LeftUpLeg", "RightUpLeg"}
    names = [g.name for g in body.vertex_groups]
    dom = []
    for v in body.data.vertices:
        g = max(v.groups, key=lambda g: g.weight, default=None)
        dom.append(names[g.group] if g else "")
    o = body.copy()
    o.data = body.data.copy()
    o.modifiers.clear()
    o.parent = None
    bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    keep = lambda v: hem <= v.co.z <= top and dom[v.index] in allowed
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(keep(v) for v in f.verts)], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    for v in bm.verts:
        if v.is_boundary:
            v.co.z = top if v.co.z > (top + hem) / 2 else hem
    bm.normal_update()
    for v in bm.verts:
        k = max(0.0, (top - v.co.z) / (top - hem)) ** 1.5
        v.co += v.normal * (0.010 + 0.022 * k) * H / 1.75
    for _ in range(4):
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    ring = [v.co.copy() for v in bm.verts if v.is_boundary and v.co.z > (top + hem) / 2]
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.clear()
    o.data.materials.append(material("Linen"))
    sol = o.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.004
    sol.offset = 1.0
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=sol.name)
    cord = waist_cord(ring, top)
    o = join([o, cord], "Hero_Braies")
    return o


def waist_cord(ring, top):
    pts = sorted(ring, key=lambda p: math.atan2(p.y, p.x))
    cu = bpy.data.curves.new("Cord", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.004
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        c = c + (c - Vector((0, 0, c.z))).normalized() * 0.003
        p.co = (c.x, c.y, top - 0.006, 1)
    sp.use_cyclic_u = True
    front = min(pts, key=lambda p: p.y)
    for dx, dz in ((-0.012, -0.07), (0.014, -0.085)):
        s2 = cu.splines.new("POLY")
        s2.points.add(2)
        y = front.y - 0.006
        s2.points[0].co = (0.0, y, top - 0.006, 1)
        s2.points[1].co = (dx * 0.6, y - 0.004, top - 0.006 + dz * 0.5, 1)
        s2.points[2].co = (dx, y - 0.002, top - 0.006 + dz, 1)
    co = bpy.data.objects.new("Cord", cu)
    bpy.context.scene.collection.objects.link(co)
    bpy.ops.object.select_all(action="DESELECT")
    co.select_set(True)
    bpy.context.view_layer.objects.active = co
    bpy.ops.object.convert(target="MESH")
    co = bpy.context.active_object
    co.data.materials.append(material("Cord"))
    rigid(co, "Hips")
    return co


def export(arm, meshes):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(
        filepath=FBX,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=False,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=False,
    )


def set_engine(scn, prefs):
    for e in prefs:
        try:
            scn.render.engine = e
            return e
        except TypeError:
            pass


def camera(name, loc, target, ortho=None, lens=60):
    cam = bpy.data.cameras.new(name)
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    o = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def render(prefix, views):
    scn = bpy.context.scene
    print("engine", set_engine(scn, ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"]))
    try:
        scn.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    if not bpy.data.objects.get("Sun"):
        setup_light(scn)
    for name, (loc, target, ortho, res) in views.items():
        cam = camera(name, loc, target, ortho)
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = res
        scn.render.filepath = os.path.join(SHOTS, f"{prefix}_{name}.png")
        bpy.ops.render.render(write_still=True)


def setup_light(scn):
    w = bpy.data.worlds.new("Grey")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.42, 0.42, 0.43, 1)
    bg.inputs[1].default_value = 0.9
    scn.world = w
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 2.6
    sun.data.angle = 0.3
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    scn.collection.objects.link(sun)


def eye_presets(objs):
    import json
    presets = json.load(open(LOOKS, encoding="utf-8"))["eyePresets"]
    for p in presets:
        for o in objs:
            for k in o.data.shape_keys.key_blocks[1:]:
                k.value = p["keys"].get(k.name, 0.0)
        render("eyes", {p["id"]: ((0, -0.75, 1.585), (0, -0.08, 1.578), None, (800, 420))})
    for o in objs:
        for k in o.data.shape_keys.key_blocks[1:]:
            k.value = 0.0


def face_variants(objs, count=6, spread=1.0, seed=3):
    rng = np.random.default_rng(seed)
    names = [k.name for k in objs[0].data.shape_keys.key_blocks[1:]]
    for i in range(count):
        vals = rng.uniform(-spread, spread, len(names)) if i else np.zeros(len(names))
        for o in objs:
            for n, v in zip(names, vals):
                o.data.shape_keys.key_blocks[n].value = v
        render("var", {str(i): ((0.35, -0.95, 1.6), (0, -0.08, 1.55), None, (600, 600))})
    for o in objs:
        for n in names:
            o.data.shape_keys.key_blocks[n].value = 0.0


def joint_preview(body, J):
    scn = bpy.context.scene
    set_engine(scn, ["BLENDER_WORKBENCH"])
    scn.display.shading.color_type = "OBJECT"
    marks = []
    for n, (h, t, p) in J.items():
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=Vector(h))
        m = bpy.context.active_object
        m.color = (1, 0.1, 0.05, 1)
        m.show_in_front = True
        marks.append(m)
    body.color = (0.8, 0.8, 0.8, 1)
    c = Vector((0, 0, body.dimensions.z / 2))
    Hh = body.dimensions.z
    for name, (loc, ortho) in {"front": ((0, -6, Hh / 2), Hh * 1.1), "side": ((6, 0, Hh / 2), Hh * 1.1)}.items():
        cam = camera("J" + name, loc, c, ortho)
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = 500, 700
        scn.render.filepath = os.path.join(SHOTS, f"joints_{name}.png")
        bpy.ops.render.render(write_still=True)
    for m in marks:
        bpy.data.objects.remove(m)
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o)


def main():
    body, eyes = load()
    pack_uv(body)
    V = normalize(body, eyes)
    J = joints(V, edges(body))
    refine_face(body)
    trim_lats(body, edges(body))
    marks = face_marks(body)
    shapes = face_shapes(body, eyes)
    if SHOTS:
        joint_preview(body, J)
    J = reshape(body, eyes, J, shapes)
    bvh = body_bvh(body)
    for e in eyes:
        fill_cornea(e)
    openings = [eye_uv(e, bvh) for e in eyes]
    brow = brows(body, bvh, openings)
    rig = make_armature("Hero_Base_Armature", J)
    rig.show_in_front = True
    body.name = "Hero_Body"
    body.data.materials.clear()
    bind(body, rig)
    body.data.materials.append(skin_material(bake_skin(body, body_marks(body, J, bvh, marks))))
    eyes = join(eyes, "Hero_Eyes")
    outward_eyes(eyes)
    eyes.data.materials.clear()
    eyes.data.materials.append(eye_material())
    rigid(eyes, "Head")
    attach(eyes, rig)
    rigid(brow, "Head")
    attach(brow, rig)
    pants = braies(body, J)
    attach(pants, rig)
    for o in (body, eyes, pants, brow):
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth()
    follow_keys(brow, body, shapes)
    add_keys(body, shapes)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hero_hair
    hair = hero_hair.build(body, rig)
    export(rig, [body, eyes, pants, brow] + hair)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True)
    print("verts", len(body.data.vertices), len(pants.data.vertices), "dims", tuple(round(x, 3) for x in body.dimensions))
    if SHOTS:
        Hh = HEIGHT
        c = (0, 0, Hh * 0.5)
        render("hero", {
            "front": ((0, -8, Hh * 0.5), c, Hh * 1.12, (640, 900)),
            "side": ((8, 0, Hh * 0.5), c, Hh * 1.12, (640, 900)),
            "look": ((1.75, -3.3, Hh * 0.62), (0, 0, Hh * 0.48), None, (900, 900)),
            "face": ((0.35, -0.95, 1.6), (0, -0.08, 1.55), None, (900, 900)),
            "face_front": ((0, -1.0, 1.58), (0, -0.08, 1.565), None, (900, 900)),
        })

        face_variants([body, brow])
        eye_presets([body, brow])

if __name__ == "__main__":
    main()
