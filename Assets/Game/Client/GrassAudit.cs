#if UNITY_EDITOR
using System.Text;
using System.Collections.Generic;
using UnityEngine;

namespace Warfare.Client
{
    public sealed partial class WorldMap
    {
        public string AuditGrass()
        {
            int instances = 0, water = 0, road = 0, bridge = 0, building = 0, outside = 0, mismatch = 0;
            uint checksum = 2166136261;
            int cx0 = Mathf.FloorToInt((grassAreaPx.x - grassAreaR) / grassCfg.Cell), cx1 = Mathf.CeilToInt((grassAreaPx.x + grassAreaR) / grassCfg.Cell);
            int cy0 = Mathf.FloorToInt((grassAreaPx.y - grassAreaR) / grassCfg.Cell), cy1 = Mathf.CeilToInt((grassAreaPx.y + grassAreaR) / grassCfg.Cell);
            var cells = new List<Vector2Int>();
            if (grassAreaR > 0)
            {
                for (int cy = cy0; cy <= cy1; cy++)
                for (int cx = cx0; cx <= cx1; cx++) cells.Add(new Vector2Int(cx, cy));
            }
            else cells.AddRange(grassCells.Keys);
            int desert = 0;
            foreach (var cell in cells)
            {
                int cx = cell.x, cy = cell.y;
                var first = BuildGrassCell(cx, cy);
                var second = BuildGrassCell(cx, cy);
                for (int v = 0; v < first.Length; v++)
                {
                    if (first[v].Count != second[v].Count) mismatch++;
                    for (int i = 0; i < first[v].Count; i++)
                    {
                        var m = first[v][i];
                        if (i >= second[v].Count || m != second[v][i]) mismatch++;
                        for (int k = 0; k < 16; k++) checksum = (checksum ^ (uint)m[k].GetHashCode()) * 16777619;
                        var p = new Vector3(m.m03, m.m13, m.m23);
                        var px = new Vector2(p.x + Meta.width / 2f, Meta.height / 2f - p.z);
                        instances++;
                        if (p.y <= SeaLevel) water++;
                        if (RoadValue(px.x, px.y) >= 110) road++;
                        if (grassAreaR > 0 && Vector2.Distance(px, grassAreaPx) > grassAreaR) outside++;
                        if (GrassBiomeDensity(px.x, px.y) <= 0) desert++;
                        foreach (var st in placed)
                            if (st.HasFootprint && Mathf.Abs(p.x - st.Footprint.center.x) < st.Footprint.extents.x && Mathf.Abs(p.z - st.Footprint.center.z) < st.Footprint.extents.z) { building++; break; }
                        foreach (var b in bridgeSpans)
                        {
                            var ab = b.B - b.A;
                            float t = Mathf.Clamp01(Vector2.Dot(px - b.A, ab) / Mathf.Max(ab.sqrMagnitude, 0.0001f));
                            if (Vector2.Distance(px, b.A + ab * t) < 1.2f) { bridge++; break; }
                        }
                    }
                }
            }
            var report = new StringBuilder();
            report.AppendLine($"instances={instances}, checksum={checksum:X8}, repeatMismatch={mismatch}");
            report.AppendLine($"forbidden roots: water={water}, roadway={road}, buildings={building}, bridges={bridge}, outside={outside}");
            report.AppendLine($"audited cells={cells.Count}, excluded biomes={desert}, habitat={grassHabitat.width}x{grassHabitat.height}");
            foreach (var mesh in grassMeshes) report.AppendLine($"{mesh.name}: vertices={mesh.vertexCount}, triangles={mesh.triangles.Length / 3}, bounds={mesh.bounds.size}");
            return report.ToString();
        }
    }
}
#endif
