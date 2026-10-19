using System;
using System.Collections.Generic;

namespace Warfare.Core.World
{
    public sealed class WalkGrid
    {
        public const float Blocked = float.PositiveInfinity;

        public readonly int Width;
        public readonly int Height;
        readonly float[] cost;
        int[] region;

        public WalkGrid(int width, int height, float fill = 1f)
        {
            Width = width;
            Height = height;
            cost = new float[width * height];
            if (fill != 0f) Array.Fill(cost, fill);
        }

        public float this[int x, int y]
        {
            get => cost[y * Width + x];
            set
            {
                cost[y * Width + x] = value;
                region = null;
            }
        }

        internal float CostOf(int i) => cost[i];

        public bool InBounds(int x, int y) => x >= 0 && y >= 0 && x < Width && y < Height;

        public bool Walkable(int x, int y) => InBounds(x, y) && !float.IsInfinity(cost[y * Width + x]);

        public static int Cell(float v) => (int)MathF.Floor(v + 0.5f);

        public bool Walkable(Vec2 p) => Walkable(Cell(p.X), Cell(p.Y));

        public float CostAt(Vec2 p)
        {
            int x = Cell(p.X), y = Cell(p.Y);
            return InBounds(x, y) ? cost[y * Width + x] : Blocked;
        }

        public sealed class Crossing
        {
            public Vec2 A;
            public Vec2 B;
        }

        public readonly List<Crossing> Crossings = new List<Crossing>();
        readonly Dictionary<int, int> crossingCells = new Dictionary<int, int>();

        public void AddCrossing(Vec2 a, Vec2 b, float halfWidth, float crossingCost)
        {
            int index = Crossings.Count;
            Crossings.Add(new Crossing { A = a, B = b });
            var ab = b - a;
            float len2 = Math.Max(ab.LengthSq, 1e-6f);
            int x0 = Math.Max(0, (int)MathF.Floor(Math.Min(a.X, b.X) - halfWidth - 1)), x1 = Math.Min(Width - 1, (int)MathF.Ceiling(Math.Max(a.X, b.X) + halfWidth + 1));
            int y0 = Math.Max(0, (int)MathF.Floor(Math.Min(a.Y, b.Y) - halfWidth - 1)), y1 = Math.Min(Height - 1, (int)MathF.Ceiling(Math.Max(a.Y, b.Y) + halfWidth + 1));
            for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                var p = new Vec2(x, y);
                float t = Math.Clamp(Vec2.Dot(p - a, ab) / len2, 0f, 1f);
                if (Vec2.Distance(a + ab * t, p) > halfWidth) continue;
                int i = y * Width + x;
                cost[i] = crossingCost;
                crossingCells[i] = index;
            }
            region = null;
        }

        public int CrossingAt(int cell) => crossingCells.TryGetValue(cell, out var k) ? k : -1;

        public void BuildRegions()
        {
            var r = new int[cost.Length];
            var queue = new int[cost.Length];
            int next = 0;
            for (int start = 0; start < cost.Length; start++)
            {
                if (r[start] != 0 || float.IsInfinity(cost[start])) continue;
                next++;
                int head = 0, tail = 0;
                queue[tail++] = start;
                r[start] = next;
                while (head < tail)
                {
                    int i = queue[head++];
                    int x = i % Width, y = i / Width;
                    if (x > 0) Visit(i - 1);
                    if (x < Width - 1) Visit(i + 1);
                    if (y > 0) Visit(i - Width);
                    if (y < Height - 1) Visit(i + Width);
                }

                void Visit(int j)
                {
                    if (r[j] != 0 || float.IsInfinity(cost[j])) return;
                    r[j] = next;
                    queue[tail++] = j;
                }
            }
            region = r;
        }

        public int Region(int x, int y)
        {
            if (!InBounds(x, y)) return 0;
            if (region == null) BuildRegions();
            return region[y * Width + x];
        }

        public int Region(Vec2 p) => Region(Cell(p.X), Cell(p.Y));

        public bool Nearest(Vec2 p, int inRegion, int maxRadius, out Vec2 found)
        {
            int cx = Cell(p.X), cy = Cell(p.Y);
            float best = float.MaxValue;
            found = p;
            for (int r = 0; r <= maxRadius; r++)
            {
                for (int dy = -r; dy <= r; dy++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != r) continue;
                    int x = cx + dx, y = cy + dy;
                    if (!Walkable(x, y) || inRegion != 0 && Region(x, y) != inRegion) continue;
                    float d = dx * dx + dy * dy;
                    if (d < best)
                    {
                        best = d;
                        found = new Vec2(x, y);
                    }
                }
                if (best <= (float)r * r) return true;
            }
            return best < float.MaxValue;
        }
    }
}
