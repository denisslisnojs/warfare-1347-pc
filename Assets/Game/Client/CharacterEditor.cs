using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using Warfare.Core;

namespace Warfare.Client
{
    public sealed class CharacterEditor : MonoBehaviour
    {
        public GameObject Model;

        static readonly Color Ink = new Color(0.97f, 0.93f, 0.82f);
        static readonly Color Gold = new Color(0.78f, 0.62f, 0.32f);
        static readonly string[] Tabs = { "Тело", "Лицо", "Глаза", "Волосы" };
        static readonly string[] TabIcons = { "icon_tab_body", "icon_tab_face", "icon_tab_eyes", "icon_tab_hair" };
        static readonly string[] TabTips = { "Случайный цвет кожи", "Случайное лицо", "Случайные глаза", "Случайные волосы" };

        LooksData data;
        HeroLook look;
        GameObject hero;
        Transform turntable;
        Camera cam;
        int tab;
        float yaw;
        float zoom;
        float zoomTarget;
        readonly System.Random rng = new System.Random();

        [System.NonSerialized] bool styled;
        [System.NonSerialized] GUIStyle title, label, button, tabStyle, chosen, tabChosen, panelStyle, sliderTrack, sliderThumb;
        Transform[] feet;
        readonly System.Collections.Generic.Dictionary<string, Texture2D> icons = new System.Collections.Generic.Dictionary<string, Texture2D>();
        float[] footRest;
        [System.NonSerialized] Texture2D panelTex;
        Rect panel;

        void Start()
        {
            data = HeroLooks.LoadData();
            look = HeroLooks.LoadSaved() ?? HeroLooks.Default(data);
            if (!data.HairStyles.Exists(h => h.Id == look.HairStyle)) look.HairStyle = HeroLooks.Default(data).HairStyle;
            look.Beard ??= "none";
            look.Moustache ??= "none";
            cam = Camera.main;
            Stage();
            Spawn();
            Refresh();
        }

        void Refresh()
        {
            if (hero != null) HeroLooks.Apply(hero, look, data);
        }

