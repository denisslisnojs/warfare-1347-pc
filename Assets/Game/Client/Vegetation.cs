using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Warfare.Client
{
    public sealed class Vegetation : MonoBehaviour
    {
        sealed class Layer
        {
            public Mesh Mesh;
            public Material Material;
            public readonly List<Matrix4x4[]> Batches = new List<Matrix4x4[]>();
            public readonly List<int> Counts = new List<int>();
        }

        const int Batch = 1023;
        readonly List<Layer> layers = new List<Layer>();

        public static Vegetation Create(MapData map, Material template)
        {
            var go = new GameObject("Vegetation");
            var v = go.AddComponent<Vegetation>();
            v.Build(map, template);
            return v;
        }

        void Build(MapData map, Material template)
        {
            var rnd = new System.Random(1347);
            var grassMats = new[] { Mat(template, new Color(0.38f, 0.55f, 0.22f)), Mat(template, new Color(0.45f, 0.6f, 0.25f)), Mat(template, new Color(0.33f, 0.5f, 0.2f)) };
            var grass = Tuft(rnd, 7, 0.22f, 0.45f, 0.035f);
            var grassLayers = new List<Layer>();
            foreach (var m in grassMats) grassLayers.Add(NewLayer(grass, m));

            var wheatMat = Mat(template, new Color(0.86f, 0.73f, 0.4f));
            var flaxMat = Mat(template, new Color(0.5f, 0.62f, 0.36f));
            var wheat = Stalks(rnd, 9, 0.75f, 1.0f);
            var wheatLayer = NewLayer(wheat, wheatMat);
            var flaxLayer = NewLayer(Stalks(rnd, 9, 0.6f, 0.8f), flaxMat);

            var flowerColors = new[] { new Color(0.95f, 0.9f, 0.4f), new Color(0.95f, 0.95f, 0.98f), new Color(0.85f, 0.3f, 0.3f), new Color(0.55f, 0.5f, 0.9f) };
            var flower = Flower();
            var flowerLayers = new List<Layer>();
            foreach (var c in flowerColors) flowerLayers.Add(NewLayer(flower, Mat(template, c)));

            float x0 = -170f, x1 = 170f, z0 = -125f, z1 = 125f;
            int grassCount = 52000;
            for (int i = 0; i < grassCount; i++)
            {
                float x = Range(rnd, x0, x1), z = Range(rnd, z0, z1);
                if (z > 86f && Mathf.Abs(x - 6f) < 45f && z < 160f) continue;
                string kind = KindAt(map, x, z);
                if (kind == "road" || kind == "plowed" || kind == "wheat" || kind == "barley" || kind == "flax") continue;
                Add(grassLayers[rnd.Next(grassLayers.Count)], rnd, x, z, Range(rnd, 0.7f, 1.35f));
                if ((kind == "meadow" ? 0.09 : 0.025) > rnd.NextDouble())
                    Add(flowerLayers[rnd.Next(flowerLayers.Count)], rnd, x + Range(rnd, -0.3f, 0.3f), z + Range(rnd, -0.3f, 0.3f), Range(rnd, 0.8f, 1.3f));
            }

            foreach (var p in map.patches)
            {
                if (p.kind != "wheat" && p.kind != "barley" && p.kind != "flax") continue;
                int n = Mathf.RoundToInt(p.w * p.h * 1.3f);
                var rot = Quaternion.Euler(0f, p.rot, 0f);
                var layer = p.kind == "flax" ? flaxLayer : wheatLayer;
                for (int i = 0; i < n; i++)
                {
                    var local = new Vector3(Range(rnd, -p.w / 2f, p.w / 2f), 0f, Range(rnd, -p.h / 2f, p.h / 2f));
                    var w = rot * local + new Vector3(p.x, 0f, p.z);
                    Add(layer, rnd, w.x, w.z, Range(rnd, 0.85f, 1.15f));
                }
            }
            int total = 0;
            foreach (var l in layers)
                foreach (var c in l.Counts) total += c;
            Debug.Log($"[W1347] vegetation instances: {total}");
        }

        static float Range(System.Random r, float a, float b) => a + (float)r.NextDouble() * (b - a);

        static string KindAt(MapData map, float x, float z)
        {
            string kind = "grass";
            foreach (var p in map.patches)
            {
                float a = -p.rot * Mathf.Deg2Rad;
                float dx = x - p.x, dz = z - p.z;
                float lx = dx * Mathf.Cos(a) - dz * Mathf.Sin(a);
                float lz = dx * Mathf.Sin(a) + dz * Mathf.Cos(a);
                if (Mathf.Abs(lx) <= p.w / 2f && Mathf.Abs(lz) <= p.h / 2f)
                {
                    if (p.layer > 0) return p.kind;
                    kind = p.kind;
                }
            }
            return kind;
        }

        Layer NewLayer(Mesh mesh, Material mat)
        {
            var l = new Layer { Mesh = mesh, Material = mat };
            layers.Add(l);
            return l;
        }

        static void Add(Layer l, System.Random rnd, float x, float z, float scale)
        {
            if (l.Batches.Count == 0 || l.Counts[l.Counts.Count - 1] >= Batch)
            {
                l.Batches.Add(new Matrix4x4[Batch]);
                l.Counts.Add(0);
            }
            int b = l.Batches.Count - 1;
            l.Batches[b][l.Counts[b]] = Matrix4x4.TRS(new Vector3(x, 0.01f, z), Quaternion.Euler(Range(rnd, -6f, 6f), Range(rnd, 0f, 360f), Range(rnd, -6f, 6f)), new Vector3(scale, scale * Range(rnd, 0.85f, 1.2f), scale));
            l.Counts[b]++;
        }

        void Update()
        {
            foreach (var l in layers)
            {
                var rp = new RenderParams(l.Material)
                {
                    shadowCastingMode = ShadowCastingMode.Off,
                    receiveShadows = true,
                    worldBounds = new Bounds(Vector3.zero, new Vector3(800f, 50f, 800f)),
                };
                for (int b = 0; b < l.Batches.Count; b++)
                    Graphics.RenderMeshInstanced(rp, l.Mesh, 0, l.Batches[b], l.Counts[b]);
            }
        }

        static Material Mat(Material template, Color c)
        {
            var m = new Material(template) { name = "veg", color = c, enableInstancing = true };
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", 0.05f);
            if (m.HasProperty("_Cull")) m.SetFloat("_Cull", 0f);
            m.doubleSidedGI = true;
            return m;
        }

        static Mesh Tuft(System.Random rnd, int blades, float hMin, float hMax, float width)
        {
            var v = new List<Vector3>();
            var t = new List<int>();
            for (int i = 0; i < blades; i++)
            {
                float a = Range(rnd, 0f, Mathf.PI * 2f);
                var dir = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
                var side = new Vector3(-dir.z, 0f, dir.x) * width;
                var basePos = dir * Range(rnd, 0f, 0.06f);
                float h = Range(rnd, hMin, hMax);
                var tip = basePos + dir * Range(rnd, 0.05f, 0.16f) + Vector3.up * h;
                int s = v.Count;
                v.Add(basePos - side);
                v.Add(basePos + side);
                v.Add(tip);
                t.AddRange(new[] { s, s + 1, s + 2 });
            }
            return Build(v, t);
        }

        static Mesh Stalks(System.Random rnd, int count, float hMin, float hMax)
        {
            var v = new List<Vector3>();
            var t = new List<int>();
            for (int i = 0; i < count; i++)
            {
                var basePos = new Vector3(Range(rnd, -0.18f, 0.18f), 0f, Range(rnd, -0.18f, 0.18f));
                float h = Range(rnd, hMin, hMax);
                float a = Range(rnd, 0f, Mathf.PI);
                var side = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
                var lean = new Vector3(Range(rnd, -0.08f, 0.08f), 0f, Range(rnd, -0.08f, 0.08f));
                Quad(v, t, basePos, basePos + lean + Vector3.up * h * 0.78f, side * 0.012f);
                Quad(v, t, basePos + lean + Vector3.up * h * 0.74f, basePos + lean * 1.15f + Vector3.up * h, side * 0.03f);
            }
            return Build(v, t);
        }

        static Mesh Flower()
        {
            var v = new List<Vector3>();
            var t = new List<int>();
            Quad(v, t, Vector3.zero, Vector3.up * 0.2f, new Vector3(0.008f, 0, 0));
            for (int i = 0; i < 3; i++)
            {
                float a = i * Mathf.PI / 3f;
                var side = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * 0.045f;
                Quad(v, t, Vector3.up * 0.17f, Vector3.up * 0.25f, side);
            }
            return Build(v, t);
        }

        static void Quad(List<Vector3> v, List<int> t, Vector3 bottom, Vector3 top, Vector3 halfWidth)
        {
            int s = v.Count;
            v.Add(bottom - halfWidth);
            v.Add(bottom + halfWidth);
            v.Add(top + halfWidth);
            v.Add(top - halfWidth);
            t.AddRange(new[] { s, s + 1, s + 2, s, s + 2, s + 3 });
        }

        static Mesh Build(List<Vector3> v, List<int> t)
        {
            var m = new Mesh { name = "veg" };
            m.SetVertices(v);
            m.SetTriangles(t, 0);
            var n = new Vector3[v.Count];
            for (int i = 0; i < n.Length; i++) n[i] = Vector3.up;
            m.normals = n;
            m.RecalculateBounds();
            return m;
        }
    }
}
