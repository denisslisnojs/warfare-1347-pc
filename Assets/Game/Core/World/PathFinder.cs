using System;
using System.Collections.Generic;

namespace Warfare.Core.World
{
    public sealed class PathFinder
    {
        const float Sqrt2 = 1.41421356f;
        static readonly int[] Dx = { 1, -1, 0, 0, 1, 1, -1, -1 };
        static readonly int[] Dy = { 0, 0, 1, -1, 1, -1, 1, -1 };
        static readonly float[] Len = { 1, 1, 1, 1, Sqrt2, Sqrt2, Sqrt2, Sqrt2 };

        readonly WalkGrid grid;
        readonly float minCost;
        readonly float[] g;
        readonly int[] came;
        readonly int[] seen;
        readonly int[] done;
        int stamp;
        int[] heapIdx = new int[4096];
        float[] heapPri = new float[4096];
        int heapSize;

        public int Lookahead = 48;
        public float SmoothTolerance = 0.2f;
        public int LastExpanded { get; private set; }

        public PathFinder(WalkGrid grid, float minCost)
        {
            this.grid = grid;
            this.minCost = minCost;
            int n = grid.Width * grid.Height;
            g = new float[n];
            came = new int[n];
            seen = new int[n];
            done = new int[n];
        }

        public List<Vec2> Find(Vec2 from, Vec2 to)
        {
            int w = grid.Width;
            var startAt = from;
            if (!grid.Walkable(from) && !grid.Nearest(from, 0, 4, out startAt)) return null;
            int sx = WalkGrid.Cell(startAt.X), sy = WalkGrid.Cell(startAt.Y);
            int tx = WalkGrid.Cell(to.X), ty = WalkGrid.Cell(to.Y);
            if (!grid.Walkable(tx, ty) || grid.Region(sx, sy) != grid.Region(tx, ty)) return null;
            stamp++;
            int start = sy * w + sx, goal = ty * w + tx;
            heapSize = 0;
            g[start] = 0;
            seen[start] = stamp;
            came[start] = -1;
            Push(start, 0);
            int expanded = 0;
            while (heapSize > 0)
            {
                int cur = Pop();
                if (cur == goal) break;
                if (done[cur] == stamp) continue;
                done[cur] = stamp;
                expanded++;
                int cx = cur % w, cy = cur / w;
                float g0 = g[cur], c0 = grid.CostOf(cur);
                for (int k = 0; k < 8; k++)
                {
                    int nx = cx + Dx[k], ny = cy + Dy[k];
                    if (!grid.InBounds(nx, ny)) continue;
                    int ni = ny * w + nx;
                    float c1 = grid.CostOf(ni);
                    if (float.IsInfinity(c1)) continue;
                    if (k >= 4 && (float.IsInfinity(grid.CostOf(cy * w + nx)) || float.IsInfinity(grid.CostOf(ny * w + cx)))) continue;
                    float gn = g0 + Len[k] * (c0 + c1) * 0.5f;
                    if (seen[ni] == stamp && gn >= g[ni]) continue;
                    seen[ni] = stamp;
                    g[ni] = gn;
                    came[ni] = cur;
                    int hx = Math.Abs(nx - tx), hy = Math.Abs(ny - ty);
                    Push(ni, gn + (Math.Max(hx, hy) + (Sqrt2 - 1f) * Math.Min(hx, hy)) * minCost);
                }
            }
            LastExpanded = expanded;
            if (seen[goal] != stamp) return null;
            var cells = new List<int>();
            for (int c = goal; c != -1; c = came[c]) cells.Add(c);
            cells.Reverse();
            var path = new List<Vec2> { from };
            var run = new List<int>();
            int i = 0;
            while (i < cells.Count)
            {
                int k = grid.CrossingAt(cells[i]);
                int j = i;
                if (k >= 0)
                    while (j + 1 < cells.Count && grid.CrossingAt(cells[j + 1]) == k) j++;
                if (k < 0)
                {
                    run.Add(cells[i++]);
                    continue;
                }
                var cr = grid.Crossings[k];
                bool enterA = Near(cells[i], cr.A, cr.B), leaveA = Near(cells[j], cr.A, cr.B);
                if (i > 0 && enterA == leaveA)
                {
                    for (int q = i; q <= j; q++) run.Add(cells[q]);
                    i = j + 1;
                    continue;
                }
                Append(path, run, false);
                run.Clear();
                if (i > 0) path.Add(enterA ? cr.A : cr.B);
                path.Add(leaveA ? cr.A : cr.B);
                i = j + 1;
            }
            Append(path, run, true);
            if (Vec2.Distance(path[path.Count - 1], to) > 1e-4f) path.Add(to);
            return path;
        }

