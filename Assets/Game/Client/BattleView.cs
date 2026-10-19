using System.Collections.Generic;
using UnityEngine;
using Warfare.Core;
using Warfare.Core.Battle;

namespace Warfare.Client
{
    public sealed class BattleView : MonoBehaviour
    {
        sealed class UnitView
        {
            public BattleUnit Unit;
            public Transform Root;
            public Transform Body;
            public Renderer[] Tinted;
            public Color[][] BaseColors;
            public GameObject Ring;
            public Vector3 Prev;
            public Vector3 Curr;
            public float Yaw;
            public bool DeathShown;
            public float Bob;
            public Animator Anim;
            public string Loco;
            public float BusyUntil;
            public float LastSwing;
            public float LastFlash;
            public bool Flashing;
            public int IdleVariant;
            public int WalkVariant;
            public int RunVariant;
            public Transform Sword;
            public Transform Shield;
            public int CreatedFrame;
        }

        struct Mount
        {
            public Vector3 Position;
            public Quaternion Rotation;
        }

        static bool mountsReady;
        static Mount swordMount;
        static Mount shieldMount;

        sealed class ProjectileView
        {
            public Transform T;
            public Vector3 Last;
        }

        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        static readonly int ColorId = Shader.PropertyToID("_Color");
        static readonly int MetallicId = Shader.PropertyToID("_Metallic");
        static readonly int SmoothnessId = Shader.PropertyToID("_Smoothness");

        public static readonly Color[] SideColors = { new Color(0.22f, 0.42f, 0.92f), new Color(0.86f, 0.2f, 0.18f) };
        static readonly Color HeroColor = new Color(1f, 0.78f, 0.2f);
        static readonly Color ShieldColor = new Color(0.92f, 0.9f, 0.84f);
        static readonly Color WoodColor = new Color(0.45f, 0.3f, 0.16f);
        static readonly Color HorseColor = new Color(0.42f, 0.28f, 0.18f);
        static readonly Color DeadTint = new Color(0.35f, 0.33f, 0.3f);
        static readonly Color RingColor = new Color(1f, 0.85f, 0.3f);

        readonly Dictionary<int, UnitView> units = new Dictionary<int, UnitView>();
        readonly Dictionary<int, ProjectileView> projectiles = new Dictionary<int, ProjectileView>();
        readonly Stack<ProjectileView> projectilePool = new Stack<ProjectileView>();
        readonly Dictionary<Color, Material> materials = new Dictionary<Color, Material>();
        readonly Dictionary<string, Material[]> modelMaterials = new Dictionary<string, Material[]>();
        readonly HashSet<int> seen = new HashSet<int>();
        readonly List<int> stale = new List<int>();
        MaterialPropertyBlock block;
        Material baseMaterial;
        BattleSim sim;
        Transform unitRoot;
        Transform projectileRoot;
        UnitArt art;
        float modelYaw = float.NaN;
        System.Random variety = new System.Random(1);

        public void Bind(BattleSim battle)
        {
            Clear();
            sim = battle;
            block ??= new MaterialPropertyBlock();
            if (art == null) art = UnitArt.Load();
            variety = new System.Random((int)battle.Options.Seed);
            unitRoot = new GameObject("Units").transform;
            unitRoot.SetParent(transform, false);
            projectileRoot = new GameObject("Projectiles").transform;
            projectileRoot.SetParent(transform, false);
            SyncUnits(true);
        }

        public void Clear()
        {
            if (unitRoot != null) Destroy(unitRoot.gameObject);
            if (projectileRoot != null) Destroy(projectileRoot.gameObject);
            units.Clear();
            projectiles.Clear();
            projectilePool.Clear();
            sim = null;
        }

        public static Vector3 ToWorld(Vec2 p, float height = 0f) => new Vector3(p.X, height, p.Y);

        public Transform RootOf(int uid) => units.TryGetValue(uid, out var v) ? v.Root : null;

        public void AfterStep()
        {
            if (sim == null) return;
            SyncUnits(false);
        }

