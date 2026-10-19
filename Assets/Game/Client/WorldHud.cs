using UnityEngine;
using Warfare.Core.World;

namespace Warfare.Client
{
    public sealed class WorldHud : MonoBehaviour
    {
        public WorldParty Party;

        static readonly string[] Months = { "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря" };
        static readonly Color Ink = new Color(0.97f, 0.93f, 0.82f);
        static readonly Color Gold = new Color(0.78f, 0.62f, 0.32f);

        GUIStyle date, small, hint, button, buttonOn, notice;
        Texture2D panelTex;

        static Texture2D Solid(Color c)
        {
            var t = new Texture2D(1, 1) { hideFlags = HideFlags.DontSave };
            t.SetPixel(0, 0, c);
            t.Apply();
            return t;
        }

        void Setup()
        {
            var serif = GameFonts.Text;
            date = new GUIStyle(GUI.skin.label) { font = serif, alignment = TextAnchor.MiddleLeft, clipping = TextClipping.Overflow, wordWrap = false };
            date.normal.textColor = Ink;
            small = new GUIStyle(date);
            small.normal.textColor = new Color(Ink.r, Ink.g, Ink.b, 0.75f);
            hint = new GUIStyle(small) { alignment = TextAnchor.MiddleCenter };
            notice = new GUIStyle(date) { alignment = TextAnchor.MiddleCenter };
            notice.normal.textColor = new Color(1f, 0.86f, 0.5f);
            button = new GUIStyle(GUI.skin.button) { font = GameFonts.Button, alignment = TextAnchor.MiddleCenter, border = new RectOffset(0, 0, 0, 0) };
            button.normal.background = Solid(new Color(0.17f, 0.14f, 0.1f, 0.95f));
            button.hover.background = Solid(new Color(0.27f, 0.21f, 0.14f, 0.95f));
            button.active.background = Solid(new Color(0.42f, 0.32f, 0.17f, 0.95f));
            button.normal.textColor = button.hover.textColor = button.active.textColor = Ink;
            buttonOn = new GUIStyle(button);
            buttonOn.normal.background = buttonOn.hover.background = Solid(new Color(0.6f, 0.46f, 0.2f, 0.98f));
            buttonOn.normal.textColor = buttonOn.hover.textColor = new Color(0.1f, 0.07f, 0.04f);
            panelTex = Solid(new Color(0.07f, 0.06f, 0.05f, 0.82f));
        }

        static string Cap(string t) => string.IsNullOrEmpty(t) ? t : char.ToUpper(t[0]) + t.Substring(1);

        static string PartName(DayPart p) => p switch
        {
            DayPart.Morning => "утро",
            DayPart.Day => "день",
            DayPart.Evening => "вечер",
            _ => "ночь",
        };

        void OnGUI()
        {
            if (Party == null || Party.Travel == null || Party.InSettlement) return;
            GUI.depth = -10;
            if (date == null) Setup();
            float k = Mathf.Max(1f, Screen.height / 720f);
            date.fontSize = Mathf.RoundToInt(20 * k);
            small.fontSize = Mathf.RoundToInt(14 * k);
            hint.fontSize = Mathf.RoundToInt(13 * k);
            notice.fontSize = Mathf.RoundToInt(17 * k);
            button.fontSize = buttonOn.fontSize = Mathf.RoundToInt(15 * k);
            var travel = Party.Travel;
            var speeds = travel.Rules.Speeds;
            float bw = 46f * k, bh = 30f * k, gap = 6f * k, waitW = 96f * k;
            float w = 250f * k + speeds.Length * (bw + gap) + waitW + 16f * k, h = 62f * k;
            var panel = new Rect((Screen.width - w) / 2f, 10f * k, w, h);
            var hintRect = new Rect(panel.x - 60f * k, panel.yMax + 4f * k, w + 120f * k, 18f * k);
            var followRect = new Rect((Screen.width - 150f * k) / 2f, hintRect.yMax + 4f * k, 150f * k, 28f * k);
            Party.HudRect = Rect.MinMaxRect(panel.xMin, panel.yMin, panel.xMax, Party.Following ? panel.yMax : followRect.yMax);
            GUI.DrawTexture(panel, panelTex);
            GUI.color = Gold;
            GUI.DrawTexture(new Rect(panel.x, panel.y, panel.width, Mathf.Max(1f, 1.5f * k)), Texture2D.whiteTexture);
            GUI.DrawTexture(new Rect(panel.x, panel.yMax - Mathf.Max(1f, 1.5f * k), panel.width, Mathf.Max(1f, 1.5f * k)), Texture2D.whiteTexture);
            GUI.color = Color.white;
            var (day, month, year) = travel.Clock.Date;
            string state = travel.Party.Moving ? "отряд в пути" : travel.Waiting ? "привал" : "отряд стоит";
            GUI.Label(new Rect(panel.x + 16f * k, panel.y + 6f * k, 230f * k, 28f * k), $"{day} {Months[month]} {year}", date);
            GUI.Label(new Rect(panel.x + 16f * k, panel.y + 34f * k, 230f * k, 22f * k), $"{Cap(PartName(travel.Clock.Part))}, {state}", small);
            float x = panel.x + 250f * k, y = panel.y + (h - bh) / 2f;
            foreach (int s in speeds)
            {
                if (GUI.Button(new Rect(x, y, bw, bh), "×" + s, travel.Clock.Speed == s ? buttonOn : button)) travel.Clock.Speed = s;
                x += bw + gap;
            }
            if (GUI.Button(new Rect(x, y, waitW, bh), travel.Waiting ? "Ждём" : "Ждать", travel.Waiting ? buttonOn : button)) Party.Wait();
            GUI.color = new Color(1f, 1f, 1f, 0.7f);
            GUI.DrawTexture(hintRect, panelTex);
            GUI.color = Color.white;
            GUI.Label(hintRect, "ЛКМ  идти, можно держать        Пробел  ждать        + и −  скорость        F  к отряду", hint);
            if (!Party.Following && GUI.Button(followRect, "К отряду (F)", button)) Party.FollowParty();
            float left = Party.NoticeUntil - Time.unscaledTime;
            if (left > 0f && !string.IsNullOrEmpty(Party.Notice))
            {
                float a = Mathf.Clamp01(left / 0.6f);
                var r = new Rect((Screen.width - 420f * k) / 2f, (Party.Following ? hintRect.yMax : followRect.yMax) + 8f * k, 420f * k, 30f * k);
                GUI.color = new Color(1f, 1f, 1f, a);
                GUI.DrawTexture(r, panelTex);
                GUI.Label(r, Party.Notice, notice);
                GUI.color = Color.white;
            }
        }
    }
}
