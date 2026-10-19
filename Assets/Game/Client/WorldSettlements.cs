using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Warfare.Client
{
    [Serializable]
    public sealed class SettlementData
    {
        public string id;
        public string name;
        public string nameEn;
        public float lon;
        public float lat;
        public bool capital;
        public string owner;
        public string model;
        public string note;
        public string about;
    }

    [Serializable]
    public sealed class FactionSettlements
    {
        public string faction;
        public string name;
        public string nameOf;
        public float[] color;
        public float[] trim;
        public SettlementData[] towns = Array.Empty<SettlementData>();
        public SettlementData[] castles = Array.Empty<SettlementData>();
        public SettlementData[] villages = Array.Empty<SettlementData>();
    }

    public enum SettlementKind { Town, Castle, Village }

    public sealed class PlacedSettlement
    {
        public SettlementData Data;
        public SettlementKind Kind;
        public FactionSettlements Faction;
        public Vector3 Position;
        public float Px;
        public float Py;
        public Bounds Footprint;
        public bool HasFootprint;
    }

    public static class WorldSettlements
    {
        public static List<FactionSettlements> LoadAll()
        {
            var list = new List<FactionSettlements>();
            var dir = Path.Combine(Application.streamingAssetsPath, "Data", "world", "factions");
            if (!Directory.Exists(dir)) return list;
            var files = Directory.GetFiles(dir, "*.json");
            Array.Sort(files, StringComparer.Ordinal);
            foreach (var file in files)
            {
                try
                {
                    var f = JsonUtility.FromJson<FactionSettlements>(File.ReadAllText(file));
                    if (f != null) list.Add(f);
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[W1347] {Path.GetFileName(file)}: {e.Message}");
                }
            }
            return list;
        }

        public static IEnumerable<(SettlementData, SettlementKind)> All(FactionSettlements f)
        {
            foreach (var s in f.towns) yield return (s, SettlementKind.Town);
            foreach (var s in f.castles) yield return (s, SettlementKind.Castle);
            foreach (var s in f.villages) yield return (s, SettlementKind.Village);
        }

        public static float FlattenRadius(SettlementKind k, bool capital) => k switch
        {
            SettlementKind.Town => capital ? 9f : 7f,
            SettlementKind.Castle => 5f,
            _ => 4f,
        };

        public static float ModelScale(SettlementKind k, bool capital) => k switch
        {
            SettlementKind.Town => capital ? 2.3f : 1.9f,
            SettlementKind.Castle => 1.6f,
            _ => 1.25f,
        };

        public static string ModelId(SettlementKind k) => k switch
        {
            SettlementKind.Town => "WorldTown",
            SettlementKind.Castle => "WorldCastle",
            _ => "WorldVillage",
        };

        public static IEnumerable<string> ModelCandidates(SettlementKind k, FactionSettlements f, SettlementData s)
        {
            string id = ModelId(k);
            if (!string.IsNullOrEmpty(s.model)) yield return $"{id}_{f.faction}_{s.model}";
            yield return $"{id}_{f.faction}";
            yield return id;
        }

        public static Color ToColor(float[] c, Color fallback) => c != null && c.Length >= 3 ? new Color(c[0], c[1], c[2]) : fallback;
    }

    public sealed class WorldLabels : MonoBehaviour
    {
        public readonly List<PlacedSettlement> Settlements = new List<PlacedSettlement>();
        public PlacedSettlement Hovered { get; private set; }
        GUIStyle town, castle, village;
        Texture2D bannerFill, bannerEdge, bannerShadow, ribbon;
        readonly Dictionary<string, Texture2D> emblems = new Dictionary<string, Texture2D>();
        string uiDir;
        static readonly Color Ink = new Color(0.93f, 0.9f, 0.83f);
        static readonly Color Parchment = new Color(0.86f, 0.82f, 0.72f);
        static readonly Color Soot = new Color(0.12f, 0.11f, 0.1f);

        static Color Muted(Color c)
        {
            float g = c.grayscale;
            var dull = Color.Lerp(c, new Color(g, g, g), 0.35f);
            return Color.Lerp(dull, Soot, 0.38f);
        }

        static Texture2D Load(string dir, string name)
        {
            string path = Path.Combine(dir, name + ".png");
            if (!File.Exists(path)) return null;
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, true) { name = name, wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Trilinear };
            t.LoadImage(File.ReadAllBytes(path), true);
            return t;
        }

        Texture2D Emblem(string faction)
        {
            if (!emblems.TryGetValue(faction, out var t)) emblems[faction] = t = Load(uiDir, "emblem_" + faction);
            return t;
        }

        void Setup()
        {
            uiDir = Path.Combine(Application.streamingAssetsPath, "Data", "world", "ui");
            bannerFill = Load(uiDir, "banner_fill");
            bannerEdge = Load(uiDir, "banner_edge");
            bannerShadow = Load(uiDir, "banner_shadow");
            ribbon = Load(uiDir, "ribbon");
            var serif = GameFonts.Text;
            town = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleLeft, richText = false, clipping = TextClipping.Overflow, wordWrap = false };
            if (serif != null) town.font = serif;
            castle = new GUIStyle(town);
            village = new GUIStyle(town) { alignment = TextAnchor.MiddleCenter };
        }

        void Draw(Texture2D t, Rect r, Color c)
        {
            if (t == null) return;
            GUI.color = c;
            GUI.DrawTexture(r, t);
        }

        void DrawRibbon(Rect r, float alpha)
        {
            if (ribbon == null) return;
            GUI.color = new Color(1f, 1f, 1f, alpha);
            const float tipU = 196f / 256f;
            float tipW = (256f - 196f) * r.height / 48f;
            GUI.DrawTextureWithTexCoords(new Rect(r.x, r.y, r.width - tipW, r.height), ribbon, new Rect(0.02f, 0f, 0.5f, 1f));
            GUI.DrawTextureWithTexCoords(new Rect(r.xMax - tipW, r.y, tipW, r.height), ribbon, new Rect(tipU, 0f, 1f - tipU, 1f));
        }

        void Text(Rect r, string text, GUIStyle style, Color ink, float k)
        {
            GUI.color = Color.white;
            Paint(style, new Color(0f, 0f, 0f, ink.a * 0.85f));
            style.Draw(new Rect(r.x + 1.2f * k, r.y + 1.2f * k, r.width, r.height), text, false, false, false, false);
            Paint(style, ink);
            style.Draw(r, text, false, false, false, false);
        }

        struct Entry
        {
            public PlacedSettlement S;
            public float X, Y, Alpha, Depth;
            public int Rank;
        }

        readonly List<Entry> entries = new List<Entry>();
        readonly List<Rect> taken = new List<Rect>();

        static int Rank(PlacedSettlement s) => s.Data.capital ? 0 : s.Kind == SettlementKind.Town ? 1 : s.Kind == SettlementKind.Castle ? 2 : 3;

        bool Free(Rect r)
        {
            foreach (var t in taken)
                if (t.Overlaps(r)) return false;
            return true;
        }

        static void Paint(GUIStyle style, Color c)
        {
            style.normal.textColor = c;
            style.hover.textColor = c;
            style.active.textColor = c;
            style.focused.textColor = c;
        }

        void OnGUI()
        {
            var cam = Camera.main;
            if (cam == null || Settlements.Count == 0 || Event.current.type != EventType.Repaint) return;
            if (town == null) Setup();
            float k = Mathf.Max(1f, Screen.height / 720f);
            town.fontSize = Mathf.RoundToInt(17 * k);
            castle.fontSize = Mathf.RoundToInt(13 * k);
            village.fontSize = Mathf.RoundToInt(11.5f * k);
            var prev = GUI.color;
            Hovered = null;
            entries.Clear();
            taken.Clear();
            foreach (var s in Settlements)
            {
                float limit = s.Kind == SettlementKind.Town ? 2200f : s.Kind == SettlementKind.Castle ? 700f : 380f;
                var head = s.Position + Vector3.up * (s.Kind == SettlementKind.Town ? 9f : 6f);
                float d = Vector3.Distance(cam.transform.position, head);
                if (d > limit) continue;
                var sp = cam.WorldToScreenPoint(head);
                if (sp.z <= 0) continue;
                entries.Add(new Entry { S = s, X = sp.x, Y = Screen.height - sp.y, Alpha = Mathf.Clamp01((limit - d) / (limit * 0.25f)), Depth = d, Rank = Rank(s) });
            }
            entries.Sort((a, b) => a.Rank != b.Rank ? a.Rank.CompareTo(b.Rank) : a.Depth.CompareTo(b.Depth));
            foreach (var e in entries)
            {
                var s = e.S;
                float x = e.X, y = e.Y, alpha = e.Alpha;
                var field = Muted(WorldSettlements.ToColor(s.Faction.color, Color.gray));
                var trim = Color.Lerp(WorldSettlements.ToColor(s.Faction.trim, Color.white), Parchment, 0.55f);
                if (Mathf.Abs(trim.grayscale - field.grayscale) < 0.3f) trim = Parchment;
                var mouse = Event.current.mousePosition;
                if (s.Kind == SettlementKind.Village)
                {
                    var vs = village.CalcSize(new GUIContent(s.Data.name));
                    var vr = new Rect(x - vs.x / 2, y - vs.y / 2, vs.x, vs.y);
                    if (!Free(vr)) continue;
                    taken.Add(vr);
                    bool vhover = vr.Contains(mouse);
                    if (vhover) Hovered = s;
                    var vink = vhover ? new Color(1f, 0.9f, 0.68f) : Color.Lerp(Ink, field, 0.12f);
                    vink.a = alpha;
                    if (vhover)
                    {
                        GUI.color = new Color(field.r, field.g, field.b, 0.9f * alpha);
                        GUI.DrawTexture(new Rect(vr.x + 1f * k, vr.yMax - 1.5f * k, vr.width - 2f * k, Mathf.Max(1f, 1.4f * k)), Texture2D.whiteTexture);
                    }
                    Text(vr, s.Data.name, village, vink, k);
                    continue;
                }
                var style = s.Kind == SettlementKind.Town ? town : castle;
                style.fontStyle = s.Data.capital ? FontStyle.Bold : FontStyle.Normal;
                var size = style.CalcSize(new GUIContent(s.Data.name));
                float sh = (s.Kind == SettlementKind.Castle ? 28f : s.Data.capital ? 46f : 37f) * k;
                float sw = sh * 96f / 128f;
                float rh = Mathf.Max(size.y * 1.2f, sh * 0.55f);
                float bandW = sw * 0.5f + 6f * k + size.x + rh * 1.2f;
                Rect shield = default, band = default, box = default;
                bool placedOk = false;
                foreach (float dy in new[] { 0f, -1.15f, 1.15f, -2.3f })
                {
                    shield = new Rect(x - (sw * 0.5f + bandW) / 2f, y - sh * 0.62f + dy * sh, sw, sh);
                    band = new Rect(shield.center.x, shield.y + sh * 0.32f - rh / 2, bandW, rh);
                    box = new Rect(shield.x, shield.y, band.xMax - shield.x, sh);
                    if (!Free(box)) continue;
                    taken.Add(box);
                    placedOk = true;
                    break;
                }
                if (!placedOk && s.Kind == SettlementKind.Castle) continue;
                float textX = shield.xMax + 5f * k;
                bool hover = box.Contains(mouse);
                if (hover) Hovered = s;
                DrawRibbon(band, alpha * 0.85f);
                if (hover)
                {
                    DrawRibbon(band, alpha * 0.45f);
                    GUI.color = new Color(trim.r, trim.g, trim.b, 0.95f * alpha);
                    GUI.DrawTexture(new Rect(shield.xMax, band.yMax - 2f * k, band.width - sw * 0.5f - rh * 0.9f, Mathf.Max(1f, 1.6f * k)), Texture2D.whiteTexture);
                    float grow = sh * 0.06f;
                    shield = new Rect(shield.x - grow * 0.41f, shield.y - grow, sw + grow * 0.83f, sh + grow);
                }
                Draw(bannerShadow, new Rect(shield.x - shield.width * 0.06f, shield.y + shield.height * 0.03f, shield.width * 1.12f, shield.height * 1.06f), new Color(1f, 1f, 1f, (hover ? 0.6f : 0.45f) * alpha));
                Draw(bannerFill, shield, new Color(field.r, field.g, field.b, alpha));
                var edge = s.Data.capital ? new Color(0.72f, 0.6f, 0.38f) : Color.Lerp(field, Soot, 0.55f);
                if (hover) edge = Color.Lerp(edge, Parchment, 0.4f);
                Draw(bannerEdge, shield, new Color(edge.r, edge.g, edge.b, alpha));
                var em = Emblem(s.Faction.faction);
                float es = shield.width * 0.62f;
                Draw(em, new Rect(shield.center.x - es / 2, shield.y + shield.height * 0.2f, es, es), new Color(trim.r, trim.g, trim.b, 0.92f * alpha));
                var ink = hover ? new Color(1f, 0.88f, 0.55f) : Ink;
                ink.a = alpha;
                Text(new Rect(textX, band.y, size.x + 4f, band.height), s.Data.name, style, ink, k);
            }
            GUI.color = prev;
        }
    }
}
