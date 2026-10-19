using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Warfare.Core;
using Warfare.Core.World;

namespace Warfare.Client
{
    public sealed class VegetationFile
    {
        public int Seed = 1347;
        public float SouthLat = 44f;
        public float NorthLat = 55f;
        public int CellSize = 128;
        public Dictionary<string, VegetationGroup> Groups = new Dictionary<string, VegetationGroup>();
        public Dictionary<string, VegetationBiome> Biomes = new Dictionary<string, VegetationBiome>();
        public VegetationForest Forest = new VegetationForest();
        public VegetationLimits Limits = new VegetationLimits();
        public VegetationClearance Clearance = new VegetationClearance();
        public VegetationRocks Rocks = new VegetationRocks();
        public VegetationBoulders Boulders = new VegetationBoulders();
        public List<VegetationSite> TestSites = new List<VegetationSite>();
    }

    public sealed class VegetationGroup
    {
        public float Radius = 0.6f;
        public float[] Scale = { 0.85f, 1.15f };
        public bool Shadows = true;
        public float Draw = 900f;
        public string Models;
    }

    public sealed class VegetationBiome
    {
        public bool Forest;
        public float Groves;
        public float Solitary;
        public float Banks;
        public float Hedges;
        public Dictionary<string, float> Mix = new Dictionary<string, float>();
        public Dictionary<string, float> South;
        public Dictionary<string, float> North;
        public Dictionary<string, float> Edge;
    }

    public sealed class VegetationForest
    {
        public float Density = 0.85f;
        public float Step = 1.5f;
        public float MassScale = 0.011f;
        public float ClearingScale = 0.035f;
        public float Clearings = 0.3f;
        public float EdgeRadius = 3f;
        public float EdgeNoiseScale = 0.12f;
        public float EdgeNoise = 0.45f;
        public float PatchScale = 0.03f;
        public float Dominance = 0.7f;
        public float GroveScale = 0.06f;
        public float GroveThreshold = 0.64f;
        public float BankScale = 0.08f;
        public float BankThreshold = 0.58f;
    }

    public sealed class VegetationLimits
    {
        public float MaxSlope = 2.4f;
        public float[] Treeline = { 0.3f, 0.46f };
        public float[] Mountain = { 0.12f, 0.42f };
        public float WaterGap = 0.7f;
    }

    public sealed class VegetationClearance
    {
        public float Road = 0.5f;
        public float Bridge = 2.5f;
        public float Settlement = 0.8f;
        public float Village = 3f;
        public float Falloff = 6f;
        public float Wobble = 2.5f;
    }

    public sealed class VegetationRocks
    {
        public float Step = 9f;
        public float Slopes = 0.5f;
        public float Banks = 0.16f;
        public float Rocky = 0.14f;
        public float Open = 0.012f;
        public float FootRadius = 6f;
        public float FootRise = 2.5f;
        public float BigChance = 0.45f;
        public int[] Count = { 2, 6 };
        public float[] BigScale = { 1.5f, 2.1f };
        public float[] SmallScale = { 0.45f, 0.9f };
        public float[] Spread = { 0.8f, 2.6f };
        public float Sink = 0.3f;
        public float Tilt = 8f;
    }

    public sealed class VegetationBoulders
    {
        public float Step = 40f;
        public float Beach = 0.12f;
        public float Foot = 0.1f;
        public float Forest = 0.05f;
        public float[] Scale = { 2.8f, 4f };
        public float Sink = 0.25f;
        public float Tilt = 6f;
    }

    public sealed class VegetationSite
    {
        public string Name;
        public float Lon;
        public float Lat;
    }

    public sealed partial class WorldMap
    {
        static readonly string[] BiomeNames = { "sea", "grass", "forest", "taiga", "steppe", "dry", "desert", "tundra", "snow", "jungle", "farm" };

        public VegetationFile Vegetation { get; private set; }
        public string VegetationReport { get; private set; } = "";
        public uint VegetationChecksum { get; private set; }

        readonly Dictionary<string, List<int>> groupKinds = new Dictionary<string, List<int>>();
        readonly Dictionary<int, string> kindGroup = new Dictionary<int, string>();

