using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Warfare.Client.Editor
{
    sealed class AnimationSetBuilder : AssetPostprocessor
    {
        const string AnimDir = "Assets/Art/Animations";
        const string ControllerPath = "Assets/Art/Animations/Chibi.controller";
        const string ModelPath = "Assets/Art/Characters/Chibi_Soldier.fbx";
        const string EquipDir = "Assets/Art/Equipment";
        const string ArtPath = "Assets/Resources/UnitArt.asset";

        static readonly (string category, string[] words)[] Categories =
        {
            ("Death", new[] { "death", "dying", "die" }),
            ("Impact", new[] { "impact", "hit", "react" }),
            ("BlockIdle", new[] { "block idle" }),
            ("Block", new[] { "block" }),
            ("Strafe", new[] { "strafe" }),
            ("Attack", new[] { "slash", "attack", "stab", "thrust", "strike" }),
            ("Run", new[] { "run" }),
            ("Walk", new[] { "walk" }),
            ("Idle", new[] { "idle" }),
        };

        static bool pending;

        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            bool touched = imported.Concat(deleted).Concat(moved).Any(p => p.Replace('\\', '/').StartsWith(AnimDir + "/", StringComparison.Ordinal) && p.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
                           || imported.Any(p => p.Replace('\\', '/') == ModelPath || p.Replace('\\', '/').StartsWith(EquipDir + "/", StringComparison.Ordinal));
            if (!touched || pending) return;
            pending = true;
            EditorApplication.delayCall += () =>
            {
                pending = false;
                Build();
            };
        }

        static string Categorize(string name)
        {
            var n = name.ToLowerInvariant();
            int at = n.IndexOf('@');
            if (at >= 0) n = n.Substring(at + 1);
            foreach (var (category, words) in Categories)
                if (words.Any(n.Contains)) return category;
            return null;
        }

        [MenuItem("Warfare/Пересобрать анимации")]
        public static void Build()
        {
            var clips = new List<AnimationClip>();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { AnimDir }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (!Path.GetFileName(path).ToLowerInvariant().Contains("sword and shield")) continue;
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path))
                    if (o is AnimationClip c && !c.name.StartsWith("__preview__", StringComparison.Ordinal)) clips.Add(c);
            }
            clips.Sort((a, b) => string.CompareOrdinal(a.name, b.name));

            var groups = new Dictionary<string, List<UnitArt.Clip>>();
            AssetDatabase.DeleteAsset(ControllerPath);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            controller.AddParameter("Speed", AnimatorControllerParameterType.Float);
            var ps = controller.parameters;
            foreach (var prm in ps)
                if (prm.name == "Speed") prm.defaultFloat = 1f;
            controller.parameters = ps;
            var sm = controller.layers[0].stateMachine;
            var skipped = new List<string>();
            foreach (var clip in clips)
            {
                var cat = Categorize(clip.name);
                if (cat == null)
                {
                    skipped.Add(clip.name);
                    continue;
                }
                if (!groups.TryGetValue(cat, out var list)) groups[cat] = list = new List<UnitArt.Clip>();
                string state = cat + list.Count;
                var st = sm.AddState(state);
                st.motion = clip;
                st.writeDefaultValues = true;
                st.speedParameterActive = true;
                st.speedParameter = "Speed";
                list.Add(new UnitArt.Clip { State = state, Length = clip.length, SideSpeed = clip.averageSpeed.x, ForwardSpeed = clip.averageSpeed.z });
                if (cat == "Idle" && list.Count == 1) sm.defaultState = st;
            }

            Directory.CreateDirectory("Assets/Resources");
            var art = AssetDatabase.LoadAssetAtPath<UnitArt>(ArtPath);
            if (art == null)
            {
                art = ScriptableObject.CreateInstance<UnitArt>();
                AssetDatabase.CreateAsset(art, ArtPath);
            }
            art.Infantry = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
            art.Sword = AssetDatabase.LoadAssetAtPath<GameObject>(EquipDir + "/Sword.fbx");
            art.Shield = AssetDatabase.LoadAssetAtPath<GameObject>(EquipDir + "/Shield_Round.fbx");
            art.Spear = AssetDatabase.LoadAssetAtPath<GameObject>(EquipDir + "/Spear.fbx");
            art.Controller = controller;
            UnitArt.Clip[] Get(string c) => groups.TryGetValue(c, out var l) ? l.ToArray() : Array.Empty<UnitArt.Clip>();
            art.Idle = Get("Idle");
            art.Walk = Get("Walk");
            art.Run = Get("Run");
            art.Attack = Get("Attack");
            art.Impact = Get("Impact");
            art.Death = Get("Death");
            art.Block = Get("Block");
            art.BlockIdle = Get("BlockIdle");
            art.Strafe = Get("Strafe");
            EditorUtility.SetDirty(art);
            AssetDatabase.SaveAssets();

            string summary = string.Join(", ", groups.Select(kv => $"{kv.Key} {kv.Value.Count}")) + "; strafe side speeds: " + string.Join(" ", art.Strafe.Select(c => c.SideSpeed.ToString("0.00"))) + "; walk/run forward speeds: " + string.Join(" ", art.Walk.Concat(art.Run).Select(c => c.State + "=" + c.ForwardSpeed.ToString("0.00")));
            Debug.Log($"[W1347] animations: {summary}; model {(art.Infantry != null ? "ok" : "missing")}" + (skipped.Count > 0 ? "; skipped: " + string.Join(" | ", skipped) : ""));
        }
    }
}