        public void Render(float alpha, bool[] selected, int playerSide, bool paused)
        {
            if (sim == null) return;
            float dt = Time.deltaTime;
            float now = Time.time;
            bool everyone = selected[0] && selected[1] && selected[2] && selected[3];
            foreach (var v in units.Values)
            {
                var u = v.Unit;
                if (v.Anim != null) v.Anim.speed = paused ? 0f : v.Anim.speed == 0f ? 1f : v.Anim.speed;
                if (u.State == UnitState.Fled)
                {
                    if (v.Root.gameObject.activeSelf) v.Root.gameObject.SetActive(false);
                    continue;
                }
                var pos = Vector3.Lerp(v.Prev, v.Curr, alpha);
                if (u.State == UnitState.Dead)
                {
                    if (!v.DeathShown) ShowDeath(v);
                    float sink = Mathf.Clamp01((u.DeadTime - 20f) / 5f);
                    v.Root.position = pos + Vector3.down * sink * 0.8f;
                    if (sink >= 1f) v.Root.gameObject.SetActive(false);
                    continue;
                }

                float targetYaw = Mathf.Atan2(u.Facing.X, u.Facing.Y) * Mathf.Rad2Deg;
                v.Yaw = Mathf.MoveTowardsAngle(v.Yaw, targetYaw, 540f * dt);
                v.Root.SetPositionAndRotation(pos, Quaternion.Euler(0f, v.Yaw, 0f));

                if (v.Anim != null) Animate(v, now, paused);
                else
                {
                    if (u.State == UnitState.Walk) v.Bob += dt * (u.Troop.IsCavalry ? 9f : 11f);
                    float bob = u.State == UnitState.Walk ? Mathf.Abs(Mathf.Sin(v.Bob)) * 0.12f : 0f;
                    v.Body.localPosition = new Vector3(0f, bob, 0f);
                    v.Body.localRotation = Quaternion.Euler(u.Swing > 0 ? 18f : 0f, 0f, 0f);
                }

                Tint(v, Mathf.Clamp01(u.Flash / 0.18f), u.Routed);
                bool ring = !everyone && u.Side == playerSide && selected[(int)u.Group];
                if (v.Ring.activeSelf != ring) v.Ring.SetActive(ring);
                v.LastSwing = u.Swing;
                v.LastFlash = u.Flash;
            }
            RenderProjectiles();
        }

        void Animate(UnitView v, float now, bool paused)
        {
            if (paused) return;
            var u = v.Unit;
            if (u.Swing > 0 && v.LastSwing <= 0 && art.Attack.Length > 0)
            {
                var c = art.Attack[variety.Next(art.Attack.Length)];
                Play(v, c.State, 0.08f, 1f);
                v.BusyUntil = now + c.Length * 0.85f;
                return;
            }
            if (u.Flash > v.LastFlash + 0.05f && now >= v.BusyUntil && art.Impact.Length > 0)
            {
                var c = art.Impact[variety.Next(art.Impact.Length)];
                Play(v, c.State, 0.06f, 1.3f);
                v.BusyUntil = now + c.Length / 1.3f * 0.8f;
                return;
            }
            if (now < v.BusyUntil) return;

            float speed = new Vector2(u.Velocity.X, u.Velocity.Y).magnitude;
            float side = u.Velocity.X * u.Facing.Y - u.Velocity.Y * u.Facing.X;
            float ahead = u.Velocity.X * u.Facing.X + u.Velocity.Y * u.Facing.Y;
            if (speed > 0.3f && art.Strafe.Length >= 2 && Mathf.Abs(side) > Mathf.Abs(ahead) * 1.2f)
            {
                var c = side > 0 ? StrafeClip(true) : StrafeClip(false);
                Play(v, c.State, 0.2f, Mathf.Clamp(speed / art.StrafeSpeed, 0.6f, 1.8f));
                return;
            }
            if (speed > 0.3f && ahead < 0f && art.Walk.Length > 0)
            {
                Play(v, art.Walk[v.WalkVariant % art.Walk.Length].State, 0.2f, Mathf.Clamp(speed / art.WalkSpeed, 0.6f, 1.6f), -1f);
                return;
            }
            if (u.Blocking && art.BlockIdle.Length > 0)
            {
                Play(v, art.BlockIdle[0].State, 0.12f, 1f);
                return;
            }
            if (speed < 0.3f || art.Walk.Length == 0)
                Play(v, art.Idle[v.IdleVariant % art.Idle.Length].State, 0.25f, 1f);
            else if (speed < 2.2f || art.Run.Length == 0)
                Play(v, art.Walk[v.WalkVariant % art.Walk.Length].State, 0.2f, Mathf.Clamp(speed / art.WalkSpeed, 0.6f, 2f));
            else
                Play(v, art.Run[v.RunVariant % art.Run.Length].State, 0.2f, Mathf.Clamp(speed / art.RunSpeed, 0.7f, 1.8f));
        }

