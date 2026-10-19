using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using Warfare.Core;
using Warfare.Core.Battle;

namespace Warfare.Client
{
    public enum OrderMenu { None, Movement, Formation, Fire }

    [Serializable]
    public sealed class StackConfig
    {
        public string TroopId;
        public int Count;
    }

    [Serializable]
    public sealed class ArmyConfig
    {
        public string Name = "Армия";
        public string Culture = "aurelia";
        public string HeroTroopId = "";
        public float HeroHpMultiplier = 3f;
        public Formation Formation = Formation.Classic;
        public List<StackConfig> Troops = new List<StackConfig>();
    }

    public sealed class BattleController : MonoBehaviour
    {
        public const float StepDt = 1f / 30f;

        public ArmyConfig Blue = new ArmyConfig
        {
            Name = "Синие",
            Culture = "aurelia",
            HeroTroopId = "aurelia_i3m",
            Troops = new List<StackConfig>
            {
                new StackConfig { TroopId = "aurelia_i3m", Count = 12 },
                new StackConfig { TroopId = "aurelia_i3r", Count = 8 },
                new StackConfig { TroopId = "aurelia_c3m", Count = 6 },
            },
        };

        public ArmyConfig Red = new ArmyConfig
        {
            Name = "Красные",
            Culture = "nordmark",
            Troops = new List<StackConfig>
            {
                new StackConfig { TroopId = "nordmark_i3m", Count = 14 },
                new StackConfig { TroopId = "nordmark_i3r", Count = 8 },
                new StackConfig { TroopId = "nordmark_c3m", Count = 6 },
            },
        };

        public uint Seed;
        public string MapId = "village_fields";

        public BattleSim Sim { get; private set; }
        public TroopCatalog Troops { get; private set; }
        public bool Paused { get; private set; }
        public OrderMenu Menu { get; private set; }
        public readonly bool[] Selected = { true, true, true, true };
        public string Toast { get; private set; }
        public float ToastUntil { get; private set; }
        public string LoadError { get; private set; }
        public bool HeroView { get; private set; }
        public bool Deploying => Sim != null && Sim.Deploying;
        public int PlayerSide => Sim?.PlayerSide ?? 0;

        BattleView view;
        BattleHud hud;
        RtsCamera rts;
        HeroCamera heroCam;
        GameObject deployZone;
        float accumulator;
        uint lastSeed;
        bool heroWasActive;

        void Start()
        {
            view = GetComponent<BattleView>();
            if (view == null) view = gameObject.AddComponent<BattleView>();
            hud = GetComponent<BattleHud>();
            if (hud == null) hud = gameObject.AddComponent<BattleHud>();
            var cam = Camera.main;
            if (cam != null)
            {
                cam.fieldOfView = 35f;
                cam.nearClipPlane = 0.5f;
                rts = cam.GetComponent<RtsCamera>();
                if (rts == null) rts = cam.gameObject.AddComponent<RtsCamera>();
                heroCam = cam.GetComponent<HeroCamera>();
                if (heroCam == null) heroCam = cam.gameObject.AddComponent<HeroCamera>();
                heroCam.enabled = false;
            }
            CreateGround();
            try
            {
                var path = Path.Combine(Application.streamingAssetsPath, "Data", "troops.json");
                Troops = TroopCatalog.FromJson(File.ReadAllText(path));
            }
            catch (Exception e)
            {
                LoadError = e.Message;
                Debug.LogException(e);
                return;
            }
            NewBattle(Seed);
        }

        public void NewBattle(uint seed = 0)
        {
            if (Troops == null) return;
            if (seed == 0) seed = (uint)UnityEngine.Random.Range(1, int.MaxValue);
            lastSeed = seed;
            try
            {
                Sim = new BattleSim(Build(Blue), Build(Red), Troops, new BattleOptions { Seed = seed, Deployment = true, ManualHero = true });
            }
            catch (Exception e)
            {
                LoadError = e.Message;
                Debug.LogException(e);
                return;
            }
            LoadError = null;
            accumulator = 0;
            Paused = false;
            Menu = OrderMenu.None;
            heroWasActive = false;
            for (int i = 0; i < Selected.Length; i++) Selected[i] = true;
            view.Bind(Sim);
            SetHeroView(false);
            if (deployZone != null) deployZone.SetActive(true);
            if (rts != null && Sim.TryCenter(0, out var c)) rts.LookAt(BattleView.ToWorld(c) + new Vector3(14f, 0f, 0f), 90f, 40f);
            Show("Расставьте войска и нажмите Enter");
            Debug.Log($"Battle seed {seed}");
        }

        public void Restart() => NewBattle(lastSeed);

