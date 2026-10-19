using System.Collections.Generic;

namespace Warfare.Core.Battle
{
    public enum Group { Hero = 0, Infantry = 1, Ranged = 2, Cavalry = 3 }

    public enum Order { Attack, Hold, Retreat, Follow }

    public enum Formation { Classic, ArchersFront, CavCharge }

    public enum UnitState { Idle, Walk, Attack, Dead, Fled }

    public enum ProjectileKind { Arrow, Bolt, Ball }

    public enum BattleEventKind { Hit, Crit, Block, Dodge, Death, Shoot, Gun, Charge, Brace, Rout, HeroDown }

    public readonly struct BattleEvent
    {
        public readonly BattleEventKind Kind;
        public readonly Vec2 Pos;
        public readonly int Side;
        public readonly float Amount;

        public BattleEvent(BattleEventKind kind, Vec2 pos, int side, float amount = 0)
        {
            Kind = kind;
            Pos = pos;
            Side = side;
            Amount = amount;
        }
    }

    public sealed class ArmyStack
    {
        public string TroopId { get; set; }
        public int Count { get; set; }
        public string Key { get; set; }

        public ArmyStack() { }

        public ArmyStack(string troopId, int count)
        {
            TroopId = troopId;
            Count = count;
        }
    }

    public sealed class ArmyDef
    {
        public string Name { get; set; }
        public string Culture { get; set; }
        public List<ArmyStack> Troops { get; set; } = new List<ArmyStack>();
        public TroopDef Hero { get; set; }
        public Formation Formation { get; set; } = Formation.Classic;
        public float Morale { get; set; } = 100;
    }

    public struct HeroInput
    {
        public Vec2 Move;
        public Vec2 Aim;
        public bool Attack;
        public bool Block;
    }

    public sealed class BattleOptions
    {
        public bool Deployment { get; set; }
        public bool ManualHero { get; set; }
        public uint Seed { get; set; } = 1;
        public int PlayerSide { get; set; } = 0;
        public int MaxOnField { get; set; } = BattleRules.MaxOnField;
        public float TimeLimit { get; set; } = BattleRules.TimeLimit;
    }

    public sealed class Projectile
    {
        public int Id;
        public ProjectileKind Kind;
        public Vec2 From;
        public Vec2 To;
        public Vec2 Pos;
        public float Height;
        public float Arc;
        public float T;
        public float Duration;
        public BattleUnit Source;
        public BattleUnit Target;
        public bool WillHit;
        public float Mult;
        public bool Done;

        public float Progress => Duration <= 0 ? 1 : T / Duration;
    }

    public sealed class StackResult
    {
        public string Key;
        public TroopDef Troop;
        public int Dead;
        public int Survived;
        public float Xp;
    }

    public sealed class BattleSummary
    {
        public readonly Dictionary<string, StackResult> Stacks = new Dictionary<string, StackResult>();
        public bool HeroDead;
        public int Dead;
        public int Survived;
    }
}
