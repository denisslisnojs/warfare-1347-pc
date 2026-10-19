using System;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.InputSystem;
using Warfare.Core;

namespace Warfare.Client
{
    public sealed class SettlementMenuItem
    {
        public string id;
        public string name;
        public string nameEn;
        public string capitalName;
        public string capitalNameEn;
        public string open;
    }

    public sealed class SettlementMenus
    {
        public SettlementMenuItem[] town = Array.Empty<SettlementMenuItem>();
        public SettlementMenuItem[] castle = Array.Empty<SettlementMenuItem>();
        public SettlementMenuItem[] village = Array.Empty<SettlementMenuItem>();
    }

    public sealed partial class SettlementScreen : MonoBehaviour
    {
        public WorldMap Map;
        public GameObject Party;
        public WorldParty Owner;
        public PlacedSettlement Current { get; private set; }
        public bool Open => Current != null;

        static readonly Color Ink = new Color(0.97f, 0.93f, 0.82f);
        static readonly Color Gold = new Color(0.78f, 0.62f, 0.32f);

        SettlementMenus menus;
        float openedAt;
        string message;
        GUIStyle title, kind, about, button, small, panelStyle, ribbonStyle;
        Texture2D panelTex, ribbon, shieldFill, shieldEdge, shieldShadow, divider;
        readonly System.Collections.Generic.Dictionary<string, Texture2D> emblems = new System.Collections.Generic.Dictionary<string, Texture2D>();
        string uiDir;