        UnitArt.Clip StrafeClip(bool right)
        {
            var best = art.Strafe[0];
            foreach (var c in art.Strafe)
                if (right ? c.SideSpeed > best.SideSpeed : c.SideSpeed < best.SideSpeed) best = c;
            return best;
        }

        static readonly int SpeedParam = Animator.StringToHash("Speed");

        static void Play(UnitView v, string state, float fade, float speed, float direction = 1f)
        {
            v.Anim.speed = speed;
            v.Anim.SetFloat(SpeedParam, direction);
            string key = direction < 0 ? state + "<" : state;
            if (v.Loco == key) return;
            v.Loco = key;
            v.Anim.CrossFadeInFixedTime(state, fade);
        }

        void Tint(UnitView v, float flash, bool routed)
        {
            bool active = flash > 0f || routed;
            if (!active && !v.Flashing) return;
            v.Flashing = active;
            for (int r = 0; r < v.Tinted.Length; r++)
            {
                var colors = v.BaseColors[r];
                for (int m = 0; m < colors.Length; m++)
                {
                    var c = Color.Lerp(colors[m], Color.white, flash * 0.7f);
                    if (routed) c = Color.Lerp(c, Color.gray, 0.4f);
                    block.SetColor(BaseColorId, c);
                    block.SetColor(ColorId, c);
                    if (colors.Length > 1) v.Tinted[r].SetPropertyBlock(block, m);
                    else v.Tinted[r].SetPropertyBlock(block);
                }
            }
        }

        void SyncUnits(bool snap)
        {
            foreach (var u in sim.Units)
            {
                if (!units.TryGetValue(u.Uid, out var v))
                {
                    v = Create(u);
                    units[u.Uid] = v;
                    v.Prev = v.Curr = ToWorld(u.Pos);
                    v.Yaw = Mathf.Atan2(u.Facing.X, u.Facing.Y) * Mathf.Rad2Deg;
                    continue;
                }
                v.Prev = snap ? ToWorld(u.Pos) : v.Curr;
                v.Curr = ToWorld(u.Pos);
            }
        }

        UnitView Create(BattleUnit u)
        {
            var root = new GameObject($"{u.Troop.Id}#{u.Uid}").transform;
            root.SetParent(unitRoot, false);
            var body = new GameObject("Body").transform;
            body.SetParent(root, false);
            bool cav = u.Troop.IsCavalry;

            var view = new UnitView { Unit = u, Root = root, Body = body };
            if (!cav && art != null && art.Ready) BuildModel(view, u);
            else BuildPrimitive(view, u);

            var ring = Part(PrimitiveType.Cylinder, root, new Vector3(0f, 0.02f, 0f), new Vector3(cav ? 1.9f : 1.0f, 0.01f, cav ? 1.9f : 1.0f), RingColor);
            ring.gameObject.SetActive(false);
            view.Ring = ring.gameObject;
            return view;
        }

        void BuildModel(UnitView view, BattleUnit u)
        {
            var model = Instantiate(art.Infantry, view.Body, false);
            model.name = "Model";
            var anim = model.GetComponent<Animator>();
            if (anim == null) anim = model.AddComponent<Animator>();
            anim.runtimeAnimatorController = art.Controller;
            anim.applyRootMotion = false;
            anim.cullingMode = AnimatorCullingMode.CullUpdateTransforms;
            if (float.IsNaN(modelYaw)) modelYaw = DetectYaw(anim);
            model.transform.localRotation = Quaternion.Euler(0f, -modelYaw, 0f);
            if (u.IsHero) model.transform.localScale = Vector3.one * 1.12f;

            var rightHand = anim.GetBoneTransform(HumanBodyBones.RightHand);
            var leftArm = anim.GetBoneTransform(HumanBodyBones.LeftLowerArm);
            if (art.Sword != null && rightHand != null) view.Sword = AttachEquipment(art.Sword, rightHand, swordMount);
            if (art.Shield != null && leftArm != null && u.Troop.Look != null && u.Troop.Look.Shield) view.Shield = AttachEquipment(art.Shield, leftArm, shieldMount);
            view.CreatedFrame = Time.frameCount;

            var renderers = model.GetComponentsInChildren<Renderer>(true);
            var colors = new Color[renderers.Length][];
            for (int i = 0; i < renderers.Length; i++)
            {
                var mats = MaterialsFor(renderers[i].sharedMaterials, u);
                renderers[i].sharedMaterials = mats;
                colors[i] = new Color[mats.Length];
                for (int m = 0; m < mats.Length; m++)
                    colors[i][m] = mats[m] != null && mats[m].HasProperty(BaseColorId) ? mats[m].GetColor(BaseColorId) : Color.white;
            }
            view.Anim = anim;
            view.Tinted = renderers;
            view.BaseColors = colors;
            view.IdleVariant = variety.Next(64);
            view.WalkVariant = variety.Next(64);
            view.RunVariant = variety.Next(64);
            anim.Play(art.Idle[view.IdleVariant % art.Idle.Length].State, 0, (float)variety.NextDouble());
            view.Loco = art.Idle[view.IdleVariant % art.Idle.Length].State;
        }

