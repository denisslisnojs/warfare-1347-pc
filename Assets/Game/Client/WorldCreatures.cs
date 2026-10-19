using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Warfare.Core;

namespace Warfare.Client
{
    public sealed class CreatureFile
    {
        public Dictionary<string, CreatureKind> Creatures = new Dictionary<string, CreatureKind>();
        public List<WildRule> Wild = new List<WildRule>();
        public ShipSettings Ships;
    }

    public sealed class ShipSettings
    {
        public float ShipScale = 3f;
        public float BoatScale = 2f;
        public float SeaSpeed = 2.6f;
        public float FishingSpeed = 0.7f;
    }

    public sealed class WildRule
    {
        public string Kind;
        public List<string> Biomes = new List<string>();
        public float Step = 40f;
        public float Chance = 0.2f;
        public int[] Group = { 1, 3 };
        public float Roam = 8f;
        public float FromSettlement = 12f;
    }

    public sealed class CreatureKind
    {
        public List<string> Models = new List<string>();
        public float Length = 1f;
        public float Speed = 0.2f;
    }

    public sealed partial class WorldMap
    {
        CreatureFile creatures;
        readonly Dictionary<string, Material> creatureMats = new Dictionary<string, Material>();
        bool creaturesLoaded;

        public CreatureFile Creatures
        {
            get
            {
                if (creaturesLoaded) return creatures;
                creaturesLoaded = true;
                string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "creatures.json");
                creatures = File.Exists(path) ? DataJson.Read<CreatureFile>(File.ReadAllText(path)) : null;
                return creatures;
            }
        }

