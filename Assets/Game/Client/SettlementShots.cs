using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Warfare.Client
{
    public sealed class SettlementShots : MonoBehaviour
    {
        public WorldMap Map;
        bool busy;
        string note;
        float noteUntil;

        [Serializable] sealed class ShotsFile { public string tag = "shots"; public string[] settlements = new string[0]; public float[] distances = { 40f, 120f, 330f }; public float yaw = 30f; }

        void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || busy || Map == null || Map.Cam == null) return;
            if (kb[Key.F11].wasPressedThisFrame) StartCoroutine(Run());
        }

        IEnumerator Run()
        {
            busy = true;
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "shots.json");
            var cfg = File.Exists(path) ? JsonUtility.FromJson<ShotsFile>(File.ReadAllText(path)) : new ShotsFile();
            var cam = Map.Cam;
            var focus = cam.Focus;
            float yaw = cam.Yaw, distance = cam.Distance, scale = Time.timeScale;
            Time.timeScale = 0f;
            string dir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "Screenshots", "settlements", cfg.tag);
            Directory.CreateDirectory(dir);
            int count = 0;
            foreach (var id in cfg.settlements)
            {
                PlacedSettlement s = null;
                foreach (var p in Map.Settlements)
                    if (p.Data.id == id) { s = p; break; }
                if (s == null) continue;
                foreach (var d in cfg.distances)
                {
                    cam.LookAt(s.Position, cfg.yaw, d);
                    for (int i = 0; i < 40; i++) yield return null;
                    yield return new WaitForEndOfFrame();
                    var tex = ScreenCapture.CaptureScreenshotAsTexture();
                    File.WriteAllBytes(Path.Combine(dir, $"{id}_{d:0}.png"), tex.EncodeToPNG());
                    Destroy(tex);
                    count++;
                }
            }
            cam.LookAt(focus, yaw, distance);
            Time.timeScale = scale;
            busy = false;
            note = $"Снимки поселений сохранены: {count}";
            noteUntil = Time.unscaledTime + 4f;
        }

        void OnGUI()
        {
            if (Time.unscaledTime > noteUntil || note == null) return;
            var style = new GUIStyle(GUI.skin.box) { fontSize = 18, alignment = TextAnchor.MiddleLeft };
            GUI.Box(new Rect(16, 56, 520, 34), note, style);
        }
    }
}
