using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using Warfare.Core;

namespace Warfare.Client
{
    public sealed class GrassFile
    {
        public bool Enabled = true;
        public float Meadow = 1f;
        public float GroundVariation = 1f;
        public float FarDensity = 0.2f;
        public float ThinningStart = 50f;
        public float ThinningEnd = 95f;
        public GrassArea TestArea;
        public float Radius = 55f;
        public float Cell = 16f;
        public float Step = 0.5f;
        public float Footprint = 0.8f;
        public int Shells = 12;
        public float ShellHeight = 0.22f;
        public float ShellDensity = 34f;
        public float ShellFadeStart = 90f;
        public float ShellFadeEnd = 150f;
        public float ShellSteppe = 0.5f;
        public float SmoothFrom = 35f;
        public float SmoothTo = 85f;
        public float MaxSlope = 1.4f;
        public float ShellRoot = 0.84f;
        public float ShellTip = 1.1f;
        public float TuftRoot = 0.82f;
        public float[] TuftTip = { 1.1f, 1.12f, 0.95f };
        public float TuftBend = 0.055f;
        public float FadeStart = 70f;
        public float FadeEnd = 110f;
        public float[] Scale = { 0.8f, 1.25f };
        public float PatchScale = 0.09f;
        public float GapScale = 0.6f;
        public float Gaps = 0.78f;
        public float FlowerScale = 0.2f;
        public float Flowers = 0.8f;
        public Dictionary<string, float> Biomes = new Dictionary<string, float>();
        public List<GrassVariant> Variants = new List<GrassVariant>();
    }

    public sealed class GrassArea
    {
        public float Lon;
        public float Lat;
        public float Radius = 45f;
    }

    public sealed class GrassVariant
    {
        public string Name;
        public int Blades = 24;
        public float[] Height = { 0.06f, 0.11f };
        public float Width = 0.012f;
        public float Spread = 0.22f;
        public int FlowerHeads;
    }

    public sealed partial class WorldMap
    {
        Material terrainMat;
        readonly List<(Mesh mesh, Bounds bounds)> terrainChunks = new List<(Mesh, Bounds)>();
        Material shellMat;
        MaterialPropertyBlock[] shellProps;
        float[] vegForest;
        float[] vegOpen;
        GrassFile grassCfg;
        Material grassMat;
        Mesh[] grassMeshes;
        readonly Dictionary<Vector2Int, List<Matrix4x4>[]> grassCells = new Dictionary<Vector2Int, List<Matrix4x4>[]>();
        readonly Dictionary<Vector2Int, List<Matrix4x4>[]> grassFarCells = new Dictionary<Vector2Int, List<Matrix4x4>[]>();
        Vector2 grassAreaPx;
        float grassAreaR = -1f;
        public int GrassInstances { get; private set; }
        int grassMode;