        GameObject SpawnCreature(CreatureKind kind, EnvironmentArt art, System.Random rnd, Transform root, out Animator anim, out Quaternion face)
        {
            anim = null;
            face = Quaternion.identity;
            if (kind.Models.Count == 0) return null;
            string id = kind.Models[rnd.Next(kind.Models.Count)];
            var prefab = art.Get(id);
            if (prefab == null) return null;
            var go = Instantiate(prefab, root);
            go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            var renderers = go.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return go;
            foreach (var r in renderers)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null) continue;
                    string key = id + "/" + mats[i].name;
                    if (!creatureMats.TryGetValue(key, out var m)) creatureMats[key] = m = new Material(mats[i]) { name = key };
                    mats[i] = m;
                }
                r.sharedMaterials = mats;
            }
            var b = renderers[0].bounds;
            foreach (var r in renderers) b.Encapsulate(r.bounds);
            var head = FindDeep(go.transform, "Head");
            var fwd = head != null ? head.position - b.center : Vector3.forward;
            fwd.y = 0f;
            if (fwd.sqrMagnitude < 1e-6f) fwd = Vector3.forward;
            face = Quaternion.Inverse(Quaternion.LookRotation(fwd.normalized));
            float length = Mathf.Max(b.size.x, b.size.z);
            if (length > 1e-4f) go.transform.localScale = Vector3.one * (kind.Length / length);
            anim = go.GetComponentInChildren<Animator>();
            if (anim == null) anim = go.AddComponent<Animator>();
            anim.runtimeAnimatorController = Resources.Load<RuntimeAnimatorController>("Creatures/" + id);
            anim.applyRootMotion = false;
            anim.cullingMode = AnimatorCullingMode.CullCompletely;
            if (anim.runtimeAnimatorController == null) anim = null;
            return go;
        }

        void BuildWild()
        {
            var cfg = Creatures;
            var art = EnvironmentArt.Load();
            if (cfg == null || art == null || cfg.Wild.Count == 0) return;
            var root = new GameObject("Wildlife").transform;
            root.SetParent(transform, false);
            var rnd = new System.Random(77);
            int W = Meta.width, H = Meta.height, made = 0;
            float sx = (float)biomeW / W, sy = (float)biomeH / H;
            foreach (var rule in cfg.Wild)
            {
                if (!cfg.Creatures.TryGetValue(rule.Kind, out var kind)) continue;
                int salt = StableHash(rule.Kind);
                for (float gy = 0; gy < H; gy += rule.Step)
                for (float gx = 0; gx < W; gx += rule.Step)
                {
                    int ix = (int)(gx / rule.Step), iy = (int)(gy / rule.Step);
                    if (Hash01(ix, iy, salt, 1) >= rule.Chance) continue;
                    float x = gx + Hash01(ix, iy, salt, 2) * rule.Step, y = gy + Hash01(ix, iy, salt, 3) * rule.Step;
                    if (x < 3 || y < 3 || x >= W - 3 || y >= H - 3) continue;
                    float h = HeightAt(x, y);
                    if (h < SeaLevel + 0.3f || Smooth01(rockLo, rockHi, h) > 0.4f || RoadNear(x, y, 2f)) continue;
                    byte b = biomes[Mathf.Clamp((int)(y * sy), 0, biomeH - 1) * biomeW + Mathf.Clamp((int)(x * sx), 0, biomeW - 1)];
                    if (b >= BiomeNames.Length || !rule.Biomes.Contains(BiomeNames[b])) continue;
                    bool far = true;
                    foreach (var st in placed)
                        if ((st.Px - x) * (st.Px - x) + (st.Py - y) * (st.Py - y) < rule.FromSettlement * rule.FromSettlement) { far = false; break; }
                    if (!far) continue;
                    int n = rule.Group[0] + (int)(Hash01(ix, iy, salt, 4) * (rule.Group[1] - rule.Group[0] + 1));
                    var home = new Vector2(x, y);
                    for (int i = 0; i < n; i++)
                    {
                        var pos = home + new Vector2(Hash01(ix, iy, salt, 10 + i) - 0.5f, Hash01(ix, iy, salt, 20 + i) - 0.5f) * 3f;
                        float hp = HeightAt(pos.x, pos.y);
                        if (hp < SeaLevel + 0.25f) continue;
                        var go = SpawnCreature(kind, art, rnd, root, out var anim, out var face);
                        if (go == null) continue;
                        foreach (var rd in go.GetComponentsInChildren<Renderer>())
                        {
                            var mats = rd.sharedMaterials;
                            for (int m = 0; m < mats.Length; m++)
                                if (mats[m] != null) mats[m] = PropMaterial(mats[m], placed[0].Faction);
                            rd.sharedMaterials = mats;
                        }
                        var g = new Grazer { T = go.transform, Home = home, Pos = pos, Target = pos, Speed = kind.Speed, Wait = (float)rnd.NextDouble() * 6f, Anim = anim, Face = face, Eats = rnd.NextDouble() < 0.5, Roam = rule.Roam };
                        go.transform.SetPositionAndRotation(new Vector3(pos.x - W / 2f, hp, H / 2f - pos.y), Quaternion.Euler(0f, (float)rnd.NextDouble() * 360f, 0f) * face);
                        if (anim != null) anim.SetFloat("State", g.Eats ? 0f : 1f);
                        grazers.Add(g);
                        made++;
                    }
                }
            }
            Debug.Log($"[W1347] wild animals: {made}");
        }

        public bool NearestShip(Vector3 from, out Vector3 at)
        {
            at = default;
            float best = float.MaxValue;
            foreach (var sl in sailers)
            {
                float d = (sl.T.position - from).sqrMagnitude;
                if (d < best) { best = d; at = sl.T.position; }
            }
            return best < float.MaxValue;
        }

        public bool NearestCreature(Vector3 from, bool wild, out Vector3 at)
        {
            at = default;
            float best = float.MaxValue;
            foreach (var g in grazers)
            {
                if (g.Anim == null || (g.Roam > 4f) != wild) continue;
                float d = (g.T.position - from).sqrMagnitude;
                if (d < best) { best = d; at = g.T.position; }
            }
            return best < float.MaxValue;
        }

        static Transform FindDeep(Transform t, string name)
        {
            if (t.name == name) return t;
            foreach (Transform c in t)
            {
                var f = FindDeep(c, name);
                if (f != null) return f;
            }
            return null;
        }
    }
}
