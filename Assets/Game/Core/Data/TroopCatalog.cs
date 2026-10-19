using System;
using System.Collections.Generic;

namespace Warfare.Core
{
    public sealed class TroopCatalog
    {
        sealed class FileModel
        {
            public List<TroopDef> Troops { get; set; } = new List<TroopDef>();
        }

        readonly Dictionary<string, TroopDef> byId = new Dictionary<string, TroopDef>(StringComparer.Ordinal);

        public IReadOnlyCollection<TroopDef> All => byId.Values;

        public TroopCatalog(IEnumerable<TroopDef> troops)
        {
            foreach (var t in troops)
            {
                if (string.IsNullOrEmpty(t.Id)) throw new FormatException("Troop without id");
                if (byId.ContainsKey(t.Id)) throw new FormatException($"Duplicate troop id '{t.Id}'");
                byId[t.Id] = t;
            }
        }

        public static TroopCatalog FromJson(string json)
        {
            var file = DataJson.Read<FileModel>(json) ?? throw new FormatException("Empty troops file");
            return new TroopCatalog(file.Troops);
        }

        public bool TryGet(string id, out TroopDef troop) => byId.TryGetValue(id, out troop);

        public TroopDef Get(string id)
        {
            if (byId.TryGetValue(id, out var t)) return t;
            throw new KeyNotFoundException($"Unknown troop id '{id}'");
        }
    }
}
