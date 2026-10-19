using System;

namespace Warfare.Core.Battle
{
    public sealed partial class BattleSim
    {
        void Think(BattleUnit u, float dt)
        {
            if (u.Stun > 0)
            {
                u.Stun -= dt;
                u.Swing = 0;
                u.State = UnitState.Idle;
                Separate(u, dt, 0.3f);
                return;
            }

            bool berserk = u.Troop.Has(Traits.Berserk);
            var order = Routed[u.Side] && !berserk ? Order.Retreat : orders[u.Side, (int)u.Group];
            if (berserk) order = Order.Attack;
            if (u.Routed && !berserk) order = Order.Retreat;
            if (order == Order.Retreat)
            {
                u.Swing = 0;
                u.Target = null;
                Flee(u, dt);
                return;
            }

            u.Retarget -= dt;
            if (u.Target == null || !u.Target.Alive || u.Retarget <= 0)
            {
                u.Target = FindTarget(u);
                u.Retarget = 0.6f + rng.Value * 0.4f;
            }
            var t = u.Target;
            if (t == null)
            {
                if (order == Order.Hold || order == Order.Follow) HoldPosition(u, dt, null, float.MaxValue);
                else u.State = UnitState.Idle;
                return;
            }

            var delta = t.Pos - u.Pos;
            float dist = delta.Length;

            if (u.Swing > 0)
            {
                if (dist > 0.05f) u.Facing = delta / dist;
                u.Swing -= dt;
                u.State = UnitState.Attack;
                Separate(u, dt, 0.5f);
                if (u.Swing <= 0) Strike(u, t);
                return;
            }

            float reach = Reach(u, t);
            bool ranged = u.Troop.IsRanged && u.Ammo > 0;

            if (dist <= reach)
            {
                if (dist > 0.05f) u.Facing = delta / dist;
                u.State = UnitState.Attack;
                Separate(u, dt, 0.9f);
                if (u.Cooldown <= 0)
                {
                    bool brace = t.Troop.IsCavalry && t.Charging && Braced(u);
                    StartSwing(u, brace ? 0.1f : ranged ? 0.25f : 0.3f);
                }
                return;
            }

            if (ranged && dist <= RangeOf(u))
            {
                if (dist > 0.05f) u.Facing = delta / dist;
                Separate(u, dt, 0.5f);
                u.State = u.Cooldown <= 0.3f ? UnitState.Attack : UnitState.Idle;
                if (u.Cooldown <= 0) Shoot(u, t);
                return;
            }

            if (order == Order.Hold || order == Order.Follow)
            {
                HoldPosition(u, dt, t, dist);
                return;
            }

            if (u.IsHero && HeroWaits(u, dist))
            {
                if (dist > 0.05f) u.Facing = delta / dist;
                Separate(u, dt, 0.6f);
                u.State = UnitState.Idle;
                return;
            }

            float stand = reach * 0.8f;
            if (!u.Troop.IsRanged && Crowded(u, t)) stand = reach + BattleRules.WaitBehindGap;
            var approach = t.Pos + (u.Pos - t.Pos).Normalized * stand;
            Steer(u, approach - u.Pos, dt, 1f);
        }

        void Manual(BattleUnit u, float dt)
        {
            var input = HeroInput;
            u.Target = null;
            if (u.Stun > 0)
            {
                u.Stun -= dt;
                u.Swing = 0;
                u.Blocking = false;
                u.State = UnitState.Idle;
                return;
            }
            var aim = input.Aim.LengthSq > 0.01f ? input.Aim.Normalized : u.Facing;
            var move = input.Move.LengthSq > 1f ? input.Move.Normalized : input.Move;

            if (u.Swing > 0)
            {
                u.Blocking = false;
                u.Swing -= dt;
                u.State = UnitState.Attack;
                u.Facing = aim;
                if (move.LengthSq > 0.02f) MoveManual(u, move, BattleRules.HeroSwingSpeed, dt);
                if (u.Swing <= 0)
                {
                    var t = FoeInFront(u, Reach(u, null) + BattleRules.StrikeSlack);
                    if (t != null) Strike(u, t);
                    else u.Cooldown = u.Troop.AttackTime * 0.8f;
                }
                return;
            }

            u.Blocking = input.Block;
            if (input.Attack && !input.Block && u.Cooldown <= 0)
            {
                u.Facing = aim;
                StartSwing(u, BattleRules.HeroWindup);
                return;
            }

            u.Facing = aim;
            if (move.LengthSq > 0.02f)
            {
                float along = Vec2.Dot(move.Normalized, aim);
                float k = along < -0.3f ? BattleRules.HeroBackSpeed : along < 0.5f ? BattleRules.HeroStrafeSpeed : 1f;
                MoveManual(u, move, (input.Block ? BattleRules.HeroBlockSpeed : 1f) * k, dt);
                return;
            }
            Separate(u, dt, 0.3f);
            u.State = UnitState.Idle;
        }

