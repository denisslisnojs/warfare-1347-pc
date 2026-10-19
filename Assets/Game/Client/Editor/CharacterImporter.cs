using System;
using UnityEditor;
using UnityEngine;

namespace Warfare.Client.Editor
{
    sealed class CharacterImporter : AssetPostprocessor
    {
        const string Characters = "Assets/Art/Characters/";
        const string Animations = "Assets/Art/Animations/";
        const string Marker = "w1347-humanoid";

        public override uint GetVersion() => 5;

        static bool Ours(string path) => path.StartsWith(Characters, StringComparison.Ordinal) || path.StartsWith(Animations, StringComparison.Ordinal);

        void OnPreprocessModel()
        {
            var path = assetPath.Replace('\\', '/');
            if (!Ours(path)) return;
            var mi = (ModelImporter)assetImporter;
            if (mi.userData == Marker) return;
            mi.animationType = ModelImporterAnimationType.Human;
            mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            mi.importCameras = false;
            mi.importLights = false;
            bool anim = path.StartsWith(Animations, StringComparison.Ordinal);
            mi.importAnimation = anim;
            if (anim) mi.materialImportMode = ModelImporterMaterialImportMode.None;
            mi.userData = Marker;
        }

        void OnPreprocessAnimation()
        {
            var path = assetPath.Replace('\\', '/');
            if (!path.StartsWith(Animations, StringComparison.Ordinal)) return;
            var mi = (ModelImporter)assetImporter;
            var clips = mi.defaultClipAnimations;
            if (clips == null || clips.Length == 0) return;
            string file = System.IO.Path.GetFileNameWithoutExtension(path);
            bool loop = Loops(file);
            for (int i = 0; i < clips.Length; i++)
            {
                clips[i].name = file;
                clips[i].loopTime = loop;
                clips[i].lockRootRotation = true;
                clips[i].lockRootHeightY = true;
                clips[i].lockRootPositionXZ = file.ToLowerInvariant().Contains("idle");
                clips[i].keepOriginalOrientation = true;
                clips[i].keepOriginalPositionY = true;
                clips[i].keepOriginalPositionXZ = true;
            }
            mi.clipAnimations = clips;
        }

        static bool Loops(string name)
        {
            var n = name.ToLowerInvariant();
            return n.Contains("idle") || n.Contains("walk") || n.Contains("run") || n.Contains("strafe");
        }

        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            foreach (var p in imported)
            {
                var path = p.Replace('\\', '/');
                if (!Ours(path) || !path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase)) continue;
                Avatar avatar = null;
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path))
                    if (o is Avatar a) avatar = a;
                if (avatar == null) Debug.LogWarning($"[W1347] {path}: no avatar");
                else if (!avatar.isValid || !avatar.isHuman) Debug.LogWarning($"[W1347] {path}: avatar invalid (valid={avatar.isValid}, human={avatar.isHuman})");
                else Debug.Log($"[W1347] {path}: humanoid avatar OK");
            }
        }
    }
}
