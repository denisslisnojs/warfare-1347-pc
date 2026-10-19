using System;
using System.Collections.Generic;
using System.IO;
using Warfare.Core.Battle;

namespace Warfare.Core.Tests
{
    public static class TestData
    {
        static TroopCatalog troops;

        public static string DataDir
        {
            get
            {
                foreach (var start in new[] { Environment.CurrentDirectory, AppContext.BaseDirectory })
                {
                    var dir = new DirectoryInfo(start);
                    while (dir != null)
                    {
                        var candidate = Path.Combine(dir.FullName, "Assets", "StreamingAssets", "Data");
                        if (File.Exists(Path.Combine(candidate, "troops.json"))) return candidate;
                        dir = dir.Parent;
                    }
                }
                throw new DirectoryNotFoundException("Assets/StreamingAssets/Data not found");
            }
        }

        public static TroopCatalog Troops => troops ??= TroopCatalog.FromJson(File.ReadAllText(Path.Combine(DataDir, "troops.json")));

        public static ArmyDef Army(string culture, params (string id, int count)[] stacks)
        {
            var army = new ArmyDef { Name = culture, Culture = culture, Troops = new List<ArmyStack>() };
            foreach (var (id, count) in stacks) army.Troops.Add(new ArmyStack(id, count));
            return army;
        }

        public static BattleSim Battle(ArmyDef a, ArmyDef b, uint seed = 1, int maxOnField = BattleRules.MaxOnField)
        {
            return new BattleSim(a, b, Troops, new BattleOptions { Seed = seed, MaxOnField = maxOnField });
        }
    }
}
