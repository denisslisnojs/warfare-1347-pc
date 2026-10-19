using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Warfare.Client
{
    public sealed class Atmosphere : MonoBehaviour
    {
        public Vector2 CloudWind = new Vector2(2.2f, 1.1f);
        public float CloudSize = 160f;

        UniversalAdditionalLightData sunData;
        Vector2 cloudOffset;
        Transform pollen;
        DepthOfField dof;

        public VolumeProfile Profile { get; private set; }
        Vector3 dofBase, dofGoal;

        public sealed class Options
        {
            public float DofStart = 55f;
            public float DofEnd = 220f;
            public float CloudSize = 160f;
            public Vector2 CloudWind = new Vector2(2.2f, 1.1f);
            public bool Pollen = true;
        }

        public static Atmosphere Create(Light sun, Camera cam, Color fogColor, Options options = null)
        {
            var go = new GameObject("Atmosphere");
            var a = go.AddComponent<Atmosphere>();
            a.Setup(sun, cam, fogColor, options ?? new Options());
            return a;
        }

        void Setup(Light sun, Camera cam, Color fogColor, Options o)
        {
            CloudSize = o.CloudSize;
            CloudWind = o.CloudWind;
            Sky(sun, fogColor);
            Profile = PostProcessing(o);
            Profile.TryGet(out dof);
            dofBase = dofGoal = new Vector3(o.DofStart, o.DofEnd, 1.1f);
            if (cam != null)
            {
                var data = cam.GetUniversalAdditionalCameraData();
                data.renderPostProcessing = true;
                data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
                data.antialiasingQuality = AntialiasingQuality.High;
                cam.allowHDR = true;
            }
            if (sun != null)
            {
                sun.shadows = LightShadows.Soft;
                sun.shadowStrength = 0.82f;
                sun.shadowBias = 0.04f;
                sun.shadowNormalBias = 0.3f;
                sunData = sun.GetComponent<UniversalAdditionalLightData>();
                if (sunData == null) sunData = sun.gameObject.AddComponent<UniversalAdditionalLightData>();
                sun.cookie = CloudCookie();
                sunData.lightCookieSize = new Vector2(CloudSize, CloudSize);
            }
            if (cam != null && o.Pollen) pollen = Pollen(cam.transform).transform;
        }

        public void BlurBeyond(float start, float end, float radius) => dofGoal = new Vector3(start, end, radius);

        public void ClearBlur() => dofGoal = dofBase;

        public void SetBaseBlur(float start, float end)
        {
            bool idle = dofGoal == dofBase;
            dofBase = new Vector3(start, end, dofBase.z);
            if (idle) dofGoal = dofBase;
        }

        void Update()
        {
            if (dof != null)
            {
                var now = new Vector3(dof.gaussianStart.value, dof.gaussianEnd.value, dof.gaussianMaxRadius.value);
                if ((now - dofGoal).sqrMagnitude > 1e-4f)
                {
                    var next = Vector3.Lerp(now, dofGoal, 1f - Mathf.Exp(-3.5f * Time.unscaledDeltaTime));
                    if ((next - dofGoal).sqrMagnitude < 0.01f) next = dofGoal;
                    dof.gaussianStart.Override(next.x);
                    dof.gaussianEnd.Override(Mathf.Max(next.y, next.x + 1f));
                    dof.gaussianMaxRadius.Override(next.z);
                }
            }
            if (sunData != null)
            {
                cloudOffset += CloudWind * Time.deltaTime;
                sunData.lightCookieOffset = cloudOffset;
            }
        }

        static void Sky(Light sun, Color fogColor)
        {
            var shader = Shader.Find("Skybox/Procedural");
            if (shader != null)
            {
                var sky = new Material(shader) { name = "W1347 Sky" };
                sky.SetFloat("_SunDisk", 2f);
                sky.SetFloat("_SunSize", 0.035f);
                sky.SetFloat("_SunSizeConvergence", 6f);
                sky.SetFloat("_AtmosphereThickness", 0.85f);
                sky.SetColor("_SkyTint", new Color(0.5f, 0.6f, 0.78f));
                sky.SetColor("_GroundColor", new Color(0.42f, 0.44f, 0.38f));
                sky.SetFloat("_Exposure", 1.2f);
                RenderSettings.skybox = sky;
            }
            if (sun != null) RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Skybox;
            RenderSettings.ambientIntensity = 1.05f;
            RenderSettings.reflectionIntensity = 0.6f;
            RenderSettings.fogColor = fogColor;
            DynamicGI.UpdateEnvironment();
        }

        static VolumeProfile PostProcessing(Options o)
        {
            var go = new GameObject("PostProcessing");
            var volume = go.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.priority = 10;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            volume.sharedProfile = profile;

            var tone = profile.Add<Tonemapping>(true);
            tone.mode.Override(TonemappingMode.Neutral);

            var color = profile.Add<ColorAdjustments>(true);
            color.postExposure.Override(0.2f);
            color.contrast.Override(16f);
            color.saturation.Override(14f);

            var wb = profile.Add<WhiteBalance>(true);
            wb.temperature.Override(9f);
            wb.tint.Override(2f);

            var smh = profile.Add<ShadowsMidtonesHighlights>(true);
            smh.shadows.Override(new Vector4(0.92f, 0.95f, 1.08f, 0f));
            smh.highlights.Override(new Vector4(1.06f, 1.02f, 0.94f, 0f));

            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.Override(0.95f);
            bloom.intensity.Override(0.35f);
            bloom.scatter.Override(0.68f);

            var vignette = profile.Add<Vignette>(true);
            vignette.intensity.Override(0.26f);
            vignette.smoothness.Override(0.45f);

            var dof = profile.Add<DepthOfField>(true);
            dof.mode.Override(DepthOfFieldMode.Gaussian);
            dof.gaussianStart.Override(o.DofStart);
            dof.gaussianEnd.Override(o.DofEnd);
            dof.gaussianMaxRadius.Override(1.1f);
            dof.highQualitySampling.Override(true);
            return profile;
        }

        static Texture2D CloudCookie()
        {
            const int n = 256;
            var t = new Texture2D(n, n, TextureFormat.RGBA32, true) { name = "CloudShadows", wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float u = (float)x / n, v = (float)y / n;
                float c = 0, amp = 0.5f, norm = 0;
                for (int i = 0; i < 4; i++)
                {
                    int f = 3 << i;
                    float fx = u * f, fy = v * f;
                    float a = Mathf.PerlinNoise(fx + 11.3f, fy + 7.1f);
                    float b = Mathf.PerlinNoise(fx - f + 11.3f, fy + 7.1f);
                    float cc = Mathf.PerlinNoise(fx + 11.3f, fy - f + 7.1f);
                    float d = Mathf.PerlinNoise(fx - f + 11.3f, fy - f + 7.1f);
                    c += amp * Mathf.Lerp(Mathf.Lerp(a, b, u), Mathf.Lerp(cc, d, u), v);
                    norm += amp;
                    amp *= 0.5f;
                }
                c /= norm;
                float shade = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.42f, 0.62f, c));
                float lit = 1f - shade * 0.45f;
                px[y * n + x] = new Color(lit, lit, lit, lit);
            }
            t.SetPixels(px);
            t.Apply(true, true);
            return t;
        }

        static GameObject Pollen(Transform cam)
        {
            var go = new GameObject("Pollen");
            go.transform.SetParent(cam, false);
            go.transform.localPosition = new Vector3(0f, -2f, 14f);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.loop = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(6f, 10f);
            main.startSpeed = 0f;
            main.startSize = new ParticleSystem.MinMaxCurve(0.04f, 0.1f);
            main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.95f, 0.75f, 0.55f), new Color(1f, 1f, 0.9f, 0.3f));
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 600;
            var emission = ps.emission;
            emission.rateOverTime = 60f;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(40f, 8f, 40f);
            var vel = ps.velocityOverLifetime;
            vel.enabled = true;
            vel.space = ParticleSystemSimulationSpace.World;
            vel.x = new ParticleSystem.MinMaxCurve(0.2f, 0.7f);
            vel.y = new ParticleSystem.MinMaxCurve(-0.1f, 0.15f);
            vel.z = new ParticleSystem.MinMaxCurve(0.05f, 0.35f);
            var noise = ps.noise;
            noise.enabled = true;
            noise.strength = 0.25f;
            noise.frequency = 0.3f;
            var col = ps.colorOverLifetime;
            col.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                      new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.25f), new GradientAlphaKey(1f, 0.75f), new GradientAlphaKey(0f, 1f) });
            col.color = g;
            var r = go.GetComponent<ParticleSystemRenderer>();
            var shader = Shader.Find("Universal Render Pipeline/Particles/Unlit");
            if (shader != null)
            {
                var m = new Material(shader) { name = "Pollen" };
                m.SetFloat("_Surface", 1f);
                m.SetFloat("_Blend", 2f);
                m.SetOverrideTag("RenderType", "Transparent");
                m.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
                m.SetInt("_DstBlend", (int)BlendMode.One);
                m.SetInt("_ZWrite", 0);
                m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                m.renderQueue = (int)RenderQueue.Transparent;
                m.mainTexture = Dot();
                r.sharedMaterial = m;
            }
            ps.Play();
            return go;
        }

        static Texture2D Dot()
        {
            const int n = 32;
            var t = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
                t.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(1f - d * d)));
            }
            t.Apply();
            return t;
        }
    }
}
