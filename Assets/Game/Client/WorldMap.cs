using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Warfare.Core;
using Warfare.Core.World;

namespace Warfare.Client
{
    [Serializable]
    public sealed class WorldMeta
    {
        public int width;
        public int height;
        public int colorScale;
        public float lonMin;
        public float lonMax;
        public float latMin;
        public float latMax;
        public float pxPerDegLat;
        public float lonFactor;
        public float heightMin;
        public float heightMax;
        public float[] rockHeight;
    }

    public sealed partial class WorldMap : MonoBehaviour
    {
        public float HeightScale = 42f;
        public int MeshStep = 2;
        public int ChunkQuads = 128;
        public float TreeScale = 2f;
        public float TreeLodDistance = 170f;
        public float TreeFadeStart = 620f;
        public float TreeFadeEnd = 880f;
        static readonly Vector2 StartLonLat = new Vector2(2.5f, 47.5f);

        public WorldMeta Meta { get; private set; }
        public string LoadError { get; private set; }
        public TravelRules Rules { get; private set; }
        public WalkGrid Walk { get; private set; }
        public float MinTravelCost { get; private set; } = 0.5f;
        public RtsCamera Cam => rtsCam;
        public WorldLabels Labels { get; private set; }
        public Atmosphere Air { get; private set; }
        public IReadOnlyList<PlacedSettlement> Settlements => placed;

        float[] heights;
        float rockLo = 15f, rockHi = 25f;
        readonly List<PlacedSettlement> placed = new List<PlacedSettlement>();
        RtsCamera rtsCam;
        float savedShadowDistance = -1f;
        byte[] biomes;
        int biomeW, biomeH;
        sealed class TreeKind
        {
            public string Id;
            public float Scale;
            public Mesh Near, Far;
            public Material[] NearMats, FarMats;
            public Matrix4x4 NearBase, FarBase;
            public bool Shadows = true;
            public float Draw = float.MaxValue;
        }

        sealed class TreeCell
        {
            public Bounds Bounds;
            public bool HasBounds;
            public List<Matrix4x4[]>[] Batches;
            public List<int>[] Counts;
        }

        readonly List<TreeKind> treeKinds = new List<TreeKind>();
        readonly List<TreeCell> treeCells = new List<TreeCell>();

        void Start()
        {
            try
            {
                Load();
            }
            catch (Exception e)
            {
                LoadError = e.Message;
                Debug.LogException(e);
                return;
            }
            var probe = GameObject.CreatePrimitive(PrimitiveType.Plane);
            var template = probe.GetComponent<Renderer>().sharedMaterial;
            Destroy(probe);
            PrepareSettlements();
            LoadRoads();
            BuildTerrain(template);
            PlaceSettlements();
            BuildBridges();
            BuildQuays();
            BuildWalkGrid();
            BuildSmoke();
            BuildShips();
            BuildHerds();
            BuildWild();
            BuildWater(template);
            BuildLandmarks();
            BuildVegetation();
            SetupGrass();
            BuildBirds(template);
            var sun = RenderSettings.sun;
            if (sun == null)
                foreach (var l in FindObjectsByType<Light>(FindObjectsSortMode.None))
                    if (l.type == LightType.Directional) { sun = l; break; }
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            Air = Atmosphere.Create(sun, Camera.main, new Color(0.74f, 0.8f, 0.86f), new Atmosphere.Options { DofStart = 700f, DofEnd = 2600f, CloudSize = 900f, CloudWind = new Vector2(7f, 3f), Pollen = false });
            var cam = Camera.main;
            if (cam != null)
            {
                cam.farClipPlane = 6000f;
                cam.fieldOfView = 35f;
                var rts = cam.GetComponent<RtsCamera>();
                if (rts == null) rts = cam.gameObject.AddComponent<RtsCamera>();
                rtsCam = rts;
                rts.MinDistance = 25f;
                rts.MaxDistance = 1400f;
                rts.MinPitch = 38f;
                rts.MaxPitch = 72f;
                rts.Bounds = new Vector2(Meta.width / 2f, Meta.height / 2f);
                rts.Ground = (x, z) => Mathf.Max(SeaLevel, HeightAt(x + Meta.width / 2f, Meta.height / 2f - z));
                rts.LookAt(GeoToWorld(StartLonLat.x, StartLonLat.y), 0f, 330f);
            }
            gameObject.AddComponent<MapLighting>().Setup(sun, rtsCam, Air);
            gameObject.AddComponent<VegetationTour>().Map = this;
            gameObject.AddComponent<SettlementShots>().Map = this;
            if (GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp) savedShadowDistance = urp.shadowDistance;
            if (Walk != null) gameObject.AddComponent<WorldParty>().Map = this;
        }

        void LateUpdate()
        {
            if (savedShadowDistance < 0f || rtsCam == null || !(GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp)) return;
            float d = Vector3.Distance(rtsCam.transform.position, rtsCam.Focus);
            urp.shadowDistance = Mathf.Clamp(d * 2.2f, 140f, 2600f);
            if (smokeRoot != null && smokeRoot.gameObject.activeSelf != d < 650f) smokeRoot.gameObject.SetActive(d < 650f);
        }

        void OnDestroy()
        {
            DisposeGrass();
            if (savedShadowDistance >= 0f && GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp) urp.shadowDistance = savedShadowDistance;
        }

        void Load()
        {
            string dir = Path.Combine(Application.streamingAssetsPath, "Data", "world");
            Meta = JsonUtility.FromJson<WorldMeta>(File.ReadAllText(Path.Combine(dir, "world.json")));
            if (Meta.rockHeight != null && Meta.rockHeight.Length >= 2)
            {
                rockLo = Meta.rockHeight[0];
                rockHi = Meta.rockHeight[1];
            }
            var raw = File.ReadAllBytes(Path.Combine(dir, "height.r16"));
            int n = Meta.width * Meta.height;
            if (raw.Length < n * 2) throw new InvalidDataException("height.r16 is too small");
            heights = new float[n];
            float span = Meta.heightMax - Meta.heightMin;
            for (int i = 0; i < n; i++) heights[i] = Meta.heightMin + (raw[i * 2] | (raw[i * 2 + 1] << 8)) / 65535f * span;
            var biomeTex = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
            biomeTex.LoadImage(File.ReadAllBytes(Path.Combine(dir, "biome.png")));
            biomeW = biomeTex.width;
            biomeH = biomeTex.height;
            var px = biomeTex.GetPixels32();
            biomes = new byte[px.Length];
            for (int y = 0; y < biomeH; y++)
            for (int x = 0; x < biomeW; x++)
                biomes[y * biomeW + x] = px[(biomeH - 1 - y) * biomeW + x].r;
            Destroy(biomeTex);
        }

        public Vector3 GeoToWorld(float lon, float lat)
        {
            float px = (lon - Meta.lonMin) * Meta.pxPerDegLat * Meta.lonFactor;
            float py = (Meta.latMax - lat) * Meta.pxPerDegLat;
            return new Vector3(px - Meta.width / 2f, Mathf.Max(0f, HeightAt(px, py)), Meta.height / 2f - py);
        }

        float HeightAt(float px, float py)
        {
            int x = Mathf.Clamp(Mathf.RoundToInt(px), 0, Meta.width - 1);
            int y = Mathf.Clamp(Mathf.RoundToInt(py), 0, Meta.height - 1);
            return heights[y * Meta.width + x] * HeightScale;
        }

        void PrepareSettlements()
        {
            string rulesPath = Path.Combine(Application.streamingAssetsPath, "Data", "world", "models.json");
            var rules = File.Exists(rulesPath) ? JsonUtility.FromJson<ModelRules>(File.ReadAllText(rulesPath)) : null;
            foreach (var f in WorldSettlements.LoadAll())
                foreach (var (s, kind) in WorldSettlements.All(f))
                {
                    float px = (s.lon - Meta.lonMin) * Meta.pxPerDegLat * Meta.lonFactor;
                    float py = (Meta.latMax - s.lat) * Meta.pxPerDegLat;
                    var p = new PlacedSettlement { Data = s, Kind = kind, Faction = f, Px = px, Py = py };
                    ShiftToShore(p, rules);
                    Flatten(p.Px, p.Py, WorldSettlements.FlattenRadius(kind, s.capital));
                    placed.Add(p);
                }
        }

        void ShiftToShore(PlacedSettlement s, ModelRules rules)
        {
            if (rules?.waterSide == null || rules.waterWall == null) return;
            string id = null;
            foreach (var c in WorldSettlements.ModelCandidates(s.Kind, s.Faction, s.Data)) { id = c; break; }
            int i = Array.IndexOf(rules.waterSide, id);
            if (i < 0 || i >= rules.waterWall.Length || !WaterDirection(s, out var dir, out float dist)) return;
            bool variant = id != WorldSettlements.ModelId(s.Kind);
            float wall = rules.waterWall[i] * WorldSettlements.ModelScale(s.Kind, s.Data.capital && !variant);
            float shift = dist - wall - 0.4f;
            s.Px += dir.x * shift;
            s.Py -= dir.z * shift;
        }

        const float FlattenBlend = 2.4f;
        const float Waterline = 0.004f;

