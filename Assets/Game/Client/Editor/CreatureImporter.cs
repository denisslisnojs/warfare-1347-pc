using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    sealed class CreatureImporter : AssetPostprocessor
    {
        const string Dir = "Assets/Art/Environment/Creatures/";
        const string Out = "Assets/Resources/Creatures/";
        static readonly string[] States = { "Eating", "Idle", "Walk", "Gallop" };

        public override uint GetVersion() => 2;

        static CreatureImporter()
        {
            EditorApplication.delayCall += () =>
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode) return;
                foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Dir.TrimEnd('/') }))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    if (!File.Exists(Out + Path.GetFileNameWithoutExtension(path) + ".controller")) Build(path);
                }
            };
        }

        void OnPreprocessModel()
        {
            if (!assetPath.Replace('\\', '/').StartsWith(Dir, StringComparison.Ordinal)) return;
            var mi = (ModelImporter)assetImporter;
            mi.animationType = ModelImporterAnimationType.Generic;
            mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            mi.importAnimation = true;
            mi.importCameras = false;
            mi.importLights = false;
        }

        void OnPreprocessAnimation()
        {
            if (!assetPath.Replace('\\', '/').StartsWith(Dir, StringComparison.Ordinal)) return;
            var mi = (ModelImporter)assetImporter;
            var clips = mi.defaultClipAnimations;
            if (clips == null || clips.Length == 0) return;
            foreach (var c in clips)
            {
                int bar = c.name.LastIndexOf('|');
                if (bar >= 0) c.name = c.name.Substring(bar + 1);
                c.loopTime = States.Contains(c.name) || c.name.StartsWith("Idle", StringComparison.Ordinal);
                c.lockRootPositionXZ = true;
                c.lockRootHeightY = true;
                c.lockRootRotation = true;
            }
            mi.clipAnimations = clips;
        }

        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            foreach (var p in imported)
            {
                var path = p.Replace('\\', '/');
                if (path.StartsWith(Dir, StringComparison.Ordinal) && path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
                    EditorApplication.delayCall += () => Build(path);
            }
        }

        [MenuItem("Warfare/Пересобрать анимации животных")]
        static void BuildAll()
        {
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Dir.TrimEnd('/') }))
                Build(AssetDatabase.GUIDToAssetPath(guid));
        }

        static void Build(string path)
        {
            var clips = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__", StringComparison.Ordinal)).ToList();
            if (clips.Count == 0) return;
            Directory.CreateDirectory(Out);
            string target = Out + Path.GetFileNameWithoutExtension(path) + ".controller";
            AssetDatabase.DeleteAsset(target);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(target);
            controller.AddParameter("State", AnimatorControllerParameterType.Float);
            controller.CreateBlendTreeInController("Move", out var tree, 0);
            tree.blendParameter = "State";
            tree.useAutomaticThresholds = false;
            for (int i = 0; i < States.Length; i++)
            {
                var clip = clips.FirstOrDefault(c => c.name == States[i]) ?? clips.FirstOrDefault(c => c.name.StartsWith(States[i], StringComparison.Ordinal)) ?? clips.FirstOrDefault(c => c.name == "Idle");
                if (clip != null) tree.AddChild(clip, i);
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[W1347] creature controller: {target} ({string.Join(", ", clips.Select(c => c.name))})");
        }
    }
}