        bool Near(int cell, Vec2 a, Vec2 b)
        {
            var p = new Vec2(cell % grid.Width, cell / grid.Width);
            return Vec2.Distance(p, a) <= Vec2.Distance(p, b);
        }

        void Append(List<Vec2> path, List<int> run, bool last)
        {
            if (run.Count == 0) return;
            var smooth = Smooth(run);
            int w = grid.Width;
            for (int i = 0; i < smooth.Count; i++)
            {
                if (path.Count == 1 && i == 0) continue;
                if (last && i == smooth.Count - 1) continue;
                path.Add(new Vec2(smooth[i] % w, smooth[i] / w));
            }
        }

        List<int> Smooth(List<int> cells)
        {
            var output = new List<int> { cells[0] };
            int anchor = 0;
            while (anchor < cells.Count - 1)
            {
                int best = anchor + 1;
                for (int j = Math.Min(cells.Count - 1, anchor + Lookahead); j > anchor + 1; j--)
                    if (LineClear(cells[anchor], cells[j], Budget(cells[anchor], cells[j])))
                    {
                        best = j;
                        break;
                    }
                output.Add(cells[best]);
                anchor = best;
            }
            for (int i = 1; i < output.Count - 1;)
                if (LineClear(output[i - 1], output[i + 1], Budget(output[i - 1], output[i + 1]))) output.RemoveAt(i);
                else i++;
            return output;
        }

        float Budget(int a, int b) => (g[b] - g[a]) * 1.02f + 0.01f;

        bool LineClear(int a, int b, float budget)
        {
            int w = grid.Width;
            int x0 = a % w, y0 = a / w, x1 = b % w, y1 = b / w;
            int dx = Math.Abs(x1 - x0), dy = -Math.Abs(y1 - y0);
            int sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
            int err = dx + dy;
            float c0 = grid.CostOf(a), prev = c0, spent = 0f;
            bool first = true, diagonal = false;
            while (true)
            {
                float c = grid.CostOf(y0 * w + x0);
                if (float.IsInfinity(c) || Math.Abs(c - c0) > SmoothTolerance) return false;
                if (!first)
                {
                    spent += (diagonal ? Sqrt2 : 1f) * (prev + c) * 0.5f;
                    if (spent > budget) return false;
                }
                first = false;
                prev = c;
                if (x0 == x1 && y0 == y1) return true;
                int e2 = 2 * err;
                bool stepX = e2 >= dy, stepY = e2 <= dx;
                diagonal = stepX && stepY;
                if (stepX && stepY && (float.IsInfinity(grid.CostOf(y0 * w + x0 + sx)) || float.IsInfinity(grid.CostOf((y0 + sy) * w + x0)))) return false;
                if (stepX)
                {
                    err += dy;
                    x0 += sx;
                }
                if (stepY)
                {
                    err += dx;
                    y0 += sy;
                }
            }
        }

        void Push(int i, float p)
        {
            if (heapSize >= heapIdx.Length)
            {
                Array.Resize(ref heapIdx, heapIdx.Length * 2);
                Array.Resize(ref heapPri, heapPri.Length * 2);
            }
            int k = heapSize++;
            while (k > 0)
            {
                int parent = (k - 1) >> 1;
                if (heapPri[parent] <= p) break;
                heapIdx[k] = heapIdx[parent];
                heapPri[k] = heapPri[parent];
                k = parent;
            }
            heapIdx[k] = i;
            heapPri[k] = p;
        }

        int Pop()
        {
            int top = heapIdx[0];
            int lastI = heapIdx[--heapSize];
            float lastP = heapPri[heapSize];
            int k = 0;
            while (true)
            {
                int c = 2 * k + 1;
                if (c >= heapSize) break;
                if (c + 1 < heapSize && heapPri[c + 1] < heapPri[c]) c++;
                if (heapPri[c] >= lastP) break;
                heapIdx[k] = heapIdx[c];
                heapPri[k] = heapPri[c];
                k = c;
            }
            heapIdx[k] = lastI;
            heapPri[k] = lastP;
            return top;
        }
    }
}
