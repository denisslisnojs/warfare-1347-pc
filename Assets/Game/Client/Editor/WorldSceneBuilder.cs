using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    static class WorldSceneBuilder
    {
        const string ScenePath = "Assets/Scenes/World.unity";

        static WorldSceneBuilder()
        {
            EditorApplication.delayCall += () =>
            {
                if (File.Exists(ScenePath) || EditorApplication.isPlayingOrWillChangePlaymode) return;
                Build(false);
            };
        }

        [MenuItem("Warfare/Пересоздать сцену карты мира")]
        static void BuildFromMenu() => Build(true);

        static void Build(bool open)
        {
            var current = EditorSceneManager.GetActiveScene().path;
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            foreach (var root in scene.GetRootGameObjects())
            {
                var light = root.GetComponent<Light>();
                if (light != null && light.type == LightType.Directional)
                {
                    root.name = "Sun";
                    light.shadows = LightShadows.Soft;
                }
                var cam = root.GetComponent<Camera>();
                if (cam != null)
                {
                    cam.farClipPlane = 6000f;
                    cam.fieldOfView = 35f;
                    if (root.GetComponent<RtsCamera>() == null) root.AddComponent<RtsCamera>();
                }
            }
            new GameObject("World").AddComponent<WorldMap>();
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
            var scenes = EditorBuildSettings.scenes.Where(s => s.path != ScenePath).ToList();
            scenes.Add(new EditorBuildSettingsScene(ScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            Debug.Log("[W1347] world scene created: " + ScenePath);
            if (!open && !string.IsNullOrEmpty(current)) EditorSceneManager.OpenScene(current);
        }
    }
}
