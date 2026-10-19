PACK = os.path.join(ROOT, "ArtSource", "packs", "village")
BUILD = os.path.join(PACK, "buildings", "FBX")
PROPS = os.path.join(PACK, "props", "FBX")
UNIT = 0.3
BUDGET = 1800
AO_DISTANCE = 0.3
AO_FLOOR = 0.3

M["plaster"] = mat("env_plaster", (0.93, 0.89, 0.79), 0.9)
M["beige"] = mat("env_plaster_warm", (0.88, 0.78, 0.6), 0.9)
M["beam"] = mat("env_beam_dark", (0.3, 0.2, 0.13), 0.85)
M["slate"] = mat("env_slate", (0.27, 0.31, 0.39), 0.55)
M["tile"] = mat("env_roof_tile", (0.62, 0.3, 0.2), 0.8)
M["lime"] = mat("env_limestone", (0.86, 0.81, 0.68), 0.85)
M["grey"] = mat("env_stone_grey", (0.6, 0.58, 0.55), 0.9)
M["dark"] = mat("env_stone_dark", (0.4, 0.38, 0.36), 0.9)
M["metal"] = mat("env_metal", (0.32, 0.32, 0.34), 0.5, 0.6)
M["leaf"] = mat("env_leaf_round", (0.26, 0.46, 0.18), 0.9)
M["vine"] = mat("env_vine", (0.22, 0.38, 0.14), 0.9)
M["soil"] = mat("env_soil", (0.48, 0.38, 0.25), 1.0)
mat("env_flag", (0.14, 0.28, 0.78), 0.8)

ROLES = {
    "Plaster": "plaster", "Beige": "beige", "RoofTiles": "slate", "RoofTiles_Red": "tile",
    "Stone": "grey", "Stone_Dark": "dark", "Stone_Light": "lime", "Windows": "window",
    "Wood": "beam", "Wood_Side": "beam", "DarkWood": "beam", "Wood_Light": "plank",
    "Bell": "metal", "Metal": "metal", "Green": "leaf",
}
ROOF_SWAP = {"slate": "tile", "tile": "slate"}


def role(name):
    base = name.split(".")[0]
    if base in ROLES:
        return ROLES[base]
    low = base.lower()
    for key, r in (("roof", "tile"), ("metal", "metal"), ("stone", "grey"), ("wood", "beam"), ("hay", "hay"), ("leaf", "leaf"), ("green", "leaf"), ("window", "window")):
        if key in low:
            return r
    return "plank"


def simplify(o, budget):
    d = o.modifiers.new("flat", "DECIMATE")
    d.decimate_type = "DISSOLVE"
    d.angle_limit = math.radians(4)
    d.delimit = {"MATERIAL"}
    t = o.modifiers.new("tri", "TRIANGULATE")
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    o.data = me
    tris = len(me.polygons)
    if tris > budget:
        c = o.modifiers.new("cut", "DECIMATE")
        c.ratio = budget / tris
        c.use_collapse_triangulate = True
        dg = bpy.context.evaluated_depsgraph_get()
        o.data = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        o.modifiers.clear()


def place(path, c, rz, s=1.0, roof=None, budget=None, wall=None, remap=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = []
    for o in new:
        if o.type != "MESH":
            continue
        mw = o.matrix_world.copy()
        me = o.data.copy()
        me.transform(mw)
        for a in list(me.color_attributes):
            me.color_attributes.remove(a)
        idx = [p.material_index for p in me.polygons]
        names = [m.name if m else "" for m in me.materials]
        me.materials.clear()
        slots = []
        for n in names:
            r = role(n)
            if roof and r in ROOF_SWAP and n.split(".")[0].startswith("RoofTiles"):
                r = roof
            if wall and r in ("plaster", "beige"):
                r = wall
            if remap:
                r = remap.get(r, r)
            slots.append(M[r])
        for m in slots:
            me.materials.append(m)
        for p, i in zip(me.polygons, idx):
            p.material_index = i
        fresh = bpy.data.objects.new("part", me)
        coll.objects.link(fresh)
        meshes.append(fresh)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    lo = min((v.co.z for o in meshes for v in o.data.vertices), default=0.0)
    xs = [v.co.x for o in meshes for v in o.data.vertices]
    ys = [v.co.y for o in meshes for v in o.data.vertices]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = UNIT * s
    mx = Matrix.Translation(Vector((c[0], c[1], c[2] if len(c) > 2 else 0.0))) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Scale(k, 4) @ Matrix.Translation(Vector((-cx, -cy, -lo)))
    total = sum(len(o.data.polygons) for o in meshes) or 1
    for o in meshes:
        o.data.transform(mx)
        if budget:
            simplify(o, max(60, int(budget * len(o.data.polygons) / total)))
        for p in o.data.polygons:
            p.use_smooth = False
        parts.append(o)
    return meshes


def building(name, c, rz, s=1.0, roof=None, budget=BUDGET, wall=None, remap=None):
    return place(os.path.join(BUILD, name + ".fbx"), c, rz, s, roof, budget, wall, remap)


def prop(name, c, rz, s=1.0):
    return place(os.path.join(PROPS, name + ".fbx"), c, rz, s, None, 300)


building = grouped(building)
prop = grouped(prop)


def export_tree(o, path):
    bpy.ops.object.select_all(action="DESELECT")
    for x in [o] + list(o.children):
        x.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", bake_space_transform=True, mesh_smooth_type="FACE")


def pack_export(models):
    out = []
    for o in models:
        for x in [o] + list(o.children):
            bake_ao(x, AO_DISTANCE)
            for c in x.data.color_attributes["AO"].data:
                v = AO_FLOOR + (1.0 - AO_FLOOR) * c.color[0]
                c.color = (v, v, v, 1.0)
        export_tree(o, os.path.join(OUT, o.name + ".fbx"))
        out.append((o.name, len(o.children)))
    return out