        void MoveManual(BattleUnit u, Vec2 move, float k, float dt)
        {
            float speed = u.Troop.Speed * BattleRules.SpeedK * k;
            var push = Separation(u) * 0.6f;
            u.Pos = Clamp(u.Pos + (move + push) * (speed * dt));
            if (u.State != UnitState.Attack) u.State = UnitState.Walk;
        }

        BattleUnit FoeInFront(BattleUnit u, float range)
        {
            BattleUnit best = null;
            float bestScore = float.MaxValue;
            foreach (var e in Units)
            {
                if (e.Side == u.Side || !e.Alive) continue;
                var d = e.Pos - u.Pos;
                float dist = d.Length;
                if (dist > range) continue;
                float dot = dist > 0.01f ? Vec2.Dot(d / dist, u.Facing) : 1f;
                if (dot < BattleRules.HeroStrikeCone) continue;
                float score = dist * (2f - dot);
                if (score < bestScore)
                {
                    bestScore = score;
                    best = e;
                }
            }
            return best;
        }

        void HoldPosition(BattleUnit u, float dt, BattleUnit target, float targetDist)
        {
            if (u.HasAnchor && Vec2.Distance(u.Pos, u.Anchor) > BattleRules.AnchorTolerance)
            {
                Steer(u, u.Anchor - u.Pos, dt, 1f);
                return;
            }
            Separate(u, dt, 0.6f);
            u.State = UnitState.Idle;
            if (target != null && targetDist < BattleRules.FaceEnemyRadius) u.Facing = (target.Pos - u.Pos).Normalized;
            else
            {
                var hold = holds[u.Side, (int)u.Group];
                if (hold != null) u.Facing = hold.Facing;
            }
        }

        bool Crowded(BattleUnit u, BattleUnit t)
        {
            int engaged = 0;
            foreach (var a in Units)
            {
                if (a == u || a.Target != t || !a.Alive || a.Side == t.Side) continue;
                if (Vec2.Distance(a.Pos, t.Pos) <= Reach(a, t) + 0.3f) engaged++;
            }
            return engaged >= BattleRules.MaxMeleeAttackers;
        }

        bool HeroWaits(BattleUnit u, float dist)
        {
            var forward = Forward(u.Side);
            float front = float.MinValue;
            foreach (var a in Units)
                if (a.Side == u.Side && a.Group == Group.Infantry && a.Alive) front = Math.Max(front, Vec2.Dot(a.Pos, forward));
            if (front == float.MinValue) return false;
            return Vec2.Dot(u.Pos, forward) - front > -BattleRules.HeroBehindFront && dist > BattleRules.HeroEngageDistance;
        }

        BattleUnit FindTarget(BattleUnit u)
        {
            BattleUnit best = null;
            float bestD = float.MaxValue;
            bool melee = !u.Troop.IsRanged;
            foreach (var e in Units)
            {
                if (e.Side == u.Side || !e.Alive) continue;
                float d = Vec2.Distance(e.Pos, u.Pos);
                if (u.Group == Group.Cavalry && e.Troop.IsRanged) d *= 0.8f;
                if (melee && e != u.Target && attackers.TryGetValue(e.Uid, out int busy))
                {
                    d += busy * BattleRules.BusyTargetPenalty;
                    if (busy >= BattleRules.MaxMeleeAttackers) d += BattleRules.FullTargetPenalty;
                }
                if (d < bestD)
                {
                    bestD = d;
                    best = e;
                }
            }
            return best;
        }

        float Reach(BattleUnit u, BattleUnit t)
        {
            if (u.Troop.IsCavalry) return BattleRules.ReachCavalry;
            float r = BattleRules.IsPole(u.Troop) ? BattleRules.ReachPole : BattleRules.ReachShort;
            if (t != null && t.Troop.IsCavalry && Braced(u)) r += BattleRules.BraceExtraReach;
            return r;
        }

