using System.Collections.Generic;
using UnityEngine;
using Warfare.Core.Battle;

namespace Warfare.Client
{
    public sealed class BattleHud : MonoBehaviour
    {
        static readonly Color Ink = new Color(1f, 0.86f, 0.55f);
        static readonly Color Dim = new Color(0.75f, 0.7f, 0.6f);
        static readonly Color Panel = new Color(0.07f, 0.06f, 0.05f, 0.82f);

        BattleController ctl;
        Texture2D white;
        GUIStyle label;
        GUIStyle small;
        GUIStyle title;
        GUIStyle button;
        float scale = 1f;
        readonly List<Rect> uiRects = new List<Rect>();

        public bool IsOverUi(Vector2 screen)
        {
            var p = new Vector2(screen.x, Screen.height - screen.y);
            foreach (var r in uiRects)
                if (r.Contains(p)) return true;
            return false;
        }

        void Mark(Rect r)
        {
            if (Event.current.type == EventType.Repaint) uiRects.Add(new Rect(r.x * scale, r.y * scale, r.width * scale, r.height * scale));
        }

        void Awake()
        {
            ctl = GetComponent<BattleController>();
            white = Texture2D.whiteTexture;
        }

        void Styles()
        {
            if (label != null) return;
            label = new GUIStyle(GUI.skin.label) { fontSize = 18, richText = true };
            label.normal.textColor = Ink;
            small = new GUIStyle(label) { fontSize = 15 };
            small.normal.textColor = Dim;
            title = new GUIStyle(label) { fontSize = 44, alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
            button = new GUIStyle(GUI.skin.button) { fontSize = 20 };
        }

        void OnGUI()
        {
            if (ctl == null) return;
            Styles();
            if (!string.IsNullOrEmpty(ctl.LoadError))
            {
                GUI.Label(new Rect(20, 20, Screen.width - 40, 200), "Ошибка загрузки данных: " + ctl.LoadError, label);
                return;
            }
            var sim = ctl.Sim;
            if (sim == null) return;

            if (Event.current.type == EventType.Repaint) uiRects.Clear();
            HealthBars(sim);

            scale = Mathf.Max(0.6f, Screen.height / 1080f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
            float w = Screen.width / scale;
            float h = Screen.height / scale;

            MoraleBars(sim, w);
            Groups(sim, h);
            MenuHint(w, h);
            Toast(w, h);
            Help(w);
            if (ctl.Deploying) Deploy(w);
            if (ctl.HeroView && Cursor.lockState == CursorLockMode.Locked && !sim.Finished) Crosshair(w, h);
            if (ctl.Paused && !sim.Finished) GUI.Label(new Rect(0, 120, w, 60), "<b>ПАУЗА</b>", Centered(title, 34));
            if (sim.Finished) Result(sim, w, h);
            GUI.matrix = Matrix4x4.identity;
        }

        static GUIStyle Centered(GUIStyle s, int size)
        {
            return new GUIStyle(s) { alignment = TextAnchor.MiddleCenter, fontSize = size };
        }

        void Box(Rect r, Color c)
        {
            var old = GUI.color;
            GUI.color = c;
            GUI.DrawTexture(r, white);
            GUI.color = old;
        }

        void MoraleBars(BattleSim sim, float w)
        {
            float bw = 360, bh = 18, y = 16;
            for (int side = 0; side < 2; side++)
            {
                float x = side == 0 ? w / 2 - bw - 20 : w / 2 + 20;
                Box(new Rect(x - 6, y - 6, bw + 12, bh + 40), Panel);
                Box(new Rect(x, y, bw, bh), new Color(0.2f, 0.18f, 0.15f));
                float k = sim.MaxMorale[side] <= 0 ? 0 : sim.Morale[side] / sim.MaxMorale[side];
                var c = BattleView.SideColors[side];
                float fill = bw * Mathf.Clamp01(k);
                Box(side == 0 ? new Rect(x + bw - fill, y, fill, bh) : new Rect(x, y, fill, bh), c);
                int alive = sim.ActiveCount(side) + sim.Reserves[side].Count;
                string name = sim.Armies[side].Name;
                string text = $"{name}: {alive}   боевой дух {Mathf.CeilToInt(sim.Morale[side])}";
                if (sim.Routed[side]) text += "   <color=#ff9070>бегут!</color>";
                var st = new GUIStyle(small) { alignment = side == 0 ? TextAnchor.UpperRight : TextAnchor.UpperLeft };
                GUI.Label(new Rect(x, y + bh + 2, bw, 24), text, st);
            }
            int t = Mathf.FloorToInt(sim.Time);
            GUI.Label(new Rect(w / 2 - 20, y, 40, 24), $"{t / 60}:{t % 60:00}", Centered(small, 15));
        }

        void Groups(BattleSim sim, float h)
        {
            int side = ctl.PlayerSide;
            float x = 16, rowH = 30, width = 330;
            float y = h - 16 - rowH * 4 - 36;
            Box(new Rect(x - 6, y - 6, width + 12, rowH * 4 + 42), Panel);
            Mark(new Rect(x - 6, y - 6, width + 12, rowH * 4 + 42));
            GUI.Label(new Rect(x, y, width, 26), $"Отряды  <color=#c8b890>(выбрано: {ctl.SelectionName()})</color>", small);
            y += 30;
            foreach (var g in BattleRules.AllGroups)
            {
                int n = sim.GroupCount(side, g);
                bool sel = ctl.Selected[(int)g];
                if (sel) Box(new Rect(x - 2, y, width + 4, rowH - 2), new Color(1f, 0.8f, 0.3f, 0.16f));
                string order = n > 0 ? BattleController.OrderName(sim.OrderOf(side, g)) : "никого не осталось";
                string color = n > 0 ? "" : "<color=#777060>";
                string end = n > 0 ? "" : "</color>";
                GUI.Label(new Rect(x + 4, y + 2, width, rowH), $"{color}<b>{(int)g + 1}</b>  {BattleController.GroupName(g)}{(n > 0 ? $" ({n})" : "")}, {order}{end}", label);
                y += rowH;
            }
        }

        void MenuHint(float w, float h)
        {
            string text = ctl.Menu switch
            {
                OrderMenu.Movement => "<b>Движение</b>     F1 стоять здесь   F2 за мной   F3 в атаку   F4 стоять на месте   F5 отступить   F6 вперёд на 10 шагов   F7 назад на 10 шагов   Esc назад",
                OrderMenu.Formation => "<b>Строй</b>     пока не готов   Esc назад",
                OrderMenu.Fire => "<b>Стрельба</b>     пока не готова   Esc назад",
                _ => "1-4 выбрать отряд, с Shift добавить   0 все отряды      F1 движение   F2 строй   F3 стрельба",
            };
            float bw = Mathf.Min(w - 380, 1180);
            float x = (w - bw) / 2 + 170;
            Box(new Rect(x, h - 56, bw, 40), Panel);
            Mark(new Rect(x, h - 56, bw, 40));
            GUI.Label(new Rect(x + 12, h - 50, bw - 24, 30), text, ctl.Menu == OrderMenu.None ? small : label);
        }

        void Toast(float w, float h)
        {
            if (string.IsNullOrEmpty(ctl.Toast) || Time.unscaledTime > ctl.ToastUntil) return;
            GUI.Label(new Rect(0, h - 110, w, 40), ctl.Toast, Centered(label, 22));
        }

        void Help(float w)
        {
            string text = ctl.Deploying
                ? "WASD камера   колесо приближение   Q и E поворот"
                : ctl.HeroView
                    ? "WASD идти   курсор взгляд   ЛКМ удар   ПКМ блок\nQ и E поворот камеры   колесо приближение   Tab вид сверху   Пробел пауза"
                    : "WASD камера   колесо приближение   Q и E поворот\nTab к герою   Пробел пауза";
            GUI.Label(new Rect(w - 460, 84, 444, 80), text, new GUIStyle(small) { alignment = TextAnchor.UpperRight, fontSize = 13 });
        }

        void Deploy(float w)
        {
            var panel = new Rect(w / 2 - 330, 78, 660, 104);
            Box(panel, Panel);
            Mark(panel);
            GUI.Label(new Rect(panel.x, panel.y + 6, panel.width, 30), "<b>Расстановка войск</b>", Centered(label, 22));
            GUI.Label(new Rect(panel.x + 10, panel.y + 34, panel.width - 20, 24), "Выберите отряд клавишами 1-4 и щёлкните по светлой полосе поля, чтобы поставить его туда", Centered(small, 15));
            if (GUI.Button(new Rect(panel.x + panel.width / 2 - 110, panel.y + 60, 220, 36), "К бою! (Enter)", button)) ctl.StartBattle();
        }

        void Crosshair(float w, float h)
        {
            Box(new Rect(w / 2 - 2, h / 2 - 2, 4, 4), new Color(1f, 0.95f, 0.8f, 0.9f));
        }

        void Result(BattleSim sim, float w, float h)
        {
            int me = ctl.PlayerSide;
            bool won = sim.Winner == me;
            var r = new Rect(w / 2 - 300, h / 2 - 170, 600, 340);
            Mark(r);
            Box(r, new Color(0.05f, 0.04f, 0.03f, 0.92f));
            GUI.Label(new Rect(r.x, r.y + 20, r.width, 60), won ? "Победа!" : "Поражение", title);
            var mine = sim.Summary(me);
            var theirs = sim.Summary(1 - me);
            string lines = $"Ваши потери: {mine.Dead} из {mine.Dead + mine.Survived}{(mine.HeroDead ? ", герой пал" : "")}\n" +
                           $"Потери врага: {theirs.Dead} из {theirs.Dead + theirs.Survived}\n" +
                           $"Бой длился {Mathf.FloorToInt(sim.Time / 60)}:{Mathf.FloorToInt(sim.Time % 60):00}";
            GUI.Label(new Rect(r.x + 40, r.y + 100, r.width - 80, 120), lines, Centered(label, 22));
            if (GUI.Button(new Rect(r.x + 60, r.y + 250, 220, 50), "Новый бой", button)) ctl.NewBattle();
            if (GUI.Button(new Rect(r.x + 320, r.y + 250, 220, 50), "Тот же бой", button)) ctl.Restart();
        }

        void HealthBars(BattleSim sim)
        {
            var cam = Camera.main;
            if (cam == null) return;
            foreach (var u in sim.Units)
            {
                if (!u.Alive || u.Hp >= u.MaxHp) continue;
                var world = BattleView.ToWorld(u.Pos, u.Troop.IsCavalry ? 3.5f : 2.6f);
                var sp = cam.WorldToScreenPoint(world);
                if (sp.z <= 0 || sp.z > 90f) continue;
                float bw = Mathf.Clamp(600f / sp.z, 14f, 48f);
                float x = sp.x - bw / 2, y = Screen.height - sp.y;
                Box(new Rect(x - 1, y - 1, bw + 2, 6), new Color(0, 0, 0, 0.7f));
                Box(new Rect(x, y, bw * u.HpFraction, 4), u.Side == ctl.PlayerSide ? new Color(0.4f, 0.9f, 0.4f) : new Color(0.95f, 0.35f, 0.3f));
            }
        }
    }
}