        static Transform AttachEquipment(GameObject prefab, Transform bone, Mount mount)
        {
            var t = Instantiate(prefab, bone, false).transform;
            t.name = prefab.name;
            foreach (var c in t.GetComponentsInChildren<Collider>()) Destroy(c);
            if (mountsReady)
            {
                t.localPosition = mount.Position;
                t.localRotation = mount.Rotation;
            }
            else t.gameObject.SetActive(false);
            return t;
        }

        void LateUpdate()
        {
            if (mountsReady || sim == null) return;
            foreach (var v in units.Values)
            {
                if (v.Anim == null || !v.Unit.Alive || Time.frameCount - v.CreatedFrame < 2 || v.Sword == null) continue;
                Calibrate(v);
                mountsReady = true;
                foreach (var w in units.Values)
                {
                    Apply(w.Sword, swordMount);
                    Apply(w.Shield, shieldMount);
                }
                break;
            }
        }

        static void Apply(Transform t, Mount m)
        {
            if (t == null) return;
            t.localPosition = m.Position;
            t.localRotation = m.Rotation;
            t.gameObject.SetActive(true);
        }

        static Vector3 PrefabAxis(Transform root, bool thinnest)
        {
            var mf = root.GetComponentInChildren<MeshFilter>(true);
            if (mf == null || mf.sharedMesh == null) return Vector3.up;
            var b = mf.sharedMesh.bounds;
            var center = root.InverseTransformPoint(mf.transform.TransformPoint(b.center));
            if (!thinnest) return center.sqrMagnitude > 1e-6f ? center.normalized : Vector3.up;
            var s = b.size;
            Vector3 axis = s.x <= s.y && s.x <= s.z ? Vector3.right : s.y <= s.z ? Vector3.up : Vector3.forward;
            axis = root.InverseTransformDirection(mf.transform.TransformDirection(axis)).normalized;
            if (Vector3.Dot(axis, center) < 0) axis = -axis;
            return axis;
        }

        void Calibrate(UnitView v)
        {
            var anim = v.Anim;
            var fwd = v.Root.forward;
            var right = v.Root.right;
            var hand = anim.GetBoneTransform(HumanBodyBones.RightHand);
            var lowerR = anim.GetBoneTransform(HumanBodyBones.RightLowerArm);
            if (hand != null && lowerR != null && v.Sword != null)
            {
                var handDir = (hand.position - lowerR.position).normalized;
                var grip = hand.position + handDir * 0.07f;
                var want = (fwd * 0.55f + Vector3.up * 0.8f).normalized;
                var axis = PrefabAxis(v.Sword, false);
                swordMount.Rotation = Quaternion.FromToRotation(axis, Quaternion.Inverse(hand.rotation) * want);
                swordMount.Position = hand.InverseTransformPoint(grip);
            }
            var fore = anim.GetBoneTransform(HumanBodyBones.LeftLowerArm);
            var handL = anim.GetBoneTransform(HumanBodyBones.LeftHand);
            if (fore != null && handL != null)
            {
                var face = (fwd * 0.9f - right * 0.3f).normalized;
                var mid = Vector3.Lerp(fore.position, handL.position, 0.55f) + face * 0.09f;
                var probe = v.Shield != null ? v.Shield : Instantiate(art.Shield, fore, false).transform;
                var axis = PrefabAxis(probe, true);
                shieldMount.Rotation = Quaternion.FromToRotation(axis, Quaternion.Inverse(fore.rotation) * face);
                shieldMount.Position = fore.InverseTransformPoint(mid);
                if (probe != v.Shield) Destroy(probe.gameObject);
            }
            Debug.Log($"[W1347] weapon mounts calibrated on {v.Unit.Troop.Id}");
        }

