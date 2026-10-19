using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    static class GraphicsSetup
    {
        const string Marker = "W1347.GraphicsSetup.v1";

        static GraphicsSetup()
        {
            EditorApplication.delayCall += () =>
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode) return;
                if (EditorPrefs.GetString(Marker + Application.dataPath, "") == "done") return;
                Apply();
                EditorPrefs.SetString(Marker + Application.dataPath, "done");
            };
        }

        [MenuItem("Warfare/Настроить графику")]
        public static void Apply()
        {
            var assets = new HashSet<UniversalRenderPipelineAsset>();
            if (GraphicsSettings.defaultRenderPipeline is UniversalRenderPipelineAsset d) assets.Add(d);
            for (int i = 0; i < QualitySettings.count; i++)
                if (QualitySettings.GetRenderPipelineAssetAt(i) is UniversalRenderPipelineAsset q) assets.Add(q);
            var log = new List<string>();
            foreach (var asset in assets)
            {
                var so = new SerializedObject(asset);
                Set(so, "m_SupportsHDR", true, log);
                Set(so, "m_MSAA", 4, log);
                Set(so, "m_MainLightShadowsSupported", true, log);
                Set(so, "m_MainLightShadowmapResolution", 4096, log);
                Set(so, "m_ShadowDistance", 140f, log);
                Set(so, "m_ShadowCascadeCount", 4, log);
                Set(so, "m_SoftShadowsSupported", true, log);
                Set(so, "m_SoftShadowQuality", 3, log);
                Set(so, "m_SupportsLightCookies", true, log);
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(asset);

                var list = so.FindProperty("m_RendererDataList");
                for (int r = 0; list != null && r < list.arraySize; r++)
                    if (list.GetArrayElementAtIndex(r).objectReferenceValue is ScriptableRendererData data) AddSsao(data, log);
                log.Add(asset.name);
            }
            AssetDatabase.SaveAssets();
            Debug.Log("[W1347] graphics setup: " + string.Join("; ", log));
        }

        static void Set(SerializedObject so, string name, object value, List<string> log)
        {
            var p = so.FindProperty(name);
            if (p == null)
            {
                log.Add("no " + name);
                return;
            }
            switch (value)
            {
                case bool b: p.boolValue = b; break;
                case int i: p.intValue = i; break;
                case float f: p.floatValue = f; break;
            }
        }

        static void AddSsao(ScriptableRendererData data, List<string> log)
        {
            if (data.rendererFeatures.Any(f => f != null && f.GetType().Name == "ScreenSpaceAmbientOcclusion")) return;
            var type = typeof(UniversalRenderPipelineAsset).Assembly.GetType("UnityEngine.Rendering.Universal.ScreenSpaceAmbientOcclusion");
            if (type == null)
            {
                log.Add("SSAO type not found");
                return;
            }
            var feature = (ScriptableRendererFeature)ScriptableObject.CreateInstance(type);
            feature.name = "ScreenSpaceAmbientOcclusion";
            AssetDatabase.AddObjectToAsset(feature, data);
            var so = new SerializedObject(data);
            var features = so.FindProperty("m_RendererFeatures");
            var map = so.FindProperty("m_RendererFeatureMap");
            features.arraySize++;
            features.GetArrayElementAtIndex(features.arraySize - 1).objectReferenceValue = feature;
            if (map != null && AssetDatabase.TryGetGUIDAndLocalFileIdentifier(feature, out _, out long id))
            {
                map.arraySize++;
                map.GetArrayElementAtIndex(map.arraySize - 1).longValue = id;
            }
            so.ApplyModifiedPropertiesWithoutUndo();

            var fs = new SerializedObject(feature);
            var intensity = fs.FindProperty("m_Settings.Intensity");
            if (intensity != null) intensity.floatValue = 1.6f;
            var radius = fs.FindProperty("m_Settings.Radius");
            if (radius != null) radius.floatValue = 0.6f;
            var direct = fs.FindProperty("m_Settings.DirectLightingStrength");
            if (direct != null) direct.floatValue = 0.35f;
            fs.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(data);
            log.Add("SSAO -> " + data.name);
        }
    }
}
