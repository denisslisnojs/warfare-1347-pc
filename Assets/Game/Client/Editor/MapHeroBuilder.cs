using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    static class MapHeroBuilder
    {
        const string ModelPath = "Assets/Art/Characters/Hero_Base.fbx";
        const string IdlePath = "Assets/Art/Animations/Idle.fbx";
        const string WalkPath = "Assets/Art/Animations/Walking.fbx";
        const string PrefabPath = "Assets/Resources/Characters/MapHero.prefab";
        const string ControllerPath = "Assets/Resources/Characters/MapHero.controller";

        static MapHeroBuilder()
        {
            EditorApplication.delayCall += () =>
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode) return;
                if (File.Exists(PrefabPath) && File.Exists(ControllerPath)) return;
                Build();
            };
        }

        static AnimationClip Clip(string path) => AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().FirstOrDefault(c => !c.name.StartsWith("__preview__"));

        [MenuItem("Warfare/Пересобрать героя для карты")]
        static void Build()
        {
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
            var idle = Clip(IdlePath);
            var walk = Clip(WalkPath);
            if (model == null || idle == null || walk == null) return;
            Directory.CreateDirectory(Path.GetDirectoryName(PrefabPath));
            AssetDatabase.DeleteAsset(ControllerPath);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            controller.AddParameter("Move", AnimatorControllerParameterType.Float);
            var state = controller.CreateBlendTreeInController("Travel", out var tree, 0);
            tree.blendParameter = "Move";
            tree.useAutomaticThresholds = false;
            tree.AddChild(idle, 0f);
            tree.AddChild(walk, 1f);
            state.iKOnFeet = true;
            var go = (GameObject)PrefabUtility.InstantiatePrefab(model);
            var anim = go.GetComponent<Animator>();
            if (anim != null)
            {
                anim.runtimeAnimatorController = controller;
                anim.applyRootMotion = false;
            }
            PrefabUtility.SaveAsPrefabAsset(go, PrefabPath);
            Object.DestroyImmediate(go);
            AssetDatabase.SaveAssets();
            Debug.Log("[W1347] map hero created: " + PrefabPath);
        }
    }
}