        bool Braced(BattleUnit u) => u.Troop.Has(Traits.Brace) && u.State != UnitState.Walk;

        public float RangeOf(BattleUnit u) => u.Troop.Range * BattleRules.RangeK;

        void StartSwing(BattleUnit u, float windup)
        {
            u.Swing = windup;
            u.State = UnitState.Attack;
        }

        void Strike(BattleUnit u, BattleUnit t)
        {
            u.Cooldown = u.Troop.AttackTime * rng.Range(0.9f, 1.1f);
            if (!t.Alive) return;
            if (Vec2.Distance(t.Pos, u.Pos) > Reach(u, t) + BattleRules.StrikeSlack) return;

            float mult = u.Troop.IsRanged ? 0.55f : 1f;
            if (u.Charging && u.Troop.IsCavalry)
            {
                mult *= u.Troop.Look?.Weapon == "lance" ? 1.9f : 1.5f;
                if (Braced(t)) mult *= 0.55f;
                u.Charging = false;
                u.ChargeDist = 0;
                Events.Add(new BattleEvent(BattleEventKind.Charge, t.Pos, u.Side));
            }
            if (BattleRules.IsPole(u.Troop) && t.Troop.IsCavalry)
            {
                mult *= 1.4f;
                if (t.Charging && Braced(u))
                {
                    mult *= 2f;
                    t.Charging = false;
                    t.ChargeDist = 0;
                    t.Stun = Math.Max(t.Stun, 0.6f);
                    Events.Add(new BattleEvent(BattleEventKind.Brace, t.Pos, u.Side));
                }
            }
            ResolveHit(u, t, mult, false, ProjectileKind.Arrow);
        }

        void Shoot(BattleUnit u, BattleUnit t)
        {
            bool gun = u.Troop.Has(Traits.Gun);
            u.State = UnitState.Attack;
            u.Ammo--;
            u.Cooldown = u.Troop.AttackTime * rng.Range(0.9f, 1.15f);

            float dist = Vec2.Distance(t.Pos, u.Pos);
            float range = Math.Max(1f, RangeOf(u));
            double hitChance = gun ? 0.76 - dist / range * 0.3 : 0.88 - dist / range * 0.35;
            bool willHit = rng.Chance(hitChance);
            var kind = gun ? ProjectileKind.Ball : u.Troop.Look?.Weapon == "crossbow" ? ProjectileKind.Bolt : ProjectileKind.Arrow;
            float dur = gun ? 0.05f + dist / BattleRules.BulletSpeed : 0.25f + dist / BattleRules.ArrowSpeed;
            var aim = t.Pos + t.Velocity * dur;
            if (!willHit) aim += new Vec2(rng.Range(-1f, 1f), rng.Range(-1f, 1f)) * BattleRules.MissSpread;

            Projectiles.Add(new Projectile
            {
                Id = nextProjectileId++,
                Kind = kind,
                From = u.Pos,
                To = aim,
                Pos = u.Pos,
                Height = BattleRules.ShotHeight,
                Arc = gun ? 0 : Math.Min(BattleRules.MaxArc, dist * 0.22f),
                Duration = dur,
                Source = u,
                Target = t,
                WillHit = willHit,
                Mult = 1f,
            });

            if (gun)
            {
                Events.Add(new BattleEvent(BattleEventKind.Gun, u.Pos, u.Side));
                Shake(t.Side, BattleRules.GunShake);
            }
            else Events.Add(new BattleEvent(BattleEventKind.Shoot, u.Pos, u.Side));
        }

        void UpdateProjectiles(float dt)
        {
            foreach (var p in Projectiles)
            {
                if (p.Done) continue;
                p.T += dt;
                float k = Math.Min(1f, p.Progress);
                p.Pos = p.From + (p.To - p.From) * k;
                p.Height = BattleRules.ShotHeight + (BattleRules.HitHeight - BattleRules.ShotHeight) * k + MathF.Sin(k * MathF.PI) * p.Arc;
                if (k < 1f) continue;
                p.Done = true;
                if (p.WillHit && p.Target.Alive && Vec2.Distance(p.Target.Pos, p.To) < BattleRules.ProjectileHitRadius)
                    ResolveHit(p.Source, p.Target, p.Mult, true, p.Kind);
            }
        }

