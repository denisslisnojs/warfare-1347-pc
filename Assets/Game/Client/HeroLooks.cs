using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Warfare.Core;

namespace Warfare.Client
{
    public sealed class LookColor
    {
        public string Id;
        public string Name;
        public string NameEn;
        public string Color;
    }

    public sealed class LookKey
    {
        public string Id;
        public string Name;
        public string NameEn;
    }

    public sealed class EyePreset
    {
        public string Id;
        public string Name;
        public string NameEn;
        public Dictionary<string, float> Keys = new Dictionary<string, float>();
    }

    public sealed class LooksData
    {
        public string SkinBase = "#FBCCA9";
        public float SoldierFaceSpread = 0.5f;
        public float SkinSmoothness = 0.38f;
        public List<LookColor> Skin = new List<LookColor>();
        public List<LookColor> Hair = new List<LookColor>();
        public List<LookKey> Face = new List<LookKey>();
        public List<LookKey> HairStyles = new List<LookKey>();
        public List<LookKey> Beards = new List<LookKey>();
        public List<LookKey> Moustaches = new List<LookKey>();
        public List<EyePreset> EyePresets = new List<EyePreset>();
    }

    public sealed class HeroLook
    {
        public string Faction;
        public string Skin;
        public string Hair;
        public string Eyes;
        public string HairStyle;
        public string Beard;
        public string Moustache;
        public Dictionary<string, float> Face = new Dictionary<string, float>();

        public float Get(string key) => Face.TryGetValue(key, out var v) ? v : 0f;
    }

    public static class HeroLooks
    {
        static string SavePath => Path.Combine(Application.persistentDataPath, "hero_look.json");

        public static LooksData LoadData()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "looks.json");
            return File.Exists(path) ? DataJson.Read<LooksData>(File.ReadAllText(path)) : new LooksData();
        }

        public static HeroLook LoadSaved() => File.Exists(SavePath) ? DataJson.Read<HeroLook>(File.ReadAllText(SavePath)) : null;

        public static void Save(HeroLook look) => File.WriteAllText(SavePath, DataJson.Write(look));

        public static HeroLook Default(LooksData data) => new HeroLook
        {
            Skin = data.Skin.Count > 0 ? data.Skin[0].Id : null,
            Hair = data.Hair.Exists(h => h.Id == "brown") ? "brown" : data.Hair.Count > 0 ? data.Hair[0].Id : null,
            Eyes = data.EyePresets.Count > 0 ? data.EyePresets[0].Id : null,
            HairStyle = data.HairStyles.Count > 1 ? data.HairStyles[1].Id : null,
            Beard = "none",
            Moustache = "none",
        };

        public static HeroLook Random(LooksData data, float spread, System.Random rng, bool colours)
        {
            var look = Default(data);
            foreach (var k in data.Face) look.Face[k.Id] = (float)(rng.NextDouble() * 2.0 - 1.0) * spread;
            look.Eyes = null;
            if (colours)
            {
                if (data.Skin.Count > 0) look.Skin = data.Skin[rng.Next(data.Skin.Count)].Id;
                if (data.Hair.Count > 0) look.Hair = data.Hair[rng.Next(data.Hair.Count)].Id;
                RandomStyles(look, data, rng);
            }
            return look;
        }

        public static void RandomStyles(HeroLook look, LooksData data, System.Random rng)
        {
            if (data.HairStyles.Count > 0) look.HairStyle = data.HairStyles[rng.Next(data.HairStyles.Count)].Id;
            if (data.Beards.Count > 0) look.Beard = rng.Next(3) == 0 ? "none" : data.Beards[rng.Next(data.Beards.Count)].Id;
            if (data.Moustaches.Count > 0) look.Moustache = data.Moustaches[rng.Next(data.Moustaches.Count)].Id;
        }

        static bool Shown(string name, HeroLook look)
        {
            if (name.StartsWith("Hair_")) return name == look.HairStyle;
            if (name.StartsWith("Beard_")) return name == look.Beard;
            if (name.StartsWith("Moustache_")) return name == look.Moustache;
            return true;
        }

        public static void UsePreset(HeroLook look, EyePreset preset)
        {
            foreach (var key in new List<string>(look.Face.Keys))
                if (key.StartsWith("Eyes")) look.Face[key] = 0f;
            foreach (var kv in preset.Keys) look.Face[kv.Key] = kv.Value;
            look.Eyes = preset.Id;
        }

        public static void Apply(GameObject model, HeroLook look, LooksData data)
        {
            var skin = Tint(Hex(Find(data.Skin, look.Skin)?.Color ?? data.SkinBase), Hex(data.SkinBase));
            var hair = Hex(Find(data.Hair, look.Hair)?.Color ?? "#523D2D");
            foreach (var r in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                r.enabled = Shown(r.name, look);
                var mesh = r.sharedMesh;
                if (mesh != null)
                    for (int i = 0; i < mesh.blendShapeCount; i++)
                    {
                        string name = mesh.GetBlendShapeName(i);
                        int dot = name.LastIndexOf('.');
                        if (dot >= 0) name = name.Substring(dot + 1);
                        r.SetBlendShapeWeight(i, look.Get(name) * 100f);
                    }
                foreach (var m in r.materials)
                {
                    if (m.name.StartsWith("Skin"))
                    {
                        SetColor(m, skin);
                        if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", data.SkinSmoothness);
                        var tex = Resources.Load<Texture2D>(look.Beard == "Beard_Stubble" ? "Characters/Hero_Skin_Stubble" : "Characters/Hero_Skin");
                        if (tex != null && m.HasProperty("_BaseMap")) m.SetTexture("_BaseMap", tex);
                    }
                    else if (m.name.StartsWith("Hair")) SetColor(m, hair);
                }
            }
        }

        public static Color Hex(string s) => s != null && ColorUtility.TryParseHtmlString(s, out var c) ? c : Color.white;

        public static LookColor Find(List<LookColor> list, string id) => list.Find(c => c.Id == id);

        static void SetColor(Material m, Color c)
        {
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Color")) m.SetColor("_Color", c);
        }

        static Color Tint(Color tone, Color b)
        {
            var t = tone.linear;
            var bl = b.linear;
            return new Color(Mathf.Min(1f, t.r / Mathf.Max(bl.r, 1e-4f)), Mathf.Min(1f, t.g / Mathf.Max(bl.g, 1e-4f)), Mathf.Min(1f, t.b / Mathf.Max(bl.b, 1e-4f))).gamma;
        }
    }
}
