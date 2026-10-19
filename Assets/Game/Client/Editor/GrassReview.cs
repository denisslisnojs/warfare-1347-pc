using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    public static class GrassReview
    {
        static int frames, shot, lastFrame = -1;
        static double sum, worst;
        static readonly double[] Samples = new double[120];
        [System.Serializable]
        sealed class Site { public float lon = 18.65f, lat = 54.35f, offsetX = 0f, offsetZ = -12f; }
        static Site site;
        static bool motion;
        static readonly float[] Distances = { 12f, 40f, 80f, 110f, 150f, 330f, 1400f, 40f };
        static string Run => File.Exists("grass-review-run.txt") ? File.ReadAllText("grass-review-run.txt").Trim() : "final-review";
        static GrassReview() { EditorApplication.update += Tick; }
        [MenuItem("Warfare/Трава/Снять тестовый участок")]
        public static void Start()
        {
            frames = 0; shot = 0; lastFrame = -1; sum = 0; worst = 0;
            site = File.Exists("grass-review-site.json") ? JsonUtility.FromJson<Site>(File.ReadAllText("grass-review-site.json")) : new Site();
            SessionState.SetBool("GrassReview", true);
            EditorSceneManager.OpenScene("Assets/Scenes/World.unity");
            Application.runInBackground = true;
            EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (File.Exists("grass-review-command.txt"))
            {
                File.Delete("grass-review-command.txt");
                SessionState.SetBool("GrassReviewRestart", true);
                EditorApplication.isPlaying = false;
                return;
            }
            if (SessionState.GetBool("GrassReviewRestart", false) && !EditorApplication.isPlaying && !EditorApplication.isCompiling)
            {
                SessionState.SetBool("GrassReviewRestart", false);
                motion = false;
                Start();
                return;
            }
            if (!SessionState.GetBool("GrassReview", false) || !EditorApplication.isPlaying || EditorApplication.isPaused) return;
            var map = Object.FindFirstObjectByType<WorldMap>();
            if (map == null || map.Cam == null) return;
            if (Time.frameCount == lastFrame) return;
            lastFrame = Time.frameCount;
            if (motion) { MoveCamera(map); return; }
            Time.timeScale = 0f;
            var cam = map.Cam;
            if (site == null) site = File.Exists("grass-review-site.json") ? JsonUtility.FromJson<Site>(File.ReadAllText("grass-review-site.json")) : new Site();
            cam.MinDistance = 8f;
            cam.MinPitch = shot == 7 ? 84f : 38f;
            cam.MaxPitch = shot == 7 ? 84f : 72f;
            cam.LookAt(map.GeoToWorld(site.lon, site.lat) + new Vector3(site.offsetX, 0, site.offsetZ), 0f, Distances[shot]);
            frames++;
            if (frames < 180) return;
            if (frames < 300)
            {
                sum += Time.unscaledDeltaTime;
                Samples[frames - 180] = Time.unscaledDeltaTime;
                worst = System.Math.Max(worst, Time.unscaledDeltaTime);
                return;
            }
            string dir = "Screenshots/grass-review/" + Run;
            Directory.CreateDirectory(dir);
            ScreenCapture.CaptureScreenshot(dir + "/" + shot + "_" + Distances[shot] + "_game.png");
            var camera = Camera.main;
            var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32);
            camera.targetTexture = rt;
            camera.Render();
            RenderTexture.active = rt;
            var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0);
            tex.Apply();
            File.WriteAllBytes(dir + "/" + shot + "_" + Distances[shot] + ".png", tex.EncodeToPNG());
            camera.targetTexture = null;
            RenderTexture.active = null;
            Object.Destroy(tex);
            Object.Destroy(rt);
            System.Array.Sort(Samples);
            File.AppendAllText(dir + "/timings.txt", $"shot {shot}, distance {Distances[shot]}, 120 editor frames mean {sum / 120 * 1000:F2} ms, median {Samples[60] * 1000:F2} ms, p95 {Samples[114] * 1000:F2} ms, worst {worst * 1000:F2} ms, grass {map.GrassInstances}, Game View {Screen.width}x{Screen.height}, GPU {SystemInfo.graphicsDeviceName}\n");
            Debug.Log("GRASS_REVIEW_CAPTURE " + Run + " " + shot + " project=" + Application.dataPath);
            frames = 0; sum = 0; worst = 0;
            shot++;
            if (shot < Distances.Length) return;
            var audit = typeof(WorldMap).GetMethod("AuditGrass");
            if (audit != null) File.WriteAllText(dir + "/audit.txt", (string)audit.Invoke(map, null));
            foreach (var name in new[] { "Warfare/WorldTerrain", "Warfare/Grass", "Warfare/GrassShell" })
            {
                var shader = Shader.Find(name);
                File.AppendAllText(dir + "/shaders.txt", name + " error=" + (shader == null || ShaderUtil.ShaderHasError(shader)) + "\n");
            }
            if (Run.StartsWith("final")) { motion = true; frames = 0; return; }
            SessionState.SetBool("GrassReview", false);
            Time.timeScale = 1;
            if (File.Exists("grass-review-auto-exit.txt") && !File.Exists("grass-review-keep-open.txt")) EditorApplication.Exit(0);
        }

        static void MoveCamera(WorldMap map)
        {
            var cam = map.Cam;
            cam.MinPitch = 38; cam.MaxPitch = 72;
            float t = frames / 159f;
            var home = map.GeoToWorld(site.lon, site.lat) + new Vector3(site.offsetX, 0, site.offsetZ);
            cam.LookAt(home + new Vector3(t * 12f, 0, 0), t * 15f, Mathf.Lerp(55f, 210f, t));
            string dir = "Screenshots/grass-review/" + Run + "/motion";
            if (frames % 8 == 0)
            {
                Directory.CreateDirectory(dir);
                var camera = Camera.main;
                var rt = new RenderTexture(960, 540, 24);
                camera.targetTexture = rt; camera.Render(); RenderTexture.active = rt;
                var tex = new Texture2D(960, 540, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, 960, 540), 0, 0); tex.Apply();
                File.WriteAllBytes(dir + "/" + frames.ToString("D3") + ".png", tex.EncodeToPNG());
                camera.targetTexture = null; RenderTexture.active = null;
                Object.Destroy(tex); Object.Destroy(rt);
            }
            frames++;
            if (frames < 160) return;
            cam.LookAt(home, 0, 110);
            motion = false;
            SessionState.SetBool("GrassReview", false);
            Time.timeScale = 1;
            File.WriteAllText(dir + "/complete.txt", "160 real game frames, zoom 55 to 210, translation 12, yaw 0 to 15\n");
            if (File.Exists("grass-review-auto-exit.txt") && !File.Exists("grass-review-keep-open.txt")) EditorApplication.Exit(0);
        }

        [MenuItem("Warfare/Трава/Снять тестовый участок", true)]
        static bool CanStart() => !EditorApplication.isPlayingOrWillChangePlaymode && !EditorApplication.isCompiling;
    }
}
