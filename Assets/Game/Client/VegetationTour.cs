using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Warfare.Client
{
    public sealed class VegetationTour : MonoBehaviour
    {
        public WorldMap Map;
        bool busy;
        string note;
        float noteUntil;

        static readonly float[] Distances = { 60f, 330f };
        const float Overview = 1400f;

        void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || busy || Map == null || Map.Cam == null) return;
            if (kb[Key.F10].wasPressedThisFrame) StartCoroutine(Run());
        }

        IEnumerator Run()
        {
            busy = true;
            var cam = Map.Cam;
            var focus = cam.Focus;
            float yaw = cam.Yaw, distance = cam.Distance, scale = Time.timeScale;
            Time.timeScale = 0f;
            string dir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "Screenshots", "vegetation");
            Directory.CreateDirectory(dir);
            var report = new StringBuilder();
            report.AppendLine("vegetation " + Map.VegetationReport);
            var sites = Map.Vegetation?.TestSites ?? new List<VegetationSite>();
            var shots = new List<(string name, Vector3 at, float d)>();
            foreach (var s in sites)
                foreach (var d in Distances) shots.Add((s.Name, Map.GeoToWorld(s.Lon, s.Lat), d));
            if (sites.Count > 0)
            {
                Map.RebuildVegetation();
                var home = Map.GeoToWorld(sites[0].Lon, sites[0].Lat);
                if (Map.NearestOfGroup("rockbig", home, false, out var rock)) shots.Add(("rocks", rock, 35f));
                if (Map.NearestOfGroup("rock", home, true, out var bank)) shots.Add(("rocks_bank", bank, 35f));
                if (Map.NearestOfGroup("boulder", home, false, out var boulder)) shots.Add(("boulder", boulder, 45f));
                foreach (var (lm, dist) in new[] { ("windmill", 30f), ("ruined_house", 30f), ("castle_ruins", 45f), ("castle_wall", 40f) })
                    if (Map.NearestLandmark(lm, home, out var spot)) shots.Add((lm, spot, dist));
                if (Map.NearestOfGroup("bush", home, false, out var bush)) shots.Add(("bushes", bush, 35f));
                if (Map.NearestCreature(home, false, out var herd)) shots.Add(("herd", herd, 35f));
                if (Map.NearestCreature(home, true, out var wild)) shots.Add(("wild", wild, 40f));
                if (Map.NearestShip(home, out var ship)) shots.Add(("ship", ship, 40f));
                var meadow = home + new Vector3(19f, 0f, 3f);
                shots.Add(("grass_close", meadow, 25f));
                shots.Add(("grass_mid", meadow, 55f));
                shots.Add(("grass_game", meadow, 330f));
                shots.Add(("overview", home, Overview));
            }

            foreach (var set in new[] { "packs" })
            {
                foreach (var (name, at, d) in shots)
                {
                    cam.LookAt(at, 0f, d);
                    for (int i = 0; i < 25; i++) yield return null;
                    float sum = 0f, worst = 0f;
                    for (int i = 0; i < 60; i++)
                    {
                        yield return null;
                        sum += Time.unscaledDeltaTime;
                        worst = Mathf.Max(worst, Time.unscaledDeltaTime);
                    }
                    var (inst, calls) = Map.VisibleVegetation(Camera.main.transform.position);
                    report.AppendLine($"{set} {name} {d:0}: {1000f * sum / 60f:0.0} ms avg, {1000f * worst:0.0} ms worst, {inst} instances, {calls} draws, grass {Map.GrassInstances}");
                    yield return new WaitForEndOfFrame();
                    var tex = ScreenCapture.CaptureScreenshotAsTexture();
                    File.WriteAllBytes(Path.Combine(dir, $"{name}_{d:0}_{set}.png"), tex.EncodeToPNG());
                    Destroy(tex);
                }
            }

            Map.RebuildVegetation();
            uint a = Map.VegetationChecksum;
            Map.RebuildVegetation();
            uint b = Map.VegetationChecksum;
            report.AppendLine(a == b ? $"repeat: same result {a:X8}" : $"repeat: DIFFERENT {a:X8} vs {b:X8}");
            File.WriteAllText(Path.Combine(dir, "report.txt"), report.ToString());
            Debug.Log("[W1347] vegetation tour\n" + report);
            cam.LookAt(focus, yaw, distance);
            Time.timeScale = scale;
            busy = false;
            note = "Снимки растительности сохранены";
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
