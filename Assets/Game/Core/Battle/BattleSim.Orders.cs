using System;
using System.Collections.Generic;

namespace Warfare.Core.Battle
{
    public sealed partial class BattleSim
    {
        public Order OrderOf(int side, Group g) => orders[side, (int)g];

        public void SetOrder(int side, Group g, Order order)
        {
            if (order == Order.Hold)
            {
                HoldInPlace(side, g);
                return;
            }
            if (order == Order.Follow)
            {
                var hero = Hero(side);
                if (hero == null || !hero.Alive) order = Order.Attack;
                else
                {
                    orders[side, (int)g] = Order.Follow;
                    FollowAnchor(side, g, hero);
                    return;
                }
            }
            orders[side, (int)g] = order;
            holds[side, (int)g] = null;
            foreach (var u in Units)
                if (u.Side == side && u.Group == g) u.HasAnchor = false;
        }

        public void HoldInPlace(int side, Group g)
        {
            orders[side, (int)g] = Order.Hold;
            if (!TryGroupCenter(side, g, out var center))
            {
                holds[side, (int)g] = null;
                return;
            }
            holds[side, (int)g] = new GroupHold { Block = false, Center = center, Facing = FacingFrom(side, center) };
            foreach (var u in Units)
            {
                if (u.Side != side || u.Group != g || !u.Alive) continue;
                u.HasAnchor = true;
                u.Anchor = u.Pos;
            }
        }

        public void HoldAt(int side, IReadOnlyList<Group> groups, Vec2 point)
        {
            var facing = FacingFrom(side, point);
            float depth = 0;
            foreach (var g in BattleRules.DepthOrder(Armies[side].Formation))
            {
                if (!Contains(groups, g)) continue;
                int n = 0;
                foreach (var u in Units)
                    if (u.Side == side && u.Group == g && u.Alive) n++;
                if (n == 0) continue;
                AssignBlock(side, g, ClampToField(point - facing * depth), facing);
                Shape(n, out _, out int rows);
                depth += rows * Spacing(g) + BattleRules.BlockGap;
            }
        }

        public void Advance(int side, Group g, float meters)
        {
            var hold = holds[side, (int)g];
            if (orders[side, (int)g] != Order.Hold || hold == null) HoldInPlace(side, g);
            hold = holds[side, (int)g];
            if (hold == null) return;
            var shift = hold.Facing * meters;
            hold.Center = ClampToField(hold.Center + shift);
            if (hold.Block)
            {
                AssignBlock(side, g, hold.Center, hold.Facing);
                return;
            }
            foreach (var u in Units)
            {
                if (u.Side != side || u.Group != g || !u.Alive) continue;
                u.Anchor = ClampToField((u.HasAnchor ? u.Anchor : u.Pos) + shift);
                u.HasAnchor = true;
            }
        }

        static bool Contains(IReadOnlyList<Group> groups, Group g)
        {
            for (int i = 0; i < groups.Count; i++)
                if (groups[i] == g) return true;
            return false;
        }

        Vec2 FacingFrom(int side, Vec2 from)
        {
            if (TryCenter(1 - side, out var enemy))
            {
                var d = (enemy - from).Normalized;
                if (d.LengthSq > 0.5f) return d;
            }
            return Forward(side);
        }

        public Vec2 DeployMin(int side) => side == 0
            ? new Vec2(-BattleRules.FieldLength / 2f + BattleRules.DeployEdge, -BattleRules.FieldWidth / 2f + BattleRules.DeployEdge)
            : new Vec2(BattleRules.DeployFrontLimit, -BattleRules.FieldWidth / 2f + BattleRules.DeployEdge);

        public Vec2 DeployMax(int side) => side == 0
            ? new Vec2(-BattleRules.DeployFrontLimit, BattleRules.FieldWidth / 2f - BattleRules.DeployEdge)
            : new Vec2(BattleRules.FieldLength / 2f - BattleRules.DeployEdge, BattleRules.FieldWidth / 2f - BattleRules.DeployEdge);

        public bool InDeployZone(int side, Vec2 p)
        {
            var a = DeployMin(side);
            var b = DeployMax(side);
            return p.X >= a.X && p.X <= b.X && p.Y >= a.Y && p.Y <= b.Y;
        }

