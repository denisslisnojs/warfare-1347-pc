namespace Warfare.Core.Battle
{
    public sealed class BattleUnit
    {
        public int Uid;
        public int Side;
        public TroopDef Troop;
        public Group Group;
        public bool IsHero;
        public string StackKey;
        public float Hp;
        public float MaxHp;
        public Vec2 Pos;
        public Vec2 Velocity;
        public Vec2 Facing;
        public UnitState State;
        public float Swing;
        public float Cooldown;
        public BattleUnit Target;
        public float Retarget;
        public bool Charging;
        public float ChargeDist;
        public float Flash;
        public float Xp;
        public bool Routed;
        public float DeadTime;
        public int Ammo;
        public float Stun;
        public bool Blocking;
        public bool HasAnchor;
        public Vec2 Anchor;

        public bool Alive => State != UnitState.Dead && State != UnitState.Fled;
        public float HpFraction => MaxHp <= 0 ? 0 : Hp / MaxHp;
    }
}