        static Material Lit(Color c, float smooth)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) return null;
            var m = new Material(shader);
            m.SetColor("_BaseColor", c);
            m.SetFloat("_Smoothness", smooth);
            return m;
        }

        void Stage()
        {
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.075f, 0.065f, 0.06f);
            cam.fieldOfView = 30f;
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 200f;
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = true;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.3f, 0.25f, 0.2f);
            RenderSettings.ambientEquatorColor = new Color(0.22f, 0.17f, 0.13f);
            RenderSettings.ambientGroundColor = new Color(0.1f, 0.075f, 0.055f);
            var sun = FindAnyObjectByType<Light>();
            if (sun != null)
            {
                sun.transform.rotation = Quaternion.Euler(34f, 150f, 0f);
                sun.intensity = 1.5f;
                sun.color = new Color(1f, 0.76f, 0.48f);
                sun.shadows = LightShadows.Soft;
                sun.shadowStrength = 0.9f;
            }
            foreach (var (name, rot, power, tint) in new[]
            {
                ("Fill", new Vector3(12f, -160f, 0f), 0.42f, new Color(0.95f, 0.82f, 0.68f)),
                ("Rim", new Vector3(20f, 15f, 0f), 1.1f, new Color(1f, 0.7f, 0.42f)),
            })
            {
                var l = new GameObject(name).AddComponent<Light>();
                l.type = LightType.Directional;
                l.intensity = power;
                l.color = tint;
                l.shadows = LightShadows.None;
                l.transform.rotation = Quaternion.Euler(rot);
            }
            Backdrop();
            Grade();
            var floor = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            floor.name = "Podium";
            podium = floor;
            Destroy(floor.GetComponent<Collider>());
            floor.transform.localScale = new Vector3(1.8f, 0.02f, 1.8f);
            floor.transform.position = new Vector3(0f, -0.02f, 0f);
            var mat = Lit(new Color(0.2f, 0.15f, 0.105f), 0.08f);
            if (mat != null) floor.GetComponent<Renderer>().material = mat;
            ContactShadow();
        }

        void ContactShadow()
        {
            var shader = Shader.Find("Universal Render Pipeline/Unlit");
            if (shader == null) return;
            const int n = 128;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float dx = (x + 0.5f) / n * 2f - 1f, dy = (y + 0.5f) / n * 2f - 1f;
                float a = Mathf.Clamp01(1f - Mathf.Sqrt(dx * dx + dy * dy));
                px[y * n + x] = new Color(0.03f, 0.02f, 0.015f, a * a * (3f - 2f * a) * 0.75f);
            }
            tex.SetPixels(px);
            tex.Apply();
            var m = new Material(shader);
            m.SetTexture("_BaseMap", tex);
            m.SetColor("_BaseColor", Color.white);
            m.SetFloat("_Surface", 1f);
            m.SetFloat("_Blend", 0f);
            m.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            m.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            m.SetFloat("_ZWrite", 0f);
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad.name = "ContactShadow";
            Destroy(quad.GetComponent<Collider>());
            var r = quad.GetComponent<Renderer>();
            r.material = m;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            quad.transform.position = new Vector3(0f, 0.003f, 0f);
            quad.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            quad.transform.localScale = new Vector3(0.75f, 0.55f, 1f);
            if (podium != null) quad.transform.SetParent(podium.transform, true);
        }

        static readonly string[] Backdrops = { "editor_bg_1" };
        int backdropIndex;
        Transform backdrop;
        Material backdropMat;

        void Backdrop()
        {
            var shader = Shader.Find("Universal Render Pipeline/Unlit");
            if (shader == null) return;
            var quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad.name = "Backdrop";
            Destroy(quad.GetComponent<Collider>());
            var r = quad.GetComponent<Renderer>();
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            backdropMat = new Material(shader);
            r.material = backdropMat;
            backdrop = quad.transform;
            backdrop.SetParent(cam.transform, false);
            UseBackdrop(0);
        }

        void UseBackdrop(int i)
        {
            if (backdropMat == null) return;
            backdropIndex = (i + Backdrops.Length) % Backdrops.Length;
            var tex = Load(Path.Combine(Application.streamingAssetsPath, "Data", "world", "ui"), Backdrops[backdropIndex], ".jpg");
            backdropMat.SetTexture("_BaseMap", tex);
            backdropMat.SetColor("_BaseColor", new Color(0.82f, 0.8f, 0.78f));
        }

        void FitBackdrop()
        {
            if (backdrop == null) return;
            const float d = 150f;
            float h = 2f * d * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) * 1.02f;
            float w = h * cam.aspect;
            if (w / h < 16f / 9f) w = h * 16f / 9f; else h = w * 9f / 16f;
            backdrop.localPosition = new Vector3(0f, 0f, d);
            backdrop.localRotation = Quaternion.identity;
            backdrop.localScale = new Vector3(w, h, 1f);
        }

        void Grade()
        {
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            var vignette = profile.Add<Vignette>(true);
            vignette.intensity.Override(0.38f);
            vignette.smoothness.Override(0.5f);
            vignette.color.Override(new Color(0.05f, 0.03f, 0.02f));
            var colour = profile.Add<ColorAdjustments>(true);
            colour.colorFilter.Override(new Color(1f, 0.93f, 0.84f));
            colour.contrast.Override(8f);
            colour.saturation.Override(-6f);
            var bloom = profile.Add<Bloom>(true);
            bloom.intensity.Override(0.35f);
            bloom.threshold.Override(1.1f);
            var vol = new GameObject("Grade").AddComponent<Volume>();
            vol.isGlobal = true;
            vol.priority = 10f;
            vol.profile = profile;
        }

        void Spawn()
        {
            turntable = new GameObject("Turntable").transform;
            if (Model == null) return;
            hero = Instantiate(Model, turntable);
            hero.name = "Hero";
            var anim = hero.GetComponent<Animator>();
            if (anim != null)
            {
                anim.applyRootMotion = false;
                anim.runtimeAnimatorController = Resources.Load<RuntimeAnimatorController>("EditorIdle");
            }
            if (anim != null && anim.isHuman)
            {
                feet = new[] { HumanBodyBones.LeftFoot, HumanBodyBones.RightFoot, HumanBodyBones.LeftToes, HumanBodyBones.RightToes }
                    .Select(anim.GetBoneTransform).Where(b => b != null).ToArray();
                footRest = feet.Select(f => f.position.y - hero.transform.position.y).ToArray();
            }
            var head = anim != null && anim.isHuman ? anim.GetBoneTransform(HumanBodyBones.Head) : null;
            var eyes = hero.GetComponentsInChildren<Renderer>().FirstOrDefault(r => r.name.Contains("Eyes"));
            if (head == null || eyes == null) return;
            var f = eyes.bounds.center - head.position;
            f.y = 0f;
            if (f.sqrMagnitude > 1e-6f) hero.transform.rotation = Quaternion.Euler(0f, Vector3.SignedAngle(f, Vector3.forward, Vector3.up), 0f) * hero.transform.rotation;
            if (anim == null || anim.runtimeAnimatorController == null) Stand(anim);
        }

        Transform chest;
        Quaternion chestRest;

        void Aim(Transform bone, Transform child, Vector3 dir)
        {
            if (bone == null || child == null) return;
            bone.rotation = Quaternion.FromToRotation(child.position - bone.position, dir) * bone.rotation;
        }

        void Stand(Animator anim)
        {
            var t = hero.transform;
            foreach (var (upper, lower, hand, side) in new[]
            {
                (HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand, 1f),
                (HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand, -1f),
            })
            {
                var u = anim.GetBoneTransform(upper);
                var l = anim.GetBoneTransform(lower);
                var h = anim.GetBoneTransform(hand);
                if (u == null || l == null) continue;
                var outward = Vector3.Dot(l.position - u.position, t.right) >= 0f ? t.right : -t.right;
                Aim(u, l, (-t.up * 0.985f + outward * 0.17f).normalized);
                Aim(l, h, (-t.up * 0.96f + outward * 0.1f + t.forward * 0.25f).normalized);
            }
            chest = anim.GetBoneTransform(HumanBodyBones.UpperChest) ?? anim.GetBoneTransform(HumanBodyBones.Chest);
            if (chest != null) chestRest = chest.localRotation;
        }

        bool shooting;

        void Update()
        {
            var kb = UnityEngine.InputSystem.Keyboard.current;
            if (kb != null && kb.f11Key.wasPressedThisFrame && !shooting) StartCoroutine(Shots());
        }

        System.Collections.IEnumerator Shots()
        {
            shooting = true;
            string dir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "docs", "showcase", "raw");
            Directory.CreateDirectory(dir);
            int keepStep = step, keepTab = tab;
            float keepZoom = zoomTarget;
            step = 0;
            pick = Mathf.Max(0, factions?.FindIndex(f => f.Faction == "vallerois") ?? 0);
            for (int i = 0; i < 20; i++) yield return null;
            ScreenCapture.CaptureScreenshot(Path.Combine(dir, "faction.png"));
            yield return new WaitForSeconds(0.5f);
            step = 1;
            for (int t = 0; t < Tabs.Length; t++)
            {
                tab = t;
                zoomTarget = t == 1 || t == 2 ? 0.8f : 0f;
                yield return new WaitForSeconds(1.6f);
                ScreenCapture.CaptureScreenshot(Path.Combine(dir, "editor_" + t + ".png"));
                yield return new WaitForSeconds(0.4f);
            }
            step = keepStep;
            tab = keepTab;
            zoomTarget = keepZoom;
            shooting = false;
            Debug.Log("[W1347] showcase screenshots saved: " + dir);
        }

        void LateUpdate()
        {
            if (chest != null) chest.localRotation = chestRest * Quaternion.Euler(Mathf.Sin(Time.time * 1.6f) * 1.2f, 0f, 0f);
            zoom = Mathf.Lerp(zoom, zoomTarget, 1f - Mathf.Exp(-7f * Time.deltaTime));
            var target = Vector3.Lerp(new Vector3(0f, 0.92f, 0f), new Vector3(0f, 1.56f, 0f), zoom);
            float dist = Mathf.Lerp(4.6f, 1.05f, zoom);
            cam.transform.position = target + new Vector3(0f, Mathf.Lerp(0.2f, 0.02f, zoom), dist);
            cam.transform.LookAt(target);
            cam.transform.position -= cam.transform.right * Mathf.Lerp(0.62f, 0.15f, zoom);
            if (turntable != null)
            {
                turntable.rotation = Quaternion.Euler(0f, yaw, 0f);
                turntable.gameObject.SetActive(step == 1);
            }
            if (podium != null) podium.SetActive(step == 1);
            FitBackdrop();
            if (feet != null && feet.Length > 0)
            {
                float low = float.MaxValue;
                for (int i = 0; i < feet.Length; i++) low = Mathf.Min(low, feet[i].position.y - hero.transform.position.y - footRest[i]);
                hero.transform.localPosition = new Vector3(0f, -low, 0f);
            }
        }

        static Texture2D Load(string dir, string name, string ext = ".png")
        {
            string path = Path.Combine(dir, name + ext);
            if (!File.Exists(path)) return null;
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, true) { name = name, wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Trilinear };
            t.LoadImage(File.ReadAllBytes(path), true);
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

        static void Paint(GUIStyle style, Color c)
        {
            style.normal.textColor = c;
            style.hover.textColor = c;
            style.active.textColor = c;
            style.focused.textColor = c;
        }

        void Setup()
        {
            styled = true;
            string uiDir = Path.Combine(Application.streamingAssetsPath, "Data", "world", "ui");
            var serif = GameFonts.Text;
            title = new GUIStyle(GUI.skin.label) { font = GameFonts.Heading, alignment = TextAnchor.MiddleCenter, wordWrap = false };
            Paint(title, Ink);
            label = new GUIStyle(GUI.skin.label) { font = serif, alignment = TextAnchor.MiddleLeft, wordWrap = false };
            Paint(label, new Color(0.93f, 0.78f, 0.47f));
            var edge = new Color(0.62f, 0.48f, 0.25f);
            var dark = new Color(0.05f, 0.035f, 0.025f);
            button = new GUIStyle(GUI.skin.button) { font = GameFonts.Button, alignment = TextAnchor.MiddleCenter, border = new RectOffset(4, 4, 4, 4), padding = new RectOffset(8, 8, 2, 2) };
            button.normal.background = Plate(new Color(0.16f, 0.12f, 0.085f), new Color(0.09f, 0.07f, 0.05f), edge, dark);
            button.hover.background = Plate(new Color(0.55f, 0.4f, 0.19f), new Color(0.33f, 0.22f, 0.1f), new Color(0.96f, 0.8f, 0.45f), dark);
            button.active.background = button.hover.background;
            Paint(button, Ink);
            chosen = new GUIStyle(button);
            chosen.normal.background = Plate(new Color(0.66f, 0.5f, 0.24f), new Color(0.42f, 0.29f, 0.13f), new Color(1f, 0.88f, 0.55f), dark);
            chosen.hover.background = chosen.normal.background;
            Paint(chosen, new Color(1f, 0.96f, 0.85f));
            tabStyle = new GUIStyle(button) { padding = new RectOffset(2, 2, 2, 2) };
            tabChosen = new GUIStyle(chosen) { padding = new RectOffset(2, 2, 2, 2) };
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
                foreach (var st in new[] { button, chosen, tabStyle, tabChosen })
                {
                    st.border = Border("ui_button");
                    st.normal.background = st == chosen || st == tabChosen ? lit : plate;
                    st.hover.background = st.active.background = lit;
                }
                button.padding = chosen.padding = new RectOffset(40, 40, 2, 2);
                tabStyle.padding = tabChosen.padding = new RectOffset(14, 14, 2, 2);
            }
            panelTex = new Texture2D(1, 2, TextureFormat.RGBA32, false) { hideFlags = HideFlags.DontSave, wrapMode = TextureWrapMode.Clamp };
            panelTex.SetPixels(new[] { new Color(0.06f, 0.045f, 0.035f, 0.95f), new Color(0.13f, 0.095f, 0.07f, 0.95f) });
            panelTex.Apply();
            sliderTrack = new GUIStyle();
            sliderThumb = new GUIStyle();
            sliderThumb.normal.background = Plate(new Color(0.85f, 0.68f, 0.36f), new Color(0.6f, 0.45f, 0.2f), new Color(1f, 0.9f, 0.6f), dark);
            sliderThumb.hover.background = Plate(new Color(1f, 0.85f, 0.5f), new Color(0.75f, 0.58f, 0.28f), new Color(1f, 0.95f, 0.75f), dark);
            sliderThumb.active.background = sliderThumb.hover.background;
        }

        void Bar(Rect r, Color c)
        {
            GUI.color = c;
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            GUI.color = Color.white;
        }

        float Slider(Rect r, float v, float k)
        {
            float tw = 12f * k;
            sliderThumb.fixedWidth = tw;
            sliderThumb.fixedHeight = r.height;
            float mid = r.y + r.height * 0.5f;
            Bar(new Rect(r.x, mid - 3f * k, r.width, 6f * k), new Color(0.03f, 0.025f, 0.02f, 0.9f));
            float cx = r.x + r.width * 0.5f;
            float vx = r.x + tw * 0.5f + (r.width - tw) * (v + 1f) * 0.5f;
            Bar(new Rect(Mathf.Min(cx, vx), mid - 2f * k, Mathf.Abs(vx - cx), 4f * k), Gold);
            Bar(new Rect(cx - 1f, mid - 7f * k, 2f, 14f * k), new Color(Gold.r, Gold.g, Gold.b, 0.6f));
            return GUI.HorizontalSlider(r, v, -1f, 1f, sliderTrack, sliderThumb);
        }

        float SliderRows(System.Collections.Generic.IEnumerable<LookKey> keys, float x, float y, float w, float k)
        {
            foreach (var key in keys)
            {
                GUI.Label(new Rect(x, y, w, 20f * k), key.Name, label);
                y += 20f * k;
                float v = look.Get(key.Id);
                float nv = Slider(new Rect(x, y, w, 20f * k), v, k);
                if (!Mathf.Approximately(nv, v))
                {
                    look.Face[key.Id] = nv;
                    if (key.Id.StartsWith("Eyes")) look.Eyes = null;
                    Refresh();
                }
                y += 26f * k;
            }
            return y;
        }

        float Swatches(System.Collections.Generic.List<LookColor> list, string current, System.Action<string> pick, float x, float y, float w, float k)
        {
            float s = 38f * k, gap = 8f * k;
            int perRow = Mathf.Max(1, Mathf.FloorToInt((w + gap) / (s + gap)));
            for (int i = 0; i < list.Count; i++)
            {
                var r = new Rect(x + (i % perRow) * (s + gap), y + (i / perRow) * (s + gap), s, s);
                bool on = list[i].Id == current;
                Bar(r, on ? new Color(1f, 0.88f, 0.55f) : new Color(0.62f, 0.48f, 0.25f));
                Bar(new Rect(r.x + 3f * k, r.y + 3f * k, r.width - 6f * k, r.height - 6f * k), HeroLooks.Hex(list[i].Color));
                if (GUI.Button(r, GUIContent.none, GUIStyle.none))
                {
                    pick(list[i].Id);
                    Refresh();
                }
            }
            int rows = (list.Count + perRow - 1) / perRow;
            float yEnd = y + rows * (s + gap);
            var name = HeroLooks.Find(list, current)?.Name ?? "";
            GUI.Label(new Rect(x, yEnd, w, 24f * k), name, label);
            return yEnd + 34f * k;
        }

        float Picker(string caption, System.Collections.Generic.List<LookKey> list, string current, System.Action<string> pick, float x, float y, float w, float k)
        {
            if (list.Count == 0) return y;
            GUI.Label(new Rect(x, y, w, 24f * k), caption, label);
            y += 28f * k;
            int i = Mathf.Max(0, list.FindIndex(s => s.Id == current));
            float a = 34f * k;
            int step = 0;
            if (GUI.Button(new Rect(x, y, a, a), "‹", tabStyle)) step = -1;
            if (GUI.Button(new Rect(x + w - a, y, a, a), "›", tabStyle)) step = 1;
            GUI.Box(new Rect(x + a + 6f * k, y, w - 2f * a - 12f * k, a), list[i].Name, tabStyle);
            if (step != 0)
            {
                pick(list[(i + step + list.Count) % list.Count].Id);
                Refresh();
            }
            return y + a + 16f * k;
        }

        Texture2D Icon(string id)
        {
            if (!icons.TryGetValue(id, out var t)) icons[id] = t = Load(Path.Combine(Application.streamingAssetsPath, "Data", "world", "ui", "icons"), id);
            return t;
        }

        bool IconButton(Rect r, string icon, string fallback, Vector2 mouse, float k)
        {
            bool hover = r.Contains(mouse);
            var tex = Icon(icon);
            if (tex != null)
            {
                GUI.color = new Color(1f, 1f, 1f, hover ? 1f : 0.85f);
                GUI.DrawTexture(r, tex, ScaleMode.ScaleToFit);
                GUI.color = Color.white;
                return GUI.Button(r, GUIContent.none, GUIStyle.none);
            }
            return GUI.Button(r, fallback, hover ? tabChosen : tabStyle);
        }

        void RandomTab()
        {
            if (tab == 0)
            {
                if (data.Skin.Count > 0) look.Skin = data.Skin[rng.Next(data.Skin.Count)].Id;
                return;
            }
            if (tab == 3)
            {
                if (data.Hair.Count > 0) look.Hair = data.Hair[rng.Next(data.Hair.Count)].Id;
                HeroLooks.RandomStyles(look, data, rng);
                return;
            }
            bool eyes = tab == 2;
            foreach (var key in data.Face)
                if (key.Id.StartsWith("Eyes") == eyes) look.Face[key.Id] = (float)(rng.NextDouble() * 2.0 - 1.0) * 0.8f;
            if (eyes) look.Eyes = null;
        }

        sealed class TownFile
        {
            public string Name;
            public bool Capital;
        }

        sealed class FactionFile
        {
            public string Faction;
            public string Name;
            public string Motto;
            public string Lore;
            public float[] Color;
            public System.Collections.Generic.List<TownFile> Towns = new System.Collections.Generic.List<TownFile>();
            [System.NonSerialized] public Texture2D Art;
            [System.NonSerialized] public Texture2D Emblem;
            [System.NonSerialized] public Texture2D Banner;
        }

        static readonly string[] FactionOrder = { "vallerois", "varden", "vinland", "grim", "azhar", "khordan" };
        System.Collections.Generic.List<FactionFile> factions;
        int step;
        int pick;
        GameObject podium;
        [System.NonSerialized] GUIStyle lore, motto, cardName, bigName, capStyle;

        void LoadFactions()
        {
            factions = new System.Collections.Generic.List<FactionFile>();
            string dir = Path.Combine(Application.streamingAssetsPath, "Data", "world", "factions");
            string ui = Path.Combine(Application.streamingAssetsPath, "Data", "world", "ui");
            if (!Directory.Exists(dir)) return;
            foreach (var path in Directory.GetFiles(dir, "*.json"))
            {
                var f = DataJson.Read<FactionFile>(File.ReadAllText(path));
                if (f == null || string.IsNullOrEmpty(f.Faction)) continue;
                f.Art = Load(Path.Combine(ui, "factions"), "faction_" + f.Faction);
                f.Emblem = Load(ui, "emblem_" + f.Faction);
                f.Banner = Load(Path.Combine(ui, "factions"), "card_" + f.Faction);
                factions.Add(f);
            }
            factions.Sort((a, b) =>
            {
                int ia = System.Array.IndexOf(FactionOrder, a.Faction), ib = System.Array.IndexOf(FactionOrder, b.Faction);
                return (ia < 0 ? 99 : ia).CompareTo(ib < 0 ? 99 : ib);
            });
            pick = Mathf.Max(0, factions.FindIndex(f => f.Faction == look.Faction));
        }

        static Color FactionColor(FactionFile f) => f.Color != null && f.Color.Length >= 3 ? new Color(f.Color[0], f.Color[1], f.Color[2]) : new Color(0.3f, 0.25f, 0.2f);

        void Frame(Rect r, Color c, float t)
        {
            Bar(new Rect(r.x, r.y, r.width, t), c);
            Bar(new Rect(r.x, r.yMax - t, r.width, t), c);
            Bar(new Rect(r.x, r.y, t, r.height), c);
            Bar(new Rect(r.xMax - t, r.y, t, r.height), c);
        }

        void Picture(Rect r, FactionFile f, bool big)
        {
            GUI.color = Color.white;
            if (!big && f.Banner != null)
            {
                GUI.DrawTexture(r, f.Banner, ScaleMode.ScaleAndCrop);
                return;
            }
            if (big && f.Art != null)
            {
                GUI.DrawTexture(r, f.Art, big ? ScaleMode.ScaleToFit : ScaleMode.ScaleAndCrop);
                return;
            }
            var c = FactionColor(f);
            if (!big) Bar(r, new Color(c.r * 0.55f, c.g * 0.55f, c.b * 0.55f, 0.95f));
            if (f.Emblem != null)
            {
                float s = Mathf.Min(r.width, r.height) * (big ? 0.8f : 0.62f);
                GUI.DrawTexture(new Rect(r.center.x - s / 2f, r.center.y - s / 2f - (big ? 0f : r.height * 0.06f), s, s), f.Emblem, ScaleMode.ScaleToFit);
            }
        }

        void DrawFactions(float k)
        {
            if (lore == null)
            {
                lore = new GUIStyle(label) { wordWrap = true, alignment = TextAnchor.UpperCenter };
                Paint(lore, new Color(Ink.r, Ink.g, Ink.b, 0.92f));
                motto = new GUIStyle(label) { wordWrap = true, alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Italic };
                cardName = new GUIStyle(title) { font = GameFonts.Button, wordWrap = true };
                bigName = new GUIStyle(title);
                capStyle = new GUIStyle(motto) { fontStyle = FontStyle.Normal };
            }
            lore.fontSize = Mathf.RoundToInt(15 * k);
            motto.fontSize = capStyle.fontSize = Mathf.RoundToInt(15 * k);
            cardName.fontSize = Mathf.RoundToInt(12.5f * k);
            bigName.fontSize = Mathf.RoundToInt(28 * k);
            Bar(new Rect(0f, 0f, Screen.width, Screen.height), new Color(0f, 0f, 0f, 0.55f));
            if (factions == null || factions.Count == 0) return;
            var e = Event.current;
            var right = new Rect(Screen.width - 24f * k - 500f * k, 24f * k, 500f * k, Screen.height - 48f * k);
            GUI.color = Color.white;
            if (panelStyle != null) GUI.Box(right, GUIContent.none, panelStyle);
            else GUI.DrawTexture(right, panelTex);
            float x = right.x + 30f * k, w = right.width - 60f * k, y = right.y + 26f * k;
            GUI.Label(new Rect(x, y, w, 34f * k), "Выберите державу", title);
            y += 52f * k;
            int cols = 3, rows = (factions.Count + cols - 1) / cols;
            float gap = 14f * k;
            float cw = (w - gap) / cols;
            float avail = right.yMax - 96f * k - y;
            float ch = Mathf.Min(cw * 1.5f, (avail - gap * (rows - 1)) / rows);
            for (int i = 0; i < factions.Count; i++)
            {
                var f = factions[i];
                var r = new Rect(x + (i % cols) * (cw + gap), y + (i / cols) * (ch + gap), cw, ch);
                bool on = i == pick, hover = r.Contains(e.mousePosition);
                Picture(r, f, false);
                Bar(new Rect(r.x, r.yMax - 40f * k, r.width, 40f * k), new Color(0f, 0f, 0f, 0.62f));
                Paint(cardName, on ? new Color(1f, 0.86f, 0.5f) : Ink);
                GUI.Label(new Rect(r.x + 4f * k, r.yMax - 40f * k, r.width - 8f * k, 40f * k), f.Name, cardName);
                Frame(r, on ? new Color(1f, 0.86f, 0.5f) : hover ? new Color(0.85f, 0.68f, 0.36f) : new Color(0.45f, 0.35f, 0.18f), (on ? 3f : 1.5f) * k);
                if (GUI.Button(r, GUIContent.none, GUIStyle.none)) pick = i;
            }
            if (GUI.Button(new Rect(x, right.yMax - 70f * k, w, 42f * k), "Далее", chosen))
            {
                look.Faction = factions[pick].Faction;
                step = 1;
            }

            var cur = factions[pick];
            float lx = 24f * k;
            float lw = right.x - 16f * k - lx;
            float pictureH = Mathf.Min(Screen.height * 0.66f, lw * 0.75f);
            Picture(new Rect(lx, 16f * k, lw, pictureH), cur, true);
            float ty = 16f * k + pictureH + 2f * k;
            GUI.Label(new Rect(lx, ty, lw, 40f * k), cur.Name, bigName);
            ty += 44f * k;
            if (!string.IsNullOrEmpty(cur.Motto))
            {
                GUI.Label(new Rect(lx + lw * 0.1f, ty, lw * 0.8f, 26f * k), "«" + cur.Motto + "»", motto);
                ty += 36f * k;
            }
            GUI.Label(new Rect(lx + lw * 0.1f, ty, lw * 0.8f, Screen.height - ty - 16f * k), cur.Lore ?? "", lore);
        }

        void OnGUI()
        {
            if (data == null) return;
            if (!styled) Setup();
            float k = Mathf.Max(1f, Screen.height / 720f);
            title.fontSize = Mathf.RoundToInt(24 * k);
            label.fontSize = Mathf.RoundToInt(14 * k);
            button.fontSize = chosen.fontSize = Mathf.RoundToInt(15 * k);
            tabStyle.fontSize = tabChosen.fontSize = Mathf.RoundToInt(13 * k);
            if (factions == null) LoadFactions();
            if (step == 0)
            {
                DrawFactions(k);
                return;
            }

            panel = new Rect(24f * k, 24f * k, 380f * k, Screen.height - 48f * k);
            var e = Event.current;
            if (!panel.Contains(e.mousePosition))
            {
                if (e.type == EventType.MouseDrag && e.button == 0)
                {
                    yaw -= e.delta.x * 0.5f;
                    e.Use();
                }
                else if (e.type == EventType.ScrollWheel)
                {
                    zoomTarget = Mathf.Clamp01(zoomTarget - e.delta.y * 0.06f);
                    e.Use();
                }
            }

            GUI.color = Color.white;
            if (panelStyle != null) GUI.Box(panel, GUIContent.none, panelStyle);
            else GUI.DrawTexture(panel, panelTex);

            float x = panel.x + 28f * k, w = panel.width - 56f * k, y = panel.y + 26f * k;
            GUI.Label(new Rect(x, y, w, 34f * k), "Облик героя", title);
            y += 48f * k;
            float ts = 54f * k, tg = 14f * k;
            float tx = panel.center.x - (ts * Tabs.Length + tg * (Tabs.Length - 1)) / 2f;
            for (int i = 0; i < Tabs.Length; i++)
            {
                var r = new Rect(tx + i * (ts + tg), y, ts, ts);
                if (i == tab) Bar(new Rect(r.x - 3f * k, r.yMax + 4f * k, r.width + 6f * k, 3f * k), new Color(1f, 0.85f, 0.5f));
                var tex = Icon(TabIcons[i]);
                bool hover = r.Contains(e.mousePosition);
                if (tex != null)
                {
                    GUI.color = new Color(1f, 1f, 1f, i == tab ? 1f : hover ? 0.9f : 0.55f);
                    GUI.DrawTexture(r, tex, ScaleMode.ScaleToFit);
                    GUI.color = Color.white;
                    if (GUI.Button(r, GUIContent.none, GUIStyle.none)) tab = i;
                }
                else if (GUI.Button(r, Tabs[i].Substring(0, 1), i == tab ? tabChosen : tabStyle)) tab = i;
            }
            y += ts + 14f * k;
            var head = new GUIStyle(title) { fontSize = Mathf.RoundToInt(17 * k) };
            GUI.Label(new Rect(x, y, w, 26f * k), Tabs[tab], head);
            y += 38f * k;

            if (tab == 0)
            {
                GUI.Label(new Rect(x, y, w, 24f * k), "Цвет кожи", label);
                y += 30f * k;
                Swatches(data.Skin, look.Skin, id => look.Skin = id, x, y, w, k);
            }
            else if (tab == 1) SliderRows(data.Face.Where(f => !f.Id.StartsWith("Eyes")), x, y, w, k);
            else if (tab == 2)
            {
                float bw = (w - 8f * k) / 2f;
                for (int i = 0; i < data.EyePresets.Count; i++)
                {
                    var p = data.EyePresets[i];
                    var r = new Rect(x + (i % 2) * (bw + 8f * k), y + (i / 2) * 42f * k, bw, 34f * k);
                    if (GUI.Button(r, p.Name, look.Eyes == p.Id ? tabChosen : tabStyle))
                    {
                        HeroLooks.UsePreset(look, p);
                        Refresh();
                    }
                }
                y += ((data.EyePresets.Count + 1) / 2) * 42f * k + 18f * k;
                SliderRows(data.Face.Where(f => f.Id.StartsWith("Eyes")), x, y, w, k);
            }
            else
            {
                y = Picker("Причёска", data.HairStyles, look.HairStyle, id => look.HairStyle = id, x, y, w, k);
                y = Picker("Борода", data.Beards, look.Beard, id => look.Beard = id, x, y, w, k);
                y = Picker("Усы", data.Moustaches, look.Moustache, id => look.Moustache = id, x, y, w, k);
                GUI.Label(new Rect(x, y, w, 24f * k), "Цвет волос и бровей", label);
                y += 30f * k;
                Swatches(data.Hair, look.Hair, id => look.Hair = id, x, y, w, k);
            }

            float by = panel.yMax - 112f * k;
            float sq = 46f * k;
            var mouse = e.mousePosition;
            string tip = null;
            float gx = panel.center.x - (sq * 3f + 20f * k) / 2f;
            float lx = x;
            x = gx;
            if (IconButton(new Rect(x, by - 10f * k, sq, sq), "icon_dice", "Вкладка", mouse, k))
            {
                RandomTab();
                Refresh();
            }
            if (new Rect(x, by - 10f * k, sq, sq).Contains(mouse)) tip = TabTips[tab];
            if (IconButton(new Rect(x + sq + 10f * k, by - 10f * k, sq, sq), "icon_dice_all", "Всё", mouse, k))
            {
                look = HeroLooks.Random(data, 0.8f, rng, true);
                Refresh();
            }
            if (new Rect(x + sq + 10f * k, by - 10f * k, sq, sq).Contains(mouse)) tip = "Всё случайно";
            if (IconButton(new Rect(x + (sq + 10f * k) * 2f, by - 10f * k, sq, sq), "icon_reset", "Сброс", mouse, k))
            {
                look = HeroLooks.Default(data);
                Refresh();
            }
            if (new Rect(x + (sq + 10f * k) * 2f, by - 10f * k, sq, sq).Contains(mouse)) tip = "Сбросить всё";
            x = lx;
            if (tip != null)
            {
                var centred = new GUIStyle(label) { alignment = TextAnchor.MiddleCenter };
                GUI.Label(new Rect(x, by - 38f * k, w, 24f * k), tip, centred);
            }
            if (GUI.Button(new Rect(x, by + 46f * k, w * 0.36f, 40f * k), "Назад", tabStyle)) step = 0;
            if (GUI.Button(new Rect(x + w * 0.39f, by + 46f * k, w * 0.61f, 40f * k), "Завершить", chosen))
            {
                HeroLooks.Save(look);
                SceneManager.LoadScene("World");
            }
        }
    }
}
