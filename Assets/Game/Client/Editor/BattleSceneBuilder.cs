using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    static class BattleSceneBuilder
    {
        const string ScenePath = "Assets/Scenes/Battle.unity";

        static BattleSceneBuilder()
        {
            EditorApplication.delayCall += AutoCreate;
        }

        static void AutoCreate()
        {
            if (File.Exists(ScenePath) || EditorApplication.isPlayingOrWillChangePlaymode) return;
            Build();
        }

        [MenuItem("Warfare/Пересоздать сцену боя")]
        public static void Build()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            foreach (var root in scene.GetRootGameObjects())
            {
                var light = root.GetComponent<Light>();
                if (light != null && light.type == LightType.Directional)
                {
                    root.name = "Sun";
                    root.transform.rotation = Quaternion.Euler(48f, -35f, 0f);
                    light.intensity = 1.3f;
                    light.shadows = LightShadows.Soft;
                }
                var cam = root.GetComponent<Camera>();
                if (cam != null)
                {
                    cam.farClipPlane = 1500f;
                    cam.fieldOfView = 45f;
                    if (root.GetComponent<RtsCamera>() == null) root.AddComponent<RtsCamera>();
                }
            }

            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.62f, 0.68f, 0.78f);
            RenderSettings.ambientEquatorColor = new Color(0.5f, 0.52f, 0.46f);
            RenderSettings.ambientGroundColor = new Color(0.25f, 0.24f, 0.2f);

            var battle = new GameObject("Battle");
            battle.AddComponent<BattleController>();
            battle.AddComponent<BattleView>();
            battle.AddComponent<BattleHud>();

            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            Debug.Log("Battle scene created: " + ScenePath);
        }
    }
}