        public void StartBattle()
        {
            if (Sim == null || !Sim.Deploying) return;
            Sim.Begin();
            if (deployZone != null) deployZone.SetActive(false);
            Menu = OrderMenu.None;
            heroWasActive = Sim.HeroManualActive;
            if (heroWasActive)
            {
                SetHeroView(true);
                Show("В бой! ЛКМ удар, ПКМ блок, Tab вид сверху");
            }
            else Show("В бой!");
        }

        ArmyDef Build(ArmyConfig cfg)
        {
            var army = new ArmyDef { Name = cfg.Name, Culture = cfg.Culture, Formation = cfg.Formation };
            foreach (var s in cfg.Troops)
                if (!string.IsNullOrEmpty(s.TroopId) && s.Count > 0) army.Troops.Add(new ArmyStack(s.TroopId, s.Count));
            if (!string.IsNullOrEmpty(cfg.HeroTroopId))
            {
                var hero = Troops.Get(cfg.HeroTroopId).Clone();
                hero.Name = "Герой";
                hero.Hp *= cfg.HeroHpMultiplier;
                army.Hero = hero;
            }
            return army;
        }

        void SetHeroView(bool on)
        {
            var hero = Sim?.Hero(PlayerSide);
            var target = hero != null ? view.RootOf(hero.Uid) : null;
            HeroView = on && target != null;
            if (heroCam != null)
            {
                heroCam.Target = target;
                heroCam.enabled = HeroView;
                if (HeroView) heroCam.Snap(PlayerSide == 0 ? 0f : 180f);
            }
            if (rts != null)
            {
                rts.enabled = !HeroView;
                if (!HeroView && hero != null && hero.Alive && Sim != null && !Sim.Deploying) rts.LookAt(BattleView.ToWorld(hero.Pos), heroCam != null ? heroCam.Yaw : 90f, 45f);
            }
            LockCursor(false);
        }

        static void LockCursor(bool locked)
        {
            Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !locked;
        }

        void Update()
        {
            if (Sim == null) return;
            HandleInput();
            if (Sim.Deploying) DeployInput();
            else HeroControl();

            if (!Paused)
            {
                accumulator += Mathf.Min(Time.deltaTime, 0.25f);
                while (accumulator >= StepDt)
                {
                    Sim.Step(StepDt);
                    view.AfterStep();
                    accumulator -= StepDt;
                }
            }
            view.Render(Paused ? 1f : accumulator / StepDt, Selected, PlayerSide, Paused);

            if (heroWasActive && !Sim.HeroManualActive)
            {
                heroWasActive = false;
                SetHeroView(false);
                if (!Sim.Finished) Show("Герой пал. Командуйте войском с высоты");
            }
            if (Sim.Finished && Cursor.lockState == CursorLockMode.Locked) LockCursor(false);
        }

        void DeployInput()
        {
            var kb = Keyboard.current;
            var mouse = Mouse.current;
            if (kb != null && (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame))
            {
                StartBattle();
                return;
            }
            if (mouse == null || !mouse.leftButton.wasPressedThisFrame) return;
            var screen = mouse.position.ReadValue();
            if (hud != null && hud.IsOverUi(screen)) return;
            var point = MouseGround(out bool hit);
            if (!hit) return;
            var groups = SelectedGroups();
            if (groups.Count == 0) return;
            Sim.PlaceGroups(PlayerSide, groups, point);
            view.AfterStep();
            Show($"{Cap(SelectionName())}: сюда");
        }

