using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Warfare.Client.Editor
{
    [InitializeOnLoad]
    sealed class EnvironmentArtBuilder : AssetPostprocessor
    {
        const string Dir = "Assets/Art/Environment";
        const string ArtPath = "Assets/Resources/EnvironmentArt.asset";
        static bool pending;

        static EnvironmentArtBuilder()
        {
            EditorApplication.delayCall += () =>
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode) return;
                var art = AssetDatabase.LoadAssetAtPath<EnvironmentArt>(ArtPath);
                if (art == null || art.Props.Count == 0) Build();
            };
        }

        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            bool touched = imported.Concat(deleted).Concat(moved).Any(p => p.Replace('\\', '/').StartsWith(Dir + "/", StringComparison.Ordinal));
            if (!touched || pending) return;
            pending = true;
            EditorApplication.delayCall += () =>
            {
                pending = false;
                Build();
            };
        }

        [MenuItem("Warfare/Пересобрать окружение")]
        public static void Build()
        {
            Directory.CreateDirectory("Assets/Resources");
            var art = AssetDatabase.LoadAssetAtPath<EnvironmentArt>(ArtPath);
            if (art == null)
            {
                art = ScriptableObject.CreateInstance<EnvironmentArt>();
                AssetDatabase.CreateAsset(art, ArtPath);
            }
            art.Props.Clear();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Dir }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (go != null) art.Props.Add(new EnvironmentArt.Entry { Id = Path.GetFileNameWithoutExtension(path), Prefab = go });
            }
            art.Props.Sort((a, b) => string.CompareOrdinal(a.Id, b.Id));
            EditorUtility.SetDirty(art);
            AssetDatabase.SaveAssets();
            Debug.Log($"[W1347] environment props: {art.Props.Count} ({string.Join(", ", art.Props.Select(p => p.Id))})");
        }
    }
}