        static float DetectYaw(Animator anim)
        {
            var foot = anim.GetBoneTransform(HumanBodyBones.LeftFoot);
            var toes = anim.GetBoneTransform(HumanBodyBones.LeftToes);
            if (foot == null || toes == null) return 0f;
            var d = toes.position - foot.position;
            d.y = 0f;
            if (d.sqrMagnitude < 1e-6f) return 0f;
            return Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
        }

        Material[] MaterialsFor(Material[] source, BattleUnit u)
        {
            var names = new string[source.Length];
            for (int i = 0; i < source.Length; i++) names[i] = source[i] != null ? source[i].name : "-";
            string key = $"{u.Side}:{(u.IsHero ? "hero" : u.Group.ToString())}:{string.Join(",", names)}";
            if (modelMaterials.TryGetValue(key, out var cached)) return cached;
            var side = SideColors[u.Side];
            Color cloth = u.IsHero ? HeroColor : u.Group == Group.Ranged ? Color.Lerp(side, Color.white, 0.35f) : side;
            Color trim = u.IsHero ? side : u.Side == 0 ? new Color(0.95f, 0.74f, 0.18f) : new Color(0.93f, 0.91f, 0.86f);
            var result = new Material[source.Length];
            for (int i = 0; i < source.Length; i++)
            {
                var m = source[i];
                if (m == null) continue;
                string n = m.name.ToLowerInvariant();
                bool metal = n.Contains("metal");
                Color? replace = n.Contains("blue") ? cloth : n.Contains("gold") ? trim : metal ? new Color(0.58f, 0.6f, 0.64f) : (Color?)null;
                if (replace == null)
                {
                    result[i] = m;
                    continue;
                }
                var copy = new Material(m) { name = m.name + "_" + key, color = replace.Value };
                if (copy.HasProperty(BaseColorId)) copy.SetColor(BaseColorId, replace.Value);
                if (metal)
                {
                    if (copy.HasProperty(MetallicId)) copy.SetFloat(MetallicId, 0.55f);
                    if (copy.HasProperty(SmoothnessId)) copy.SetFloat(SmoothnessId, 0.35f);
                }
                result[i] = copy;
            }
            modelMaterials[key] = result;
            return result;
        }

        void BuildPrimitive(UnitView view, BattleUnit u)
        {
            var body = view.Body;
            var tinted = new List<Renderer>();
            var colors = new List<Color>();
            var color = u.IsHero ? HeroColor : GroupShade(SideColors[u.Side], u.Group);
            bool cav = u.Troop.IsCavalry;
            float riderBase = 0f;
            float scale = u.IsHero ? 1.15f : 1f;

            void Add(Renderer r, Color c)
            {
                tinted.Add(r);
                colors.Add(c);
            }

            if (cav)
            {
                Add(Part(PrimitiveType.Cube, body, new Vector3(0f, 0.75f, 0f), new Vector3(0.75f, 0.8f, 2.0f), HorseColor), HorseColor);
                Add(Part(PrimitiveType.Cube, body, new Vector3(0f, 1.25f, 1.1f), new Vector3(0.35f, 0.45f, 0.7f), HorseColor), HorseColor);
                riderBase = 1.0f;
            }
            Add(Part(PrimitiveType.Capsule, body, new Vector3(0f, riderBase + 0.85f * scale, 0f), new Vector3(0.75f, 0.85f, 0.6f) * scale, color), color);
            Add(Part(PrimitiveType.Sphere, body, new Vector3(0f, riderBase + 1.85f * scale, 0f), Vector3.one * 0.62f * scale, color * 0.85f), color * 0.85f);

            var look = u.Troop.Look;
            if (look != null && look.Shield)
                Add(Part(PrimitiveType.Cube, body, new Vector3(-0.32f, riderBase + 0.95f, 0.38f), new Vector3(0.6f, 0.75f, 0.08f), ShieldColor), ShieldColor);
            if (BattleRules.IsPole(u.Troop) || look?.Weapon == "lance")
                Add(Part(PrimitiveType.Cube, body, new Vector3(0.38f, riderBase + 1.0f, 0.9f), new Vector3(0.06f, 0.06f, cav ? 3.2f : 2.4f), WoodColor), WoodColor);
            else if (u.Troop.IsRanged)
                Add(Part(PrimitiveType.Cube, body, new Vector3(0.4f, riderBase + 1.1f, 0.35f), new Vector3(0.06f, 0.9f, 0.06f), WoodColor), WoodColor);
            else
            {
                var steel = new Color(0.75f, 0.77f, 0.8f);
                Add(Part(PrimitiveType.Cube, body, new Vector3(0.4f, riderBase + 1.0f, 0.55f), new Vector3(0.07f, 0.07f, 0.95f), steel), steel);
            }

            view.Tinted = tinted.ToArray();
            view.BaseColors = new Color[colors.Count][];
            for (int i = 0; i < colors.Count; i++) view.BaseColors[i] = new[] { colors[i] };
        }

