using System;

namespace Warfare.Core.Battle
{
    public sealed partial class BattleSim
    {
        float SpaceOf(BattleUnit u) => u.Troop.IsCavalry ? BattleRules.SpaceCavalry : BattleRules.SpaceLine;

        Vec2 Separation(BattleUnit u)
        {
            float sx = 0, sy = 0;
            float own = SpaceOf(u);
            foreach (var a in Units)
            {
                if (a == u || !a.Alive) continue;
                bool same = a.Side == u.Side;
                float r = a.Troop.IsCavalry || u.Troop.IsCavalry ? BattleRules.SpaceCavalry : same ? own : BattleRules.SpaceEnemy;
                float dx = u.Pos.X - a.Pos.X;
                if (dx > r || dx < -r) continue;
                float dy = u.Pos.Y - a.Pos.Y;
                if (dy > r || dy < -r) continue;
                float d = MathF.Sqrt(dx * dx + dy * dy);
                if (d >= r) continue;
                float k = (r - d) / r * (same ? 1f : 0.7f);
                if (d < 0.05f)
                {
                    sx += (rng.Value - 0.5f) * k;
                    sy += (rng.Value - 0.5f) * k;
                }
                else
                {
                    sx += dx / d * k;
                    sy += dy / d * k;
                }
            }
            return new Vec2(sx, sy);
        }

        void Separate(BattleUnit u, float dt, float k)
        {
            var s = Separation(u);
            if (s.X == 0 && s.Y == 0) return;
            u.Pos = Clamp(u.Pos + s * (u.Troop.Speed * BattleRules.SpeedK * k * dt));
        }

        void Steer(BattleUnit u, Vec2 goal, float dt, float k)
        {
            float speed = u.Troop.Speed * BattleRules.SpeedK * k;
            var v = goal.Normalized + Separation(u) * BattleRules.SteerSeparation;
            float len = v.Length;
            if (len < 0.05f)
            {
                u.State = UnitState.Idle;
                return;
            }
            v /= len;
            if (len < 0.5f) speed *= len * 2f;
            float goalLen = goal.Length;
            float stepLen = Math.Min(speed * dt, Math.Max(goalLen, speed * dt * 0.25f));
            var step = v * stepLen;
            u.Pos = Clamp(u.Pos + step);
            u.Facing = v;
            u.State = UnitState.Walk;
            if (u.Troop.IsCavalry)
            {
                u.ChargeDist += step.Length;
                if (u.ChargeDist > BattleRules.ChargeDistance) u.Charging = true;
            }
        }

        void Flee(BattleUnit u, float dt)
        {
            var back = -Forward(u.Side);
            Steer(u, back * 100f, dt, u.Routed ? BattleRules.RouteSpeedK : 1f);
            if (Vec2.Dot(u.Pos, back) > BattleRules.FieldLength / 2f + BattleRules.FleeMargin) u.State = UnitState.Fled;
        }

        static Vec2 Clamp(Vec2 p)
        {
            float hx = BattleRules.FieldLength / 2f + BattleRules.FleeMargin + 2f;
            float hy = BattleRules.FieldWidth / 2f;
            return new Vec2(Math.Clamp(p.X, -hx, hx), Math.Clamp(p.Y, -hy, hy));
        }
    }
}
