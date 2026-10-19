using System;
using System.IO;
using UnityEditor;

namespace Warfare.Client.Editor
{
    sealed class SettlementModelImporter : AssetPostprocessor
    {
        const string Dir = "Assets/Art/Environment/World/";

        public override uint GetVersion() => 1;

        void OnPreprocessModel()
        {
            string path = assetPath.Replace('\\', '/');
            if (!path.StartsWith(Dir, StringComparison.Ordinal)) return;
            string name = Path.GetFileNameWithoutExtension(path);
            if (!name.StartsWith("WorldTown", StringComparison.Ordinal) && !name.StartsWith("WorldCastle", StringComparison.Ordinal) && !name.StartsWith("WorldVillage", StringComparison.Ordinal)) return;
            ((ModelImporter)assetImporter).isReadable = true;
        }
    }
}