        void Start()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "settlement_menu.json");
            menus = (File.Exists(path) ? DataJson.Read<SettlementMenus>(File.ReadAllText(path)) : null) ?? new SettlementMenus();
            LoadMarket();
        }

        public void Enter(PlacedSettlement s)
        {
            if (Map == null || Map.Cam == null || s == null) return;
            Current = s;
            openedAt = Time.unscaledTime;
            message = null;
            CloseMarket();
            float r = WorldSettlements.FlattenRadius(s.Kind, s.Data.capital);
            float distance = r * 3.6f + 2f;
            Map.Cam.Showcase(s.Position + Vector3.up * (r * 0.15f), distance, 24f, distance * 0.2f, 3f);
            if (Map.Air != null) Map.Air.BlurBeyond(distance + r * 1.2f, distance + r * 6f, 1.4f);
            if (Map.Labels != null) Map.Labels.enabled = false;
            if (Party != null) Party.SetActive(false);
            Debug.Log($"[W1347] enter {s.Data.id} ({s.Kind}), camera {distance:0.0}, menu {Items(s).Length}");
        }

        public void Leave()
        {
            if (Current == null) return;
            Current = null;
            Map.Cam.EndShowcase();
            if (Map.Air != null) Map.Air.ClearBlur();
            if (Map.Labels != null) Map.Labels.enabled = true;
            if (Party != null) Party.SetActive(true);
        }

        void Update()
        {
            var kb = Keyboard.current;
            if (!Open || kb == null || !kb.escapeKey.wasPressedThisFrame) return;
            if (market && selectedGood != null) selectedGood = null;
            else if (market) CancelMarket();
            else Leave();
        }

        SettlementMenuItem[] Items(PlacedSettlement s) => (s.Kind switch
        {
            SettlementKind.Town => menus?.town,
            SettlementKind.Castle => menus?.castle,
            _ => menus?.village,
        }) ?? Array.Empty<SettlementMenuItem>();

        static string Label(SettlementMenuItem item, bool capital) => capital && !string.IsNullOrEmpty(item.capitalName) ? item.capitalName : item.name;

        static string KindName(PlacedSettlement s) => s.Kind switch
        {
            SettlementKind.Town => s.Data.capital ? "Столица" : "Город",
            SettlementKind.Castle => "Замок",
            _ => "Деревня",
        };

        static readonly Regex DesignNote = new Regex(@"\s*\((?:[^)]*?(?:добавлен|в лоре|лора|рабоч|по плану|добавлю))[^)]*\)");

        static string Sentence(string note)
        {
            if (string.IsNullOrEmpty(note)) return "";
            note = DesignNote.Replace(note, "").Trim();
            if (note.Length == 0) return "";
            string t = char.ToUpper(note[0]) + note.Substring(1);
            return t.EndsWith(".") ? t : t + ".";
        }

        string OwnerName(PlacedSettlement s)
        {
            if (string.IsNullOrEmpty(s.Data.owner) || Map == null) return null;
            foreach (var p in Map.Settlements)
                if (p.Data.id == s.Data.owner) return p.Data.name;
            return null;
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

        static Texture2D Plate(Color top, Color bottom, Color edge, Color inner)
        {
            const int n = 32;
            var t = new Texture2D(n, n, TextureFormat.RGBA32, false) { hideFlags = HideFlags.DontSave, wrapMode = TextureWrapMode.Clamp };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    int d = Mathf.Min(Mathf.Min(x, y), Mathf.Min(n - 1 - x, n - 1 - y));
                    px[y * n + x] = d < 2 ? edge : d < 3 ? inner : Color.Lerp(bottom, top, y / (n - 1f));
                }
            t.SetPixels(px);
            t.Apply();
            return t;
        }

        void Setup()
        {
            uiDir = Path.Combine(Application.streamingAssetsPath, "Data", "world", "ui");
            ribbon = Load(uiDir, "ribbon");
            shieldFill = Load(uiDir, "shield_fill");
            shieldEdge = Load(uiDir, "shield_edge");
            shieldShadow = Load(uiDir, "shield_shadow");
            var serif = GameFonts.Text;
            title = new GUIStyle(GUI.skin.label) { font = GameFonts.Heading, alignment = TextAnchor.MiddleCenter, clipping = TextClipping.Overflow, wordWrap = false };
            kind = new GUIStyle(title) { font = serif, fontStyle = FontStyle.Normal };
            kind.normal.textColor = new Color(0.93f, 0.78f, 0.47f);
            about = new GUIStyle(kind) { wordWrap = true, alignment = TextAnchor.UpperCenter };
            about.normal.textColor = new Color(Ink.r, Ink.g, Ink.b, 0.9f);
            small = new GUIStyle(about) { fontStyle = FontStyle.Italic };
            small.normal.textColor = new Color(0.93f, 0.78f, 0.47f, 0.9f);
            button = new GUIStyle(GUI.skin.button) { font = GameFonts.Button, alignment = TextAnchor.MiddleCenter, border = new RectOffset(4, 4, 4, 4), padding = new RectOffset(8, 8, 2, 2) };
            var edge = new Color(0.62f, 0.48f, 0.25f);
            var dark = new Color(0.05f, 0.035f, 0.025f);
            button.normal.background = Plate(new Color(0.16f, 0.12f, 0.085f), new Color(0.09f, 0.07f, 0.05f), edge, dark);
            button.hover.background = Plate(new Color(0.55f, 0.4f, 0.19f), new Color(0.33f, 0.22f, 0.1f), new Color(0.96f, 0.8f, 0.45f), dark);
            button.active.background = Plate(new Color(0.66f, 0.5f, 0.24f), new Color(0.42f, 0.29f, 0.13f), new Color(1f, 0.88f, 0.55f), dark);
            button.normal.textColor = Ink;
            button.hover.textColor = button.active.textColor = new Color(1f, 0.95f, 0.8f);
            string slicesPath = Path.Combine(uiDir, "ui_slices.json");
            var slices = File.Exists(slicesPath) ? DataJson.Read<System.Collections.Generic.Dictionary<string, int[]>>(File.ReadAllText(slicesPath)) : null;
            RectOffset Border(string id) => slices != null && slices.TryGetValue(id, out var b) && b.Length == 4 ? new RectOffset(b[0], b[2], b[1], b[3]) : new RectOffset(0, 0, 0, 0);
            var art = Load(uiDir, "ui_panel");
            if (art != null)
            {
                panelStyle = new GUIStyle { border = Border("ui_panel") };
                panelStyle.normal.background = art;
            }
            var plate = Load(uiDir, "ui_button");
            var lit = Load(uiDir, "ui_button_hover");
            if (plate != null && lit != null)
            {
                button.border = Border("ui_button");
                button.normal.background = plate;
                button.hover.background = button.active.background = lit;
                button.padding = new RectOffset(40, 40, 2, 2);
            }
            art = Load(uiDir, "ui_title");
            if (art != null)
            {
                ribbonStyle = new GUIStyle { border = Border("ui_title") };
                ribbonStyle.normal.background = art;
            }
            divider = Load(uiDir, "ui_divider");
            panelTex = new Texture2D(1, 2, TextureFormat.RGBA32, false) { hideFlags = HideFlags.DontSave, wrapMode = TextureWrapMode.Clamp };
            panelTex.SetPixels(new[] { new Color(0.06f, 0.045f, 0.035f, 0.95f), new Color(0.13f, 0.095f, 0.07f, 0.95f) });
            panelTex.Apply();
        }

        void Line(Rect r, Color c)
        {
            GUI.color = c;
            GUI.DrawTexture(r, Texture2D.whiteTexture);
        }

        void Frame(Rect r, float k)
        {
            float t = Mathf.Max(1f, 2f * k), i = Mathf.Max(1f, 1f * k), inset = 6f * k;
            var c = Gold;
            Line(new Rect(r.x, r.y, r.width, t), c);
            Line(new Rect(r.x, r.yMax - t, r.width, t), c);
            Line(new Rect(r.x, r.y, t, r.height), c);
            Line(new Rect(r.xMax - t, r.y, t, r.height), c);
            var c2 = new Color(c.r, c.g, c.b, 0.55f);
            var q = new Rect(r.x + inset, r.y + inset, r.width - inset * 2, r.height - inset * 2);
            Line(new Rect(q.x, q.y, q.width, i), c2);
            Line(new Rect(q.x, q.yMax - i, q.width, i), c2);
            Line(new Rect(q.x, q.y, i, q.height), c2);
            Line(new Rect(q.xMax - i, q.y, i, q.height), c2);
            float m = 14f * k;
            foreach (var p in new[] { new Vector2(q.x, q.y), new Vector2(q.xMax, q.y), new Vector2(q.x, q.yMax), new Vector2(q.xMax, q.yMax) })
            {
                var pivot = new Vector2(p.x, p.y);
                var keep = GUI.matrix;
                GUIUtility.RotateAroundPivot(45f, pivot);
                Line(new Rect(p.x - m * 0.28f, p.y - m * 0.28f, m * 0.56f, m * 0.56f), c);
                GUI.matrix = keep;
            }
        }

        void Ribbon(Rect r)
        {
            if (ribbon == null) return;
            GUI.color = Color.white;
            GUI.DrawTextureWithTexCoords(r, ribbon, new Rect(0.02f, 0f, 0.5f, 1f));
        }

        static void Paint(GUIStyle style, Color c)
        {
            style.normal.textColor = c;
            style.hover.textColor = c;
            style.active.textColor = c;
            style.focused.textColor = c;
        }

        void Shadowed(Rect r, string text, GUIStyle style, Color ink, float k)
        {
            GUI.color = Color.white;
            var keep = style.normal.textColor;
            Paint(style, new Color(0f, 0f, 0f, 0.85f * ink.a));
            GUI.Label(new Rect(r.x + 1.3f * k, r.y + 1.3f * k, r.width, r.height), text, style);
            Paint(style, ink);
            GUI.Label(r, text, style);
            Paint(style, keep);
        }

        void OnGUI()
        {
            var s = Current;
            if (s == null) return;
            if (title == null) Setup();
            GUI.depth = -20;
            float k = Mathf.Max(1f, Screen.height / 720f);
            title.fontSize = Mathf.RoundToInt(21 * k);
            kind.fontSize = Mathf.RoundToInt(13 * k);
            about.fontSize = Mathf.RoundToInt(13.5f * k);
            small.fontSize = Mathf.RoundToInt(12.5f * k);
            button.fontSize = Mathf.RoundToInt(16 * k);

            if (market)
            {
                DrawMarket(s, k);
                return;
            }
            float slide = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01((Time.unscaledTime - openedAt) / 0.4f));
            float w = Mathf.Min(Screen.width * 0.31f, 430f * k), h = Screen.height * 0.92f;
            var panel = new Rect(Screen.width * 0.025f - (1f - slide) * (w + Screen.width * 0.03f), Screen.height * 0.04f, w, h);
            var prev = GUI.color;
            GUI.color = Color.white;
            if (panelStyle != null) GUI.Box(panel, GUIContent.none, panelStyle);
            else
            {
                GUI.DrawTexture(panel, panelTex);
                Frame(panel, k);
            }

            var field = WorldSettlements.ToColor(s.Faction.color, Color.gray);
            var trim = WorldSettlements.ToColor(s.Faction.trim, Color.white);
            if (Mathf.Abs(trim.grayscale - field.grayscale) < 0.3f) trim = Color.Lerp(field, Color.black, 0.68f);
            float sh = 84f * k, sw = sh * 96f / 116f;
            var shield = new Rect(panel.center.x - sw / 2f, panel.y + 22f * k, sw, sh);
            var band = new Rect(panel.x + w * 0.07f, shield.yMax - 16f * k, w * 0.86f, 46f * k);
            if (ribbonStyle != null)
            {
                GUI.color = Color.white;
                GUI.Box(new Rect(band.x - w * 0.03f, band.y - 4f * k, band.width + w * 0.06f, band.height + 8f * k), GUIContent.none, ribbonStyle);
            }
            else Ribbon(band);
            GUI.color = new Color(1f, 1f, 1f, 0.6f);
            if (shieldShadow != null) GUI.DrawTexture(new Rect(shield.x - sw * 0.06f, shield.y + sh * 0.02f, sw * 1.12f, sh * 1.1f), shieldShadow);
            GUI.color = field;
            if (shieldFill != null) GUI.DrawTexture(shield, shieldFill);
            GUI.color = new Color(1f, 0.84f, 0.4f);
            if (shieldEdge != null) GUI.DrawTexture(shield, shieldEdge);
            var em = Emblem(s.Faction.faction);
            float es = sw * 0.68f;
            GUI.color = trim;
            if (em != null) GUI.DrawTexture(new Rect(shield.center.x - es / 2f, shield.y + sh * 0.13f, es, es), em);
            Shadowed(new Rect(band.x, band.y + 3f * k, band.width, band.height - 6f * k), s.Data.name.ToUpperInvariant(), title, Ink, k);

            float y = band.yMax + 8f * k, inner = w * 0.84f, x0 = panel.center.x - inner / 2f;
            Shadowed(new Rect(x0, y, inner, 20f * k), $"{KindName(s)} {s.Faction.nameOf ?? s.Faction.name}", kind, kind.normal.textColor, k);
            y += 22f * k;
            string owner = OwnerName(s);
            if (owner != null)
            {
                Shadowed(new Rect(x0, y, inner, 20f * k), "Под защитой: " + owner, kind, new Color(Ink.r, Ink.g, Ink.b, 0.75f), k);
                y += 20f * k;
            }
            y += 6f * k;
            string text = string.IsNullOrEmpty(s.Data.about) ? Sentence(s.Data.note) : s.Data.about;
            float th = about.CalcHeight(new GUIContent(text), inner);
            Shadowed(new Rect(x0, y, inner, th), text, about, about.normal.textColor, k);
            y += th + 12f * k;
            if (divider != null)
            {
                float dw = inner * 0.85f, dh = dw * divider.height / divider.width;
                GUI.color = Color.white;
                GUI.DrawTexture(new Rect(panel.center.x - dw / 2f, y - dh / 2f, dw, dh), divider);
            }
            else Line(new Rect(panel.center.x - inner * 0.3f, y, inner * 0.6f, Mathf.Max(1f, 1.2f * k)), new Color(Gold.r, Gold.g, Gold.b, 0.7f));
            y += 16f * k;

            float bh = 42f * k, gap = 9f * k;
            var leaveRect = new Rect(x0, panel.yMax - 26f * k - bh, inner, bh);
            GUI.color = Color.white;
            foreach (var item in Items(s))
            {
                bool leave = item.id == "leave";
                var r = leave ? leaveRect : new Rect(x0, y, inner, bh);
                if (!leave) y += bh + gap;
                if (GUI.Button(r, Label(item, s.Data.capital), button) && Time.unscaledTime - openedAt > 0.35f)
                {
                    if (leave)
                    {
                        Leave();
                        GUI.color = prev;
                        return;
                    }
                    if (item.open == "market")
                    {
                        OpenMarket(Label(item, s.Data.capital));
                        GUI.color = prev;
                        return;
                    }
                    message = "Сюда пока не пускают. Загляните позже.";
                }
            }
            if (!string.IsNullOrEmpty(message))
                Shadowed(new Rect(x0, leaveRect.y - 30f * k, inner, 22f * k), message, small, small.normal.textColor, k);
            GUI.color = prev;
        }
    }
}