        void SetupGrass()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "grass.json");
            grassCfg = File.Exists(path) ? DataJson.Read<GrassFile>(File.ReadAllText(path)) : null;
            if (terrainMat != null && terrainMat.HasProperty("_Meadow")) terrainMat.SetFloat("_Meadow", grassCfg != null ? grassCfg.Meadow : 0f);
            if (grassCfg == null || !grassCfg.Enabled || grassCfg.Variants.Count == 0 || terrainMat == null) return;
            var shader = Shader.Find("Warfare/Grass");
            if (shader == null) return;
            grassMat = new Material(shader) { name = "Grass", enableInstancing = true };
            grassMat.CopyPropertiesFromMaterial(terrainMat);
            grassMat.enableInstancing = true;
            grassMat.SetTexture("_BaseMap", terrainMat.GetTexture("_BaseMap"));
            grassMat.SetTexture("_Grass", terrainMat.GetTexture("_Grass"));
            if (terrainMat.HasProperty("_Steppe")) grassMat.SetTexture("_SteppeTex", terrainMat.GetTexture("_Steppe"));
            grassMat.SetTexture("_Splat0", terrainMat.GetTexture("_Splat0"));
            grassMat.SetTexture("_Splat1", terrainMat.GetTexture("_Splat1"));
            grassMat.SetFloat("_Tile", terrainMat.GetFloat("_Tile"));
            grassMat.SetFloat("_DetailStrength", terrainMat.GetFloat("_DetailStrength"));
            grassMat.SetVector("_MapSize", new Vector4(Meta.width, Meta.height, 0f, 0f));
            grassMat.SetFloat("_Meadow", grassCfg.Meadow);
            grassMat.SetFloat("_FadeStart", grassCfg.FadeStart);
            grassMat.SetFloat("_FadeEnd", grassCfg.FadeEnd);
            grassMat.SetFloat("_RootShade", grassCfg.TuftRoot);
            grassMat.SetFloat("_NormalBend", grassCfg.TuftBend);
            grassMat.SetColor("_DryColor", new Color(1.10f, 1.06f, 0.94f, 1f));
            grassMat.SetColor("_TipColor", new Color(grassCfg.TuftTip[0], grassCfg.TuftTip[1], grassCfg.TuftTip[2], 1f));
            var shellShader = Shader.Find("Warfare/GrassShell");
            if (shellShader != null && grassCfg.Shells > 0)
            {
                shellMat = new Material(shellShader) { name = "GrassShell" };
                shellMat.CopyPropertiesFromMaterial(terrainMat);
                shellMat.renderQueue = (int)RenderQueue.AlphaTest;
                foreach (var t in new[] { "_BaseMap", "_Splat0", "_Splat1", "_RoadMask", "_YardMask", "_Grass" })
                    if (terrainMat.HasProperty(t)) shellMat.SetTexture(t, terrainMat.GetTexture(t));
                shellMat.SetFloat("_Tile", terrainMat.GetFloat("_Tile"));
                if (terrainMat.HasProperty("_Steppe")) shellMat.SetTexture("_SteppeTex", terrainMat.GetTexture("_Steppe"));
                shellMat.SetFloat("_DetailStrength", terrainMat.GetFloat("_DetailStrength"));
                shellMat.SetFloat("_Meadow", grassCfg.Meadow);
                shellMat.SetFloat("_Height", grassCfg.ShellHeight);
                shellMat.SetFloat("_Density", grassCfg.ShellDensity);
                shellMat.SetFloat("_FadeStart", grassCfg.ShellFadeStart);
                shellMat.SetFloat("_FadeEnd", grassCfg.ShellFadeEnd);
                shellMat.SetFloat("_SteppeCover", grassCfg.ShellSteppe);
                shellMat.SetFloat("_RootShade", grassCfg.ShellRoot);
                shellMat.SetFloat("_TipLight", grassCfg.ShellTip);
                shellMat.SetVector("_Smooth", new Vector4(grassCfg.SmoothFrom, grassCfg.SmoothTo, 0f, 0f));
                if (terrainMat.HasProperty("_RockHeight")) shellMat.SetVector("_RockHeight", terrainMat.GetVector("_RockHeight"));
                if (grassCfg.TestArea != null)
                {
                    var a = GeoToWorld(grassCfg.TestArea.Lon, grassCfg.TestArea.Lat);
                    shellMat.SetVector("_Area", new Vector4(a.x, a.z, grassCfg.TestArea.Radius, 1f));
                }
                shellProps = new MaterialPropertyBlock[grassCfg.Shells];
                for (int i = 0; i < grassCfg.Shells; i++)
                {
                    shellProps[i] = new MaterialPropertyBlock();
                    shellProps[i].SetFloat("_Shell", (i + 1f) / grassCfg.Shells);
                }
            }
            SetupGrassHabitat();
            grassMeshes = new Mesh[grassCfg.Variants.Count];
            for (int i = 0; i < grassMeshes.Length; i++) grassMeshes[i] = GrassPatch(grassCfg.Variants[i], 7000 + i);
            if (grassCfg.TestArea != null)
            {
                grassAreaPx = new Vector2((grassCfg.TestArea.Lon - Meta.lonMin) * Meta.pxPerDegLat * Meta.lonFactor, (Meta.latMax - grassCfg.TestArea.Lat) * Meta.pxPerDegLat);
                grassAreaR = grassCfg.TestArea.Radius;
            }
        }

        static Mesh GrassPatch(GrassVariant v, int seed)
        {
            var rnd = new System.Random(seed);
            var verts = new List<Vector3>();
            var norms = new List<Vector3>();
            var uvs = new List<Vector2>();
            var cols = new List<Color>();
            var tris = new List<int>();
            float R() => (float)rnd.NextDouble();
            var tips = new List<Vector3>();
            for (int b = 0; b < v.Blades; b++)
            {
                float a = R() * Mathf.PI * 2f, rr = Mathf.Sqrt(R()) * v.Spread;
                var root = new Vector3(Mathf.Cos(a) * rr, 0f, Mathf.Sin(a) * rr);
                float h = Mathf.Lerp(v.Height[0], v.Height[1], R());
                h *= Mathf.Lerp(1.1f, 0.65f, rr / Mathf.Max(v.Spread, 0.001f));
                float w = v.Width * Mathf.Lerp(0.7f, 1.3f, R());
                float face = R() * Mathf.PI * 2f;
                var side = new Vector3(Mathf.Cos(face), 0f, Mathf.Sin(face));
                var lean = new Vector3(-side.z, 0f, side.x) * (Mathf.Lerp(0.35f, 0.95f, R()) * h);
                lean += new Vector3(root.x, 0f, root.z) * 0.75f;
                float tone = R();
                var n = Vector3.Cross(side, Vector3.up).normalized;
                int start = verts.Count;
                const int rows = 3;
                for (int r = 0; r < rows; r++)
                {
                    float t = r / (float)rows;
                    var c = root + Vector3.up * (h * Mathf.Sin(t * Mathf.PI * 0.5f)) + lean * (t * t);
                    float ww = w * (1f - t * 0.75f);
                    verts.Add(c - side * ww);
                    verts.Add(c + side * ww);
                    for (int k = 0; k < 2; k++) { norms.Add(n); uvs.Add(new Vector2(tone, t)); cols.Add(new Color(0, 0, 0, 0)); }
                }
                var tip = root + Vector3.up * h + lean;
                verts.Add(tip);
                norms.Add(n);
                uvs.Add(new Vector2(tone, 1f));
                cols.Add(new Color(0, 0, 0, 0));
                tips.Add(tip);
                for (int r = 0; r < rows - 1; r++)
                {
                    int i0 = start + r * 2;
                    tris.AddRange(new[] { i0, i0 + 2, i0 + 1, i0 + 1, i0 + 2, i0 + 3 });
                }
                int last = start + (rows - 1) * 2;
                tris.AddRange(new[] { last, start + rows * 2, last + 1 });
            }
            Color[] petals = { new Color(0.95f, 0.94f, 0.88f, 1f), new Color(0.98f, 0.82f, 0.25f, 1f), new Color(0.72f, 0.6f, 0.9f, 1f) };
            for (int f = 0; f < v.FlowerHeads && tips.Count > 0; f++)
            {
                var c = tips[rnd.Next(tips.Count)] + Vector3.up * 0.005f;
                var col = petals[rnd.Next(petals.Length)];
                float s = v.Width * 2.4f;
                int st = verts.Count;
                verts.Add(c + new Vector3(-s, 0f, 0f));
                verts.Add(c + new Vector3(0f, 0f, s));
                verts.Add(c + new Vector3(s, 0f, 0f));
                verts.Add(c + new Vector3(0f, 0f, -s));
                verts.Add(c + Vector3.up * s * 0.6f);
                for (int k = 0; k < 5; k++) { norms.Add(Vector3.up); uvs.Add(new Vector2(0.5f, 1f)); cols.Add(col); }
                tris.AddRange(new[] { st, st + 4, st + 1, st + 1, st + 4, st + 2, st + 2, st + 4, st + 3, st + 3, st + 4, st });
            }
            var m = new Mesh { name = "GrassPatch_" + v.Name };
            m.SetVertices(verts);
            m.SetNormals(norms);
            m.SetUVs(0, uvs);
            m.SetColors(cols);
            m.SetTriangles(tris, 0);
            m.RecalculateBounds();
            return m;
        }

        void DrawGrass()
        {
            if (grassMat == null || rtsCam == null) return;
            var kb = UnityEngine.InputSystem.Keyboard.current;
            if (kb != null && kb[UnityEngine.InputSystem.Key.F7].wasPressedThisFrame)
            {
                grassMode = (grassMode + 1) % 4;
            }
            GrassInstances = 0;
            if (grassMode == 3) return;
            var cam = Camera.main;
            if (cam == null) return;
            var cfg = grassCfg;
            var focus = rtsCam.Focus;
            float camDist = Vector3.Distance(cam.transform.position, focus);
            if (camDist > Mathf.Max(cfg.FadeEnd, cfg.ShellFadeEnd) + cfg.Radius)
            {
                if (grassCells.Count > 0) grassCells.Clear();
                grassFarCells.Clear();
                GrassInstances = 0;
                return;
            }
            if (grassMode != 2) DrawShells(cam);
            if (grassMode == 1) return;
            var fpx = new Vector2(focus.x + Meta.width / 2f, Meta.height / 2f - focus.z);
            int c0x = Mathf.FloorToInt((fpx.x - cfg.Radius) / cfg.Cell), c1x = Mathf.FloorToInt((fpx.x + cfg.Radius) / cfg.Cell);
            int c0y = Mathf.FloorToInt((fpx.y - cfg.Radius) / cfg.Cell), c1y = Mathf.FloorToInt((fpx.y + cfg.Radius) / cfg.Cell);
            if (grassAreaR > 0)
            {
                c0x = Mathf.Max(c0x, Mathf.FloorToInt((grassAreaPx.x - grassAreaR) / cfg.Cell));
                c1x = Mathf.Min(c1x, Mathf.FloorToInt((grassAreaPx.x + grassAreaR) / cfg.Cell));
                c0y = Mathf.Max(c0y, Mathf.FloorToInt((grassAreaPx.y - grassAreaR) / cfg.Cell));
                c1y = Mathf.Min(c1y, Mathf.FloorToInt((grassAreaPx.y + grassAreaR) / cfg.Cell));
            }
            var drop = new List<Vector2Int>();
            foreach (var k in grassCells.Keys)
                if (k.x < c0x - 1 || k.x > c1x + 1 || k.y < c0y - 1 || k.y > c1y + 1) drop.Add(k);
            foreach (var k in drop) { grassCells.Remove(k); grassFarCells.Remove(k); }
            int built = 0;
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            int total = 0;
            for (int cy = c0y; cy <= c1y; cy++)
            for (int cx = c0x; cx <= c1x; cx++)
            {
                var key = new Vector2Int(cx, cy);
                if (!grassCells.TryGetValue(key, out var lists))
                {
                    if (built >= 4) continue;
                    lists = BuildGrassCell(cx, cy);
                    grassCells[key] = lists;
                    grassFarCells[key] = GrassFarLists(lists);
                    built++;
                }
                if (lists == null) continue;
                float wx = cx * cfg.Cell - Meta.width / 2f + cfg.Cell * 0.5f, wz = Meta.height / 2f - (cy * cfg.Cell + cfg.Cell * 0.5f);
                var b = new Bounds(new Vector3(wx, HeightAt(cx * cfg.Cell + cfg.Cell * 0.5f, cy * cfg.Cell + cfg.Cell * 0.5f), wz), new Vector3(cfg.Cell, 20f, cfg.Cell));
                if (Vector3.Distance(cam.transform.position, b.ClosestPoint(cam.transform.position)) > cfg.FadeEnd) continue;
                if (!GeometryUtility.TestPlanesAABB(planes, b)) continue;
                if (Vector3.Distance(cam.transform.position, b.ClosestPoint(cam.transform.position)) >= cfg.ThinningEnd)
                    lists = grassFarCells[key];
                for (int v = 0; v < lists.Length; v++)
                {
                    var list = lists[v];
                    if (list.Count == 0) continue;
                    var rp = new RenderParams(grassMat) { shadowCastingMode = ShadowCastingMode.Off, receiveShadows = true, worldBounds = b, renderingLayerMask = uint.MaxValue };
                    for (int i = 0; i < list.Count; i += 1023)
                    {
                        int n = Mathf.Min(1023, list.Count - i);
                        Graphics.RenderMeshInstanced(rp, grassMeshes[v], 0, list, n, i);
                        total += n;
                    }
                }
            }
            GrassInstances = total;
        }

        List<Matrix4x4>[] GrassFarLists(List<Matrix4x4>[] source)
        {
            var result = new List<Matrix4x4>[source.Length];
            for (int v = 0; v < source.Length; v++)
            {
                result[v] = new List<Matrix4x4>();
                foreach (var m in source[v])
                {
                    uint h = unchecked((uint)System.BitConverter.SingleToInt32Bits(m.m03) * 747796405u ^ (uint)System.BitConverter.SingleToInt32Bits(m.m23) * 2891336453u);
                    h ^= h >> 16;
                    h = unchecked(h * 2246822519u);
                    h ^= h >> 13;
                    if ((h & 0x00ffffffu) * (1f / 16777216f) <= grassCfg.FarDensity) result[v].Add(m);
                }
            }
            return result;
        }

        void DrawShells(Camera cam)
        {
            if (shellMat == null || rtsCam == null) return;
            var eye = cam.transform.position;
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            foreach (var (mesh, bounds) in terrainChunks)
            {
                if (Vector3.Distance(eye, bounds.ClosestPoint(eye)) > grassCfg.ShellFadeEnd) continue;
                if (!GeometryUtility.TestPlanesAABB(planes, bounds)) continue;
                for (int i = 0; i < shellProps.Length; i++)
                {
                    var rp = new RenderParams(shellMat) { shadowCastingMode = ShadowCastingMode.Off, receiveShadows = true, worldBounds = bounds, matProps = shellProps[i], lightProbeUsage = LightProbeUsage.BlendProbes, reflectionProbeUsage = ReflectionProbeUsage.BlendProbes, renderingLayerMask = uint.MaxValue };
                    Graphics.RenderMesh(rp, mesh, 0, Matrix4x4.identity);
                }
            }
        }

        List<Matrix4x4>[] BuildGrassCell(int cx, int cy)
        {
            var cfg = grassCfg;
            int W = Meta.width, H = Meta.height;
            var lists = new List<Matrix4x4>[cfg.Variants.Count];
            for (int i = 0; i < lists.Length; i++) lists[i] = new List<Matrix4x4>();
            float x0 = cx * cfg.Cell, y0 = cy * cfg.Cell;
            if (grassAreaR > 0f && Vector2.Distance(new Vector2(x0 + cfg.Cell * 0.5f, y0 + cfg.Cell * 0.5f), grassAreaPx) > grassAreaR + cfg.Cell) return lists;
            float sx = (float)biomeW / W, sy = (float)biomeH / H;
            int tall = cfg.Variants.FindIndex(v => v.Name == "tall"), medium = cfg.Variants.FindIndex(v => v.Name == "medium"), shortV = cfg.Variants.FindIndex(v => v.Name == "short"), flowers = cfg.Variants.FindIndex(v => v.Name == "flowers");
            int steps = Mathf.CeilToInt(cfg.Cell / cfg.Step);
            var near = new List<(Vector2 c, Vector2 e)>();
            foreach (var st in placed)
            {
                if (!st.HasFootprint) continue;
                var c = new Vector2(st.Footprint.center.x + W / 2f, H / 2f - st.Footprint.center.z);
                var e = new Vector2(st.Footprint.extents.x, st.Footprint.extents.z);
                if (c.x + e.x < x0 - 2 || c.x - e.x > x0 + cfg.Cell + 2 || c.y + e.y < y0 - 2 || c.y - e.y > y0 + cfg.Cell + 2) continue;
                near.Add((c, e * cfg.Footprint));
            }
            foreach (var l in landmarks)
                if (l.px.x > x0 - 6 && l.px.x < x0 + cfg.Cell + 6 && l.px.y > y0 - 6 && l.px.y < y0 + cfg.Cell + 6) near.Add((l.px, Vector2.one * l.r * 0.5f));
            for (int j = 0; j < steps; j++)
            for (int i = 0; i < steps; i++)
            {
                int gx = cx * steps + i, gy = cy * steps + j;
                float px = x0 + (i + Hash01(gx, gy, 31, 1)) * cfg.Step, py = y0 + (j + Hash01(gx, gy, 31, 2)) * cfg.Step;
                if (px < 1 || py < 1 || px >= W - 1 || py >= H - 1) continue;
                if (grassAreaR > 0f && (new Vector2(px, py) - grassAreaPx).sqrMagnitude > grassAreaR * grassAreaR) continue;
                float h = MeshHeight(px, py);
                if (GrassBiomeDensity(px, py) <= 0) continue;
                if (GrassHabitat(px - W / 2f, H / 2f - py) < Hash01(gx, gy, 32, 1)) continue;
                if (h < SeaLevel + 0.12f || h > rockLo * 0.9f) continue;
                float slope = Mathf.Abs(HeightAt(px + 1, py) - HeightAt(px - 1, py)) + Mathf.Abs(HeightAt(px, py + 1) - HeightAt(px, py - 1));
                if (slope > cfg.MaxSlope) continue;
                byte b = biomes[Mathf.Clamp((int)(py * sy), 0, biomeH - 1) * biomeW + Mathf.Clamp((int)(px * sx), 0, biomeW - 1)];
                if (b >= BiomeNames.Length || !cfg.Biomes.TryGetValue(BiomeNames[b], out var density)) continue;
                int pi = (int)py * W + (int)px;
                bool inside = false;
                foreach (var (c, e) in near)
                    if (Mathf.Abs(px - c.x) < e.x && Mathf.Abs(py - c.y) < e.y) { inside = true; break; }
                if (inside) continue;
                if (RoadValue(px, py) >= 110f) continue;
                density *= 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(12f, 110f, RoadValue(px, py)));
                float patch = Mathf.PerlinNoise(px * cfg.PatchScale + 13.1f, py * cfg.PatchScale + 7.7f);
                density *= Mathf.Lerp(0.45f, 1.15f, Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.2f, 0.75f, patch)));
                if (Mathf.PerlinNoise(px * cfg.GapScale + 3.3f, py * cfg.GapScale + 9.9f) > cfg.Gaps) density *= 0.15f;
                if (Hash01(gx, gy, 31, 3) >= density) continue;
                float tuft = Mathf.PerlinNoise(px * 0.65f + 41.3f, py * 0.65f + 18.7f);
                int v = patch + (tuft - 0.5f) * 0.35f > 0.48f && medium >= 0 ? medium : shortV;
                float edge = vegForest != null ? vegForest[pi] : 0f;
                bool bank = NearWater(px, py, 2.2f);
                bool verge = RoadValue(px, py) > 8f;
                if (tall >= 0 && ((bank && tuft > 0.42f) || (verge && tuft > 0.55f) || (edge > 0.2f && edge < 0.75f && tuft > 0.52f) || (patch > 0.60f && tuft > 0.62f))) v = tall;
                else if (flowers >= 0 && Mathf.PerlinNoise(px * cfg.FlowerScale + 51f, py * cfg.FlowerScale + 77f) > cfg.Flowers && Hash01(gx, gy, 31, 5) < 0.35f) v = flowers;
                if (v < 0) continue;
                float s = Mathf.Lerp(cfg.Scale[0], cfg.Scale[1], Hash01(gx, gy, 31, 6));
                var pos = new Vector3(px - W / 2f, MeshHeight(px, py) - 0.004f, H / 2f - py);
                lists[v].Add(Matrix4x4.TRS(pos, Quaternion.Euler(0f, Hash01(gx, gy, 31, 7) * 360f, 0f), Vector3.one * s));
            }
            return lists;
        }

        float MeshHeight(float px, float py)
        {
            float gx = px / MeshStep, gy = py / MeshStep;
            int x0 = Mathf.FloorToInt(gx), y0 = Mathf.FloorToInt(gy);
            float fx = gx - x0, fy = gy - y0;
            float H(int x, int y) => heights[Mathf.Clamp(y * MeshStep, 0, Meta.height - 1) * Meta.width + Mathf.Clamp(x * MeshStep, 0, Meta.width - 1)] * HeightScale;
            float a = H(x0, y0), b = H(x0 + 1, y0), c = H(x0, y0 + 1), d = H(x0 + 1, y0 + 1);
            if (Mathf.Abs(a - d) < Mathf.Abs(b - c))
                return fx > fy ? a + (b - a) * fx + (d - b) * fy : a + (d - c) * fx + (c - a) * fy;
            return fx + fy < 1f ? a + (b - a) * fx + (c - a) * fy : d + (c - d) * (1f - fx) + (b - d) * (1f - fy);
        }

        float RoadValue(float px, float py)
        {
            if (roadMask == null) return 0f;
            int x = Mathf.Clamp((int)(px * 2f), 0, roadW - 1), y = Mathf.Clamp((int)(py * 2f), 0, roadH - 1);
            int i = (roadH - 1 - y) * roadW + x;
            float v = roadMask[i];
            if (trodMask != null) v = Mathf.Max(v, Mathf.Max(paveMask[i], trodMask[i] * 0.45f));
            return v;
        }
    }
}
