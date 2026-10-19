using System.Collections.Generic;

namespace Warfare.Core.World
{
    public sealed class TravelRules
    {
        public float SecondsPerDay = 10f;
        public int[] Speeds = { 1, 2, 4 };
        public float PartySpeed = 86.4f;
        public float MaxCost = 3f;
        public float Road = 0.7f;
        public float Hills = 0.8f;
        public float RockLimit = 0.5f;
        public float StartHour = 8f;
        public Dictionary<string, float> Terrain = new Dictionary<string, float>();

        public float TerrainCost(string biome) => biome != null && Terrain != null && Terrain.TryGetValue(biome, out var c) ? c : 1f;
    }

    public sealed class WorldTravel
    {
        public readonly WalkGrid Grid;
        public readonly MapParty Party;
        public readonly WorldClock Clock;
        public readonly TravelRules Rules;
        public bool Waiting;

        public WorldTravel(WalkGrid grid, TravelRules rules, Vec2 start)
        {
            Grid = grid;
            Rules = rules;
            Party = new MapParty(start, rules.PartySpeed) { MaxCost = rules.MaxCost };
            Clock = new WorldClock(rules.StartHour / 24.0) { SecondsPerDay = rules.SecondsPerDay, Speed = rules.Speeds.Length > 0 ? rules.Speeds[0] : 1 };
        }

        public bool TimeFlows => Party.Moving || Waiting;

        public void Order(IReadOnlyList<Vec2> path)
        {
            Waiting = false;
            Party.SetPath(path);
        }

        public void ToggleWait()
        {
            Waiting = !Waiting;
            if (Waiting) Party.Stop();
        }

        public void ChangeSpeed(int step)
        {
            var s = Rules.Speeds;
            if (s.Length == 0) return;
            int i = System.Array.IndexOf(s, Clock.Speed);
            if (i < 0) i = 0;
            i = System.Math.Clamp(i + step, 0, s.Length - 1);
            Clock.Speed = s[i];
        }

        public double Tick(float realSeconds)
        {
            if (!TimeFlows) return 0;
            double days = Clock.Advance(realSeconds);
            if (Party.Moving) Party.Advance(days, Grid);
            return days;
        }
    }
}
