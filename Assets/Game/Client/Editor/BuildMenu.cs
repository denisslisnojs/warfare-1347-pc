using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.Rendering;

namespace Warfare.Client.Editor
{
    static class BuildMenu
    {
        const string Output = "Builds/Windows/Warfare1347.exe";

        static readonly string[] RuntimeShaders =
        {
            "Skybox/Procedural",
            "Universal Render Pipeline/Particles/Unlit",
            "Universal Render Pipeline/Lit",
        };

        [MenuItem("Warfare/Собрать игру для Windows")]
        public static void BuildWindows()
        {
            IncludeShaders();
            PlayerSettings.fullScreenMode = FullScreenMode.FullScreenWindow;
            PlayerSettings.defaultIsNativeResolution = true;
            PlayerSettings.productName = "Warfare 1347";
            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            if (scenes.Length == 0) scenes = new[] { "Assets/Scenes/Battle.unity" };
            Directory.CreateDirectory(Path.GetDirectoryName(Output));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = Output,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            });
            var s = report.summary;
            if (s.result == BuildResult.Succeeded)
            {
                Debug.Log($"[W1347] build ok: {Path.GetFullPath(Output)} ({s.totalSize / (1024 * 1024)} MB, {s.totalTime.TotalSeconds:0} s)");
                EditorUtility.RevealInFinder(Path.GetFullPath(Output));
            }
            else Debug.LogError($"[W1347] build failed: {s.result}, errors {s.totalErrors}");
        }

        static void IncludeShaders()
        {
            var graphics = AssetDatabase.LoadAssetAtPath<GraphicsSettings>("ProjectSettings/GraphicsSettings.asset");
            if (graphics == null) return;
            var so = new SerializedObject(graphics);
            var list = so.FindProperty("m_AlwaysIncludedShaders");
            if (list == null) return;
            foreach (var name in RuntimeShaders)
            {
                var shader = Shader.Find(name);
                if (shader == null) continue;
                bool present = false;
                for (int i = 0; i < list.arraySize; i++)
                    if (list.GetArrayElementAtIndex(i).objectReferenceValue == shader) present = true;
                if (present) continue;
                list.arraySize++;
                list.GetArrayElementAtIndex(list.arraySize - 1).objectReferenceValue = shader;
            }
            so.ApplyModifiedPropertiesWithoutUndo();
            AssetDatabase.SaveAssets();
        }
    }
}