        void Flatten(float cx, float cy, float r)
        {
            float outer = r * FlattenBlend;
            int x0 = Mathf.Max(0, Mathf.FloorToInt(cx - outer)), x1 = Mathf.Min(Meta.width - 1, Mathf.CeilToInt(cx + outer));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(cy - outer)), y1 = Mathf.Min(Meta.height - 1, Mathf.CeilToInt(cy + outer));
            float sum = 0;
            int n = 0;
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                float hv = heights[y * Meta.width + x];
                if (hv >= Waterline && (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r)
                {
                    sum += hv;
                    n++;
                }
            }
            if (n == 0) return;
            float target = Mathf.Max(0.012f, sum / n);
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                float d = Mathf.Sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy));
                float t = Mathf.Clamp01((d - r) / (outer - r));
                float k = 1f - t * t * (3f - 2f * t);
                if (k <= 0) continue;
                int i = y * Meta.width + x;
                if (heights[i] < Waterline) continue;
                float near = WaterDistance(x, y, 3);
                if (near < 3f) k *= near / 3f;
                heights[i] = Mathf.Lerp(heights[i], target, k);
            }
        }

        float WaterDistance(int x, int y, int reach)
        {
            float best = reach;
            for (int dy = -reach; dy <= reach; dy++)
            for (int dx = -reach; dx <= reach; dx++)
            {
                int xx = x + dx, yy = y + dy;
                if (xx < 0 || yy < 0 || xx >= Meta.width || yy >= Meta.height) continue;
                if (heights[yy * Meta.width + xx] >= Waterline) continue;
                float dd = Mathf.Sqrt(dx * dx + dy * dy);
                if (dd < best) best = dd;
            }
            return best;
        }

        void PlaceSettlements()
        {
            var art = EnvironmentArt.Load();
            var root = new GameObject("Settlements").transform;
            root.SetParent(transform, false);
            var rnd = new System.Random(7);
            int missing = 0, facing = 0, wet = 0, gates = 0;
            string rulesPath = Path.Combine(Application.streamingAssetsPath, "Data", "world", "models.json");
            var rules = File.Exists(rulesPath) ? JsonUtility.FromJson<ModelRules>(File.ReadAllText(rulesPath)) : null;
            var waterSide = new HashSet<string>(rules?.waterSide ?? new string[0]);
            foreach (var s in placed)
            {
                s.Position = new Vector3(s.Px - Meta.width / 2f, HeightAt(s.Px, s.Py), Meta.height / 2f - s.Py);
                GameObject prefab = null;
                bool variant = false;
                string chosen = null;
                if (art != null)
                    foreach (var id in WorldSettlements.ModelCandidates(s.Kind, s.Faction, s.Data))
                    {
                        prefab = art.Get(id);
                        if (prefab == null) continue;
                        variant = id != WorldSettlements.ModelId(s.Kind);
                        chosen = id;
                        break;
                    }
                if (prefab == null)
                {
                    missing++;
                    continue;
                }
                float yaw = (float)rnd.NextDouble() * 360f;
                var rotation = Quaternion.Euler(0f, yaw, 0f);
                if (waterSide.Contains(chosen) && WaterDirection(s, out var toWater, out _))
                {
                    rotation = Quaternion.LookRotation(toWater);
                    facing++;
                }
                var go = Instantiate(prefab, s.Position, rotation, root);
                go.name = s.Data.id;
                go.transform.localScale = Vector3.one * WorldSettlements.ModelScale(s.Kind, s.Data.capital && !variant);
                foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true))
                    mf.sharedMesh = Skirted(mf.sharedMesh);
                if (RiverThrough(s)) gates += CutRiver(go, s, root, art);
                foreach (Transform child in go.transform)
                {
                    var cr = child.GetComponent<Renderer>();
                    if (cr == null || !OverWater(cr.bounds)) continue;
                    child.gameObject.SetActive(false);
                    wet++;
                }
                foreach (var r in go.GetComponentsInChildren<Renderer>())
                {
                    if (s.HasFootprint) s.Footprint.Encapsulate(r.bounds);
                    else { s.Footprint = r.bounds; s.HasFootprint = true; }
                }
                foreach (var r in go.GetComponentsInChildren<Renderer>())
                {
                    var mats = r.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                        if (mats[i] != null) mats[i] = PropMaterial(mats[i], s.Faction);
                    r.sharedMaterials = mats;
                }
            }
            StaticBatchingUtility.Combine(root.gameObject);
            var labels = gameObject.AddComponent<WorldLabels>();
            labels.Settlements.AddRange(placed);
            Labels = labels;
            Debug.Log($"[W1347] world settlements: {placed.Count}, {facing} facing water, {wet} buildings over water hidden, {gates} river gates" + (missing > 0 ? $", {missing} without model" : ""));
        }

        const float SkirtDepth = 1.4f;
        readonly Dictionary<Mesh, Mesh> skirted = new Dictionary<Mesh, Mesh>();

        Mesh Skirted(Mesh src)
        {
            if (src == null || !src.isReadable) return src;
            if (skirted.TryGetValue(src, out var m)) return m;
            m = Instantiate(src);
            var v = m.vertices;
            for (int i = 0; i < v.Length; i++)
                if (v[i].y < 0.02f) v[i].y -= SkirtDepth;
            m.vertices = v;
            m.RecalculateBounds();
            skirted[src] = m;
            return m;
        }

        bool RiverThrough(PlacedSettlement s)
        {
            float r = WorldSettlements.FlattenRadius(s.Kind, s.Data.capital) * 0.5f;
            int total = 0, water = 0;
            for (float y = -r; y <= r; y += 1f)
            for (float x = -r; x <= r; x += 1f)
            {
                if (x * x + y * y > r * r) continue;
                total++;
                if (HeightAt(s.Px + x, s.Py + y) < SeaLevel) water++;
            }
            return total > 0 && water > total * 0.04f;
        }

        int CutRiver(GameObject go, PlacedSettlement s, Transform root, EnvironmentArt art)
        {
            var mf = go.GetComponent<MeshFilter>();
            var mesh = mf != null ? mf.sharedMesh : null;
            if (mesh == null || !mesh.isReadable) return 0;
            var verts = mesh.vertices;
            var toWorld = go.transform.localToWorldMatrix;
            var cut = Instantiate(mesh);
            var wallPts = new List<(Vector2 p, float h)>();
            var subCount = new int[mesh.subMeshCount];
            for (int sub = 0; sub < mesh.subMeshCount; sub++)
            {
                var tris = mesh.GetTriangles(sub);
                var keep = new List<int>(tris.Length);
                for (int t = 0; t < tris.Length; t += 3)
                {
                    Vector3 a = verts[tris[t]], b = verts[tris[t + 1]], c = verts[tris[t + 2]];
                    var w = toWorld.MultiplyPoint3x4((a + b + c) / 3f);
                    float px = w.x + Meta.width / 2f, py = Meta.height / 2f - w.z;
                    if (HeightAt(px, py) >= SeaLevel)
                    {
                        keep.Add(tris[t]); keep.Add(tris[t + 1]); keep.Add(tris[t + 2]);
                        continue;
                    }
                    float top = Mathf.Max(a.y, Mathf.Max(b.y, c.y));
                    if (top > 0.3f)
                    {
                        wallPts.Add((new Vector2(px, py), top));
                        subCount[sub]++;
                    }
                }
                cut.SetTriangles(keep, sub);
            }
            mf.sharedMesh = cut;
            int wallSub = 0;
            for (int i = 1; i < subCount.Length; i++)
                if (subCount[i] > subCount[wallSub]) wallSub = i;
            float scale = go.transform.lossyScale.x;
            var ring = new List<float>();
            foreach (var v in verts)
                if (v.y > 0.3f) ring.Add(new Vector2(v.x, v.z).magnitude);
            if (ring.Count == 0) return 0;
            ring.Sort();
            float rw = ring[(int)(ring.Count * 0.92f)] * scale;
            var center = new Vector2(s.Px, s.Py);
            var arc = new List<(float ang, Vector2 p, float h)>();
            foreach (var (p, h) in wallPts)
            {
                float d = (p - center).magnitude;
                if (d < rw * 0.8f || d > rw * 1.1f) continue;
                arc.Add((Mathf.Atan2(p.y - center.y, p.x - center.x), p, h));
            }
            if (arc.Count < 4) return 0;
            arc.Sort((x, y) => x.ang.CompareTo(y.ang));
            var groups = new List<List<(float ang, Vector2 p, float h)>> { new List<(float ang, Vector2 p, float h)> { arc[0] } };
            for (int i = 1; i < arc.Count; i++)
            {
                if (arc[i].ang - arc[i - 1].ang > 0.3f) groups.Add(new List<(float ang, Vector2 p, float h)>());
                groups[groups.Count - 1].Add(arc[i]);
            }
            if (groups.Count > 1 && arc[0].ang + Mathf.PI * 2f - arc[arc.Count - 1].ang < 0.3f)
            {
                foreach (var e in groups[groups.Count - 1]) groups[0].Add((e.ang - Mathf.PI * 2f, e.p, e.h));
                groups.RemoveAt(groups.Count - 1);
            }
            var stone = go.GetComponent<Renderer>().sharedMaterials[Mathf.Clamp(wallSub, 0, mesh.subMeshCount - 1)];
            int built = 0;
            foreach (var g in groups)
            {
                if (g.Count < 4) continue;
                float a0 = float.MaxValue, a1 = float.MinValue;
                var hs = new List<float>();
                foreach (var e in g)
                {
                    a0 = Mathf.Min(a0, e.ang);
                    a1 = Mathf.Max(a1, e.ang);
                    hs.Add(e.h);
                }
                hs.Sort();
                float top = s.Position.y + hs[hs.Count / 2] * scale;
                var pa = center + new Vector2(Mathf.Cos(a0 - 0.08f), Mathf.Sin(a0 - 0.08f)) * rw * 0.95f;
                var pb = center + new Vector2(Mathf.Cos(a1 + 0.08f), Mathf.Sin(a1 + 0.08f)) * rw * 0.95f;
                var gate = new GameObject(s.Data.id + "_water_gate");
                gate.transform.SetParent(root, false);
                gate.AddComponent<MeshFilter>().sharedMesh = WaterGate(pa, pb, top, 0.4f * scale);
                gate.AddComponent<MeshRenderer>().sharedMaterial = PropMaterial(stone, s.Faction);
                built++;
            }
            return built;
        }

        Mesh WaterGate(Vector2 a, Vector2 b, float top, float thick)
        {
            var verts = new List<Vector3>();
            var tris = new List<int>();
            var uvs = new List<Vector2>();
            var along = (b - a).normalized;
            var n = new Vector2(-along.y, along.x) * (thick * 0.5f);
            float len = (b - a).magnitude;
            float lintel = Mathf.Max(0.3f, (top - SeaLevel) * 0.24f);
            Vector3 W(Vector2 p, float h) => new Vector3(p.x - Meta.width / 2f, h, Meta.height / 2f - p.y);
            void Face(Vector3 q0, Vector3 q1, Vector3 q2, Vector3 q3, Vector3 facing)
            {
                int i0 = verts.Count;
                verts.Add(q0); verts.Add(q1); verts.Add(q2); verts.Add(q3);
                uvs.Add(new Vector2(0f, 0f)); uvs.Add(new Vector2(1f, 0f)); uvs.Add(new Vector2(1f, 1f)); uvs.Add(new Vector2(0f, 1f));
                bool front = Vector3.Dot(Vector3.Cross(q1 - q0, q2 - q0), facing) > 0f;
                tris.AddRange(front ? new[] { i0, i0 + 1, i0 + 2, i0, i0 + 2, i0 + 3 } : new[] { i0, i0 + 2, i0 + 1, i0, i0 + 3, i0 + 2 });
            }
            void Box(Vector2 p0, Vector2 p1, float y0, float y1)
            {
                var c = new[] { p0 - n, p1 - n, p1 + n, p0 + n };
                var mid = (p0 + p1) * 0.5f;
                for (int k = 0; k < 4; k++)
                {
                    var e0 = c[k];
                    var e1 = c[(k + 1) % 4];
                    var o = (e0 + e1) * 0.5f - mid;
                    Face(W(e0, y0), W(e1, y0), W(e1, y1), W(e0, y1), new Vector3(o.x, 0f, -o.y));
                }
                Face(W(c[0], y1), W(c[1], y1), W(c[2], y1), W(c[3], y1), Vector3.up);
            }
            Box(a, b, top - lintel, top);
            int piers = Mathf.Max(0, Mathf.FloorToInt(len / 2.4f));
            for (int k = 1; k <= piers; k++)
            {
                var q = Vector2.Lerp(a, b, k / (piers + 1f));
                Box(q - along * 0.3f, q + along * 0.3f, SeaLevel - 0.4f, top - lintel);
            }
            Box(a - along * 0.25f, a + along * 0.25f, SeaLevel - 0.4f, top);
            Box(b - along * 0.25f, b + along * 0.25f, SeaLevel - 0.4f, top);
            var mesh = new Mesh { name = "WaterGate" };
            mesh.SetVertices(verts);
            mesh.SetTriangles(tris, 0);
            mesh.SetUVs(0, uvs);
            var cols = new Color[verts.Count];
            for (int i = 0; i < cols.Length; i++) cols[i] = new Color(0.85f, 0.85f, 0.85f, 1f);
            mesh.colors = cols;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        bool OverWater(Bounds b)
        {
            int wetPoints = 0;
            for (int i = 0; i < 5; i++)
            {
                float ox = i == 0 ? 0f : (i % 2 == 0 ? 0.35f : -0.35f), oz = i == 0 ? 0f : (i < 3 ? 0.35f : -0.35f);
                var p = b.center + new Vector3(b.size.x * ox, 0f, b.size.z * oz);
                if (HeightAt(p.x + Meta.width / 2f, Meta.height / 2f - p.z) < SeaLevel) wetPoints++;
            }
            return wetPoints >= 2;
        }

        [Serializable] class ModelRules { public string[] waterSide; public float quayTown = 0.82f, quayMedium = 0.55f, quayCastle = 0.6f;
            public float[] waterWall, yardTown, yardCastle, yardVillage, paveTown, paveColor; public float paveTile = 0.8f; }

        bool WaterDirection(PlacedSettlement s, out Vector3 dir, out float dist)
        {
            float r0 = WorldSettlements.FlattenRadius(s.Kind, s.Data.capital);
            float best = float.MaxValue, bx = 0f, by = 0f;
            for (int i = 0; i < 96; i++)
            {
                float a = i * Mathf.PI * 2f / 96f, cx = Mathf.Cos(a), cy = Mathf.Sin(a);
                for (float r = 1f; r <= r0 * 3f && r < best; r += 0.5f)
                    if (HeightAt(s.Px + cx * r, s.Py + cy * r) < SeaLevel)
                    {
                        best = r;
                        bx = cx;
                        by = cy;
                        break;
                    }
            }
            dir = new Vector3(bx, 0f, -by);
            dist = best;
            return best < float.MaxValue;
        }

        static readonly (string prefix, string pattern, float scale, float strength, float smooth, float metal)[] PropLooks =
        {
            ("env_white_stone", "stone", 1.1f, 0.7f, 0.1f, 0f),
            ("env_limestone", "stone", 1.1f, 0.7f, 0.1f, 0f),
            ("env_stone_grey", "stone", 1.0f, 0.8f, 0.08f, 0f),
            ("env_stone", "stone", 1.0f, 0.8f, 0.08f, 0f),
            ("env_wall_light", "stone", 1.1f, 0.6f, 0.1f, 0f),
            ("env_paving", "paving", 1.2f, 0.7f, 0.1f, 0f),
            ("env_log", "logs", 1.6f, 0.9f, 0.05f, 0f),
            ("env_plank", "planks", 1.4f, 0.7f, 0.06f, 0f),
            ("env_beam", "planks", 2.0f, 0.5f, 0.06f, 0f),
            ("env_wood", "planks", 1.4f, 0.7f, 0.06f, 0f),
            ("env_roof_wood", "shingles", 1.8f, 0.9f, 0.05f, 0f),
            ("env_thatch", "thatch", 1.4f, 0.75f, 0.02f, 0f),
            ("env_roof_turf", "thatch", 1.6f, 0.45f, 0.02f, 0f),
            ("env_olive", "leaves", 2.2f, 0.6f, 0.05f, 0f),
            ("env_vine", "leaves", 2.6f, 0.6f, 0.05f, 0f),
            ("env_cypress", "needles", 2.2f, 0.5f, 0.05f, 0f),
            ("env_fire", null, 1f, 0f, 0.4f, 0f),
            ("env_roof_tile", "tiles", 1.8f, 0.85f, 0.12f, 0f),
            ("env_roof_red", "tiles", 1.8f, 0.85f, 0.12f, 0f),
            ("env_slate", "slate", 2.0f, 0.8f, 0.25f, 0f),
            ("env_roof_slate", "slate", 2.0f, 0.8f, 0.25f, 0f),
            ("env_roof_green", "slate", 2.0f, 0.5f, 0.35f, 0.2f),
            ("env_plaster", "plaster", 1.0f, 1.0f, 0.05f, 0f),
            ("env_wall", "plaster", 1.0f, 1.0f, 0.05f, 0f),
            ("env_adobe", "mudbrick", 1.3f, 0.75f, 0.05f, 0f),
            ("env_brick", "brick", 1.2f, 0.8f, 0.08f, 0f),
            ("env_tile_turq", null, 1f, 0f, 0.55f, 0.1f),
            ("env_felt", "felt", 1.2f, 0.7f, 0.03f, 0f),
            ("env_rock_hill", "plaster", 0.6f, 1.0f, 0.04f, 0f),
            ("env_black", null, 1f, 0f, 0.2f, 0f),
            ("env_sandstone", "stone", 1.2f, 0.6f, 0.08f, 0f),
            ("env_ivory", "plaster", 1.0f, 0.9f, 0.12f, 0f),
            ("env_tile_green", null, 1f, 0f, 0.55f, 0.1f),
            ("env_palm_trunk", "planks", 3.0f, 0.5f, 0.04f, 0f),
            ("env_dome_gold", null, 1f, 0f, 0.65f, 0.85f),
            ("env_dome_dark", null, 1f, 0f, 0.5f, 0.3f),
            ("env_window", null, 1f, 0f, 0.6f, 0f),
            ("env_water", null, 1f, 0f, 0.9f, 0f),
            ("env_flag", null, 1f, 0f, 0.15f, 0f),
            ("env_mail", null, 1f, 0f, 0.45f, 0.6f),
            ("env_steel", null, 1f, 0f, 0.6f, 0.85f),
            ("env_leather", null, 1f, 0f, 0.3f, 0f),
            ("env_skin", null, 1f, 0f, 0.25f, 0f),
        };

        readonly Dictionary<string, Material> propMats = new Dictionary<string, Material>();
        readonly Dictionary<string, Texture2D> patterns = new Dictionary<string, Texture2D>();
        Shader propShader;

        public Material PropMaterial(Material src, FactionSettlements faction)
        {
            string name = src.name;
            bool isTrim = name.StartsWith("env_flag_trim", StringComparison.Ordinal);
            bool isFlag = !isTrim && name.StartsWith("env_flag", StringComparison.Ordinal);
            string key = isTrim ? "trim:" + faction.faction : isFlag ? "flag:" + faction.faction : name;
            if (propMats.TryGetValue(key, out var cached)) return cached;
            Color color = isTrim ? WorldSettlements.ToColor(faction.trim, Color.white) : isFlag ? WorldSettlements.ToColor(faction.color, Color.blue) : src.HasProperty("_BaseColor") ? src.GetColor("_BaseColor") : src.color;
            if (propShader == null) propShader = Shader.Find("Warfare/WorldProp");
            Material m;
            if (propShader == null)
            {
                m = new Material(src) { color = color };
                if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", color);
            }
            else
            {
                m = new Material(propShader) { name = name };
                m.SetColor("_BaseColor", color);
                m.SetFloat("_PatternStrength", 0f);
                foreach (var look in PropLooks)
                {
                    if (!name.StartsWith(look.prefix, StringComparison.Ordinal)) continue;
                    if (look.pattern != null)
                    {
                        m.SetTexture("_Pattern", Pattern(look.pattern));
                        m.SetFloat("_PatternScale", look.scale);
                        m.SetFloat("_PatternStrength", look.strength);
                    }
                    m.SetFloat("_Smoothness", look.smooth);
                    m.SetFloat("_Metallic", look.metal);
                    break;
                }
            }
            propMats[key] = m;
            return m;
        }

        Texture2D Pattern(string name)
        {
            if (!patterns.TryGetValue(name, out var t))
            {
                string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "props", name + ".png");
                t = File.Exists(path) ? LoadTexture(path, true, TextureWrapMode.Repeat) : Texture2D.grayTexture;
                patterns[name] = t;
            }
            return t;
        }

        void BuildTerrain(Material template)
        {
            string dir = Path.Combine(Application.streamingAssetsPath, "Data", "world");
            var color = new Texture2D(2, 2, TextureFormat.RGBA32, true, false) { name = "WorldColor" };
            color.LoadImage(File.ReadAllBytes(Path.Combine(dir, "color.png")), true);
            color.wrapMode = TextureWrapMode.Clamp;
            color.anisoLevel = 8;
            color.filterMode = FilterMode.Trilinear;

            var mat = TerrainMaterial(dir, color) ?? FallbackTerrainMaterial(template, color);
            terrainMat = mat;

            var root = new GameObject("Terrain").transform;
            root.SetParent(transform, false);
            int s = MeshStep;
            int gw = (Meta.width - 1) / s + 1;
            int gh = (Meta.height - 1) / s + 1;
            for (int cy = 0; cy < gh - 1; cy += ChunkQuads)
            for (int cx = 0; cx < gw - 1; cx += ChunkQuads)
            {
                int qw = Mathf.Min(ChunkQuads, gw - 1 - cx);
                int qh = Mathf.Min(ChunkQuads, gh - 1 - cy);
                var mesh = ChunkMesh(cx, cy, qw, qh, gw, gh);
                var go = new GameObject($"Chunk {cx},{cy}");
                go.transform.SetParent(root, false);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var r = go.AddComponent<MeshRenderer>();
                r.sharedMaterial = mat;
                r.shadowCastingMode = ShadowCastingMode.On;
                terrainChunks.Add((mesh, r.bounds));
            }
        }

        static readonly string[] DetailLayers = { "grass", "forest", "taiga", "farm", "steppe", "desert", "tundra", "snow", "rock" };

        Material TerrainMaterial(string dir, Texture2D color)
        {
            var shader = Shader.Find("Warfare/WorldTerrain");
            if (shader == null || !File.Exists(Path.Combine(dir, "splat0.png"))) return null;
            var mat = new Material(shader) { name = "WorldTerrain" };
            mat.SetTexture("_BaseMap", color);
            mat.SetTexture("_Relief", LoadTexture(Path.Combine(dir, "relief.png"), true, TextureWrapMode.Clamp));
            mat.SetTexture("_Splat0", LoadTexture(Path.Combine(dir, "splat0.png"), true, TextureWrapMode.Clamp));
            mat.SetTexture("_Splat1", LoadTexture(Path.Combine(dir, "splat1.png"), true, TextureWrapMode.Clamp));
            foreach (var layer in DetailLayers)
                mat.SetTexture("_" + char.ToUpperInvariant(layer[0]) + layer.Substring(1), LoadTexture(Path.Combine(dir, "detail", layer + ".png"), true, TextureWrapMode.Repeat));
            foreach (var (file, prop, fallback) in new[] { ("forest_floor", "_ForestFloor", "forest"), ("taiga_floor", "_TaigaFloor", "taiga") })
            {
                string path = Path.Combine(dir, "detail", file + ".png");
                mat.SetTexture(prop, LoadTexture(File.Exists(path) ? path : Path.Combine(dir, "detail", fallback + ".png"), true, TextureWrapMode.Repeat));
            }
            mat.SetVector("_CanopyFade", new Vector4(TreeFadeStart * 0.92f, TreeFadeEnd, 0f, 0f));
            mat.SetVector("_RockHeight", new Vector4(rockLo, rockHi, 0f, 0f));
            if (roadTex != null) mat.SetTexture("_RoadMask", roadTex);
            if (yardTex != null)
            {
                mat.SetTexture("_YardMask", yardTex);
                mat.SetTexture("_Paving", Pattern("paving"));
                mat.SetFloat("_PaveTile", yardRules.paveTile);
                if (yardRules.paveColor != null && yardRules.paveColor.Length >= 3) mat.SetColor("_PaveColor", new Color(yardRules.paveColor[0], yardRules.paveColor[1], yardRules.paveColor[2], 1f));
            }
            return mat;
        }

        Material FallbackTerrainMaterial(Material template, Texture2D color)
        {
            var mat = new Material(template) { name = "WorldTerrain", color = Color.white };
            mat.SetTexture("_BaseMap", color);
            mat.mainTexture = color;
            mat.SetColor("_BaseColor", Color.white);
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0.08f);
            return mat;
        }

        static Texture2D LoadTexture(string path, bool linear, TextureWrapMode wrap)
        {
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, true, linear) { name = Path.GetFileNameWithoutExtension(path) };
            t.LoadImage(File.ReadAllBytes(path), true);
            t.wrapMode = wrap;
            t.filterMode = FilterMode.Trilinear;
            t.anisoLevel = 8;
            return t;
        }

        float GridHeight(int gx, int gy, int gw, int gh)
        {
            int px = Mathf.Min(gx * MeshStep, Meta.width - 1);
            int py = Mathf.Min(gy * MeshStep, Meta.height - 1);
            return heights[py * Meta.width + px] * HeightScale;
        }

        Mesh ChunkMesh(int cx, int cy, int qw, int qh, int gw, int gh)
        {
            int vw = qw + 1, vh = qh + 1;
            var verts = new Vector3[vw * vh];
            var normals = new Vector3[vw * vh];
            var uvs = new Vector2[vw * vh];
            float s = MeshStep;
            for (int y = 0; y < vh; y++)
            for (int x = 0; x < vw; x++)
            {
                int gx = cx + x, gy = cy + y;
                float px = Mathf.Min(gx * s, Meta.width - 1), py = Mathf.Min(gy * s, Meta.height - 1);
                float h = GridHeight(gx, gy, gw, gh);
                int i = y * vw + x;
                verts[i] = new Vector3(px - Meta.width / 2f, h, Meta.height / 2f - py);
                uvs[i] = new Vector2(px / (Meta.width - 1), 1f - py / (Meta.height - 1));
                float hl = GridHeight(Mathf.Max(0, gx - 1), gy, gw, gh), hr = GridHeight(Mathf.Min(gw - 1, gx + 1), gy, gw, gh);
                float hd = GridHeight(gx, Mathf.Max(0, gy - 1), gw, gh), hu = GridHeight(gx, Mathf.Min(gh - 1, gy + 1), gw, gh);
                normals[i] = new Vector3(hl - hr, 2f * s, hu - hd).normalized;
            }
            var tris = new int[qw * qh * 6];
            int t = 0;
            for (int y = 0; y < qh; y++)
            for (int x = 0; x < qw; x++)
            {
                int a = y * vw + x, b = a + 1, c = a + vw, d = c + 1;
                if (Mathf.Abs(verts[a].y - verts[d].y) < Mathf.Abs(verts[b].y - verts[c].y))
                {
                    tris[t++] = a; tris[t++] = b; tris[t++] = d;
                    tris[t++] = a; tris[t++] = d; tris[t++] = c;
                }
                else
                {
                    tris[t++] = a; tris[t++] = b; tris[t++] = c;
                    tris[t++] = b; tris[t++] = d; tris[t++] = c;
                }
            }
            var m = new Mesh { name = "WorldChunk" };
            m.vertices = verts;
            m.normals = normals;
            m.uv = uvs;
            m.triangles = tris;
            m.RecalculateBounds();
            return m;
        }

        const float SeaLevel = 0.15f;

        void BuildWater(Material template)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Plane);
            go.name = "Sea";
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(transform, false);
            go.transform.localPosition = new Vector3(0f, SeaLevel, 0f);
            go.transform.localScale = new Vector3(Meta.width * 8f / 10f, 1f, Meta.height * 10f / 10f);
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = WaterMaterial(template);
            r.shadowCastingMode = ShadowCastingMode.Off;
            var bed = GameObject.CreatePrimitive(PrimitiveType.Plane);
            bed.name = "Seabed";
            Destroy(bed.GetComponent<Collider>());
            bed.transform.SetParent(transform, false);
            bed.transform.localPosition = new Vector3(0f, Meta.heightMin * HeightScale - 0.3f, 0f);
            bed.transform.localScale = go.transform.localScale;
            var br = bed.GetComponent<Renderer>();
            br.sharedMaterial = new Material(template) { name = "Seabed", color = new Color(0.05f, 0.14f, 0.24f) };
            br.shadowCastingMode = ShadowCastingMode.Off;
        }

        Material WaterMaterial(Material template)
        {
            var shader = Shader.Find("Warfare/Water");
            string waves = Path.Combine(Application.streamingAssetsPath, "Data", "world", "detail", "waves.png");
            if (shader == null || !File.Exists(waves))
            {
                var m = new Material(template) { name = "Sea" };
                var c = new Color(0.13f, 0.32f, 0.5f, 0.74f);
                m.SetColor("_BaseColor", c);
                m.SetFloat("_Surface", 1f);
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
                m.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
                m.SetInt("_ZWrite", 0);
                m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                m.renderQueue = (int)RenderQueue.Transparent;
                return m;
            }
            var mat = new Material(shader) { name = "Sea" };
            mat.SetTexture("_Waves", LoadTexture(waves, true, TextureWrapMode.Repeat));
            return mat;
        }

        void Update()
        {
            DrawTrees();
            MoveShips();
            MoveHerds();
            MoveBirds();
            JumpToCapital();
            SpinLandmarks();
            DrawGrass();
        }

        void JumpToCapital()
        {
            var kb = UnityEngine.InputSystem.Keyboard.current;
            if (kb == null || rtsCam == null) return;
            for (int i = 0; i < 9; i++)
            {
                if (!kb[UnityEngine.InputSystem.Key.Digit1 + i].wasPressedThisFrame) continue;
                var capitals = placed.FindAll(p => p.Data.capital);
                if (i < capitals.Count) rtsCam.LookAt(GeoToWorld(capitals[i].Data.lon, capitals[i].Data.lat), 0f, 330f);
            }
        }

        static readonly Dictionary<string, Color> TreeColors = new Dictionary<string, Color>
        {
            ["env_leaf_oak"] = new Color(0.27f, 0.42f, 0.15f),
            ["env_leaf_birch"] = new Color(0.42f, 0.55f, 0.2f),
            ["env_needle_spruce"] = new Color(0.15f, 0.3f, 0.17f),
            ["env_needle_pine"] = new Color(0.22f, 0.37f, 0.16f),
            ["env_leaf_acacia"] = new Color(0.44f, 0.48f, 0.22f),
            ["env_leaf_bush"] = new Color(0.4f, 0.47f, 0.2f),
            ["env_leaf_scrub"] = new Color(0.56f, 0.52f, 0.34f),
            ["env_bark"] = new Color(0.34f, 0.26f, 0.19f),
            ["env_bark_pine"] = new Color(0.48f, 0.31f, 0.2f),
            ["env_bark_birch"] = new Color(0.8f, 0.78f, 0.74f),
            ["env_rock"] = new Color(0.52f, 0.49f, 0.44f),
            ["env_rock_moss"] = new Color(0.38f, 0.44f, 0.28f),
            ["env_bark_dead"] = new Color(0.46f, 0.42f, 0.37f),
            ["env_leaf_cypress"] = new Color(0.16f, 0.29f, 0.14f),
            ["env_leaf_light"] = new Color(0.3f, 0.45f, 0.17f),
        };

        bool NearWater(float px, float py, float r)
        {
            for (int i = 0; i < 8; i++)
            {
                float a = i * Mathf.PI / 4f;
                float dx = Mathf.Cos(a), dy = Mathf.Sin(a);
                if (HeightAt(px + dx * r, py + dy * r) < SeaLevel - 0.05f || HeightAt(px + dx * r * 0.5f, py + dy * r * 0.5f) < SeaLevel - 0.05f) return true;
            }
            return false;
        }

        (Mesh, Material[], Matrix4x4) TreeMesh(GameObject prefab, Shader shader, Dictionary<string, Material> cache)
        {
            var mf = prefab.GetComponentInChildren<MeshFilter>();
            var mr = prefab.GetComponentInChildren<MeshRenderer>();
            if (mf == null || mr == null) return (null, null, Matrix4x4.identity);
            var src = mr.sharedMaterials;
            var outMats = new Material[src.Length];
            for (int i = 0; i < src.Length; i++)
            {
                string name = src[i] != null ? src[i].name : "env_leaf";
                if (!cache.TryGetValue(name, out var m))
                {
                    if (!TreeColors.TryGetValue(name, out var color)) color = src[i] != null && src[i].HasProperty("_BaseColor") ? src[i].GetColor("_BaseColor") : Color.green;
                    m = new Material(shader) { name = name, enableInstancing = true };
                    m.SetColor("_BaseColor", color);
                    bool foliage = name.StartsWith("env_leaf", StringComparison.Ordinal) || name.StartsWith("env_needle", StringComparison.Ordinal);
                    bool rock = name.StartsWith("env_rock", StringComparison.Ordinal);
                    string pattern = rock ? "rock" : name.StartsWith("env_needle", StringComparison.Ordinal) ? "needles" : foliage ? "leaves" : name.StartsWith("env_bark_birch", StringComparison.Ordinal) ? "birch" : "bark";
                    m.SetTexture("_Pattern", Pattern(pattern));
                    m.SetFloat("_PatternScale", foliage ? 3.2f : rock ? 1.7f : 2.6f);
                    m.SetFloat("_PatternStrength", foliage ? 0.75f : rock ? 0.6f : 0.8f);
                    m.SetFloat("_Foliage", foliage ? 1f : 0f);
                    m.SetFloat("_Variation", foliage ? 0.28f : 0.12f);
                    m.SetFloat("_AOStrength", foliage ? 0.7f : rock ? 0.55f : 0.8f);
                    m.SetFloat("_FadeStart", TreeFadeStart);
                    m.SetFloat("_FadeEnd", TreeFadeEnd);
                    cache[name] = m;
                }
                outMats[i] = m;
            }
            var baseM = prefab.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix;
            return (mf.sharedMesh, outMats, baseM);
        }

        [Serializable] class RoadFile { public RoadLine[] roads; public BridgeInfo[] bridges; public SeaRoute[] sea; public SeaRoute[] fishing; }
        [Serializable] class SeaRoute { public string ship; public string faction; public float[] pts; }

        sealed class Sailer
        {
            public Transform T;
            public Vector3[] Path;
            public float[] Cum;
            public float Speed, Pos, Phase;
            public bool Loop;
            public int Dir = 1;
        }

        readonly List<Sailer> sailers = new List<Sailer>();

        void BuildShips()
        {
            if (roadData == null || placed.Count == 0) return;
            var art = EnvironmentArt.Load();
            if (art == null) return;
            var root = new GameObject("Ships").transform;
            root.SetParent(transform, false);
            var rnd = new System.Random(9);
            void Spawn(SeaRoute r, bool loop)
            {
                var prefab = art.Get("WorldShip_" + r.ship);
                if (prefab == null || r.pts == null || r.pts.Length < 8) return;
                int n = r.pts.Length / 2;
                var path = new Vector3[loop ? n + 1 : n];
                for (int i = 0; i < n; i++) path[i] = new Vector3(r.pts[i * 2] - Meta.width / 2f, SeaLevel, Meta.height / 2f - r.pts[i * 2 + 1]);
                if (loop) path[n] = path[0];
                var cum = new float[path.Length];
                for (int i = 1; i < path.Length; i++) cum[i] = cum[i - 1] + Vector3.Distance(path[i], path[i - 1]);
                var faction = placed.Find(p => p.Faction.faction == r.faction)?.Faction ?? placed[0].Faction;
                int ships = loop ? 1 : Mathf.Clamp(Mathf.RoundToInt(cum[cum.Length - 1] / 140f), 1, 3);
                for (int k = 0; k < ships; k++)
                {
                    var go = Instantiate(prefab, root);
                    go.transform.localScale = Vector3.one * (Creatures?.Ships != null ? (r.ship == "boat" ? Creatures.Ships.BoatScale : Creatures.Ships.ShipScale) : r.ship == "boat" ? 2.0f : 3.0f);
                    foreach (var rd in go.GetComponentsInChildren<Renderer>())
                    {
                        var mats = rd.sharedMaterials;
                        for (int i = 0; i < mats.Length; i++)
                            if (mats[i] != null) mats[i] = PropMaterial(mats[i], faction);
                        rd.sharedMaterials = mats;
                    }
                    sailers.Add(new Sailer { T = go.transform, Path = path, Cum = cum, Loop = loop, Speed = Creatures?.Ships != null ? (loop ? Creatures.Ships.FishingSpeed : Creatures.Ships.SeaSpeed) : loop ? 0.7f : 2.6f, Pos = (float)rnd.NextDouble() * cum[cum.Length - 1], Phase = (float)rnd.NextDouble() * 6.28f, Dir = rnd.NextDouble() < 0.5 ? 1 : -1 });
                }
            }
            if (roadData.sea != null) foreach (var r in roadData.sea) Spawn(r, false);
            if (roadData.fishing != null) foreach (var r in roadData.fishing) Spawn(r, true);
            Debug.Log($"[W1347] ships: {sailers.Count}");
        }

        sealed class Grazer
        {
            public Transform T;
            public Vector2 Home, Pos, Target;
            public float Speed, Wait;
            public Animator Anim;
            public Quaternion Face = Quaternion.Euler(0f, 90f, 0f);
            public bool Eats;
            public float Roam = 3.6f;
        }

        readonly List<Grazer> grazers = new List<Grazer>();

        void BuildHerds()
        {
            var art = EnvironmentArt.Load();
            if (art == null || placed.Count == 0) return;
            var root = new GameObject("Herds").transform;
            root.SetParent(transform, false);
            var rnd = new System.Random(21);
            foreach (var st in placed)
            {
                if (st.Kind != SettlementKind.Village) continue;
                string main = st.Faction.faction switch { "khordan" => "horse", "azhar" => "donkey", _ => "cow" };
                string second = st.Faction.faction switch { "khordan" => "cow", "azhar" => "horse", "grim" => "donkey", _ => "horse" };
                float rIn = WorldSettlements.FlattenRadius(st.Kind, false) * 1.25f;
                int herds = rnd.NextDouble() < 0.5 ? 2 : 1;
                for (int hI = 0; hI < herds; hI++)
                {
                    float a = (float)rnd.NextDouble() * Mathf.PI * 2f;
                    var center = new Vector2(st.Px + Mathf.Cos(a) * (rIn + 3.5f), st.Py + Mathf.Sin(a) * (rIn + 3.5f));
                    float hc = HeightAt(center.x, center.y);
                    if (hc < SeaLevel + 0.3f || OnRoad(center.x, center.y)) continue;
                    string kind = rnd.NextDouble() < 0.7 ? main : second;
                    var creature = Creatures != null && Creatures.Creatures.TryGetValue(kind, out var cr) ? cr : null;
                    if (creature == null) continue;
                    int count = rnd.Next(3, 7);
                    for (int i = 0; i < count; i++)
                    {
                        var pos = center + new Vector2((float)rnd.NextDouble() - 0.5f, (float)rnd.NextDouble() - 0.5f) * 3.2f;
                        float h = HeightAt(pos.x, pos.y);
                        if (h < SeaLevel + 0.25f) continue;
                        var go = SpawnCreature(creature, art, rnd, root, out var anim, out var face);
                        if (go == null) continue;
                        foreach (var rd in go.GetComponentsInChildren<Renderer>())
                        {
                            var mats = rd.sharedMaterials;
                            for (int m = 0; m < mats.Length; m++)
                                if (mats[m] != null) mats[m] = PropMaterial(mats[m], st.Faction);
                            rd.sharedMaterials = mats;
                            rd.shadowCastingMode = ShadowCastingMode.On;
                        }
                        var g = new Grazer { T = go.transform, Home = center, Pos = pos, Target = pos, Speed = creature.Speed, Wait = (float)rnd.NextDouble() * 5f, Anim = anim, Face = face, Eats = rnd.NextDouble() < 0.6 };
                        go.transform.SetPositionAndRotation(new Vector3(pos.x - Meta.width / 2f, h, Meta.height / 2f - pos.y), Quaternion.Euler(0f, (float)rnd.NextDouble() * 360f, 0f) * face);
                        if (anim != null) anim.SetFloat("State", g.Eats ? 0f : 1f);
                        grazers.Add(g);
                    }
                }
            }
            Debug.Log($"[W1347] herd animals: {grazers.Count}");
        }

        readonly System.Random herdRnd = new System.Random(5);
        bool herdsAnimated = true;

        void MoveHerds()
        {
            if (rtsCam == null || grazers.Count == 0) return;
            float camD = Vector3.Distance(rtsCam.transform.position, rtsCam.Focus);
            bool animate = camD <= 420f;
            if (animate != herdsAnimated)
            {
                herdsAnimated = animate;
                foreach (var gr in grazers)
                    if (gr.Anim != null) gr.Anim.enabled = animate;
            }
            if (!animate) return;
            float dt = Time.deltaTime;
            var eye = rtsCam.Focus;
            foreach (var g in grazers)
            {
                var wp = g.T.position;
                if ((wp.x - eye.x) * (wp.x - eye.x) + (wp.z - eye.z) * (wp.z - eye.z) > 260f * 260f) continue;
                if (g.Wait > 0f)
                {
                    g.Wait -= dt;
                    if (g.Anim != null) g.Anim.SetFloat("State", g.Eats ? 0f : 1f, 0.25f, dt);
                    if (g.Wait <= 0f) g.Target = g.Home + new Vector2((float)herdRnd.NextDouble() - 0.5f, (float)herdRnd.NextDouble() - 0.5f) * g.Roam;
                    continue;
                }
                var d = g.Target - g.Pos;
                float len = d.magnitude;
                if (len < 0.05f)
                {
                    g.Wait = 2f + (float)herdRnd.NextDouble() * 6f;
                    g.Eats = herdRnd.NextDouble() < 0.6;
                    continue;
                }
                if (g.Anim != null) g.Anim.SetFloat("State", 2f, 0.2f, dt);
                var step = d / len * Mathf.Min(len, g.Speed * dt);
                float h = HeightAt(g.Pos.x + step.x, g.Pos.y + step.y);
                if (h < SeaLevel + 0.25f)
                {
                    g.Wait = 1f;
                    g.Target = g.Pos;
                    continue;
                }
                g.Pos += step;
                var dir = new Vector3(step.x, 0f, -step.y);
                g.T.SetPositionAndRotation(new Vector3(g.Pos.x - Meta.width / 2f, h, Meta.height / 2f - g.Pos.y), Quaternion.LookRotation(dir.normalized) * g.Face);
            }
        }

        sealed class Bird
        {
            public Transform T;
            public Vector3 Center;
            public float Radius, Speed, Angle, Phase, Height;
        }

        readonly List<Bird> birds = new List<Bird>();
        Transform birdRoot;

        void BuildBirds(Material template)
        {
            var mesh = new Mesh { name = "Bird" };
            var v = new[] { new Vector3(0f, 0f, 0.12f), new Vector3(-0.5f, 0.18f, -0.1f), new Vector3(0f, 0f, -0.12f), new Vector3(0.5f, 0.18f, -0.1f) };
            mesh.vertices = new[] { v[0], v[1], v[2], v[3], v[0], v[1], v[2], v[3] };
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3, 4, 6, 5, 4, 7, 6 };
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            var mat = new Material(template) { name = "Bird", color = new Color(0.12f, 0.12f, 0.13f) };
            mat.SetColor("_BaseColor", new Color(0.12f, 0.12f, 0.13f));
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", 0.1f);
            birdRoot = new GameObject("Birds").transform;
            birdRoot.SetParent(transform, false);
            var rnd = new System.Random(31);
            int flocks = 0, tries = 0;
            while (flocks < 32 && tries++ < 4000)
            {
                float px = (float)rnd.NextDouble() * Meta.width, py = (float)rnd.NextDouble() * Meta.height;
                float h = HeightAt(px, py);
                if (h < SeaLevel + 0.5f && rnd.NextDouble() > 0.15) continue;
                var center = new Vector3(px - Meta.width / 2f, Mathf.Max(h, SeaLevel) + 7f + (float)rnd.NextDouble() * 6f, Meta.height / 2f - py);
                int n = rnd.Next(5, 10);
                float radius = 5f + (float)rnd.NextDouble() * 9f, speed = (0.25f + (float)rnd.NextDouble() * 0.2f) * (rnd.NextDouble() < 0.5 ? 1f : -1f);
                for (int i = 0; i < n; i++)
                {
                    var go = new GameObject("bird");
                    go.transform.SetParent(birdRoot, false);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = mat;
                    mr.shadowCastingMode = ShadowCastingMode.Off;
                    go.transform.localScale = Vector3.one * 0.9f;
                    birds.Add(new Bird { T = go.transform, Center = center, Radius = radius * (0.8f + (float)rnd.NextDouble() * 0.4f), Speed = speed, Angle = (float)rnd.NextDouble() * 0.9f + i * 0.18f, Phase = (float)rnd.NextDouble() * 6.28f, Height = (float)rnd.NextDouble() * 1.5f });
                }
                flocks++;
            }
            Debug.Log($"[W1347] birds: {birds.Count} in {flocks} flocks");
        }

        void MoveBirds()
        {
            if (birdRoot == null || rtsCam == null) return;
            float camD = Vector3.Distance(rtsCam.transform.position, rtsCam.Focus);
            bool show = camD < 520f;
            if (birdRoot.gameObject.activeSelf != show) birdRoot.gameObject.SetActive(show);
            if (!show) return;
            float t = Time.time, dt = Time.deltaTime;
            foreach (var b in birds)
            {
                b.Angle += b.Speed * dt * 30f / Mathf.Max(b.Radius, 1f);
                float wob = Mathf.Sin(t * 0.7f + b.Phase) * 0.15f;
                var p = b.Center + new Vector3(Mathf.Cos(b.Angle) * b.Radius * (1f + wob), b.Height + Mathf.Sin(t * 0.9f + b.Phase) * 0.6f, Mathf.Sin(b.Angle) * b.Radius * (1f - wob));
                var tangent = new Vector3(-Mathf.Sin(b.Angle), 0f, Mathf.Cos(b.Angle)) * Mathf.Sign(b.Speed);
                float flap = 0.3f + 0.7f * (0.5f + 0.5f * Mathf.Sin(t * 9f + b.Phase * 3f));
                b.T.SetPositionAndRotation(p, Quaternion.LookRotation(tangent) * Quaternion.Euler(0f, 0f, Mathf.Sign(b.Speed) * -18f));
                b.T.localScale = new Vector3(0.9f, 0.9f * flap, 0.9f);
            }
        }

        void MoveShips()
        {
            float t = Time.time, dt = Time.deltaTime;
            foreach (var s in sailers)
            {
                float len = s.Cum[s.Cum.Length - 1];
                s.Pos += s.Speed * dt * s.Dir;
                if (s.Loop) s.Pos = Mathf.Repeat(s.Pos, len);
                else if (s.Pos > len) { s.Pos = len; s.Dir = -1; }
                else if (s.Pos < 0f) { s.Pos = 0f; s.Dir = 1; }
                int i = Array.BinarySearch(s.Cum, s.Pos);
                if (i < 0) i = ~i;
                i = Mathf.Clamp(i, 1, s.Path.Length - 1);
                float seg = Mathf.Max(1e-4f, s.Cum[i] - s.Cum[i - 1]);
                var pos = Vector3.Lerp(s.Path[i - 1], s.Path[i], (s.Pos - s.Cum[i - 1]) / seg);
                var dir = (s.Path[i] - s.Path[i - 1]) * s.Dir;
                dir.y = 0f;
                if (dir.sqrMagnitude < 1e-6f) dir = Vector3.forward;
                pos.y = SeaLevel + 0.02f + Mathf.Sin(t * 1.3f + s.Phase) * 0.03f;
                var rot = Quaternion.LookRotation(dir.normalized) * Quaternion.Euler(Mathf.Sin(t * 0.9f + s.Phase) * 3f, 90f, Mathf.Sin(t * 1.1f + s.Phase) * 2f);
                s.T.SetPositionAndRotation(pos, rot);
            }
        }
        [Serializable] class RoadLine { public string kind; public float[] pts; }
        [Serializable] class BridgeInfo { public float x, y, dx, dy, len; public string kind; }

        RoadFile roadData;
        byte[] roadMask, trodMask, paveMask;
        int roadW, roadH;
        Texture2D roadTex, yardTex;
        ModelRules yardRules;

        void LoadRoads()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "roads.json");
            if (!File.Exists(path)) return;
            roadData = JsonUtility.FromJson<RoadFile>(File.ReadAllText(path));
            if (roadData?.roads == null) return;
            roadW = Meta.width * 2;
            roadH = Meta.height * 2;
            roadMask = new byte[roadW * roadH];
            foreach (var r in roadData.roads)
            {
                float radius = r.kind == "main" ? 1.8f : r.kind == "trade" ? 1.6f : 1.15f;
                for (int i = 0; i + 3 < r.pts.Length; i += 2)
                {
                    var a = new Vector2(r.pts[i], r.pts[i + 1]) * 2f;
                    var b = new Vector2(r.pts[i + 2], r.pts[i + 3]) * 2f;
                    int steps = Mathf.Max(1, Mathf.CeilToInt(Vector2.Distance(a, b) / 0.6f));
                    for (int k = 0; k <= steps; k++) StampRoad(Vector2.Lerp(a, b, k / (float)steps), radius);
                }
            }
            StampYards();
            roadTex = new Texture2D(roadW, roadH, TextureFormat.R8, true, true) { name = "RoadMask", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Trilinear, anisoLevel = 4 };
            roadTex.SetPixelData(roadMask, 0);
            roadTex.Apply(true, true);
            Debug.Log($"[W1347] roads: {roadData.roads.Length}, bridges: {roadData.bridges?.Length ?? 0}");
        }

        void StampRoad(Vector2 c, float r)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt(c.x - r - 1.5f)), x1 = Mathf.Min(roadW - 1, Mathf.CeilToInt(c.x + r + 1.5f));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(c.y - r - 1.5f)), y1 = Mathf.Min(roadH - 1, Mathf.CeilToInt(c.y + r + 1.5f));
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), c);
                float v = Mathf.Clamp01((r + 0.9f - d) / 1.8f);
                if (v <= 0f) continue;
                int i = (roadH - 1 - y) * roadW + x;
                byte bv = (byte)(v * v * (3f - 2f * v) * 255f);
                if (bv > roadMask[i]) roadMask[i] = bv;
            }
        }

        void StampYards()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "models.json");
            var rules = File.Exists(path) ? JsonUtility.FromJson<ModelRules>(File.ReadAllText(path)) : null;
            if (rules == null) return;
            yardRules = rules;
            trodMask = new byte[roadW * roadH];
            paveMask = new byte[roadW * roadH];
            foreach (var s in placed)
            {
                var yard = s.Kind == SettlementKind.Town ? rules.yardTown : s.Kind == SettlementKind.Castle ? rules.yardCastle : rules.yardVillage;
                var c = new Vector2(s.Px, s.Py) * 2f;
                float r = WorldSettlements.FlattenRadius(s.Kind, s.Data.capital) * 2f;
                float seed = s.Px * 0.37f + s.Py * 0.11f;
                if (yard != null && yard.Length >= 2) StampYard(trodMask, c, r * yard[0], yard[1], seed);
                bool big = s.Kind == SettlementKind.Town && (s.Data.capital || s.Data.model == "large");
                if (big && rules.paveTown != null && rules.paveTown.Length >= 2) StampYard(paveMask, c, r * rules.paveTown[0], rules.paveTown[1], seed + 5.1f);
            }
            var rg = new byte[roadW * roadH * 2];
            for (int i = 0; i < trodMask.Length; i++)
            {
                rg[i * 2] = trodMask[i];
                rg[i * 2 + 1] = paveMask[i];
            }
            yardTex = new Texture2D(roadW, roadH, TextureFormat.RG16, true, true) { name = "YardMask", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Trilinear, anisoLevel = 4 };
            yardTex.SetPixelData(rg, 0);
            yardTex.Apply(true, true);
        }

        void StampYard(byte[] mask, Vector2 c, float r, float strength, float seed)
        {
            float reach = r * 1.4f + 2f;
            int x0 = Mathf.Max(0, Mathf.FloorToInt(c.x - reach)), x1 = Mathf.Min(roadW - 1, Mathf.CeilToInt(c.x + reach));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(c.y - reach)), y1 = Mathf.Min(roadH - 1, Mathf.CeilToInt(c.y + reach));
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                var o = new Vector2(x + 0.5f, y + 0.5f) - c;
                float d = o.magnitude;
                float a = Mathf.Atan2(o.y, o.x);
                float edge = r * (0.86f + 0.28f * Mathf.PerlinNoise(seed + Mathf.Cos(a) * 1.3f, seed * 0.7f + Mathf.Sin(a) * 1.3f));
                float speck = Mathf.PerlinNoise(seed + x * 0.21f, seed * 1.3f + y * 0.21f);
                float v = Mathf.Clamp01((edge - d) / (r * 0.45f)) * Mathf.Lerp(0.75f, 1.05f, speck) * strength;
                if (v <= 0f) continue;
                int i = (roadH - 1 - y) * roadW + x;
                byte bv = (byte)(Mathf.Clamp01(v) * 255f);
                if (bv > mask[i]) mask[i] = bv;
            }
        }

        bool OnRoad(float px, float py)
        {
            if (roadMask == null) return false;
            for (int i = 0; i < 9; i++)
            {
                float ox = i == 0 ? 0f : Mathf.Cos(i * Mathf.PI / 4f) * 1.6f, oy = i == 0 ? 0f : Mathf.Sin(i * Mathf.PI / 4f) * 1.6f;
                int x = Mathf.Clamp((int)((px + ox) * 2f), 0, roadW - 1), y = Mathf.Clamp((int)((py + oy) * 2f), 0, roadH - 1);
                if (roadMask[(roadH - 1 - y) * roadW + x] > 25) return true;
            }
            return false;
        }

        void BuildBridges()
        {
            if (roadData?.bridges == null || placed.Count == 0) return;
            var art = EnvironmentArt.Load();
            if (art == null) return;
            var root = new GameObject("Bridges").transform;
            root.SetParent(transform, false);
            int n = 0, dryCenter = 0, wide = 0, inTown = 0, dup = 0;
            var used = new List<Vector2>();
            bool Wet(Vector2 p) => HeightAt(p.x, p.y) < SeaLevel + 0.08f;
            foreach (var b in roadData.bridges)
            {
                var prefab = art.Get("WorldBridge_" + b.kind) ?? art.Get("WorldBridge_wood");
                if (prefab == null) continue;
                var c = new Vector2(b.x, b.y);
                var dir = RoadDirection(c) ?? new Vector2(b.dx, b.dy).normalized;
                if (!Wet(c))
                {
                    bool found = false;
                    for (float t = 0.25f; t <= 3f && !found; t += 0.25f)
                        foreach (float sgn in new[] { 1f, -1f })
                            if (Wet(c + dir * t * sgn)) { c += dir * t * sgn; found = true; break; }
                    if (!found) { dryCenter++; continue; }
                }
                float t0 = 0f, t1 = 0f;
                while (t0 < 14f && Wet(c - dir * t0)) t0 += 0.2f;
                while (t1 < 14f && Wet(c + dir * t1)) t1 += 0.2f;
                if (t0 >= 14f || t1 >= 14f) { wide++; continue; }
                var a = c - dir * t0;
                var e = c + dir * t1;
                var mid = (a + e) * 0.5f;
                float span = t0 + t1;
                bool nearTown = false;
                string townId = null;
                var endA = a - dir * 1.1f;
                var endE = e + dir * 1.1f;
                foreach (var st in placed)
                {
                    var sp = new Vector2(st.Px, st.Py);
                    float r = WorldSettlements.FlattenRadius(st.Kind, st.Data.capital) * (st.Kind == SettlementKind.Town ? 0.8f : 0.9f) + 0.3f;
                    var ab = endE - endA;
                    float t = Mathf.Clamp01(Vector2.Dot(sp - endA, ab) / Mathf.Max(ab.sqrMagnitude, 1e-6f));
                    if ((endA + ab * t - sp).sqrMagnitude < r * r) { nearTown = true; townId = st.Data.id; break; }
                }
                if (nearTown)
                {
                    inTown++;
                    if (!townBridged.Add(townId))
                    {
                        float deck = Mathf.Max(Mathf.Max(HeightAt(a.x - dir.x * 0.8f, a.y - dir.y * 0.8f), HeightAt(e.x + dir.x * 0.8f, e.y + dir.y * 0.8f)), SeaLevel + 0.3f);
                        bridgeSpans.Add(new BridgeSpan { A = endA, B = endE, Deck = deck });
                        continue;
                    }
                    prefab = art.Get("WorldBridge_stone") ?? prefab;
                }
                else if (used.Exists(u => (u - mid).sqrMagnitude < 16f)) { dup++; continue; }
                used.Add(mid);
                float bank = Mathf.Max(Mathf.Max(HeightAt(a.x - dir.x * 0.8f, a.y - dir.y * 0.8f), HeightAt(e.x + dir.x * 0.8f, e.y + dir.y * 0.8f)), SeaLevel + 0.3f);
                var go = Instantiate(prefab, root);
                go.transform.position = new Vector3(mid.x - Meta.width / 2f, bank - 0.32f, Meta.height / 2f - mid.y);
                go.transform.rotation = Quaternion.FromToRotation(Vector3.right, new Vector3(dir.x, 0f, -dir.y));
                go.transform.localScale = new Vector3(span + 2.2f, 1.5f, 1.5f);
                bridgeSpans.Add(new BridgeSpan { A = endA, B = endE, Deck = bank + (prefab.name.EndsWith("stone", StringComparison.Ordinal) ? 0.03f : -0.02f) });
                foreach (var r in go.GetComponentsInChildren<Renderer>())
                {
                    var mats = r.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                        if (mats[i] != null) mats[i] = PropMaterial(mats[i], placed[0].Faction);
                    r.sharedMaterials = mats;
                }
                n++;
            }
            Debug.Log($"[W1347] bridges placed: {n}, skipped: dry {dryCenter}, wide {wide}, in town {inTown}, duplicate {dup}");
        }

        void BuildQuays()
        {
            var art = EnvironmentArt.Load();
            var stoneSrc = art?.Get("WorldBridge_stone")?.GetComponentInChildren<Renderer>()?.sharedMaterial;
            if (stoneSrc == null) return;
            string rulesPath = Path.Combine(Application.streamingAssetsPath, "Data", "world", "models.json");
            var rules = File.Exists(rulesPath) ? JsonUtility.FromJson<ModelRules>(File.ReadAllText(rulesPath)) : new ModelRules();
            var root = new GameObject("Quays").transform;
            root.SetParent(transform, false);
            int built = 0;
            foreach (var s in placed)
            {
                if (s.Kind == SettlementKind.Village) continue;
                float reach = s.Kind == SettlementKind.Castle ? rules.quayCastle : s.Data.model == "medium" && !s.Data.capital ? rules.quayMedium : rules.quayTown;
                var mesh = QuayMesh(s, reach);
                if (mesh == null) continue;
                var go = new GameObject(s.Data.id + "_quay");
                go.transform.SetParent(root, false);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                go.AddComponent<MeshRenderer>().sharedMaterial = PropMaterial(stoneSrc, s.Faction);
                built++;
            }
            Debug.Log($"[W1347] quays: {built} settlements");
        }

        Mesh QuayMesh(PlacedSettlement s, float reach)
        {
            float r = WorldSettlements.FlattenRadius(s.Kind, s.Data.capital) * reach;
            float top = s.Position.y + 0.1f, bottom = SeaLevel - 0.35f;
            var verts = new List<Vector3>();
            var tris = new List<int>();
            var uvs = new List<Vector2>();
            float V(float x, float y) => HeightAt(x, y) - SeaLevel;
            for (float y = s.Py - r; y < s.Py + r; y += 1f)
            for (float x = s.Px - r; x < s.Px + r; x += 1f)
            {
                float a = V(x, y), b = V(x + 1f, y), c = V(x + 1f, y + 1f), d = V(x, y + 1f);
                var pts = new List<Vector2>(4);
                void Edge(Vector2 p0, Vector2 p1, float v0, float v1)
                {
                    if ((v0 < 0f) == (v1 < 0f)) return;
                    pts.Add(Vector2.Lerp(p0, p1, v0 / (v0 - v1)));
                }
                Edge(new Vector2(x, y), new Vector2(x + 1f, y), a, b);
                Edge(new Vector2(x + 1f, y), new Vector2(x + 1f, y + 1f), b, c);
                Edge(new Vector2(x + 1f, y + 1f), new Vector2(x, y + 1f), c, d);
                Edge(new Vector2(x, y + 1f), new Vector2(x, y), d, a);
                for (int k = 0; k + 1 < pts.Count; k += 2)
                {
                    var mid = (pts[k] + pts[k + 1]) * 0.5f;
                    if ((mid - new Vector2(s.Px, s.Py)).sqrMagnitude > r * r) continue;
                    AddWall(pts[k], pts[k + 1], top, bottom, verts, tris, uvs);
                }
            }
            if (tris.Count == 0) return null;
            var mesh = new Mesh { name = s.Data.id + "_quay", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.SetVertices(verts);
            mesh.SetTriangles(tris, 0);
            mesh.SetUVs(0, uvs);
            var cols = new Color[verts.Count];
            for (int i = 0; i < cols.Length; i++) cols[i] = new Color(0.85f, 0.85f, 0.85f, 1f);
            mesh.colors = cols;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        void AddWall(Vector2 p0, Vector2 p1, float top, float bottom, List<Vector3> verts, List<int> tris, List<Vector2> uvs)
        {
            var along = (p1 - p0).normalized;
            var n = new Vector2(-along.y, along.x);
            var mid = (p0 + p1) * 0.5f;
            if (HeightAt(mid.x + n.x * 0.6f, mid.y + n.y * 0.6f) < HeightAt(mid.x - n.x * 0.6f, mid.y - n.y * 0.6f)) n = -n;
            const float thick = 0.32f, extend = 0.12f;
            var a = p0 - along * extend;
            var b = p1 + along * extend;
            Vector3 W(Vector2 p, float h) => new Vector3(p.x - Meta.width / 2f, h, Meta.height / 2f - p.y);
            var outerA = a; var outerB = b;
            var innerA = a + n * thick; var innerB = b + n * thick;
            float len = (b - a).magnitude;
            void Quad(Vector3 q0, Vector3 q1, Vector3 q2, Vector3 q3, float u, Vector3 facing)
            {
                int i0 = verts.Count;
                verts.Add(q0); verts.Add(q1); verts.Add(q2); verts.Add(q3);
                uvs.Add(new Vector2(0f, 0f)); uvs.Add(new Vector2(u, 0f)); uvs.Add(new Vector2(u, 1f)); uvs.Add(new Vector2(0f, 1f));
                if (Vector3.Dot(Vector3.Cross(q1 - q0, q2 - q0), facing) > 0f)
                {
                    tris.Add(i0); tris.Add(i0 + 1); tris.Add(i0 + 2);
                    tris.Add(i0); tris.Add(i0 + 2); tris.Add(i0 + 3);
                }
                else
                {
                    tris.Add(i0); tris.Add(i0 + 2); tris.Add(i0 + 1);
                    tris.Add(i0); tris.Add(i0 + 3); tris.Add(i0 + 2);
                }
            }
            var water = new Vector3(-n.x, 0f, n.y);
            Quad(W(outerA, bottom), W(outerB, bottom), W(outerB, top), W(outerA, top), len, water);
            Quad(W(outerA, top), W(outerB, top), W(innerB, top), W(innerA, top), len, Vector3.up);
        }

        readonly HashSet<string> townBridged = new HashSet<string>();

        sealed class BridgeSpan
        {
            public Vector2 A, B;
            public float Deck;
        }

        readonly List<BridgeSpan> bridgeSpans = new List<BridgeSpan>();

        sealed class BiomeIds
        {
            public Dictionary<string, int> Biomes;
        }

        static float Smooth01(float a, float b, float x)
        {
            float t = Mathf.Clamp01((x - a) / (b - a));
            return t * t * (3f - 2f * t);
        }

        void BuildWalkGrid()
        {
            string dir = Path.Combine(Application.streamingAssetsPath, "Data", "world");
            string rulesPath = Path.Combine(dir, "travel.json");
            Rules = File.Exists(rulesPath) ? DataJson.Read<TravelRules>(File.ReadAllText(rulesPath)) : new TravelRules();
            var biomeCost = new float[256];
            for (int i = 0; i < biomeCost.Length; i++) biomeCost[i] = 1f;
            var ids = DataJson.Read<BiomeIds>(File.ReadAllText(Path.Combine(dir, "world.json")));
            float minCost = Rules.Road;
            if (ids?.Biomes != null)
                foreach (var kv in ids.Biomes)
                    if (kv.Value >= 0 && kv.Value < 256)
                    {
                        biomeCost[kv.Value] = Rules.TerrainCost(kv.Key);
                        if (kv.Key != "sea") minCost = Mathf.Min(minCost, biomeCost[kv.Value]);
                    }
            int w = Meta.width, h = Meta.height;
            var grid = new WalkGrid(w, h, 0f);
            float H(int x, int y) => heights[Mathf.Clamp(y, 0, h - 1) * w + Mathf.Clamp(x, 0, w - 1)] * HeightScale;
            int blockedWater = 0, blockedRock = 0, road = 0;
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float e = H(x, y);
                if (e < SeaLevel + 0.05f)
                {
                    grid[x, y] = WalkGrid.Blocked;
                    blockedWater++;
                    continue;
                }
                float gx = (H(x + 2, y) - H(x - 2, y)) / 4f, gy = (H(x, y + 2) - H(x, y - 2)) / 4f;
                float slope = 1f - 1f / Mathf.Sqrt(1f + gx * gx + gy * gy);
                float rock = Mathf.Max(Smooth01(0.24f, 0.5f, slope) * Mathf.Clamp01(0.25f + e / 16f), Smooth01(15f, 25f, e));
                if (rock > Rules.RockLimit)
                {
                    grid[x, y] = WalkGrid.Blocked;
                    blockedRock++;
                    continue;
                }
                int bx = Mathf.Min(biomeW - 1, x * biomeW / w), by = Mathf.Min(biomeH - 1, y * biomeH / h);
                float c = biomeCost[biomes[by * biomeW + bx]] * (1f + Rules.Hills * Mathf.Max(rock / Mathf.Max(Rules.RockLimit, 1e-3f), Smooth01(rockLo, rockHi, e)));
                if (RoadAt(x, y))
                {
                    c = Mathf.Min(c, Rules.Road);
                    road++;
                }
                grid[x, y] = c;
            }
            foreach (var b in bridgeSpans) grid.AddCrossing(new Vec2(b.A.x, b.A.y), new Vec2(b.B.x, b.B.y), 1f, Rules.Road);
            grid.BuildRegions();
            Walk = grid;
            MinTravelCost = Mathf.Max(0.05f, minCost);
            Debug.Log($"[W1347] walk grid {w}x{h}: water {blockedWater}, mountains {blockedRock}, road {road}, bridges {bridgeSpans.Count}");
        }

        bool RoadAt(int x, int y)
        {
            if (roadMask == null) return false;
            int rx = Mathf.Clamp(x * 2 + 1, 0, roadW - 1), ry = Mathf.Clamp(y * 2 + 1, 0, roadH - 1);
            return roadMask[(roadH - 1 - ry) * roadW + rx] > 110;
        }

        public float TerrainHeight(float px, float py)
        {
            float gx = px / MeshStep, gy = py / MeshStep;
            int gw = (Meta.width - 1) / MeshStep + 1, gh = (Meta.height - 1) / MeshStep + 1;
            int x0 = Mathf.Clamp(Mathf.FloorToInt(gx), 0, gw - 1), y0 = Mathf.Clamp(Mathf.FloorToInt(gy), 0, gh - 1);
            int x1 = Mathf.Min(x0 + 1, gw - 1), y1 = Mathf.Min(y0 + 1, gh - 1);
            float fx = Mathf.Clamp01(gx - x0), fy = Mathf.Clamp01(gy - y0);
            float a = Mathf.Lerp(GridHeight(x0, y0, gw, gh), GridHeight(x1, y0, gw, gh), fx);
            float b = Mathf.Lerp(GridHeight(x0, y1, gw, gh), GridHeight(x1, y1, gw, gh), fx);
            return Mathf.Lerp(a, b, fy);
        }

        public float GroundHeight(float px, float py)
        {
            float g = TerrainHeight(px, py);
            var p = new Vector2(px, py);
            foreach (var b in bridgeSpans)
            {
                var ab = b.B - b.A;
                float t = Mathf.Clamp01(Vector2.Dot(p - b.A, ab) / Mathf.Max(ab.sqrMagnitude, 1e-6f));
                if ((b.A + ab * t - p).sqrMagnitude < 1.2f) g = Mathf.Max(g, b.Deck);
            }
            return Mathf.Max(g, SeaLevel);
        }

        public Vector3 MapToWorld(Vec2 p) => new Vector3(p.X - Meta.width / 2f, GroundHeight(p.X, p.Y), Meta.height / 2f - p.Y);

        public bool RayToMap(Ray ray, out Vector2 px)
        {
            px = default;
            if (ray.direction.y >= -1e-4f) return false;
            float top = HeightScale + 2f;
            float t = ray.origin.y > top ? (ray.origin.y - top) / -ray.direction.y : 0f;
            const float step = 0.8f;
            for (int i = 0; i < 6000; i++, t += step)
            {
                var q = ray.GetPoint(t);
                if (q.y < -5f) return false;
                if (q.y > Mathf.Max(TerrainHeight(q.x + Meta.width / 2f, Meta.height / 2f - q.z), SeaLevel)) continue;
                float lo = t - step, hi = t;
                for (int k = 0; k < 10; k++)
                {
                    float mid = (lo + hi) * 0.5f;
                    var m = ray.GetPoint(mid);
                    if (m.y > Mathf.Max(TerrainHeight(m.x + Meta.width / 2f, Meta.height / 2f - m.z), SeaLevel)) lo = mid;
                    else hi = mid;
                }
                var hit = ray.GetPoint(hi);
                px = new Vector2(hit.x + Meta.width / 2f, Meta.height / 2f - hit.z);
                return px.x >= 0f && px.y >= 0f && px.x <= Meta.width - 1 && px.y <= Meta.height - 1;
            }
            return false;
        }

        Vector2? RoadDirection(Vector2 c)
        {
            float best = 16f;
            Vector2? dir = null;
            foreach (var r in roadData.roads)
                for (int i = 0; i + 3 < r.pts.Length; i += 2)
                {
                    var a = new Vector2(r.pts[i], r.pts[i + 1]);
                    var b = new Vector2(r.pts[i + 2], r.pts[i + 3]);
                    var ab = b - a;
                    float t = Mathf.Clamp01(Vector2.Dot(c - a, ab) / Mathf.Max(ab.sqrMagnitude, 1e-6f));
                    float d = (a + ab * t - c).sqrMagnitude;
                    if (d < best)
                    {
                        best = d;
                        int i0 = Mathf.Max(0, i - 4), i1 = Mathf.Min(r.pts.Length - 2, i + 6);
                        var span = new Vector2(r.pts[i1] - r.pts[i0], r.pts[i1 + 1] - r.pts[i0 + 1]);
                        if (span.sqrMagnitude > 1e-6f) dir = span.normalized;
                    }
                }
            return dir;
        }

        Transform smokeRoot;

        void BuildSmoke()
        {
            var shader = Shader.Find("Warfare/Smoke");
            if (shader == null || placed.Count == 0) return;
            var mat = new Material(shader) { name = "Smoke" };
            mat.SetTexture("_MainTex", PuffTexture());
            smokeRoot = new GameObject("Smoke").transform;
            smokeRoot.SetParent(transform, false);
            var rnd = new System.Random(77);
            var fade = new Gradient();
            fade.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(new Color(0.92f, 0.92f, 0.92f), 1f) },
                new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(0.55f, 0.14f), new GradientAlphaKey(0.3f, 0.6f), new GradientAlphaKey(0f, 1f) });
            int count = 0;
            foreach (var st in placed)
            {
                bool town = st.Kind == SettlementKind.Town;
                if (st.Kind == SettlementKind.Castle && rnd.NextDouble() > 0.5) continue;
                int sources = town ? (st.Data.capital ? 5 : 3) : 1;
                float spread = town ? 3.0f : 1.2f;
                for (int i = 0; i < sources; i++)
                {
                    var go = new GameObject("smoke");
                    go.transform.SetParent(smokeRoot, false);
                    float a = (float)rnd.NextDouble() * Mathf.PI * 2f, r = (float)rnd.NextDouble() * spread;
                    go.transform.position = st.Position + new Vector3(Mathf.Cos(a) * r, town ? 1.7f : 0.8f, Mathf.Sin(a) * r);
                    var ps = go.AddComponent<ParticleSystem>();
                    ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                    var main = ps.main;
                    main.loop = true;
                    main.duration = 6f;
                    main.prewarm = true;
                    main.startLifetime = new ParticleSystem.MinMaxCurve(6f, 9f);
                    main.startSpeed = new ParticleSystem.MinMaxCurve(0.02f, 0.06f);
                    main.startSize = new ParticleSystem.MinMaxCurve(0.9f, 1.4f);
                    main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                    main.simulationSpace = ParticleSystemSimulationSpace.World;
                    main.maxParticles = 24;
                    var emission = ps.emission;
                    emission.rateOverTime = town ? 0.9f : 0.5f;
                    var shape = ps.shape;
                    shape.shapeType = ParticleSystemShapeType.Sphere;
                    shape.radius = 0.12f;
                    var vel = ps.velocityOverLifetime;
                    vel.enabled = true;
                    vel.space = ParticleSystemSimulationSpace.World;
                    vel.x = new ParticleSystem.MinMaxCurve(0.12f, 0.24f);
                    vel.y = new ParticleSystem.MinMaxCurve(0.4f, 0.6f);
                    vel.z = new ParticleSystem.MinMaxCurve(0.03f, 0.09f);
                    var size = ps.sizeOverLifetime;
                    size.enabled = true;
                    size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 0.5f, 1f, 3f));
                    var col = ps.colorOverLifetime;
                    col.enabled = true;
                    col.color = new ParticleSystem.MinMaxGradient(fade);
                    var rot = ps.rotationOverLifetime;
                    rot.enabled = true;
                    rot.z = new ParticleSystem.MinMaxCurve(-0.3f, 0.3f);
                    var pr = go.GetComponent<ParticleSystemRenderer>();
                    pr.sharedMaterial = mat;
                    pr.renderMode = ParticleSystemRenderMode.Billboard;
                    pr.shadowCastingMode = ShadowCastingMode.Off;
                    pr.receiveShadows = false;
                    ps.Play();
                    count++;
                }
            }
            Debug.Log($"[W1347] smoke sources: {count}");
        }

        static Texture2D PuffTexture()
        {
            const int n = 64;
            var t = new Texture2D(n, n, TextureFormat.RGBA32, true) { name = "SmokePuff", wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[n * n];
            var r = new System.Random(5);
            var blobs = new Vector3[6];
            for (int i = 0; i < blobs.Length; i++) blobs[i] = new Vector3((float)r.NextDouble() * 0.5f + 0.25f, (float)r.NextDouble() * 0.5f + 0.25f, 0.16f + (float)r.NextDouble() * 0.12f);
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float u = (x + 0.5f) / n, v = (y + 0.5f) / n;
                float a = 0f;
                foreach (var b in blobs)
                {
                    float d = Mathf.Sqrt((u - b.x) * (u - b.x) + (v - b.y) * (v - b.y)) / b.z;
                    a = Mathf.Max(a, Mathf.Clamp01(1f - d));
                }
                float edge = Mathf.Clamp01((0.5f - Mathf.Sqrt((u - 0.5f) * (u - 0.5f) + (v - 0.5f) * (v - 0.5f))) / 0.12f);
                a = Mathf.SmoothStep(0f, 1f, a) * edge;
                px[y * n + x] = new Color32(255, 255, 255, (byte)(a * 255f));
            }
            t.SetPixels32(px);
            t.Apply(true, true);
            return t;
        }

        void DrawTrees()
        {
            var cam = Camera.main;
            if (cam == null || treeCells.Count == 0) return;
            var eye = cam.transform.position;
            foreach (var cell in treeCells)
            {
                if (!cell.HasBounds) continue;
                float d = Vector3.Distance(eye, cell.Bounds.ClosestPoint(eye));
                if (d > TreeFadeEnd) continue;
                bool near = d < TreeLodDistance;
                for (int k = 0; k < treeKinds.Count; k++)
                {
                    var tk = treeKinds[k];
                    var batches = cell.Batches[k];
                    if (tk == null || batches.Count == 0 || d > tk.Draw) continue;
                    var mesh = near ? tk.Near : tk.Far;
                    var mats = near ? tk.NearMats : tk.FarMats;
                    var baseM = near ? tk.NearBase : tk.FarBase;
                    int subs = Mathf.Min(mesh.subMeshCount, mats.Length);
                    for (int b = 0; b < batches.Count; b++)
                    {
                        var arr = batches[b];
                        int n = cell.Counts[k][b];
                        if (baseM != Matrix4x4.identity) arr = Rebase(arr, n, baseM);
                        for (int sm = 0; sm < subs; sm++)
                        {
                            var rp = new RenderParams(mats[sm]) { shadowCastingMode = tk.Shadows ? ShadowCastingMode.On : ShadowCastingMode.Off, receiveShadows = true, worldBounds = cell.Bounds };
                            Graphics.RenderMeshInstanced(rp, mesh, sm, arr, n);
                        }
                    }
                }
            }
        }

        readonly Matrix4x4[] rebased = new Matrix4x4[1023];

        Matrix4x4[] Rebase(Matrix4x4[] src, int n, Matrix4x4 baseM)
        {
            for (int i = 0; i < n; i++) rebased[i] = src[i] * baseM;
            return rebased;
        }

        static void Push((List<Matrix4x4[]> batches, List<int> counts) l, Matrix4x4 m)
        {
            if (l.batches.Count == 0 || l.counts[l.counts.Count - 1] >= 1023)
            {
                l.batches.Add(new Matrix4x4[1023]);
                l.counts.Add(0);
            }
            int i = l.batches.Count - 1;
            l.batches[i][l.counts[i]] = m;
            l.counts[i]++;
        }
    }
}