        void ResolveHit(BattleUnit a, BattleUnit d, float mult, bool ranged, ProjectileKind kind)
        {
            var t = d.Troop;
            bool ball = ranged && kind == ProjectileKind.Ball;
            bool twohand = !ranged && a.Troop.Has(Traits.Twohand);
            var toAttacker = (a.Pos - d.Pos).Normalized;
            float c = toAttacker.LengthSq > 0 ? Vec2.Dot(toAttacker, d.Facing) : 1f;
            bool behind = !ranged && c < -0.3f;
            bool flank = !ranged && !behind && c < 0.4f;
            bool helpless = d.Stun > 0 && !d.IsHero;

            float dodge = helpless ? 0 : t.Dodge;
            if (ranged) dodge *= ball ? 0.35f : 0.7f;
            if (rng.Chance(dodge))
            {
                Events.Add(new BattleEvent(BattleEventKind.Dodge, d.Pos, d.Side));
                return;
            }

            bool facingAttacker = c >= 0;
            if (d.Blocking && facingAttacker)
            {
                float held = t.Block > 0 ? BattleRules.HeroBlockShield : ranged ? BattleRules.HeroBlockRanged : BattleRules.HeroBlockParry;
                if (rng.Chance(held))
                {
                    Events.Add(new BattleEvent(BattleEventKind.Block, d.Pos, d.Side));
                    return;
                }
            }
            float block = t.Block;
            if (block > 0)
            {
                if (twohand) block *= 0.5f;
                if (ball) block *= 0.4f;
                if (flank) block *= 0.6f;
            }
            if (a.Troop.Has(Traits.Berserk)) block *= 0.6f;
            if (helpless) block = 0;
            if (block > 0 && facingAttacker && d.Swing <= 0 && rng.Chance(Math.Min(0.9f, block * (ranged ? 0.8f : 1f))))
            {
                Events.Add(new BattleEvent(BattleEventKind.Block, d.Pos, d.Side));
                return;
            }

            bool crit = false;
            if (rng.Chance(a.Troop.Crit))
            {
                crit = true;
                mult *= rng.Range(1.5f, 2f);
            }
            if (a.Troop.Has(Traits.Berserk)) mult *= 1f + 0.8f * (1f - a.HpFraction);
            if (!ranged)
            {
                if (behind)
                {
                    mult *= 1.35f;
                    Shake(d.Side, BattleRules.RearHitMorale);
                }
                else if (flank) mult *= 1.15f;
                if (helpless) mult *= 1.3f;
            }

            float armorK = ball ? 0.5f : twohand ? 0.65f : 1f;
            float dmg = a.Troop.Damage * rng.Range(0.85f, 1.15f) * mult * (1f - t.Armor[a.Troop.DamageType] * armorK);
            if (ball && t.IsCavalry) d.Stun = Math.Max(d.Stun, 1f);
            Damage(a, d, Math.Max(1f, MathF.Round(dmg)), crit);
        }

        public static float ArmorFactor(TroopDef target, DamageType type, float armorK = 1f) => 1f - target.Armor[type] * armorK;

        void Damage(BattleUnit a, BattleUnit d, float dmg, bool crit)
        {
            d.Hp -= dmg;
            d.Flash = 0.18f;
            Events.Add(new BattleEvent(crit ? BattleEventKind.Crit : BattleEventKind.Hit, d.Pos, d.Side, dmg));
            if (a != null) a.Xp += dmg * 0.4f;
            if (d.Hp > 0) return;

            d.Hp = 0;
            d.State = UnitState.Dead;
            d.DeadTime = 0;
            d.Swing = 0;
            d.Target = null;
            if (a != null) a.Xp += d.Troop.Tier * 14 + 6;
            int side = d.Side;
            float loss = BattleRules.MoraleLossPerArmy / Math.Max(8, InitialCount[side]);
            if (d.Troop.Has(Traits.Berserk)) loss *= 0.5f;
            if (d.IsHero)
            {
                loss += BattleRules.HeroDeathMorale;
                if (side == PlayerSide) HeroDown = true;
                Events.Add(new BattleEvent(BattleEventKind.HeroDown, d.Pos, side));
            }
            Shake(side, loss);
            Morale[1 - side] = Math.Min(MaxMorale[1 - side], Morale[1 - side] + BattleRules.KillMoraleGain);
            Events.Add(new BattleEvent(BattleEventKind.Death, d.Pos, side));
        }

        void Shake(int side, float amount)
        {
            Morale[side] = Math.Max(0, Morale[side] - amount / Resolve[side]);
        }
    }
}
