using System.Collections.Generic;
using UnityEngine;

namespace Warfare.Client
{
    public sealed partial class WorldMap
    {
        Texture2D grassHabitat;
        Texture2D grassGroundDetail;
        Vector4 grassHabitatArea;
        readonly Dictionary<Vector2Int, List<Bounds>> grassObstacles = new Dictionary<Vector2Int, List<Bounds>>();

        float GrassBiomeDensity(float px, float py)
        {
            int bx = Mathf.Clamp((int)(px * biomeW / Meta.width), 0, biomeW - 1);
            int by = Mathf.Clamp((int)(py * biomeH / Meta.height), 0, biomeH - 1);
            int b = biomes[by * biomeW + bx];
            return b < BiomeNames.Length && grassCfg.Biomes.TryGetValue(BiomeNames[b], out var density) ? density : 0f;
        }

        float GrassObstacleMask(float wx, float wz)
        {
            float mask = 1;
            if (!grassObstacles.TryGetValue(new Vector2Int(Mathf.FloorToInt(wx / 16f), Mathf.FloorToInt(wz / 16f)), out var obstacles)) return mask;
            foreach (var bounds in obstacles)
            {
                float dx = Mathf.Max(Mathf.Abs(wx - bounds.center.x) - bounds.extents.x, 0);
                float dz = Mathf.Max(Mathf.Abs(wz - bounds.center.z) - bounds.extents.z, 0);
                mask *= Mathf.SmoothStep(0, 1, Mathf.Sqrt(dx * dx + dz * dz) / 0.45f);
                if (mask == 0) break;
            }
            return mask;
        }

