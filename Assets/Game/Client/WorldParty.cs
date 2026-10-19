using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using Warfare.Core;
using Warfare.Core.World;

namespace Warfare.Client
{
    public sealed class HeroFile
    {
        public string Name = "Герой";
        public string Faction;
        public string Start;
        public Dictionary<string, string> Look = new Dictionary<string, string>();
        public int Gold;
        public Dictionary<string, string> Equipment = new Dictionary<string, string>();
        public List<HeroFile> Companions = new List<HeroFile>();
    }

    public sealed class WorldParty : MonoBehaviour
    {
        static readonly (string key, string prefix)[] Slots = { ("mount", "Mount"), ("body", "Body"), ("head", "Head"), ("shield", "Shield"), ("banner", "Banner") };

        public WorldMap Map;
        public float HeroScale = 4.2f;
        public Rect HudRect;

        public WorldTravel Travel { get; private set; }
        public HeroFile Hero { get; private set; }
        public string Notice { get; private set; }
        public float NoticeUntil { get; private set; }
        public bool Following => following;
        public bool InSettlement => screen != null && screen.Open;
        public Stock Inventory { get; } = new Stock();

        PathFinder finder;
        Task<List<Vec2>> search;
        PlacedSettlement searchFor, heading, pendingFor;
        Vec2 pendingTarget;
        bool hasPending, cancelled;
        Transform root, rig, flag, person;
        Animator personAnim;
        Quaternion personFace = Quaternion.identity;
        readonly Transform[] legs = new Transform[4];
        readonly Quaternion[] legRest = new Quaternion[4];
        readonly Vector3[] legAxis = new Vector3[4];
        Quaternion flagRest;
        Vector3 flagAxis;
        float gait, walk;
        bool following, wasMoving;
        float followSince, holdTimer, searchStarted;
        Vector2 holdTarget;
        Mesh dots;
        Transform dotsT, ring;
        PlacedSettlement hovered;
        SettlementScreen screen;
        Highlight hoverMark, destMark;

        sealed class Highlight
        {
            public Transform T;
            public Mesh Mesh;
            public Material Mat;
            public PlacedSettlement For;
            public float Fade;
        }

        static readonly Color FillGold = new Color(0.96f, 0.76f, 0.3f, 0.28f);
        static readonly Color EdgeGold = new Color(1f, 0.86f, 0.42f, 0.8f);
        float[] dotLeft = Array.Empty<float>();
        int dotCount, dotShown = -1;

        void Start()
        {
            if (Map == null || Map.Walk == null)
            {
                enabled = false;
                return;
            }
            Hero = LoadHero();
            Travel = new WorldTravel(Map.Walk, Map.Rules, StartPoint());
            finder = new PathFinder(Map.Walk, Map.MinTravelCost);
            BuildModel();
            BuildMarkers();
            Place(0f, true);
            if (Map.Cam != null) Map.Cam.LookAt(root.position, 0f, 70f);
            FollowParty();
            gameObject.AddComponent<WorldHud>().Party = this;
            screen = gameObject.AddComponent<SettlementScreen>();
            screen.Map = Map;
            screen.Party = root.gameObject;
            screen.Owner = this;
        }

