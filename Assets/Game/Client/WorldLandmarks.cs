using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using Warfare.Core;
using Warfare.Core.World;

namespace Warfare.Client
{
    public sealed class LandmarkFile
    {
        public int Seed = 1347;
        public Dictionary<string, LandmarkType> Types = new Dictionary<string, LandmarkType>();
    }

    public sealed class LandmarkType
    {
        public string Model;
        public float Scale = 1f;
        public string Place = "village";
        public float Chance = 0.4f;
        public float[] Distance = { 2.5f, 5f };
        public float MaxSlope = 1.2f;
        public float Clear = 2.5f;
        public string Spin;
        public float SpinSpeed = 20f;
        public List<string> SkipFactions = new List<string>();
        public float Step = 60f;
        public float FromSettlement = 14f;
        public float NearRoad;
        public float Prominence;
        public List<string> Biomes = new List<string>();
    }

    public sealed partial class WorldMap
    {
        readonly List<(string type, Vector2 px, float r, Transform t)> landmarks = new List<(string, Vector2, float, Transform)>();
        readonly List<(Transform t, float speed)> spinners = new List<(Transform, float)>();

        public static LandmarkFile LoadLandmarks()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "landmarks.json");
            return File.Exists(path) ? DataJson.Read<LandmarkFile>(File.ReadAllText(path)) : null;
        }

        void BuildLandmarks()
        {
            var cfg = LoadLandmarks();
            var art = EnvironmentArt.Load();
            if (cfg == null || art == null) return;
            var root = new GameObject("Landmarks").transform;
            root.SetParent(transform, false);
            float sx = (float)biomeW / Meta.width, sy = (float)biomeH / Meta.height;
            int farmCount(float x, float y)
            {
                int n = 0;
                for (int i = 0; i < 12; i++)
                {
                    float a = i * Mathf.PI / 6f;
                    int bx = Mathf.Clamp((int)((x + Mathf.Cos(a) * 3f) * sx), 0, biomeW - 1), by = Mathf.Clamp((int)((y + Mathf.Sin(a) * 3f) * sy), 0, biomeH - 1);
                    if (biomes[by * biomeW + bx] == 10) n++;
                }
                return n;
            }
            foreach (var kv in cfg.Types)
            {
                var type = kv.Value;
                var prefab = art.Get(type.Model);
                if (prefab == null) continue;
                int made = 0;
                if (type.Place != "village")
                {
                    made = PlaceOpen(kv.Key, type, prefab, cfg, root);
                    Debug.Log($"[W1347] landmarks {kv.Key}: {made}");
                    continue;
                }
                for (int si = 0; si < placed.Count; si++)
                {
                    var st = placed[si];
                    if (type.Place == "village" && st.Kind != SettlementKind.Village) continue;
                    if (type.SkipFactions.Contains(st.Faction.faction)) continue;
                    int key = StableHash(st.Data.id);
                    if (Hash01(key, si, cfg.Seed, 1) >= type.Chance) continue;
                    float rIn = WorldSettlements.FlattenRadius(st.Kind, st.Data.capital) * 1.25f;
                    float bestScore = -1f, bx = 0f, by = 0f;
                    for (int c = 0; c < 12; c++)
                    {
                        float a = Hash01(key, c, cfg.Seed, 2) * Mathf.PI * 2f;
                        float d = rIn + Mathf.Lerp(type.Distance[0], type.Distance[1], Hash01(key, c, cfg.Seed, 3));
                        float x = st.Px + Mathf.Cos(a) * d, y = st.Py + Mathf.Sin(a) * d;
                        if (x < 2 || y < 2 || x >= Meta.width - 2 || y >= Meta.height - 2) continue;
                        float h = HeightAt(x, y);
                        if (h < SeaLevel + 0.3f || NearWater(x, y, 2f) || RoadNear(x, y, type.Clear * 0.6f)) continue;
                        float slope = Mathf.Abs(HeightAt(x + 1, y) - HeightAt(x - 1, y)) + Mathf.Abs(HeightAt(x, y + 1) - HeightAt(x, y - 1));
                        if (slope > type.MaxSlope || TooClose(x, y, type.Clear)) continue;
                        float score = farmCount(x, y) + Hash01(key, c, cfg.Seed, 4);
                        if (score > bestScore) { bestScore = score; bx = x; by = y; }
                    }
                    if (bestScore < 0f) continue;
                    float low = HeightAt(bx, by);
                    for (int i = 0; i < 8; i++) low = Mathf.Min(low, HeightAt(bx + Mathf.Cos(i * Mathf.PI / 4f) * 0.8f, by + Mathf.Sin(i * Mathf.PI / 4f) * 0.8f));
                    var pos = new Vector3(bx - Meta.width / 2f, low - 0.05f, Meta.height / 2f - by);
                    var go = Instantiate(prefab, pos, Quaternion.Euler(0f, Hash01(key, 0, cfg.Seed, 5) * 360f, 0f), root);
                    go.name = kv.Key + "_" + st.Data.id;
                    go.transform.localScale = Vector3.one * type.Scale;
                    foreach (var r in go.GetComponentsInChildren<Renderer>())
                    {
                        var mats = r.sharedMaterials;
                        for (int i = 0; i < mats.Length; i++)
                            if (mats[i] != null) mats[i] = PropMaterial(mats[i], st.Faction);
                        r.sharedMaterials = mats;
                        r.shadowCastingMode = ShadowCastingMode.On;
                    }
                    if (!string.IsNullOrEmpty(type.Spin))
                    {
                        var spin = go.transform.Find(type.Spin);
                        if (spin != null) spinners.Add((spin, type.SpinSpeed * Mathf.Lerp(0.8f, 1.2f, Hash01(key, 1, cfg.Seed, 6))));
                    }
                    landmarks.Add((kv.Key, new Vector2(bx, by), type.Clear, go.transform));
                    made++;
                }
                Debug.Log($"[W1347] landmarks {kv.Key}: {made}");
            }
        }

        int PlaceOpen(string id, LandmarkType type, GameObject prefab, LandmarkFile cfg, Transform root)
        {
            int W = Meta.width, H = Meta.height, made = 0;
            float sx = (float)biomeW / W, sy = (float)biomeH / H;
            int salt = StableHash(id);
            for (float gy = 0; gy < H; gy += type.Step)
            for (float gx = 0; gx < W; gx += type.Step)
            {
                int ix = (int)(gx / type.Step), iy = (int)(gy / type.Step);
                if (Hash01(ix, iy, cfg.Seed + salt, 1) >= type.Chance) continue;
                float bestScore = -1f, bx = 0f, by = 0f;
                bool hill = type.Place == "hill";
                int side = hill ? Mathf.Max(1, (int)(type.Step / 4f)) : 1;
                int tries = hill ? side * side : 10;
                for (int c = 0; c < tries; c++)
                {
                    float x = hill ? gx + (c % side + 0.5f) * 4f : gx + Hash01(ix * 16 + c, iy, cfg.Seed + salt, 2) * type.Step;
                    float y = hill ? gy + (c / side + 0.5f) * 4f : gy + Hash01(ix * 16 + c, iy, cfg.Seed + salt, 3) * type.Step;
                    if (x < 4 || y < 4 || x >= W - 4 || y >= H - 4) continue;
                    float h = HeightAt(x, y);
                    if (h < SeaLevel + 0.4f || Smooth01(rockLo, rockHi, h) > 0.3f || NearWater(x, y, type.Clear)) continue;
                    byte b = biomes[Mathf.Clamp((int)(y * sy), 0, biomeH - 1) * biomeW + Mathf.Clamp((int)(x * sx), 0, biomeW - 1)];
                    if (type.Biomes.Count > 0 && (b >= BiomeNames.Length || !type.Biomes.Contains(BiomeNames[b]))) continue;
                    float slope = Mathf.Abs(HeightAt(x + 1, y) - HeightAt(x - 1, y)) + Mathf.Abs(HeightAt(x, y + 1) - HeightAt(x, y - 1));
                    if (slope > type.MaxSlope || RoadNear(x, y, type.Clear * 0.7f) || TooClose(x, y, type.Clear)) continue;
                    bool far = true;
                    foreach (var st in placed)
                        if ((st.Px - x) * (st.Px - x) + (st.Py - y) * (st.Py - y) < type.FromSettlement * type.FromSettlement) { far = false; break; }
                    if (!far) continue;
                    if (type.NearRoad > 0f && !RoadNear(x, y, type.NearRoad)) continue;
                    float ring = 0f;
                    for (int i = 0; i < 8; i++) ring += HeightAt(x + Mathf.Cos(i * Mathf.PI / 4f) * 8f, y + Mathf.Sin(i * Mathf.PI / 4f) * 8f);
                    float rise = h - ring / 8f;
                    if (rise < type.Prominence) continue;
                    float score = rise + Hash01(ix * 16 + c, iy, cfg.Seed + salt, 4);
                    if (score > bestScore) { bestScore = score; bx = x; by = y; }
                }
                if (bestScore < 0f) continue;
                float low = HeightAt(bx, by);
                float reach = type.Clear * 0.6f;
                for (int i = 0; i < 8; i++) low = Mathf.Min(low, HeightAt(bx + Mathf.Cos(i * Mathf.PI / 4f) * reach, by + Mathf.Sin(i * Mathf.PI / 4f) * reach));
                var pos = new Vector3(bx - W / 2f, low - 0.08f, H / 2f - by);
                var go = Instantiate(prefab, pos, Quaternion.Euler(0f, Hash01(ix, iy, cfg.Seed + salt, 5) * 360f, 0f), root);
                go.name = id + "_" + ix + "_" + iy;
                go.transform.localScale = Vector3.one * type.Scale;
                FactionSettlements owner = null;
                float bestD = float.MaxValue;
                foreach (var st in placed)
                {
                    float d = (st.Px - bx) * (st.Px - bx) + (st.Py - by) * (st.Py - by);
                    if (d < bestD) { bestD = d; owner = st.Faction; }
                }
                foreach (var r in go.GetComponentsInChildren<Renderer>())
                {
                    var mats = r.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                        if (mats[i] != null && owner != null) mats[i] = PropMaterial(mats[i], owner);
                    r.sharedMaterials = mats;
                    r.shadowCastingMode = ShadowCastingMode.On;
                }
                landmarks.Add((id, new Vector2(bx, by), type.Clear, go.transform));
                made++;
            }
            return made;
        }

        bool TooClose(float x, float y, float r)
        {
            foreach (var l in landmarks)
                if ((l.px - new Vector2(x, y)).sqrMagnitude < (l.r + r) * (l.r + r)) return true;
            foreach (var st in placed)
            {
                if (!st.HasFootprint) continue;
                float cx = st.Footprint.center.x + Meta.width / 2f, cy = Meta.height / 2f - st.Footprint.center.z;
                float dx = Mathf.Max(Mathf.Abs(x - cx) - st.Footprint.extents.x, 0f), dy = Mathf.Max(Mathf.Abs(y - cy) - st.Footprint.extents.z, 0f);
                if (dx * dx + dy * dy < r * r) return true;
            }
            return false;
        }

        void SpinLandmarks()
        {
            float dt = Time.deltaTime;
            foreach (var (t, speed) in spinners)
                if (t != null) t.Rotate(Vector3.right, speed * dt, Space.Self);
        }

        public bool NearestLandmark(string type, Vector3 from, out Vector3 at)
        {
            at = default;
            float best = float.MaxValue;
            foreach (var l in landmarks)
            {
                if (l.type != type || l.t == null) continue;
                float d = (l.t.position - from).sqrMagnitude;
                if (d < best) { best = d; at = l.t.position; }
            }
            return best < float.MaxValue;
        }

        static int StableHash(string s)
        {
            unchecked
            {
                int h = (int)2166136261;
                foreach (char c in s ?? "") h = (h ^ c) * 16777619;
                return h;
            }
        }
    }
}