        void SetupGrassHabitat()
        {
            string detailPath = System.IO.Path.Combine(Application.streamingAssetsPath, "Data", "world", "detail", "meadow.png");
            if (System.IO.File.Exists(detailPath)) grassGroundDetail = LoadTexture(detailPath, true, TextureWrapMode.Repeat);
            var area = grassCfg.TestArea;
            var center = area != null ? GeoToWorld(area.Lon, area.Lat) : Vector3.zero;
            float width = area != null ? area.Radius * 2f + 4f : Meta.width;
            float depth = area != null ? width : Meta.height;
            grassHabitatArea = new Vector4(center.x - width * 0.5f, center.z - depth * 0.5f, width, depth);
            int size = area != null ? 512 : 1024;
            int rows = area != null ? size : Mathf.CeilToInt(size * depth / width);
            grassHabitat = new Texture2D(size, rows, TextureFormat.RGBAHalf, false, true) { name = "GrassHabitat", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var obstacles = new List<Bounds>();
            foreach (var st in placed)
            {
                if (!st.HasFootprint) continue;
                var bounds = st.Footprint;
                bounds.Expand(new Vector3(0.6f, 0f, 0.6f));
                obstacles.Add(bounds);
            }
            foreach (var l in landmarks)
                obstacles.Add(new Bounds(new Vector3(l.px.x - Meta.width / 2f, 0, Meta.height / 2f - l.px.y), new Vector3(l.r * 1.2f, 1000, l.r * 1.2f)));
            grassObstacles.Clear();
            foreach (var bounds in obstacles)
            {
                for (int z = Mathf.FloorToInt((bounds.min.z - 1) / 16f); z <= Mathf.FloorToInt((bounds.max.z + 1) / 16f); z++)
                for (int x = Mathf.FloorToInt((bounds.min.x - 1) / 16f); x <= Mathf.FloorToInt((bounds.max.x + 1) / 16f); x++)
                {
                    var key = new Vector2Int(x, z);
                    if (!grassObstacles.TryGetValue(key, out var list)) grassObstacles[key] = list = new List<Bounds>();
                    list.Add(bounds);
                }
            }
            var pixels = new Color[size * rows];
            for (int y = 0; y < rows; y++)
            for (int x = 0; x < size; x++)
            {
                float wx = grassHabitatArea.x + (x + 0.5f) / size * width;
                float wz = grassHabitatArea.y + (y + 0.5f) / rows * depth;
                float px = wx + Meta.width / 2f, py = Meta.height / 2f - wz;
                var n = GrassGroundNormal(px, py);
                float h = MeshHeight(px, py);
                float mask = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(SeaLevel + 0.16f, SeaLevel + 0.55f, h));
                mask *= 1f - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(12f, 100f, RoadValue(px, py)));
                mask *= 1f - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(rockLo * 0.85f, rockLo, h));
                mask *= Mathf.SmoothStep(0, 1, Mathf.InverseLerp(0.78f, 0.94f, n.y));
                if (area != null)
                    mask *= 1f - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(area.Radius - 12f, area.Radius, Vector2.Distance(new Vector2(wx, wz), new Vector2(center.x, center.z))));
                mask *= GrassObstacleMask(wx, wz);
                if (GrassBiomeDensity(px, py) <= 0) mask = 0;
                var p = new Vector2(px, py);
                foreach (var bridge in bridgeSpans)
                {
                    var ab = bridge.B - bridge.A;
                    float t = Mathf.Clamp01(Vector2.Dot(p - bridge.A, ab) / Mathf.Max(ab.sqrMagnitude, 0.0001f));
                    mask *= Mathf.SmoothStep(0, 1, Mathf.InverseLerp(1.4f, 2f, Vector2.Distance(p, bridge.A + ab * t)));
                }
                pixels[y * size + x] = new Color(n.x * 0.5f + 0.5f, n.y * 0.5f + 0.5f, n.z * 0.5f + 0.5f, mask);
            }
            grassHabitat.SetPixels(pixels);
            grassHabitat.Apply(false, false);
            foreach (var mat in new[] { terrainMat, grassMat, shellMat })
            {
                if (mat == null) continue;
                mat.SetTexture("_Habitat", grassHabitat);
                mat.SetTexture("_MeadowGround", grassGroundDetail != null ? grassGroundDetail : terrainMat.GetTexture("_Grass"));
                mat.SetVector("_HabitatArea", grassHabitatArea);
                mat.SetFloat("_GroundVariation", grassCfg.GroundVariation);
                mat.SetFloat("_FarDensity", grassCfg.FarDensity);
                mat.SetVector("_LodRange", new Vector4(grassCfg.ThinningStart, grassCfg.ThinningEnd, 0, 0));
            }
        }

        float GrassHabitat(float wx, float wz)
        {
            if (grassHabitat == null) return 0;
            float mask = grassHabitat.GetPixelBilinear((wx - grassHabitatArea.x) / grassHabitatArea.z, (wz - grassHabitatArea.y) / grassHabitatArea.w).a;
            mask *= GrassObstacleMask(wx, wz);
            var p = new Vector2(wx + Meta.width / 2f, Meta.height / 2f - wz);
            foreach (var bridge in bridgeSpans)
            {
                var ab = bridge.B - bridge.A;
                float t = Mathf.Clamp01(Vector2.Dot(p - bridge.A, ab) / Mathf.Max(ab.sqrMagnitude, 0.0001f));
                mask *= Mathf.SmoothStep(0, 1, Mathf.InverseLerp(1.4f, 2f, Vector2.Distance(p, bridge.A + ab * t)));
            }
            return mask;
        }

        Vector3 GrassGroundNormal(float px, float py)
        {
            int gw = (Meta.width - 1) / MeshStep + 1, gh = (Meta.height - 1) / MeshStep + 1;
            int x = Mathf.Clamp(Mathf.FloorToInt(px / MeshStep), 0, gw - 2), y = Mathf.Clamp(Mathf.FloorToInt(py / MeshStep), 0, gh - 2);
            Vector3 N(int gx, int gy) => new Vector3(GridHeight(Mathf.Max(0, gx - 1), gy, gw, gh) - GridHeight(Mathf.Min(gw - 1, gx + 1), gy, gw, gh), 2f * MeshStep, GridHeight(gx, Mathf.Min(gh - 1, gy + 1), gw, gh) - GridHeight(gx, Mathf.Max(0, gy - 1), gw, gh)).normalized;
            float fx = Mathf.Clamp01(px / MeshStep - x), fy = Mathf.Clamp01(py / MeshStep - y);
            var a = N(x, y); var b = N(x + 1, y); var c = N(x, y + 1); var d = N(x + 1, y + 1);
            if (Mathf.Abs(GridHeight(x, y, gw, gh) - GridHeight(x + 1, y + 1, gw, gh)) < Mathf.Abs(GridHeight(x + 1, y, gw, gh) - GridHeight(x, y + 1, gw, gh)))
                return (fx > fy ? a + (b - a) * fx + (d - b) * fy : a + (d - c) * fx + (c - a) * fy).normalized;
            return (fx + fy < 1f ? a + (b - a) * fx + (c - a) * fy : d + (c - d) * (1f - fx) + (b - d) * (1f - fy)).normalized;
        }

        void DisposeGrass()
        {
            if (grassMat != null) Destroy(grassMat);
            if (shellMat != null) Destroy(shellMat);
            if (grassHabitat != null) Destroy(grassHabitat);
            if (grassGroundDetail != null) Destroy(grassGroundDetail);
            if (grassMeshes != null) foreach (var mesh in grassMeshes) if (mesh != null) Destroy(mesh);
            grassCells.Clear();
            grassObstacles.Clear();
            grassFarCells.Clear();
        }
    }
}
