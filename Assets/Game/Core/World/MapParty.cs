using System;
using System.Collections.Generic;

namespace Warfare.Core.World
{
    public sealed class MapParty
    {
        public Vec2 Position;
        public float Speed;
        public float MaxCost = 3f;
        readonly List<Vec2> path = new List<Vec2>();

        public MapParty(Vec2 position, float speed)
        {
            Position = position;
            Speed = speed;
        }

        public IReadOnlyList<Vec2> Path => path;
        public bool Moving => path.Count > 0;
        public Vec2 Heading { get; private set; } = new Vec2(1, 0);
        public Vec2 Destination => path.Count > 0 ? path[path.Count - 1] : Position;

        public void SetPath(IReadOnlyList<Vec2> points)
        {
            path.Clear();
            if (points == null) return;
            for (int i = 0; i < points.Count; i++)
                if (i > 0 || Vec2.Distance(points[0], Position) > 0.05f) path.Add(points[i]);
        }

        public void Stop() => path.Clear();

        public float RemainingDistance()
        {
            if (path.Count == 0) return 0f;
            float d = Vec2.Distance(Position, path[0]);
            for (int i = 1; i < path.Count; i++) d += Vec2.Distance(path[i - 1], path[i]);
            return d;
        }

        public float Advance(double days, WalkGrid grid)
        {
            float c = grid.CostAt(Position);
            if (float.IsInfinity(c) || c <= 0f) c = 1f;
            float remaining = (float)(Speed * days / Math.Min(MaxCost, c));
            float moved = 0f;
            while (remaining > 0f && path.Count > 0)
            {
                var to = path[0];
                var delta = to - Position;
                float dist = delta.Length;
                if (dist > 1e-4f) Heading = delta / dist;
                if (dist <= remaining)
                {
                    Position = to;
                    remaining -= dist;
                    moved += dist;
                    path.RemoveAt(0);
                }
                else
                {
                    Position += delta * (remaining / dist);
                    moved += remaining;
                    remaining = 0f;
                }
            }
            return moved;
        }
    }
}