        public static VegetationFile LoadVegetation()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "vegetation.json");
            return File.Exists(path) ? DataJson.Read<VegetationFile>(File.ReadAllText(path)) : null;
        }

        public void RebuildVegetation()
        {
            treeKinds.Clear();
            treeCells.Clear();
            groupKinds.Clear();
            kindGroup.Clear();
            VegetationReport = "";
            VegetationChecksum = 0;
            BuildVegetation();
        }

        public bool NearestOfGroup(string group, Vector3 from, bool nearWater, out Vector3 at)
        {
            at = default;
            float best = float.MaxValue;
            if (!groupKinds.TryGetValue(group, out var kinds)) return false;
            foreach (var cell in treeCells)
                foreach (int k in kinds)
                    for (int b = 0; b < cell.Batches[k].Count; b++)
                        for (int i = 0; i < cell.Counts[k][b]; i++)
                        {
                            var p = (Vector3)cell.Batches[k][b][i].GetColumn(3);
                            float d = (p - from).sqrMagnitude;
                            if (d >= best) continue;
                            if (nearWater && !NearWater(p.x + Meta.width / 2f, Meta.height / 2f - p.z, 4f)) continue;
                            best = d;
                            at = p;
                        }
            return best < float.MaxValue;
        }

        public (int instances, int draws) VisibleVegetation(Vector3 eye)
        {
            int inst = 0, draws = 0;
            foreach (var cell in treeCells)
            {
                if (!cell.HasBounds) continue;
                float d = Vector3.Distance(eye, cell.Bounds.ClosestPoint(eye));
                if (d > TreeFadeEnd) continue;
                for (int k = 0; k < treeKinds.Count; k++)
                {
                    var tk = treeKinds[k];
                    if (tk == null || cell.Counts[k].Count == 0 || d > tk.Draw) continue;
                    var mesh = d < TreeLodDistance ? tk.Near : tk.Far;
                    foreach (var n in cell.Counts[k]) inst += n;
                    draws += cell.Counts[k].Count * mesh.subMeshCount;
                }
            }
            return (inst, draws);
        }

        bool BuildVegetation()
        {
            var cfg = LoadVegetation();
            Vegetation = cfg;
            if (cfg == null) return false;
            if (!LoadPackKinds(cfg)) return false;
            int W = Meta.width, H = Meta.height;
            int cs = Mathf.Max(16, cfg.CellSize);
            int cw = (W + cs - 1) / cs, ch = (H + cs - 1) / cs;
            for (int i = 0; i < cw * ch; i++)
            {
                var c = new TreeCell { Batches = new List<Matrix4x4[]>[treeKinds.Count], Counts = new List<int>[treeKinds.Count] };
                for (int k = 0; k < treeKinds.Count; k++) { c.Batches[k] = new List<Matrix4x4[]>(); c.Counts[k] = new List<int>(); }
                treeCells.Add(c);
            }
            var forest = ForestMask(cfg);
            var open = SettlementOpenness(cfg);
            vegForest = forest;
            vegOpen = open;
            var taken = new bool[W * H];
            var counts = new Dictionary<string, int>();
            uint sum = 2166136261u;

            float sx = (float)biomeW / W, sy = (float)biomeH / H;
            byte BiomeAt(float x, float y) => biomes[Mathf.Clamp((int)(y * sy), 0, biomeH - 1) * biomeW + Mathf.Clamp((int)(x * sx), 0, biomeW - 1)];
            float Slope(float x, float y) => Mathf.Abs(HeightAt(x + 1, y) - HeightAt(x - 1, y)) + Mathf.Abs(HeightAt(x, y + 1) - HeightAt(x, y - 1));
            float seedX = cfg.Seed % 997 * 0.37f, seedY = cfg.Seed % 991 * 0.29f;
            float Noise(float x, float y, float scale, float salt) => Mathf.PerlinNoise(x * scale + seedX + salt * 17.3f, y * scale + seedY + salt * 9.1f);
            VegetationBiome Rules(byte b) => b < BiomeNames.Length && cfg.Biomes.TryGetValue(BiomeNames[b], out var r) ? r : null;

            void Put(int kind, Vector3 pos, Quaternion rot, Vector3 scale, float radius)
            {
                var cell = treeCells[(Mathf.Clamp((int)(H / 2f - pos.z), 0, H - 1) / cs) * cw + Mathf.Clamp((int)(pos.x + W / 2f), 0, W - 1) / cs];
                var m = Matrix4x4.TRS(pos, rot, scale);
                Push((cell.Batches[kind], cell.Counts[kind]), m);
                float top = scale.y * 1.5f;
                var tb = new Bounds(pos + Vector3.up * top * 0.5f, new Vector3(radius * 2f + 0.5f, top + 0.5f, radius * 2f + 0.5f));
                if (cell.HasBounds) cell.Bounds.Encapsulate(tb);
                else { cell.Bounds = tb; cell.HasBounds = true; }
                string g = kindGroup[kind];
                counts[g] = counts.TryGetValue(g, out var n) ? n + 1 : 1;
                sum = (sum ^ (uint)kind ^ (uint)Mathf.RoundToInt(pos.x * 100f) * 31u ^ (uint)Mathf.RoundToInt(pos.z * 100f) * 131u) * 16777619u;
            }

            void Mark(float x, float y, float r)
            {
                int x0 = Mathf.Max(0, Mathf.FloorToInt(x - r)), x1 = Mathf.Min(W - 1, Mathf.CeilToInt(x + r));
                int y0 = Mathf.Max(0, Mathf.FloorToInt(y - r)), y1 = Mathf.Min(H - 1, Mathf.CeilToInt(y + r));
                for (int yy = y0; yy <= y1; yy++)
                for (int xx = x0; xx <= x1; xx++)
                    if ((xx - x) * (xx - x) + (yy - y) * (yy - y) <= r * r) taken[yy * W + xx] = true;
            }

            bool Clear(float x, float y, float r)
            {
                if (x < 1 || y < 1 || x >= W - 1 || y >= H - 1) return false;
                if (taken[(int)y * W + (int)x]) return false;
                return !RoadNear(x, y, r);
            }

            var rk = cfg.Rocks;
            var bo = cfg.Boulders;
            var boulders = groupKinds.TryGetValue("boulder", out var bgl) ? bgl : null;
            if (bo != null && boulders != null && boulders.Count > 0)
                for (float gy = 0; gy < H; gy += bo.Step)
                for (float gx = 0; gx < W; gx += bo.Step)
                {
                    int ix = (int)(gx / bo.Step), iy = (int)(gy / bo.Step);
                    float cx = gx + Hash01(ix, iy, cfg.Seed, 61) * bo.Step, cy = gy + Hash01(ix, iy, cfg.Seed, 62) * bo.Step;
                    if (cx < 2 || cy < 2 || cx >= W - 2 || cy >= H - 2) continue;
                    float h = HeightAt(cx, cy);
                    if (h < SeaLevel + 0.05f) continue;
                    byte b = BiomeAt(cx, cy);
                    if (b == 10 || b == 8 || Smooth01(rockLo, rockHi, h) > 0.5f) continue;
                    int ci = (int)cy * W + (int)cx;
                    float chance = 0f;
                    if (h < SeaLevel + 1f && NearWater(cx, cy, 3f)) chance = bo.Beach;
                    float rise = 0f;
                    for (int i = 0; i < 8; i++) rise = Mathf.Max(rise, HeightAt(cx + Mathf.Cos(i * Mathf.PI / 4f) * rk.FootRadius, cy + Mathf.Sin(i * Mathf.PI / 4f) * rk.FootRadius) - h);
                    if (rise > rk.FootRise * 1.5f) chance = Mathf.Max(chance, bo.Foot);
                    if (forest[ci] > 0.6f) chance = Mathf.Max(chance, bo.Forest);
                    chance *= open[ci];
                    if (Hash01(ix, iy, cfg.Seed, 63) >= chance) continue;
                    float s = TreeScale * Mathf.Lerp(bo.Scale[0], bo.Scale[1], Hash01(ix, iy, cfg.Seed, 64));
                    float r = cfg.Groups["boulder"].Radius * s;
                    if (!Clear(cx, cy, r)) continue;
                    float low = h, high = h;
                    for (int i = 0; i < 8; i++)
                    {
                        float hh = HeightAt(cx + Mathf.Cos(i * Mathf.PI / 4f) * r, cy + Mathf.Sin(i * Mathf.PI / 4f) * r);
                        low = Mathf.Min(low, hh);
                        high = Mathf.Max(high, hh);
                    }
                    if (high - low > r * 1.2f || low < SeaLevel - 0.3f) continue;
                    float hl = HeightAt(cx - r, cy), hr = HeightAt(cx + r, cy), hd = HeightAt(cx, cy - r), hu = HeightAt(cx, cy + r);
                    var n = new Vector3(hl - hr, 2f * r, hu - hd).normalized;
                    float t1 = (Hash01(ix, iy, cfg.Seed, 65) - 0.5f) * 2f * bo.Tilt, t2 = (Hash01(ix, iy, cfg.Seed, 66) - 0.5f) * 2f * bo.Tilt;
                    var rot = Quaternion.FromToRotation(Vector3.up, Vector3.Lerp(Vector3.up, n, 0.5f)) * Quaternion.Euler(t1, Hash01(ix, iy, cfg.Seed, 67) * 360f, t2);
                    float squash = Mathf.Lerp(0.75f, 0.95f, Hash01(ix, iy, cfg.Seed, 68));
                    var pos = new Vector3(cx - W / 2f, low - bo.Sink * 0.42f * s * squash, H / 2f - cy);
                    Put(boulders[(int)(Hash01(ix, iy, cfg.Seed, 69) * boulders.Count) % boulders.Count], pos, rot, new Vector3(s, s * squash, s), r);
                    Mark(cx, cy, r * 1.15f);
                }
            var rockGroup = groupKinds.TryGetValue("rock", out var rl) ? rl : null;
            var bigGroup = groupKinds.TryGetValue("rockbig", out var bl) ? bl : null;
            if (rockGroup != null && rockGroup.Count > 0)
                for (float gy = 0; gy < H; gy += rk.Step)
                for (float gx = 0; gx < W; gx += rk.Step)
                {
                    int ix = (int)(gx / rk.Step), iy = (int)(gy / rk.Step);
                    float cx = gx + Hash01(ix, iy, cfg.Seed, 1) * rk.Step, cy = gy + Hash01(ix, iy, cfg.Seed, 2) * rk.Step;
                    if (cx >= W - 2 || cy >= H - 2) continue;
                    float h = HeightAt(cx, cy);
                    if (h < SeaLevel - 0.1f) continue;
                    byte b = BiomeAt(cx, cy);
                    if (b == 10 || b == 8) continue;
                    float bare = Smooth01(rockLo, rockHi, h);
                    float slope = Slope(cx, cy);
                    float chance = rk.Open;
                    float rise = 0f;
                    for (int i = 0; i < 8; i++) rise = Mathf.Max(rise, HeightAt(cx + Mathf.Cos(i * Mathf.PI / 4f) * rk.FootRadius, cy + Mathf.Sin(i * Mathf.PI / 4f) * rk.FootRadius) - h);
                    if (bare < 0.6f && (rise > rk.FootRise || bare > 0.12f || slope > 1.4f && slope < 4f)) chance = Mathf.Max(chance, rk.Slopes * (1f - bare));
                    if (b == 7 || b == 5) chance = Mathf.Max(chance, rk.Rocky);
                    bool bank = h < SeaLevel + 1.2f && NearWater(cx, cy, 3f) && Noise(cx, cy, cfg.Forest.BankScale, 7f) > 0.6f;
                    if (bank) chance = Mathf.Max(chance, rk.Banks);
                    chance *= open[(int)cy * W + (int)cx];
                    if (Hash01(ix, iy, cfg.Seed, 3) >= chance) continue;
                    bool big = bigGroup != null && bigGroup.Count > 0 && Hash01(ix, iy, cfg.Seed, 4) < rk.BigChance;
                    int smalls = rk.Count[0] + (int)(Hash01(ix, iy, cfg.Seed, 5) * (rk.Count[1] - rk.Count[0] + 1));
                    for (int i = big ? -1 : 0; i < smalls; i++)
                    {
                        bool isBig = i < 0;
                        float a = Hash01(ix, iy, cfg.Seed, 40 + i * 7) * Mathf.PI * 2f;
                        float dist = isBig ? 0f : Mathf.Lerp(rk.Spread[0], rk.Spread[1], Hash01(ix, iy, cfg.Seed, 41 + i * 7)) * (big ? 1.4f : 1f);
                        float x = cx + Mathf.Cos(a) * dist, y = cy + Mathf.Sin(a) * dist;
                        float s = TreeScale * (isBig ? Mathf.Lerp(rk.BigScale[0], rk.BigScale[1], Hash01(ix, iy, cfg.Seed, 42 + i * 7)) : Mathf.Lerp(rk.SmallScale[0], rk.SmallScale[1], Hash01(ix, iy, cfg.Seed, 42 + i * 7)));
                        var list = isBig ? bigGroup : rockGroup;
                        var grp = cfg.Groups[isBig ? "rockbig" : "rock"];
                        float r = grp.Radius * s;
                        if (!Clear(x, y, r)) continue;
                        float hc = HeightAt(x, y);
                        if (hc < SeaLevel - (bank ? 0.15f : 0f)) continue;
                        float hl = HeightAt(x - r, y), hr = HeightAt(x + r, y), hd = HeightAt(x, y - r), hu = HeightAt(x, y + r);
                        float low = Mathf.Min(hc, Mathf.Min(Mathf.Min(hl, hr), Mathf.Min(hd, hu)));
                        if (Mathf.Max(Mathf.Max(hl, hr), Mathf.Max(hd, hu)) - low > r * 1.6f) continue;
                        var n = new Vector3(hl - hr, 2f * r, hu - hd).normalized;
                        float t1 = (Hash01(ix, iy, cfg.Seed, 43 + i * 7) - 0.5f) * 2f * rk.Tilt, t2 = (Hash01(ix, iy, cfg.Seed, 44 + i * 7) - 0.5f) * 2f * rk.Tilt;
                        var rot = Quaternion.FromToRotation(Vector3.up, Vector3.Lerp(Vector3.up, n, 0.7f)) * Quaternion.Euler(t1, Hash01(ix, iy, cfg.Seed, 45 + i * 7) * 360f, t2);
                        float squash = Mathf.Lerp(0.8f, 1f, Hash01(ix, iy, cfg.Seed, 46 + i * 7));
                        var scale = new Vector3(s, s * squash, s);
                        var pos = new Vector3(x - W / 2f, low - rk.Sink * 0.42f * s * squash, H / 2f - y);
                        int kind = list[(int)(Hash01(ix, iy, cfg.Seed, 47 + i * 7) * list.Count) % list.Count];
                        Put(kind, pos, rot, scale, r);
                        Mark(x, y, r * 0.9f);
                    }
                }

            var fo = cfg.Forest;
            float step = fo.Step;
            var lim = cfg.Limits;
            for (float gy = 0; gy < H - 1; gy += step)
            for (float gx = 0; gx < W - 1; gx += step)
            {
                int ix = (int)(gx / step), iy = (int)(gy / step);
                float px = gx + (0.15f + 0.7f * Hash01(ix, iy, cfg.Seed, 21)) * step, py = gy + (0.15f + 0.7f * Hash01(ix, iy, cfg.Seed, 22)) * step;
                int pi = Mathf.Min(H - 1, (int)py) * W + Mathf.Min(W - 1, (int)px);
                if (taken[pi]) continue;
                float h = HeightAt(px, py);
                if (h < SeaLevel + 0.2f) continue;
                float bare = Smooth01(rockLo, rockHi, h);
                if (bare > 0.6f) continue;
                float slope = Slope(px, py);
                if (slope > lim.MaxSlope) continue;
                byte b = BiomeAt(px, py);
                var rules = Rules(b);
                if (rules == null) continue;
                float lat = Meta.latMax - py / Meta.pxPerDegLat;
                var mix = Climate(rules, lat, cfg);
                float density = 0f;
                float wob = (Noise(px, py, fo.EdgeNoiseScale, 3f) - 0.5f) * 2f * fo.EdgeNoise;
                float inside = forest[pi] + wob;
                if (inside > 0.5f)
                {
                    float zone = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.3f, 0.72f, Noise(px, py, fo.MassScale, 1f)));
                    float clear = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(fo.Clearings * 0.75f, fo.Clearings * 0.75f + 0.28f, Noise(px, py, fo.ClearingScale, 2f)));
                    float edge = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.5f, 0.75f, inside));
                    density = Mathf.Min(1f, fo.Density * clear * Mathf.Lerp(0.55f, 1.2f, zone) * Mathf.Lerp(0.45f, 1f, edge));
                    var fr = rules.Forest ? rules : Rules(2);
                    if (!rules.Forest && fr != null) mix = Climate(fr, lat, cfg);
                    if (edge < 0.6f && fr?.Edge != null && Hash01(ix, iy, cfg.Seed, 23) < 0.45f) mix = fr.Edge;
                }
                else
                {
                    if (b == 10)
                    {
                        if (rules.Hedges <= 0f || !NearBiomeEdge(px, py, 10, sx, sy)) continue;
                        density = rules.Hedges * Mathf.InverseLerp(0.45f, 0.75f, Noise(px, py, 0.15f, 9f));
                    }
                    else
                    {
                        float grove = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(fo.GroveThreshold, fo.GroveThreshold + 0.14f, Noise(px, py, fo.GroveScale, 4f)));
                        density = rules.Groves * grove + rules.Solitary;
                        if (rules.Banks > 0f && Noise(px, py, fo.BankScale, 5f) > fo.BankThreshold && NearWater(px, py, 4f))
                        {
                            density = Mathf.Max(density, rules.Banks);
                            if (cfg.Biomes.TryGetValue("banks", out var bk)) mix = bk.Mix;
                        }
                    }
                    if (h > HeightScale * lim.Mountain[0] && h < HeightScale * lim.Mountain[1] && b != 5 && b != 6 && b != 8 && cfg.Biomes.TryGetValue("mountain", out var mt))
                    {
                        float m = mt.Groves * Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.45f, 0.7f, Noise(px, py, 0.05f, 6f))) + mt.Solitary;
                        if (m > density) { density = m; mix = mt.Mix; }
                    }
                }
                density *= 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(HeightScale * lim.Treeline[0], HeightScale * lim.Treeline[1], h));
                density *= (1f - bare) * open[pi];
                if (mix == null || mix.Count == 0 || Hash01(ix, iy, cfg.Seed, 24) >= density) continue;
                string group = PickGroup(mix, px, py, cfg, ix, iy);
                if (group == null || !groupKinds.TryGetValue(group, out var kinds) || kinds.Count == 0) continue;
                var gr = cfg.Groups[group];
                float sc = TreeScale * Mathf.Lerp(gr.Scale[0], gr.Scale[1], Hash01(ix, iy, cfg.Seed, 25));
                float crown = gr.Radius * sc;
                if (RoadNear(px, py, crown + cfg.Clearance.Road)) continue;
                if (NearWater(px, py, lim.WaterGap)) continue;
                float pick = Noise(px, py, fo.PatchScale * 3f, 8f) * 0.6f + Hash01(ix, iy, cfg.Seed, 26) * 0.4f;
                int kind = kinds[Mathf.Clamp((int)(pick * kinds.Count), 0, kinds.Count - 1)];
                float low = Mathf.Min(h, Mathf.Min(HeightAt(px - 0.3f, py), HeightAt(px + 0.3f, py)));
                var pos = new Vector3(px - W / 2f, low - 0.06f, H / 2f - py);
                Put(kind, pos, Quaternion.Euler(0f, Hash01(ix, iy, cfg.Seed, 27) * 360f, 0f), Vector3.one * sc, crown);
            }

            VegetationChecksum = sum;
            var parts = new List<string>();
            int total = 0;
            foreach (var kv in counts) { parts.Add($"{kv.Key} {kv.Value}"); total += kv.Value; }
            parts.Sort(string.CompareOrdinal);
            VegetationReport = $"total {total}: {string.Join(", ", parts)}; checksum {sum:X8}";
            Debug.Log("[W1347] vegetation " + VegetationReport);
            return true;
        }

        static Dictionary<string, float> Climate(VegetationBiome r, float lat, VegetationFile cfg) =>
            lat > cfg.NorthLat && r.North != null ? r.North : lat < cfg.SouthLat && r.South != null ? r.South : r.Mix;

        string PickGroup(Dictionary<string, float> mix, float px, float py, VegetationFile cfg, int ix, int iy)
        {
            var fo = cfg.Forest;
            float wx = px + (Mathf.PerlinNoise(px * 0.05f + 3f, py * 0.05f) - 0.5f) * 30f;
            float wy = py + (Mathf.PerlinNoise(px * 0.05f, py * 0.05f + 7f) - 0.5f) * 30f;
            float patch = Hash01(Mathf.FloorToInt(wx * fo.PatchScale), Mathf.FloorToInt(wy * fo.PatchScale), cfg.Seed, 31);
            float roll = Hash01(ix, iy, cfg.Seed, 32) < fo.Dominance ? patch : Hash01(ix, iy, cfg.Seed, 33);
            float total = 0f;
            foreach (var v in mix.Values) total += v;
            if (total <= 0f) return null;
            roll *= total;
            foreach (var kv in mix)
            {
                roll -= kv.Value;
                if (roll <= 0f) return kv.Key;
            }
            return null;
        }

        bool LoadPackKinds(VegetationFile cfg)
        {
            var art = EnvironmentArt.Load();
            var shader = Shader.Find("Warfare/WorldTree");
            if (art == null || shader == null) return false;
            var mats = new Dictionary<string, Material>();
            foreach (var kv in cfg.Groups)
            {
                string prefix = "WorldTree_p_" + (kv.Value.Models ?? kv.Key) + "_";
                var list = new List<int>();
                foreach (var e in art.Props)
                {
                    if (!e.Id.StartsWith(prefix, StringComparison.Ordinal) || e.Id.EndsWith("_lod", StringComparison.Ordinal)) continue;
                    var near = e.Prefab;
                    var far = art.Get(e.Id + "_lod") ?? near;
                    var k = new TreeKind { Id = e.Id, Scale = 1f, Shadows = kv.Value.Shadows, Draw = kv.Value.Draw };
                    (k.Near, k.NearMats, k.NearBase) = TreeMesh(near, shader, mats);
                    (k.Far, k.FarMats, k.FarBase) = TreeMesh(far, shader, mats);
                    if (k.Near == null) continue;
                    kindGroup[treeKinds.Count] = kv.Key;
                    list.Add(treeKinds.Count);
                    treeKinds.Add(k);
                }
                groupKinds[kv.Key] = list;
            }
            if (treeKinds.Count == 0)
            {
                Debug.LogWarning("[W1347] vegetation: no pack models");
                return false;
            }
            return true;
        }

        float[] ForestMask(VegetationFile cfg)
        {
            int W = Meta.width, H = Meta.height;
            float sx = (float)biomeW / W, sy = (float)biomeH / H;
            var integral = new int[(W + 1) * (H + 1)];
            for (int y = 0; y < H; y++)
            {
                int row = 0;
                for (int x = 0; x < W; x++)
                {
                    byte b = biomes[Mathf.Clamp((int)(y * sy), 0, biomeH - 1) * biomeW + Mathf.Clamp((int)(x * sx), 0, biomeW - 1)];
                    row += b < BiomeNames.Length && cfg.Biomes.TryGetValue(BiomeNames[b], out var r) && r.Forest ? 1 : 0;
                    integral[(y + 1) * (W + 1) + x + 1] = integral[y * (W + 1) + x + 1] + row;
                }
            }
            int rad = Mathf.Max(1, Mathf.RoundToInt(cfg.Forest.EdgeRadius));
            var mask = new float[W * H];
            for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                int x0 = Mathf.Max(0, x - rad), x1 = Mathf.Min(W, x + rad + 1), y0 = Mathf.Max(0, y - rad), y1 = Mathf.Min(H, y + rad + 1);
                int s = integral[y1 * (W + 1) + x1] - integral[y0 * (W + 1) + x1] - integral[y1 * (W + 1) + x0] + integral[y0 * (W + 1) + x0];
                mask[y * W + x] = (float)s / ((x1 - x0) * (y1 - y0));
            }
            return mask;
        }

        float[] SettlementOpenness(VegetationFile cfg)
        {
            int W = Meta.width, H = Meta.height;
            var open = new float[W * H];
            for (int i = 0; i < open.Length; i++) open[i] = 1f;
            var c = cfg.Clearance;
            foreach (var st in placed)
            {
                Vector2 center = new Vector2(st.Px, st.Py), ext = Vector2.one * WorldSettlements.FlattenRadius(st.Kind, st.Data.capital) * 0.7f;
                if (st.HasFootprint)
                {
                    center = new Vector2(st.Footprint.center.x + W / 2f, H / 2f - st.Footprint.center.z);
                    ext = new Vector2(st.Footprint.extents.x, st.Footprint.extents.z);
                }
                float gap = c.Settlement + (st.Kind == SettlementKind.Village ? c.Village : 0f);
                float reach = gap + c.Falloff + c.Wobble;
                int x0 = Mathf.Max(0, Mathf.FloorToInt(center.x - ext.x - reach)), x1 = Mathf.Min(W - 1, Mathf.CeilToInt(center.x + ext.x + reach));
                int y0 = Mathf.Max(0, Mathf.FloorToInt(center.y - ext.y - reach)), y1 = Mathf.Min(H - 1, Mathf.CeilToInt(center.y + ext.y + reach));
                for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    float dx = Mathf.Max(Mathf.Abs(x - center.x) - ext.x, 0f), dy = Mathf.Max(Mathf.Abs(y - center.y) - ext.y, 0f);
                    float d = Mathf.Sqrt(dx * dx + dy * dy) + (Mathf.PerlinNoise(x * 0.13f + 51f, y * 0.13f + 23f) - 0.5f) * 2f * c.Wobble;
                    float v = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(gap, gap + c.Falloff, d));
                    if (v < open[y * W + x]) open[y * W + x] = v;
                }
            }
            foreach (var l in landmarks)
            {
                float reach = l.r + c.Falloff * 0.5f;
                int x0 = Mathf.Max(0, Mathf.FloorToInt(l.px.x - reach)), x1 = Mathf.Min(W - 1, Mathf.CeilToInt(l.px.x + reach));
                int y0 = Mathf.Max(0, Mathf.FloorToInt(l.px.y - reach)), y1 = Mathf.Min(H - 1, Mathf.CeilToInt(l.px.y + reach));
                for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    float d = Mathf.Sqrt((x - l.px.x) * (x - l.px.x) + (y - l.px.y) * (y - l.px.y));
                    float v = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(l.r, reach, d));
                    if (v < open[y * W + x]) open[y * W + x] = v;
                }
            }
            if (roadData?.bridges != null)
                foreach (var br in roadData.bridges)
                {
                    float r = br.len * 0.5f + c.Bridge;
                    int x0 = Mathf.Max(0, Mathf.FloorToInt(br.x - r)), x1 = Mathf.Min(W - 1, Mathf.CeilToInt(br.x + r));
                    int y0 = Mathf.Max(0, Mathf.FloorToInt(br.y - r)), y1 = Mathf.Min(H - 1, Mathf.CeilToInt(br.y + r));
                    for (int y = y0; y <= y1; y++)
                    for (int x = x0; x <= x1; x++)
                        if ((x - br.x) * (x - br.x) + (y - br.y) * (y - br.y) < r * r) open[y * W + x] = 0f;
                }
            return open;
        }

        bool RoadNear(float px, float py, float r)
        {
            if (roadMask == null) return false;
            for (int i = 0; i < 9; i++)
            {
                float ox = i == 0 ? 0f : Mathf.Cos(i * Mathf.PI / 4f) * r, oy = i == 0 ? 0f : Mathf.Sin(i * Mathf.PI / 4f) * r;
                int x = Mathf.Clamp((int)((px + ox) * 2f), 0, roadW - 1), y = Mathf.Clamp((int)((py + oy) * 2f), 0, roadH - 1);
                if (roadMask[(roadH - 1 - y) * roadW + x] > 25) return true;
            }
            return false;
        }

        bool NearBiomeEdge(float px, float py, byte b, float sx, float sy)
        {
            for (int i = 0; i < 8; i++)
            {
                float x = px + Mathf.Cos(i * Mathf.PI / 4f) * 2f, y = py + Mathf.Sin(i * Mathf.PI / 4f) * 2f;
                if (biomes[Mathf.Clamp((int)(y * sy), 0, biomeH - 1) * biomeW + Mathf.Clamp((int)(x * sx), 0, biomeW - 1)] != b) return true;
            }
            return false;
        }

        static float Hash01(int x, int y, int seed, int salt)
        {
            unchecked
            {
                uint h = (uint)x * 374761393u + (uint)y * 668265263u + (uint)seed * 2246822519u + (uint)salt * 3266489917u;
                h = (h ^ (h >> 13)) * 1274126177u;
                h ^= h >> 16;
                return (h & 0xFFFFFF) / 16777216f;
            }
        }
    }
}