        static HeroFile LoadHero()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "hero.json");
            var hero = (File.Exists(path) ? DataJson.Read<HeroFile>(File.ReadAllText(path)) : null) ?? new HeroFile();
            var look = HeroLooks.LoadSaved();
            if (look != null && !string.IsNullOrEmpty(look.Faction))
            {
                hero.Faction = look.Faction;
                hero.Start = null;
            }
            return hero;
        }

        Vec2 StartPoint()
        {
            PlacedSettlement s = null;
            foreach (var p in Map.Settlements)
                if (p.Data.id == Hero.Start) { s = p; break; }
            if (s == null)
                foreach (var p in Map.Settlements)
                    if (p.Data.capital && p.Faction.faction == Hero.Faction) { s = p; break; }
            if (s == null && Map.Settlements.Count > 0) s = Map.Settlements[0];
            if (s == null) return new Vec2(Map.Meta.width / 2f, Map.Meta.height / 2f);
            var center = new Vec2(s.Px, s.Py);
            var want = center + new Vec2(0f, WorldSettlements.FlattenRadius(s.Kind, s.Data.capital) * 1.5f);
            return Map.Walk.Nearest(want, Map.Walk.Region(center), 40, out var found) ? found : want;
        }

        void BuildModel()
        {
            root = new GameObject("Hero").transform;
            root.SetParent(Map.transform, false);
            rig = new GameObject("Rig").transform;
            rig.SetParent(root, false);
            int built = AddParts(rig, Hero);
            if (BuildPerson()) built = 1;
            string[] legNames = { "LegFL", "LegFR", "LegBL", "LegBR" };
            for (int i = 0; i < 4; i++)
            {
                legs[i] = Find(rig, legNames[i]);
                if (legs[i] == null) continue;
                legRest[i] = legs[i].localRotation;
                legAxis[i] = legs[i].parent.InverseTransformDirection(rig.TransformDirection(Vector3.forward));
            }
            flag = Find(rig, "Flag");
            if (flag != null)
            {
                flagRest = flag.localRotation;
                flagAxis = flag.parent.InverseTransformDirection(rig.TransformDirection(Vector3.up));
            }
            Debug.Log($"[W1347] hero {Hero.Name}: {built} parts, start {Travel.Party.Position.X:0},{Travel.Party.Position.Y:0}, region {Map.Walk.Region(Travel.Party.Position)}");
        }

        bool Mounted => Hero.Equipment != null && Hero.Equipment.TryGetValue("mount", out var m) && !string.IsNullOrEmpty(m);

        static Bounds Measure(Transform t)
        {
            var rs = t.GetComponentsInChildren<Renderer>();
            if (rs.Length == 0) return new Bounds(t.position, Vector3.zero);
            var b = rs[0].bounds;
            foreach (var r in rs) b.Encapsulate(r.bounds);
            return b;
        }

        bool BuildPerson()
        {
            if (Mounted) return false;
            var prefab = Resources.Load<GameObject>("Characters/MapHero");
            if (prefab == null) return false;
            var banner = rig.Find("Banner");
            if (banner != null) DestroyImmediate(banner.gameObject);
            float height = rig.childCount > 0 ? Measure(rig).size.y : 1f;
            for (int i = rig.childCount - 1; i >= 0; i--) DestroyImmediate(rig.GetChild(i).gameObject);
            var go = Instantiate(prefab);
            go.name = "Person";
            var data = HeroLooks.LoadData();
            HeroLooks.Apply(go, HeroLooks.LoadSaved() ?? HeroLooks.Default(data), data);
            personAnim = go.GetComponent<Animator>();
            if (personAnim != null) personAnim.applyRootMotion = false;
            var head = personAnim != null && personAnim.isHuman ? personAnim.GetBoneTransform(HumanBodyBones.Head) : null;
            Renderer eyes = null;
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                r.shadowCastingMode = ShadowCastingMode.On;
                if (r.name.Contains("Eyes")) eyes = r;
            }
            if (head != null && eyes != null)
            {
                var f = go.transform.InverseTransformDirection(eyes.bounds.center - head.position);
                f.y = 0f;
                if (f.sqrMagnitude > 1e-8f) personFace = Quaternion.Euler(0f, Vector3.SignedAngle(f, Vector3.forward, Vector3.up), 0f);
            }
            float own = Mathf.Max(Measure(go.transform).size.y, 0.01f);
            person = go.transform;
            person.SetParent(root, false);
            person.localPosition = Vector3.zero;
            person.localScale = Vector3.one * (height / own);
            return true;
        }

        public List<HeroFile> Heroes
        {
            get
            {
                var list = new List<HeroFile>();
                if (Hero == null) return list;
                list.Add(Hero);
                if (Hero.Companions != null)
                    foreach (var c in Hero.Companions)
                        if (c != null) list.Add(c);
                return list;
            }
        }

        FactionSettlements PartyFaction()
        {
            foreach (var p in Map.Settlements)
                if (p.Faction.faction == Hero.Faction) return p.Faction;
            return Map.Settlements.Count > 0 ? Map.Settlements[0].Faction : null;
        }

        int AddParts(Transform parent, HeroFile hero)
        {
            var faction = PartyFaction();
            var art = EnvironmentArt.Load();
            int built = 0;
            foreach (var (key, prefix) in Slots)
            {
                if (hero.Look == null || !hero.Look.TryGetValue(key, out var look) || string.IsNullOrEmpty(look)) continue;
                string id = $"WorldHero_{prefix}_{look}";
                var prefab = art != null ? art.Get(id) : null;
                if (prefab == null)
                {
                    Debug.LogWarning($"[W1347] hero part missing: {id}");
                    continue;
                }
                var go = Instantiate(prefab, parent, false);
                go.name = prefix;
                foreach (var r in go.GetComponentsInChildren<Renderer>())
                {
                    var mats = r.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                        if (mats[i] != null && faction != null) mats[i] = Map.PropMaterial(mats[i], faction);
                    r.sharedMaterials = mats;
                    r.shadowCastingMode = ShadowCastingMode.On;
                }
                built++;
            }
            return built;
        }

        public GameObject BuildFigure(HeroFile hero)
        {
            if (hero == null) return null;
            var figure = new GameObject("HeroFigure");
            AddParts(figure.transform, hero);
            return figure;
        }

        static Transform Find(Transform t, string name)
        {
            if (t.name == name) return t;
            for (int i = 0; i < t.childCount; i++)
            {
                var f = Find(t.GetChild(i), name);
                if (f != null) return f;
            }
            return null;
        }

        void Update()
        {
            if (Travel == null) return;
            float dt = Time.deltaTime;
            PollSearch();
            HandleInput();
            Travel.Tick(dt);
            bool moving = Travel.Party.Moving;
            if (wasMoving && !moving) Arrive();
            wasMoving = moving;
            Place(dt, false);
            Animate(dt, moving);
            UpdateMarkers();
            UpdateHighlights(dt);
        }

        void LateUpdate()
        {
            var cam = Map != null ? Map.Cam : null;
            if (cam == null || root == null) return;
            if (following && cam.ManualAt > followSince) following = false;
            if (following) cam.Track(root.position);
        }

        public void FollowParty()
        {
            following = true;
            followSince = Time.unscaledTime;
        }

        public void Wait()
        {
            hasPending = false;
            cancelled = true;
            Travel.ToggleWait();
            if (Travel.Waiting)
            {
                heading = null;
                HideMarkers();
            }
        }

        void Say(string text)
        {
            Notice = text;
            NoticeUntil = Time.unscaledTime + 3f;
        }

        void HandleInput()
        {
            if (screen != null && screen.Open)
            {
                hovered = null;
                return;
            }
            var kb = Keyboard.current;
            if (kb != null)
            {
                if (kb.spaceKey.wasPressedThisFrame) Wait();
                if (kb.fKey.wasPressedThisFrame) FollowParty();
                if (kb.equalsKey.wasPressedThisFrame || kb.numpadPlusKey.wasPressedThisFrame) Travel.ChangeSpeed(1);
                if (kb.minusKey.wasPressedThisFrame || kb.numpadMinusKey.wasPressedThisFrame) Travel.ChangeSpeed(-1);
            }
            var mouse = Mouse.current;
            if (mouse == null || Map.Cam == null) return;
            var pos = mouse.position.ReadValue();
            bool overHud = HudRect.Contains(new Vector2(pos.x, Screen.height - pos.y));
            hovered = overHud ? null : Pick(pos);
            if (mouse.leftButton.wasPressedThisFrame)
            {
                holdTimer = 0f;
                if (!overHud) Order(pos, true);
            }
            else if (mouse.leftButton.isPressed && !overHud)
            {
                holdTimer += Time.unscaledDeltaTime;
                if (holdTimer >= 0.2f)
                {
                    holdTimer = 0f;
                    Order(pos, false);
                }
            }
        }

        void Order(Vector2 screen, bool pressed)
        {
            var s = pressed ? hovered : null;
            Vector2 px;
            if (s != null) px = new Vector2(s.Px, s.Py);
            else
            {
                var cam = Map.Cam.GetComponent<Camera>();
                if (cam == null || !Map.RayToMap(cam.ScreenPointToRay(screen), out px)) return;
                if (!pressed && (px - holdTarget).sqrMagnitude < 9f) return;
            }
            holdTarget = px;
            var grid = Map.Walk;
            int region = PartyRegion();
            var target = new Vec2(px.x, px.y);
            if ((!grid.Walkable(target) || grid.Region(target) != region) && !grid.Nearest(target, region, 60, out target))
            {
                if (pressed) Say("Туда не пройти");
                return;
            }
            int k = grid.CrossingAt(WalkGrid.Cell(target.Y) * grid.Width + WalkGrid.Cell(target.X));
            if (k >= 0)
            {
                var c = grid.Crossings[k];
                target = Vec2.Distance(target, c.A) <= Vec2.Distance(target, c.B) ? c.A : c.B;
            }
            pendingTarget = target;
            pendingFor = s;
            hasPending = true;
            StartSearch();
        }

        int PartyRegion()
        {
            var grid = Map.Walk;
            int r = grid.Region(Travel.Party.Position);
            if (r == 0 && grid.Nearest(Travel.Party.Position, 0, 4, out var p)) r = grid.Region(p);
            return r;
        }

        void StartSearch()
        {
            if (search != null || !hasPending) return;
            hasPending = false;
            cancelled = false;
            var from = Travel.Party.Position;
            var to = pendingTarget;
            searchFor = pendingFor;
            var f = finder;
            searchStarted = Time.unscaledTime;
            search = Task.Run(() => f.Find(from, to));
        }

        void PollSearch()
        {
            if (search != null && !search.IsCompleted && !cancelled && Time.unscaledTime - searchStarted > 0.4f && Time.unscaledTime > NoticeUntil) Say("Ищем дорогу");
            if (search == null || !search.IsCompleted) return;
            List<Vec2> path = null;
            if (search.IsFaulted) Debug.LogException(search.Exception);
            else path = search.Result;
            search = null;
            if (!cancelled) Apply(path, searchFor, hasPending);
            StartSearch();
        }

        void Apply(List<Vec2> path, PlacedSettlement s, bool quiet)
        {
            if (Notice == "Ищем дорогу") NoticeUntil = 0f;
            if (path == null || path.Count == 0)
            {
                if (!quiet) Say("Дороги туда нет");
                return;
            }
            if (s != null) path = TrimAt(path, new Vec2(s.Px, s.Py), WorldSettlements.FlattenRadius(s.Kind, s.Data.capital));
            path[0] = Travel.Party.Position;
            Travel.Order(path);
            heading = s;
            if (!Travel.Party.Moving)
            {
                Arrive();
                return;
            }
            ShowMarkers(path);
        }

        static List<Vec2> TrimAt(List<Vec2> path, Vec2 c, float r)
        {
            var output = new List<Vec2> { path[0] };
            if (Vec2.Distance(path[0], c) <= r) return output;
            for (int i = 1; i < path.Count; i++)
            {
                var a = path[i - 1];
                var b = path[i];
                if (Vec2.Distance(b, c) > r)
                {
                    output.Add(b);
                    continue;
                }
                float lo = 0f, hi = 1f;
                for (int k = 0; k < 20; k++)
                {
                    float m = (lo + hi) * 0.5f;
                    if (Vec2.Distance(a + (b - a) * m, c) > r) lo = m;
                    else hi = m;
                }
                output.Add(a + (b - a) * lo);
                break;
            }
            return output;
        }

        void Arrive()
        {
            if (heading != null && screen != null) screen.Enter(heading);
            heading = null;
            HideMarkers();
        }

        void Place(float dt, bool snap)
        {
            var party = Travel.Party;
            var h = party.Heading;
            var dir = new Vector3(h.X, 0f, -h.Y);
            if (dir.sqrMagnitude < 1e-6f) dir = Vector3.right;
            var front = party.Position + h * 0.9f;
            var back = party.Position - h * 0.9f;
            float pitch = Mathf.Clamp(Mathf.Atan2(Map.GroundHeight(front.X, front.Y) - Map.GroundHeight(back.X, back.Y), 1.8f) * Mathf.Rad2Deg, -18f, 18f);
            var look = Quaternion.LookRotation(dir.normalized) * Quaternion.Euler(0f, 90f, 0f) * Quaternion.Euler(0f, 0f, -pitch);
            root.position = Map.MapToWorld(party.Position);
            root.rotation = snap ? look : Quaternion.Slerp(root.rotation, look, 1f - Mathf.Exp(-10f * dt));
            float camDistance = Map.Cam != null ? Map.Cam.Distance : 160f;
            root.localScale = Vector3.one * (HeroScale * Mathf.Max(1f, camDistance / 180f));
        }

        void Animate(float dt, bool moving)
        {
            walk = Mathf.MoveTowards(walk, moving ? 1f : 0f, dt * 4f);
            gait += dt * 10f * (1f + 0.3f * Mathf.Log(Mathf.Max(1, Travel.Clock.Speed), 2f)) * walk;
            float swing = Mathf.Sin(gait) * 28f * walk;
            for (int i = 0; i < 4; i++)
                if (legs[i] != null) legs[i].localRotation = Quaternion.AngleAxis(i == 0 || i == 3 ? swing : -swing, legAxis[i]) * legRest[i];
            rig.localPosition = new Vector3(0f, Mathf.Abs(Mathf.Cos(gait)) * 0.03f * walk + Mathf.Sin(Time.time * 1.6f) * 0.003f, 0f);
            rig.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(gait * 2f) * 1.6f * walk);
            if (flag != null) flag.localRotation = Quaternion.AngleAxis(Mathf.Sin(Time.time * 3.2f) * (5f + 9f * walk), flagAxis) * flagRest;
            if (person == null) return;
            var h = Travel.Party.Heading;
            var dir = new Vector3(h.X, 0f, -h.Y);
            if (dir.sqrMagnitude > 1e-6f) person.rotation = Quaternion.Slerp(person.rotation, Quaternion.LookRotation(dir.normalized) * personFace, 1f - Mathf.Exp(-10f * dt));
            if (personAnim == null) return;
            personAnim.SetFloat("Move", walk);
            personAnim.speed = moving ? 1f + 0.3f * Mathf.Log(Mathf.Max(1, Travel.Clock.Speed), 2f) : 1f;
        }

        void BuildMarkers()
        {
            var shader = Shader.Find("Warfare/MapMarker");
            if (shader == null) return;
            var dotMat = new Material(shader) { name = "PathDots" };
            var ringMat = new Material(shader) { name = "TargetRing" };
            ringMat.SetColor("_Color", new Color(1f, 0.8f, 0.3f, 0.95f));
            dots = new Mesh { name = "PathDots", indexFormat = IndexFormat.UInt32 };
            dots.MarkDynamic();
            dotsT = MarkerObject("PathDots", dots, dotMat);
            ring = MarkerObject("TargetRing", RingMesh(), ringMat);
            hoverMark = NewHighlight("HoverRing", shader);
            destMark = NewHighlight("DestinationRing", shader);
            HideMarkers();
        }

        Highlight NewHighlight(string name, Shader shader)
        {
            var h = new Highlight { Mesh = new Mesh { name = name }, Mat = new Material(shader) { name = name } };
            h.Mesh.MarkDynamic();
            h.Mat.SetColor("_Color", Color.white);
            h.T = MarkerObject(name, h.Mesh, h.Mat);
            h.T.gameObject.SetActive(false);
            return h;
        }

        static float HighlightRadius(PlacedSettlement s) => WorldSettlements.FlattenRadius(s.Kind, s.Data.capital) * 1.1f;

        Vector3 Ground(float px, float py) => new Vector3(px - Map.Meta.width / 2f, Map.GroundHeight(px, py) + 0.15f, Map.Meta.height / 2f - py);

        void BuildHighlight(Highlight h, PlacedSettlement s)
        {
            h.For = s;
            const int n = 64;
            float r = HighlightRadius(s);
            float[] radius = { 0.25f, 0.5f, 0.75f, 0.915f, 0.93f, 0.985f, 1.02f };
            var edgeOut = new Color(EdgeGold.r, EdgeGold.g, EdgeGold.b, 0f);
            Color[] colors = { FillGold, FillGold, FillGold, FillGold, EdgeGold, EdgeGold, edgeOut };
            int rings = radius.Length;
            var v = new Vector3[1 + n * rings];
            var col = new Color[v.Length];
            var uv = new Vector2[v.Length];
            var corner = new Vector2[v.Length];
            for (int i = 0; i < v.Length; i++) uv[i] = new Vector2(0.5f, 0.5f);
            v[0] = Ground(s.Px, s.Py);
            col[0] = FillGold;
            for (int k = 0; k < rings; k++)
            for (int i = 0; i < n; i++)
            {
                float a = i * Mathf.PI * 2f / n;
                v[1 + k * n + i] = Ground(s.Px + Mathf.Cos(a) * r * radius[k], s.Py + Mathf.Sin(a) * r * radius[k]);
                col[1 + k * n + i] = colors[k];
            }
            var tris = new List<int>();
            for (int i = 0; i < n; i++) tris.AddRange(new[] { 0, 1 + (i + 1) % n, 1 + i });
            for (int k = 0; k < rings - 1; k++)
            for (int i = 0; i < n; i++)
            {
                int a0 = 1 + k * n + i, a1 = 1 + k * n + (i + 1) % n, b0 = 1 + (k + 1) * n + i, b1 = 1 + (k + 1) * n + (i + 1) % n;
                tris.AddRange(new[] { a0, b0, b1, a0, b1, a1 });
            }
            h.Mesh.Clear();
            h.Mesh.vertices = v;
            h.Mesh.colors = col;
            h.Mesh.uv = uv;
            h.Mesh.uv2 = corner;
            h.Mesh.SetTriangles(tris, 0);
            h.Mesh.RecalculateBounds();
        }

        PlacedSettlement Pick(Vector2 mouse)
        {
            if (Map.Labels != null && Map.Labels.Hovered != null) return Map.Labels.Hovered;
            var cam = Map.Cam.GetComponent<Camera>();
            if (cam == null) return null;
            PlacedSettlement best = null;
            float bestScore = 1f;
            var right = cam.transform.right;
            foreach (var s in Map.Settlements)
            {
                float r = HighlightRadius(s);
                var c = s.Position + Vector3.up * (r * 0.25f);
                var sc = cam.WorldToScreenPoint(c);
                if (sc.z <= 0f) continue;
                float rpx = Vector2.Distance(sc, cam.WorldToScreenPoint(c + right * r));
                if (rpx < 2f) continue;
                float score = Vector2.Distance(mouse, sc) / rpx;
                if (score < bestScore)
                {
                    bestScore = score;
                    best = s;
                }
            }
            return best;
        }

        void UpdateHighlights(float dt)
        {
            var dest = Travel.Party.Moving ? heading : null;
            StepHighlight(destMark, dest, dt, 0.85f + 0.15f * Mathf.Sin(Time.time * 3f));
            StepHighlight(hoverMark, hovered != dest ? hovered : null, dt, 1f);
        }

        void StepHighlight(Highlight h, PlacedSettlement s, float dt, float pulse)
        {
            if (h == null) return;
            if (s != null && s != h.For)
            {
                BuildHighlight(h, s);
                h.Fade = 0f;
            }
            h.Fade = Mathf.MoveTowards(h.Fade, s != null ? 1f : 0f, dt * 6f);
            bool on = h.Fade > 0.001f;
            if (h.T.gameObject.activeSelf != on) h.T.gameObject.SetActive(on);
            if (on) h.Mat.SetColor("_Color", new Color(1f, 1f, 1f, h.Fade * pulse));
        }

        Transform MarkerObject(string name, Mesh mesh, Material mat)
        {
            var go = new GameObject(name);
            go.transform.SetParent(Map.transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = mat;
            r.shadowCastingMode = ShadowCastingMode.Off;
            r.receiveShadows = false;
            return go.transform;
        }

        static Mesh RingMesh()
        {
            const int n = 48;
            float[] radius = { 0.68f, 0.85f, 1f };
            float[] alpha = { 0f, 1f, 0f };
            var v = new Vector3[n * 3];
            var col = new Color[n * 3];
            var uv = new Vector2[n * 3];
            var corner = new Vector2[n * 3];
            for (int i = 0; i < n; i++)
            {
                float a = i * Mathf.PI * 2f / n;
                for (int k = 0; k < 3; k++)
                {
                    int j = k * n + i;
                    v[j] = new Vector3(Mathf.Cos(a) * radius[k], 0f, Mathf.Sin(a) * radius[k]);
                    col[j] = new Color(1f, 1f, 1f, alpha[k]);
                    uv[j] = new Vector2(0.5f, 0.5f);
                }
            }
            var tris = new List<int>();
            for (int k = 0; k < 2; k++)
            for (int i = 0; i < n; i++)
            {
                int a0 = k * n + i, a1 = k * n + (i + 1) % n, b0 = (k + 1) * n + i, b1 = (k + 1) * n + (i + 1) % n;
                tris.AddRange(new[] { a0, b0, b1, a0, b1, a1 });
            }
            var m = new Mesh { name = "TargetRing", vertices = v, colors = col, uv = uv, uv2 = corner };
            m.SetTriangles(tris, 0);
            m.RecalculateBounds();
            return m;
        }

        void ShowMarkers(IReadOnlyList<Vec2> path)
        {
            if (dots == null) return;
            float total = 0f;
            for (int i = 1; i < path.Count; i++) total += Vec2.Distance(path[i - 1], path[i]);
            const float spacing = 1.6f;
            var pts = new List<Vector3>();
            var left = new List<float>();
            float walked = 0f, next = spacing;
            for (int i = 1; i < path.Count; i++)
            {
                var a = path[i - 1];
                var b = path[i];
                float len = Vec2.Distance(a, b);
                while (next <= walked + len)
                {
                    var p = a + (b - a) * ((next - walked) / Mathf.Max(len, 1e-5f));
                    if (total - next > 1.2f)
                    {
                        pts.Add(Map.MapToWorld(p) + Vector3.up * 0.2f);
                        left.Add(total - next);
                    }
                    next += spacing;
                }
                walked += len;
            }
            int n = pts.Count;
            var v = new Vector3[n * 4];
            var uv = new Vector2[n * 4];
            var corner = new Vector2[n * 4];
            var idx = new int[n * 6];
            var bounds = new Bounds(n > 0 ? pts[0] : Vector3.zero, Vector3.zero);
            for (int i = 0; i < n; i++)
            {
                for (int c = 0; c < 4; c++)
                {
                    v[i * 4 + c] = pts[i];
                    float x = c == 1 || c == 2 ? 1f : 0f, y = c >= 2 ? 1f : 0f;
                    uv[i * 4 + c] = new Vector2(x, y);
                    corner[i * 4 + c] = new Vector2(x * 2f - 1f, y * 2f - 1f);
                }
                int o = i * 4;
                idx[i * 6] = o;
                idx[i * 6 + 1] = o + 1;
                idx[i * 6 + 2] = o + 2;
                idx[i * 6 + 3] = o;
                idx[i * 6 + 4] = o + 2;
                idx[i * 6 + 5] = o + 3;
                bounds.Encapsulate(pts[i]);
            }
            bounds.Expand(40f);
            dots.Clear();
            dots.vertices = v;
            dots.uv = uv;
            dots.uv2 = corner;
            dots.SetIndices(idx, MeshTopology.Triangles, 0, false);
            dots.bounds = bounds;
            dotLeft = left.ToArray();
            dotCount = n;
            dotShown = -1;
            dotsT.gameObject.SetActive(n > 0);
            ring.position = Map.MapToWorld(path[path.Count - 1]) + Vector3.up * 0.15f;
            ring.gameObject.SetActive(heading == null);
        }

        void HideMarkers()
        {
            dotCount = 0;
            if (dotsT != null) dotsT.gameObject.SetActive(false);
            if (ring != null) ring.gameObject.SetActive(false);
        }

        void UpdateMarkers()
        {
            float camDistance = Map.Cam != null ? Map.Cam.Distance : 160f;
            if (ring != null && ring.gameObject.activeSelf) ring.localScale = Vector3.one * (1.3f * Mathf.Max(1f, camDistance / 140f) * (1f + Mathf.Sin(Time.time * 4f) * 0.08f));
            if (dotCount == 0 || dotsT == null) return;
            float remaining = Travel.Party.RemainingDistance();
            int lo = 0, hi = dotCount;
            while (lo < hi)
            {
                int mid = (lo + hi) / 2;
                if (dotLeft[mid] > remaining) lo = mid + 1;
                else hi = mid;
            }
            if (lo == dotShown) return;
            dotShown = lo;
            if (lo >= dotCount)
            {
                dotsT.gameObject.SetActive(false);
                return;
            }
            dots.SetSubMesh(0, new SubMeshDescriptor(lo * 6, (dotCount - lo) * 6), MeshUpdateFlags.DontRecalculateBounds);
        }
    }
}
