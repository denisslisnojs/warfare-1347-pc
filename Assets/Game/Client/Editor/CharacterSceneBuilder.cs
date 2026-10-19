using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    static class CharacterSceneBuilder
    {
        const string ScenePath = "Assets/Scenes/CharacterEditor.unity";
        const string ModelPath = "Assets/Art/Characters/Hero_Base.fbx";

        static CharacterSceneBuilder()
        {
            EditorApplication.delayCall += () =>
            {
                if (File.Exists(ScenePath) || EditorApplication.isPlayingOrWillChangePlaymode) return;
                if (AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath) == null) return;
                Build();
            };
        }

        [MenuItem("Warfare/Пересоздать сцену редактора персонажа")]
        static void BuildFromMenu() => Build();

        static void Build()
        {
            var previous = SceneManager.GetActiveScene();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Additive);
            SceneManager.SetActiveScene(scene);
            var editor = new GameObject("CharacterEditor").AddComponent<CharacterEditor>();
            editor.Model = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
            if (previous.IsValid()) SceneManager.SetActiveScene(previous);
            EditorSceneManager.CloseScene(scene, true);
            var scenes = EditorBuildSettings.scenes.Where(s => s.path != ScenePath).ToList();
            scenes.Add(new EditorBuildSettingsScene(ScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            Debug.Log("[W1347] character editor scene created: " + ScenePath);
        }
    }
}
