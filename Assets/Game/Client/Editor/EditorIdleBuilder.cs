using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    static class EditorIdleBuilder
    {
        const string ClipPath = "Assets/Art/Animations/Idle.fbx";
        const string ControllerPath = "Assets/Resources/EditorIdle.controller";

        static EditorIdleBuilder()
        {
            EditorApplication.delayCall += () =>
            {
                if (File.Exists(ControllerPath) || EditorApplication.isPlayingOrWillChangePlaymode) return;
                Build();
            };
        }

        [MenuItem("Warfare/Пересобрать стойку редактора персонажа")]
        static void Build()
        {
            var clip = AssetDatabase.LoadAllAssetsAtPath(ClipPath).OfType<AnimationClip>().FirstOrDefault(c => !c.name.StartsWith("__preview__"));
            if (clip == null) return;
            AssetDatabase.DeleteAsset(ControllerPath);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            var state = controller.layers[0].stateMachine.AddState("Idle");
            state.motion = clip;
            state.iKOnFeet = true;
            controller.layers[0].stateMachine.defaultState = state;
            AssetDatabase.SaveAssets();
            Debug.Log("[W1347] editor idle controller created: " + ControllerPath);
        }
    }
}
