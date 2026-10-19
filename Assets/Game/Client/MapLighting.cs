using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Warfare.Core;

namespace Warfare.Client
{
    public sealed class LightPreset
    {
        public string Id = "original";
        public string Name = "Исходный";
        public float SunPitch = 42f;
        public float SunYaw = -35f;
        public float SunIntensity = 1.55f;
        public float[] SunColor = { 1f, 0.93f, 0.82f };
        public float ShadowStrength = 0.82f;
        public SoftShadowQuality SoftShadows = SoftShadowQuality.UsePipelineSettings;
        public string Ambient = "skybox";
        public float AmbientIntensity = 1.05f;
        public float[] AmbientSky;
        public float[] AmbientEquator;
        public float[] AmbientGround;
        public float ReflectionIntensity = 0.6f;
        public ColorGrade Grade = new ColorGrade();
        public float FogStart = 900f;
        public float FogEnd = 3200f;
        public bool FogFollowsCamera;
        public float[] FogColor = { 0.74f, 0.8f, 0.86f };
        public float BlurStart = 700f;
        public float BlurEnd = 2600f;
    }

    public sealed class ColorGrade
    {
        public float Exposure = 0.2f;
        public float Contrast = 16f;
        public float Saturation = 14f;
        public float Temperature = 9f;
        public float Tint = 2f;
        public float YellowGreenSaturation = 0.5f;
        public float YellowGreenHue = 0.5f;
    }

    public sealed class LightingFile
    {
        public string Active;
        public List<float> Shots = new List<float> { 60f, 330f, 1400f };
        public List<LightPreset> Presets = new List<LightPreset>();
    }

    public sealed class MapLighting : MonoBehaviour
    {
        Light sun;
        UniversalAdditionalLightData sunData;
        RtsCamera cam;
        VolumeProfile profile;
        Atmosphere air;
        LightingFile file;
        int current;
        float labelUntil;
        bool busy;
        string note;

        public void Setup(Light light, RtsCamera rts, Atmosphere air)
        {
            sun = light;
            cam = rts;
            this.air = air;
            if (air != null) profile = air.Profile;
            if (sun != null) sunData = sun.GetComponent<UniversalAdditionalLightData>();
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "lighting.json");
            file = File.Exists(path) ? DataJson.Read<LightingFile>(File.ReadAllText(path)) : null;
            if (file == null) file = new LightingFile();
            if (file.Presets.Count == 0) file.Presets.Add(new LightPreset());
            current = Mathf.Max(0, file.Presets.FindIndex(p => p.Id == file.Active));
            Apply(file.Presets[current]);
        }

        void Apply(LightPreset p)
        {
            if (sun != null)
            {
                sun.transform.rotation = Quaternion.Euler(p.SunPitch, p.SunYaw, 0f);
                sun.intensity = p.SunIntensity;
                sun.color = C(p.SunColor, Color.white);
                sun.shadowStrength = p.ShadowStrength;
                if (sunData != null) sunData.softShadowQuality = p.SoftShadows;
            }
            if (p.Ambient == "trilight")
            {
                RenderSettings.ambientMode = AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = C(p.AmbientSky, Color.gray);
                RenderSettings.ambientEquatorColor = C(p.AmbientEquator, Color.gray);
                RenderSettings.ambientGroundColor = C(p.AmbientGround, Color.gray);
            }
            else
            {
                RenderSettings.ambientMode = AmbientMode.Skybox;
                RenderSettings.ambientIntensity = p.AmbientIntensity;
            }
            RenderSettings.reflectionIntensity = p.ReflectionIntensity;
            DynamicGI.UpdateEnvironment();
            Grade(p.Grade ?? new ColorGrade());
            RenderSettings.fogColor = C(p.FogColor, Color.gray);
            Fog(p);
            if (air != null) air.SetBaseBlur(p.BlurStart, p.BlurEnd);
        }

        void Fog(LightPreset p)
        {
            float k = p.FogFollowsCamera && cam != null ? cam.Distance : 1f;
            RenderSettings.fogStartDistance = p.FogStart * k;
            RenderSettings.fogEndDistance = p.FogEnd * k;
        }

        void Grade(ColorGrade g)
        {
            if (profile == null) return;
            if (profile.TryGet(out ColorAdjustments color))
            {
                color.postExposure.Override(g.Exposure);
                color.contrast.Override(g.Contrast);
                color.saturation.Override(g.Saturation);
            }
            if (profile.TryGet(out WhiteBalance wb))
            {
                wb.temperature.Override(g.Temperature);
                wb.tint.Override(g.Tint);
            }
            if (!profile.TryGet(out ColorCurves curves)) curves = profile.Add<ColorCurves>(true);
            curves.hueVsSat.Override(HueBump(g.YellowGreenSaturation));
            curves.hueVsHue.Override(HueBump(g.YellowGreenHue));
        }

        static TextureCurve HueBump(float v) => new TextureCurve(new[] { new Keyframe(0.08f, 0.5f), new Keyframe(0.23f, v), new Keyframe(0.38f, 0.5f) }, 0.5f, true, new Vector2(0f, 1f));

        void Update()
        {
            if (file != null) Fog(file.Presets[current]);
            var kb = Keyboard.current;
            if (kb == null || busy) return;
            if (kb[Key.F8].wasPressedThisFrame)
            {
                current = (current + 1) % file.Presets.Count;
                Apply(file.Presets[current]);
                note = null;
                labelUntil = Time.unscaledTime + 3f;
            }
            if (kb[Key.F9].wasPressedThisFrame && cam != null) StartCoroutine(Compare());
        }

        IEnumerator Compare()
        {
            busy = true;
            var focus = cam.Focus;
            float yaw = cam.Yaw, distance = cam.Distance, scale = Time.timeScale;
            int keep = current;
            Time.timeScale = 0f;
            string dir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "Screenshots", "lighting");
            Directory.CreateDirectory(dir);
            foreach (var d in file.Shots)
            {
                cam.LookAt(focus, yaw, d);
                for (int i = 0; i < 4; i++) yield return null;
                for (int k = 0; k < file.Presets.Count; k++)
                {
                    Apply(file.Presets[k]);
                    for (int i = 0; i < 3; i++) yield return null;
                    yield return new WaitForEndOfFrame();
                    var tex = ScreenCapture.CaptureScreenshotAsTexture();
                    File.WriteAllBytes(Path.Combine(dir, $"{Mathf.RoundToInt(d)}_{file.Presets[k].Id}.png"), tex.EncodeToPNG());
                    Destroy(tex);
                }
            }
            current = keep;
            Apply(file.Presets[current]);
            cam.LookAt(focus, yaw, distance);
            Time.timeScale = scale;
            busy = false;
            note = "Снимки сохранены в Screenshots/lighting";
            labelUntil = Time.unscaledTime + 4f;
        }

        void OnGUI()
        {
            if (busy || Time.unscaledTime > labelUntil) return;
            var style = new GUIStyle(GUI.skin.box) { fontSize = 18, alignment = TextAnchor.MiddleLeft };
            GUI.Box(new Rect(16, 16, 520, 34), note ?? "Свет: " + file.Presets[current].Name, style);
        }

        static Color C(float[] v, Color fallback) => v != null && v.Length >= 3 ? new Color(v[0], v[1], v[2]) : fallback;
    }
}
