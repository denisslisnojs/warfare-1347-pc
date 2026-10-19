using System;
using System.IO;
using UnityEngine;
using Warfare.Core.Battle;

namespace Warfare.Client
{
    [Serializable]
    public sealed class MapSun
    {
        public float pitch = 45f;
        public float yaw = -35f;
        public float intensity = 1.3f;
        public float[] color = { 1f, 1f, 1f };
    }

    [Serializable]
    public sealed class MapPatch
    {
        public string kind = "grass";
        public float[] color;
        public float x;
        public float z;
        public float w;
        public float h;
        public float rot;
        public int layer;
    }

    [Serializable]
    public sealed class MapProp
    {
        public string id;
        public float x;
        public float z;
        public float rot;
        public float scale = 1f;
    }

    [Serializable]
    public sealed class MapData
    {
        public string name;
        public float[] ground;
        public float[] field;
        public MapSun sun;
        public float[] ambientSky;
        public float[] ambientEquator;
        public float[] ambientGround;
        public float[] fogColor;
        public float fogStart = 150f;
        public float fogEnd = 500f;
        public MapPatch[] patches = Array.Empty<MapPatch>();
        public MapProp[] props = Array.Empty<MapProp>();
    }

    public static class BattleMap
    {
        public static MapData Load(string id)
        {
            var path = Path.Combine(Application.streamingAssetsPath, "Data", "maps", id + ".json");
            if (!File.Exists(path)) return null;
            return JsonUtility.FromJson<MapData>(File.ReadAllText(path));
        }

        static Color C(float[] c, Color fallback) => c != null && c.Length >= 3 ? new Color(c[0], c[1], c[2]) : fallback;

        public static Transform Build(MapData map, Material template, out int missing)
        {
            missing = 0;
            var root = new GameObject("Map: " + map.name).transform;
            Material Mat(string kind, Color c, float w, float h)
            {
                var m = new Material(template) { color = Color.white };
                var tex = GroundTextures.Get(kind, c);
                if (m.HasProperty("_BaseMap")) m.SetTexture("_BaseMap", tex);
                m.mainTexture = tex;
                if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", Color.white);
                if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", 0.04f);
                float tile = GroundTextures.TileMeters(kind);
                m.mainTextureScale = new Vector2(w / tile, h / tile);
                if (m.HasProperty("_BaseMap")) m.SetTextureScale("_BaseMap", new Vector2(w / tile, h / tile));
                return m;
            }

            Plane(root, "Ground", new Vector3(0f, 0f, 0f), new Vector3(70f, 1f, 70f), 0f, Mat("grass", C(map.ground, new Color(0.36f, 0.5f, 0.24f)), 700f, 700f));
            Plane(root, "Field", new Vector3(0f, 0.01f, 0f), new Vector3(BattleRules.FieldLength / 10f, 1f, BattleRules.FieldWidth / 10f), 0f, Mat("grass", C(map.field, new Color(0.43f, 0.56f, 0.27f)), BattleRules.FieldLength, BattleRules.FieldWidth));
            for (int i = 0; i < map.patches.Length; i++)
            {
                var p = map.patches[i];
                float y = 0.015f + p.layer * 0.01f + (i % 7) * 0.0006f;
                Plane(root, "Patch", new Vector3(p.x, y, p.z), new Vector3(p.w / 10f, 1f, p.h / 10f), p.rot, Mat(string.IsNullOrEmpty(p.kind) ? "grass" : p.kind, C(p.color, Color.green), p.w, p.h));
            }

            var art = EnvironmentArt.Load();
            var props = new GameObject("Props").transform;
            props.SetParent(root, false);
            foreach (var p in map.props)
            {
                var prefab = art != null ? art.Get(p.id) : null;
                if (prefab == null)
                {
                    missing++;
                    continue;
                }
                var go = UnityEngine.Object.Instantiate(prefab, new Vector3(p.x, 0f, p.z), Quaternion.Euler(0f, p.rot, 0f), props);
                go.transform.localScale = Vector3.one * (p.scale <= 0 ? 1f : p.scale);
                foreach (var col in go.GetComponentsInChildren<Collider>()) UnityEngine.Object.Destroy(col);
            }

            ApplyLighting(map);
            var sunLight = RenderSettings.sun;
            if (sunLight == null)
                foreach (var l in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                    if (l.type == LightType.Directional) { sunLight = l; break; }
            Atmosphere.Create(sunLight, Camera.main, C(map.fogColor, new Color(0.75f, 0.8f, 0.85f))).transform.SetParent(root, false);
            Vegetation.Create(map, template).transform.SetParent(root, false);
            return root;
        }

        static void Plane(Transform parent, string name, Vector3 pos, Vector3 scale, float rot, Material m)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Plane);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(pos, Quaternion.Euler(0f, rot, 0f));
            go.transform.localScale = scale;
            UnityEngine.Object.Destroy(go.GetComponent<Collider>());
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = m;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }

        static void ApplyLighting(MapData map)
        {
            if (map.sun != null)
            {
                Light sun = RenderSettings.sun;
                if (sun == null)
                    foreach (var l in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
                        if (l.type == LightType.Directional) { sun = l; break; }
                if (sun != null)
                {
                    sun.transform.rotation = Quaternion.Euler(map.sun.pitch, map.sun.yaw, 0f);
                    sun.intensity = map.sun.intensity;
                    sun.color = C(map.sun.color, Color.white);
                }
            }
            if (map.ambientSky != null)
            {
                RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = C(map.ambientSky, Color.gray);
                RenderSettings.ambientEquatorColor = C(map.ambientEquator, Color.gray);
                RenderSettings.ambientGroundColor = C(map.ambientGround, Color.gray);
            }
            if (map.fogColor != null)
            {
                RenderSettings.fog = true;
                RenderSettings.fogMode = FogMode.Linear;
                RenderSettings.fogColor = C(map.fogColor, Color.gray);
                RenderSettings.fogStartDistance = map.fogStart;
                RenderSettings.fogEndDistance = map.fogEnd;
            }
        }
    }
}