        static Color GroupShade(Color side, Group g) => g switch
        {
            Group.Ranged => Color.Lerp(side, Color.white, 0.35f),
            Group.Cavalry => side * 0.7f,
            _ => side,
        };

        Renderer Part(PrimitiveType type, Transform parent, Vector3 pos, Vector3 scale, Color color)
        {
            var go = GameObject.CreatePrimitive(type);
            var col = go.GetComponent<Collider>();
            if (col != null) Destroy(col);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = MaterialFor(color, r.sharedMaterial);
            return r;
        }

        Material MaterialFor(Color color, Material template)
        {
            if (baseMaterial == null) baseMaterial = template;
            if (materials.TryGetValue(color, out var m)) return m;
            m = new Material(baseMaterial) { color = color };
            if (m.HasProperty(BaseColorId)) m.SetColor(BaseColorId, color);
            materials[color] = m;
            return m;
        }

        void ShowDeath(UnitView v)
        {
            v.DeathShown = true;
            v.Ring.SetActive(false);
            if (v.Anim != null && art.Death.Length > 0)
            {
                v.Anim.speed = 1f;
                var c = art.Death[variety.Next(art.Death.Length)];
                v.Anim.CrossFadeInFixedTime(c.State, 0.1f);
                v.Loco = c.State;
                return;
            }
            v.Body.localPosition = new Vector3(0f, 0.15f, 0f);
            v.Body.localRotation = Quaternion.Euler(-85f, 0f, 0f);
            for (int i = 0; i < v.Tinted.Length; i++)
            {
                var c = Color.Lerp(v.BaseColors[i][0], DeadTint, 0.6f);
                block.SetColor(BaseColorId, c);
                block.SetColor(ColorId, c);
                v.Tinted[i].SetPropertyBlock(block);
            }
        }

        void RenderProjectiles()
        {
            seen.Clear();
            foreach (var p in sim.Projectiles)
            {
                if (p.Done) continue;
                seen.Add(p.Id);
                if (!projectiles.TryGetValue(p.Id, out var v))
                {
                    v = projectilePool.Count > 0 ? projectilePool.Pop() : CreateProjectile();
                    v.T.gameObject.SetActive(true);
                    v.Last = ToWorld(p.From, BattleRules.ShotHeight);
                    v.T.localScale = p.Kind == ProjectileKind.Ball ? Vector3.one * 0.12f : new Vector3(0.05f, 0.05f, 0.9f);
                    projectiles[p.Id] = v;
                }
                var pos = ToWorld(p.Pos, p.Height);
                var dir = pos - v.Last;
                if (dir.sqrMagnitude > 1e-6f) v.T.rotation = Quaternion.LookRotation(dir);
                v.T.position = pos;
                v.Last = pos;
            }
            stale.Clear();
            foreach (var kv in projectiles)
                if (!seen.Contains(kv.Key)) stale.Add(kv.Key);
            foreach (var id in stale)
            {
                var v = projectiles[id];
                v.T.gameObject.SetActive(false);
                projectilePool.Push(v);
                projectiles.Remove(id);
            }
        }

        ProjectileView CreateProjectile()
        {
            var r = Part(PrimitiveType.Cube, projectileRoot, Vector3.zero, Vector3.one, new Color(0.2f, 0.15f, 0.1f));
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return new ProjectileView { T = r.transform };
        }
    }
}