        public void PlaceGroups(int side, IReadOnlyList<Group> groups, Vec2 point)
        {
            if (!Deploying) return;
            var forward = Forward(side);
            var right = forward.Perpendicular;
            var zoneMin = DeployMin(side);
            var zoneMax = DeployMax(side);
            float depth = 0;
            foreach (var g in BattleRules.DepthOrder(Armies[side].Formation))
            {
                if (!Contains(groups, g)) continue;
                var list = new List<BattleUnit>();
                foreach (var u in Units)
                    if (u.Side == side && u.Group == g && u.Alive) list.Add(u);
                if (list.Count == 0) continue;
                float spacing = Spacing(g);
                Shape(list.Count, out int cols, out int rows);
                float halfW = (cols - 1) * spacing / 2f;
                float blockDepth = (rows - 1) * spacing;
                var c = point - forward * depth;
                float minFront = forward.X > 0 ? zoneMin.X + blockDepth : zoneMin.X;
                float maxFront = forward.X > 0 ? zoneMax.X : zoneMax.X - blockDepth;
                float fx = Math.Clamp(c.X, minFront, Math.Max(minFront, maxFront));
                float fy = Math.Clamp(c.Y, zoneMin.Y + halfW, Math.Max(zoneMin.Y + halfW, zoneMax.Y - halfW));
                var center = new Vec2(fx, fy);
                for (int i = 0; i < list.Count; i++)
                {
                    int row = i / cols;
                    int col = i % cols;
                    int inRow = Math.Min(cols, list.Count - row * cols);
                    var u = list[i];
                    u.Pos = center + right * ((col - (inRow - 1) / 2f) * spacing) - forward * (row * spacing);
                    u.Facing = forward;
                    u.HasAnchor = false;
                    u.Target = null;
                    u.State = UnitState.Idle;
                }
                depth += rows * spacing + BattleRules.BlockGap;
            }
        }

        void UpdateFollow(float dt)
        {
            followTimer -= dt;
            if (followTimer > 0) return;
            followTimer = BattleRules.FollowRefresh;
            for (int side = 0; side < 2; side++)
            {
                var hero = Hero(side);
                foreach (var g in BattleRules.AllGroups)
                {
                    if (orders[side, (int)g] != Order.Follow) continue;
                    if (hero == null || !hero.Alive)
                    {
                        SetOrder(side, g, Order.Attack);
                        continue;
                    }
                    var hold = holds[side, (int)g];
                    if (hold == null || Vec2.Distance(hold.Center, FollowCenter(side, g, hero)) > 2f) FollowAnchor(side, g, hero);
                }
            }
        }

        Vec2 FollowCenter(int side, Group g, BattleUnit hero)
        {
            var facing = hero.Facing.LengthSq > 0.1f ? hero.Facing.Normalized : Forward(side);
            float back = g switch
            {
                Group.Ranged => BattleRules.FollowDistance * 2.4f,
                Group.Cavalry => BattleRules.FollowDistance * 1.6f,
                _ => BattleRules.FollowDistance,
            };
            return ClampToField(hero.Pos - facing * back);
        }

        void FollowAnchor(int side, Group g, BattleUnit hero)
        {
            var facing = hero.Facing.LengthSq > 0.1f ? hero.Facing.Normalized : Forward(side);
            AssignBlock(side, g, FollowCenter(side, g, hero), facing, Order.Follow);
        }

        void AssignBlock(int side, Group g, Vec2 center, Vec2 facing, Order order = Order.Hold)
        {
            var list = new List<BattleUnit>();
            foreach (var u in Units)
                if (u.Side == side && u.Group == g && u.Alive && !(u.IsHero && Options.ManualHero && side == PlayerSide)) list.Add(u);
            orders[side, (int)g] = order;
            holds[side, (int)g] = new GroupHold { Block = true, Center = center, Facing = facing };
            if (list.Count == 0) return;

            float spacing = Spacing(g);
            Shape(list.Count, out int cols, out int rows);
            var right = facing.Perpendicular;
            list.Sort((a, b) => Vec2.Dot(b.Pos, facing).CompareTo(Vec2.Dot(a.Pos, facing)));
            for (int row = 0; row < rows; row++)
            {
                int start = row * cols;
                int inRow = Math.Min(cols, list.Count - start);
                var chunk = list.GetRange(start, inRow);
                chunk.Sort((a, b) => Vec2.Dot(a.Pos, right).CompareTo(Vec2.Dot(b.Pos, right)));
                for (int col = 0; col < inRow; col++)
                {
                    float lateral = (col - (inRow - 1) / 2f) * spacing;
                    var u = chunk[col];
                    u.Anchor = ClampToField(center + right * lateral - facing * (row * spacing));
                    u.HasAnchor = true;
                }
            }
        }