        void HeroControl()
        {
            var input = default(HeroInput);
            var kb = Keyboard.current;
            var mouse = Mouse.current;
            var hero = Sim.Hero(PlayerSide);
            if (HeroView && heroCam != null && kb != null && mouse != null && !Sim.Finished && hero != null)
            {
                var f = heroCam.FlatForward;
                var r = new Vector2(f.y, -f.x);
                Vector2 m = Vector2.zero;
                if (kb.wKey.isPressed || kb.upArrowKey.isPressed) m += f;
                if (kb.sKey.isPressed || kb.downArrowKey.isPressed) m -= f;
                if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) m += r;
                if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) m -= r;
                if (m.sqrMagnitude > 1f) m.Normalize();
                input.Move = new Vec2(m.x, m.y);
                var aim = MouseGround(out _) - hero.Pos;
                input.Aim = aim.LengthSq > 0.04f ? aim.Normalized : hero.Facing;
                bool overUi = hud != null && hud.IsOverUi(mouse.position.ReadValue());
                input.Attack = mouse.leftButton.isPressed && !overUi;
                input.Block = mouse.rightButton.isPressed && !overUi;
            }
            Sim.HeroInput = input;
        }

        void HandleInput()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.spaceKey.wasPressedThisFrame) Paused = !Paused;
            if (kb.escapeKey.wasPressedThisFrame || kb.backspaceKey.wasPressedThisFrame)
            {
                if (Menu != OrderMenu.None) Menu = OrderMenu.None;
            }
            if (kb.tabKey.wasPressedThisFrame && !Sim.Deploying && Sim.HeroManualActive)
            {
                SetHeroView(!HeroView);
                Show(HeroView ? "Вид от героя" : "Вид сверху. Герой ждёт, Tab вернёт к нему");
            }

            bool shift = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
            if (kb.digit0Key.wasPressedThisFrame || kb.numpad0Key.wasPressedThisFrame) SelectAll();
            if (kb.digit1Key.wasPressedThisFrame || kb.numpad1Key.wasPressedThisFrame) Select(Group.Hero, shift);
            if (kb.digit2Key.wasPressedThisFrame || kb.numpad2Key.wasPressedThisFrame) Select(Group.Infantry, shift);
            if (kb.digit3Key.wasPressedThisFrame || kb.numpad3Key.wasPressedThisFrame) Select(Group.Ranged, shift);
            if (kb.digit4Key.wasPressedThisFrame || kb.numpad4Key.wasPressedThisFrame) Select(Group.Cavalry, shift);

            int f = 0;
            if (kb.f1Key.wasPressedThisFrame) f = 1;
            else if (kb.f2Key.wasPressedThisFrame) f = 2;
            else if (kb.f3Key.wasPressedThisFrame) f = 3;
            else if (kb.f4Key.wasPressedThisFrame) f = 4;
            else if (kb.f5Key.wasPressedThisFrame) f = 5;
            else if (kb.f6Key.wasPressedThisFrame) f = 6;
            else if (kb.f7Key.wasPressedThisFrame) f = 7;
            if (f > 0 && !Sim.Deploying) FunctionKey(f);
        }

        void SelectAll()
        {
            for (int i = 0; i < Selected.Length; i++) Selected[i] = true;
            Show("Выбраны все отряды");
        }

        void Select(Group g, bool add)
        {
            if (add) Selected[(int)g] = !Selected[(int)g];
            else
                for (int i = 0; i < Selected.Length; i++) Selected[i] = i == (int)g;
            Show("Выбрано: " + SelectionName());
        }

        public static string GroupName(Group g) => g switch
        {
            Group.Hero => "Герой",
            Group.Infantry => "Пехота",
            Group.Ranged => "Стрелки",
            _ => "Конница",
        };

        public static string OrderName(Order o) => o switch
        {
            Order.Attack => "в атаку",
            Order.Hold => "стоят",
            Order.Follow => "за героем",
            _ => "отступают",
        };

        public string SelectionName()
        {
            var names = new List<string>();
            foreach (var g in BattleRules.AllGroups)
                if (Selected[(int)g]) names.Add(GroupName(g).ToLowerInvariant());
            if (names.Count == 4) return "все";
            return names.Count == 0 ? "никто" : string.Join(", ", names);
        }

        List<Group> SelectedGroups()
        {
            var list = new List<Group>();
            foreach (var g in BattleRules.AllGroups)
            {
                if (!Selected[(int)g] || Sim.GroupCount(PlayerSide, g) == 0) continue;
                if (g == Group.Hero && Sim.HeroManualActive && !Sim.Deploying) continue;
                list.Add(g);
            }
            return list;
        }

        void FunctionKey(int f)
        {
            switch (Menu)
            {
                case OrderMenu.None:
                    Menu = f == 1 ? OrderMenu.Movement : f == 2 ? OrderMenu.Formation : f == 3 ? OrderMenu.Fire : OrderMenu.None;
                    return;
                case OrderMenu.Formation:
                case OrderMenu.Fire:
                    Show("Строи и стрельба появятся на следующем шаге");
                    Menu = OrderMenu.None;
                    return;
            }

            var groups = SelectedGroups();
            if (groups.Count == 0)
            {
                Show("Никто не выбран");
                Menu = OrderMenu.None;
                return;
            }
            int side = PlayerSide;
            string who = Cap(SelectionName());
            switch (f)
            {
                case 1:
                    var point = MouseGround(out bool hit);
                    if (!hit)
                    {
                        var hero = Sim.Hero(side);
                        if (hero != null && hero.Alive) point = hero.Pos;
                        else if (!Sim.TryCenter(side, out point)) break;
                    }
                    Sim.HoldAt(side, groups, point);
                    Show($"{who}: стоять здесь");
                    break;
                case 2:
                    if (!Sim.HeroManualActive)
                    {
                        Show("Героя нет на поле, вести войско некому");
                        break;
                    }
                    foreach (var g in groups) Sim.SetOrder(side, g, Order.Follow);
                    Show($"{who}: за мной!");
                    break;
                case 3:
                    foreach (var g in groups) Sim.SetOrder(side, g, Order.Attack);
                    Show($"{who}: в атаку!");
                    break;
                case 4:
                    foreach (var g in groups) Sim.HoldInPlace(side, g);
                    Show($"{who}: стоять на месте");
                    break;
                case 5:
                    foreach (var g in groups) Sim.SetOrder(side, g, Order.Retreat);
                    Show($"{who}: отступить с поля");
                    break;
                case 6:
                    foreach (var g in groups) Sim.Advance(side, g, BattleRules.AdvanceStep);
                    Show($"{who}: вперёд на 10 шагов");
                    break;
                case 7:
                    foreach (var g in groups) Sim.Advance(side, g, -BattleRules.AdvanceStep);
                    Show($"{who}: назад на 10 шагов");
                    break;
            }
            Menu = OrderMenu.None;
        }

        static string Cap(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpperInvariant(s[0]) + s.Substring(1);

        Vec2 MouseGround(out bool hit)
        {
            hit = false;
            var cam = Camera.main;
            var mouse = Mouse.current;
            if (cam == null) return Vec2.Zero;
            Vector2 screen = Cursor.lockState == CursorLockMode.Locked || mouse == null
                ? new Vector2(Screen.width / 2f, Screen.height / 2f)
                : mouse.position.ReadValue();
            var ray = cam.ScreenPointToRay(screen);
            var plane = new Plane(Vector3.up, Vector3.zero);
            if (!plane.Raycast(ray, out float d)) return Vec2.Zero;
            var p = ray.GetPoint(d);
            hit = Mathf.Abs(p.x) <= BattleRules.FieldLength / 2f && Mathf.Abs(p.z) <= BattleRules.FieldWidth / 2f;
            return new Vec2(p.x, p.z);
        }

        public void Show(string text)
        {
            Toast = text;
            ToastUntil = Time.unscaledTime + 2.5f;
        }

        void CreateGround()
        {
            MapData map = null;
            try
            {
                if (!string.IsNullOrEmpty(MapId)) map = BattleMap.Load(MapId);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
            if (map != null)
            {
                var probe = GameObject.CreatePrimitive(PrimitiveType.Plane);
                var template = probe.GetComponent<Renderer>().sharedMaterial;
                BattleMap.Build(map, template, out int missing);
                Destroy(probe);
                if (missing > 0) Debug.LogWarning($"[W1347] map {MapId}: {missing} props without a model");
                CreateDeployZone();
                return;
            }
            var outer = GameObject.CreatePrimitive(PrimitiveType.Plane);
            outer.name = "Ground";
            outer.transform.localScale = new Vector3((BattleRules.FieldLength + 200f) / 10f, 1f, (BattleRules.FieldWidth + 200f) / 10f);
            Tint(outer, new Color(0.33f, 0.45f, 0.22f));
            var field = GameObject.CreatePrimitive(PrimitiveType.Plane);
            field.name = "Field";
            field.transform.position = new Vector3(0f, 0.01f, 0f);
            field.transform.localScale = new Vector3(BattleRules.FieldLength / 10f, 1f, BattleRules.FieldWidth / 10f);
            Tint(field, new Color(0.42f, 0.55f, 0.27f));
            foreach (var go in new[] { outer, field })
            {
                var col = go.GetComponent<Collider>();
                if (col != null) Destroy(col);
            }
            CreateDeployZone();
        }

        void CreateDeployZone()
        {
            float x0 = -BattleRules.FieldLength / 2f + BattleRules.DeployEdge;
            float x1 = -BattleRules.DeployFrontLimit;
            float w = BattleRules.FieldWidth - 2f * BattleRules.DeployEdge;
            deployZone = GameObject.CreatePrimitive(PrimitiveType.Plane);
            deployZone.name = "DeployZone";
            deployZone.transform.position = new Vector3((x0 + x1) / 2f, 0.06f, 0f);
            deployZone.transform.localScale = new Vector3((x1 - x0) / 10f, 1f, w / 10f);
            Tint(deployZone, new Color(0.55f, 0.85f, 1f, 0.22f));
            var zm = deployZone.GetComponent<Renderer>().sharedMaterial;
            zm.SetFloat("_Surface", 1f);
            zm.SetFloat("_Blend", 0f);
            zm.SetOverrideTag("RenderType", "Transparent");
            zm.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            zm.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            zm.SetInt("_ZWrite", 0);
            zm.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            zm.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            deployZone.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            Destroy(deployZone.GetComponent<Collider>());
        }

        static void Tint(GameObject go, Color c)
        {
            var r = go.GetComponent<Renderer>();
            var m = new Material(r.sharedMaterial) { color = c };
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            r.sharedMaterial = m;
        }
    }
}
