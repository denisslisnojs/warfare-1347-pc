using System;
using System.Collections.Generic;
using UnityEngine;

namespace Warfare.Client
{
    public sealed class EnvironmentArt : ScriptableObject
    {
        [Serializable]
        public sealed class Entry
        {
            public string Id;
            public GameObject Prefab;
        }

        public List<Entry> Props = new List<Entry>();

        Dictionary<string, GameObject> byId;

        public GameObject Get(string id)
        {
            if (byId == null)
            {
                byId = new Dictionary<string, GameObject>(StringComparer.Ordinal);
                foreach (var e in Props)
                    if (e != null && !string.IsNullOrEmpty(e.Id) && e.Prefab != null) byId[e.Id] = e.Prefab;
            }
            return byId.TryGetValue(id, out var p) ? p : null;
        }

        public static EnvironmentArt Load() => Resources.Load<EnvironmentArt>("EnvironmentArt");
    }
}