        static Vec2 ClampToField(Vec2 p)
        {
            float hx = BattleRules.FieldLength / 2f - 2f;
            float hy = BattleRules.FieldWidth / 2f - 1f;
            return new Vec2(Math.Clamp(p.X, -hx, hx), Math.Clamp(p.Y, -hy, hy));
        }

        void Ai(float dt)
        {
            for (int side = 0; side < 2; side++)
            {
                int my = ActiveCount(side) + Reserves[side].Count;
                int their = ActiveCount(1 - side) + Reserves[1 - side].Count;
                if (my > 0 && their > my * 2) Shake(side, BattleRules.OutnumberedDrain * dt);
            }
            aiTime += dt;
            for (int side = 0; side < 2; side++)
                if (AiEnabled[side]) AiFor(side);
        }

        void AiFor(int side)
        {
            if (!TryCenter(side, out var mine) || !TryCenter(1 - side, out var enemy)) return;
            float gap = Vec2.Distance(mine, enemy);
            string culture = Armies[side].Culture ?? "";
            float t = aiTime;
            bool hurt = Morale[side] < MaxMorale[side] * 0.8f;
            float nearest = float.MaxValue;
            if (TryGroupCenter(side, Group.Infantry, out var inf))
                foreach (var e in Units)
                    if (e.Side != side && e.Alive) nearest = Math.Min(nearest, Vec2.Distance(e.Pos, inf));

            if (Once(side, "start", true))
            {
                orders[side, (int)Group.Hero] = Order.Attack;
                switch (culture)
                {
                    case "aurelia":
                        orders[side, (int)Group.Cavalry] = Order.Hold;
                        orders[side, (int)Group.Infantry] = Order.Attack;
                        break;
                    case "nordmark":
                    case "horde":
                    case "sultanate":
                        orders[side, (int)Group.Infantry] = Order.Hold;
                        orders[side, (int)Group.Cavalry] = Order.Hold;
                        break;
                    default:
                        orders[side, (int)Group.Infantry] = Order.Attack;
                        orders[side, (int)Group.Cavalry] = Order.Attack;
                        break;
                }
            }

            switch (culture)
            {
                case "aurelia":
                    if (Once(side, "knights", t > 1.5f)) SetOrder(side, Group.Cavalry, Order.Attack);
                    break;
                case "nordmark":
                    if (Once(side, "advance", nearest < 26f || hurt || t > 28f)) SetOrder(side, Group.Infantry, Order.Attack);
                    if (Once(side, "cav", t > 10f)) SetOrder(side, Group.Cavalry, Order.Attack);
                    break;
                case "horde":
                    if (Once(side, "cav", t > 9f)) SetOrder(side, Group.Cavalry, Order.Attack);
                    if (Once(side, "inf", nearest < 24f || t > 30f)) SetOrder(side, Group.Infantry, Order.Attack);
                    break;
                case "sultanate":
                    if (Once(side, "cav", t > 6f)) SetOrder(side, Group.Cavalry, Order.Attack);
                    if (Once(side, "inf", nearest < 22f || t > 24f)) SetOrder(side, Group.Infantry, Order.Attack);
                    break;
                default:
                    if (Once(side, "cav", t > 2f)) SetOrder(side, Group.Cavalry, Order.Attack);
                    break;
            }

            bool alone = true;
            foreach (var u in Units)
                if (u.Side == side && u.Alive && !u.Troop.IsRanged && !u.IsHero) { alone = false; break; }
            if (alone)
                foreach (var u in Reserves[side])
                    if (!u.Troop.IsRanged) { alone = false; break; }
            var rangedOrder = gap > BattleRules.RangedAdvanceGap || alone ? Order.Attack : Order.Hold;
            if (orders[side, (int)Group.Ranged] != rangedOrder)
            {
                orders[side, (int)Group.Ranged] = rangedOrder;
                holds[side, (int)Group.Ranged] = null;
                foreach (var u in Units)
                    if (u.Side == side && u.Group == Group.Ranged) u.HasAnchor = false;
            }
        }

        bool Once(int side, string key, bool condition)
        {
            if (!condition) return false;
            return aiStage.Add(side + ":" + key);
        }
    }
}
