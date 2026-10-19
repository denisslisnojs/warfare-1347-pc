using System;
using System.Collections.Generic;

namespace Warfare.Core.Battle
{
    public sealed partial class BattleSim
    {
        sealed class GroupHold
        {
            public bool Block;
            public Vec2 Center;
            public Vec2 Facing;
        }

        public readonly List<BattleUnit> Units = new List<BattleUnit>();
        public readonly List<BattleUnit>[] Reserves = { new List<BattleUnit>(), new List<BattleUnit>() };
        public readonly List<Projectile> Projectiles = new List<Projectile>();
        public readonly List<BattleEvent> Events = new List<BattleEvent>();
        public readonly float[] Morale = new float[2];
        public readonly float[] MaxMorale = new float[2];
        public readonly int[] InitialCount = new int[2];
        public readonly float[] Resolve = { 1f, 1f };
        public readonly bool[] Routed = new bool[2];
        public readonly bool[] AiEnabled = new bool[2];
        public readonly ArmyDef[] Armies;
        public readonly BattleOptions Options;

        public HeroInput HeroInput;
        public bool Deploying { get; private set; }
        public float Time { get; private set; }
        public int? Winner { get; private set; }
        public bool HeroDown { get; private set; }
        public int PlayerSide => Options.PlayerSide;
        public bool Finished => Winner.HasValue;

        readonly Order[,] orders = new Order[2, 4];
        readonly GroupHold[,] holds = new GroupHold[2, 4];
        readonly Rng rng;
        readonly Dictionary<int, int> attackers = new Dictionary<int, int>();
        readonly HashSet<string> aiStage = new HashSet<string>();
        int nextUid = 1;
        int nextProjectileId = 1;
        float aiTime;
        float followTimer;

        public BattleSim(ArmyDef army0, ArmyDef army1, TroopCatalog catalog, BattleOptions options = null)
        {
            Options = options ?? new BattleOptions();
            Armies = new[] { army0, army1 };
            rng = new Rng(Options.Seed);
            Deploying = Options.Deployment;
            AiEnabled[1 - PlayerSide] = true;

            for (int side = 0; side < 2; side++)
            {
                Morale[side] = MaxMorale[side] = Armies[side].Morale;
                orders[side, (int)Group.Hero] = Order.Attack;
                orders[side, (int)Group.Infantry] = Order.Attack;
                orders[side, (int)Group.Ranged] = Order.Hold;
                orders[side, (int)Group.Cavalry] = side == PlayerSide ? Order.Attack : Order.Hold;

                var all = new List<BattleUnit>();
                var army = Armies[side];
                if (army.Hero != null) all.Add(Make(side, army.Hero, "hero", true));
                foreach (var stack in army.Troops)
                {
                    var def = catalog.Get(stack.TroopId);
                    for (int i = 0; i < stack.Count; i++) all.Add(Make(side, def, stack.Key ?? stack.TroopId, false));
                }
                InitialCount[side] = all.Count;
                Deploy(side, all, army.Formation);

                int n = 0;
                float sum = 0;
                foreach (var u in all)
                {
                    if (u.IsHero) continue;
                    n++;
                    sum += u.Troop.Tier;
                }
                float tier = n > 0 ? sum / n : 3f;
                Resolve[side] = 1f + 0.1f * (tier - 1f);
            }
        }

        BattleUnit Make(int side, TroopDef troop, string stackKey, bool isHero)
        {
            return new BattleUnit
            {
                Uid = nextUid++,
                Side = side,
                Troop = troop,
                Group = isHero ? Group.Hero : BattleRules.GroupOf(troop),
                IsHero = isHero,
                StackKey = stackKey,
                Hp = troop.Hp,
                MaxHp = troop.Hp,
                Facing = Forward(side),
                State = UnitState.Idle,
                Cooldown = rng.Range(0f, 1f),
                Charging = troop.IsCavalry,
                Ammo = BattleRules.StartingAmmo(troop),
            };
        }

        public static Vec2 Forward(int side) => new Vec2(side == 0 ? 1f : -1f, 0f);

        void Deploy(int side, List<BattleUnit> all, Formation formation)
        {
            var byGroup = new List<BattleUnit>[4];
            for (int g = 0; g < 4; g++) byGroup[g] = new List<BattleUnit>();
            foreach (var u in all) byGroup[(int)u.Group].Add(u);

            int max = Options.MaxOnField;
            var onField = new HashSet<BattleUnit>();
            foreach (var g in BattleRules.AllGroups)
            {
                var list = byGroup[(int)g];
                int quota = Math.Min(list.Count, (int)Math.Ceiling(list.Count / (double)Math.Max(1, all.Count) * max));
                for (int i = 0; i < quota && onField.Count < max; i++) onField.Add(list[i]);
            }

            var forward = Forward(side);
            var right = forward.Perpendicular;
            float depth = 0;
            Vec2 front = forward * -BattleRules.DeployFront;
            foreach (var g in BattleRules.DepthOrder(formation))
            {
                var list = byGroup[(int)g].FindAll(onField.Contains);
                if (list.Count == 0) continue;
                float spacing = Spacing(g);
                Shape(list.Count, out int cols, out int rows);
                for (int i = 0; i < list.Count; i++)
                {
                    int row = i / cols;
                    int col = i % cols;
                    int inRow = row == rows - 1 ? list.Count - row * cols : cols;
                    float lateral = (col - (inRow - 1) / 2f) * spacing + rng.Range(-0.2f, 0.2f);
                    float back = depth + row * spacing + rng.Range(-0.2f, 0.2f);
                    list[i].Pos = front + right * lateral - forward * back;
                }
                depth += rows * spacing + BattleRules.BlockGap;
            }

            foreach (var u in all)
            {
                if (onField.Contains(u)) Units.Add(u);
                else Reserves[side].Add(u);
            }
        }

        static float Spacing(Group g) => g == Group.Cavalry || g == Group.Hero ? BattleRules.CavalrySpacing : BattleRules.InfantrySpacing;

        static void Shape(int n, out int cols, out int rows)
        {
            cols = Math.Max(1, Math.Min(BattleRules.MaxBlockColumns, (int)Math.Ceiling(Math.Sqrt(n * 4.0))));
            rows = (int)Math.Ceiling(n / (double)cols);
        }

        public void Begin()
        {
            Deploying = false;
        }

        public BattleUnit Hero(int side)
        {
            foreach (var u in Units)
                if (u.Side == side && u.IsHero) return u;
            return null;
        }

        public bool HeroManualActive
        {
            get
            {
                if (!Options.ManualHero || Routed[PlayerSide]) return false;
                var h = Hero(PlayerSide);
                return h != null && h.Alive;
            }
        }

        public void Step(float dt)
        {
            Events.Clear();
            if (Deploying) return;
            Projectiles.RemoveAll(p => p.Done);
            if (Finished)
            {
                foreach (var u in Units)
                    if (u.Routed && u.Alive) Flee(u, dt);
                UpdateProjectiles(dt);
                return;
            }

            Time += dt;
            Ai(dt);
            UpdateFollow(dt);

            attackers.Clear();
            foreach (var u in Units)
            {
                if (u.Target == null || !u.Alive) continue;
                attackers.TryGetValue(u.Target.Uid, out int c);
                attackers[u.Target.Uid] = c + 1;
            }

            for (int i = 0; i < Units.Count; i++)
            {
                var u = Units[i];
                if (u.State == UnitState.Dead)
                {
                    u.DeadTime += dt;
                    continue;
                }
                if (u.State == UnitState.Fled) continue;
                var before = u.Pos;
                u.Flash = Math.Max(0, u.Flash - dt);
                u.Cooldown -= dt;
                if (u.IsHero && u.Side == PlayerSide && Options.ManualHero && !Routed[u.Side]) Manual(u, dt);
                else
                {
                    u.Blocking = false;
                    Think(u, dt);
                }
                u.Velocity = (u.Pos - before) / dt;
            }

            UpdateProjectiles(dt);
            Reinforce();
            CheckEnd();
        }

        public void RunToEnd(float maxTime = BattleRules.TimeLimit + 120f, float dt = 0.1f)
        {
            Deploying = false;
            Options.ManualHero = false;
            AiEnabled[0] = AiEnabled[1] = true;
            foreach (var g in BattleRules.AllGroups) SetOrder(PlayerSide, g, Order.Attack);
            int guard = 0;
            while (!Finished && Time < maxTime && guard++ < maxTime / dt * 2) Step(dt);
            if (!Finished) Winner = Morale[0] >= Morale[1] ? 0 : 1;
        }

        public IEnumerable<BattleUnit> Active(int side)
        {
            foreach (var u in Units)
                if (u.Side == side && u.Alive) yield return u;
        }

        public int ActiveCount(int side)
        {
            int n = 0;
            foreach (var u in Units)
                if (u.Side == side && u.Alive) n++;
            return n;
        }

        public int GroupCount(int side, Group g)
        {
            int n = 0;
            foreach (var u in Units)
                if (u.Side == side && u.Group == g && u.Alive) n++;
            foreach (var u in Reserves[side])
                if (u.Group == g) n++;
            return n;
        }

        public bool TryGroupCenter(int side, Group g, out Vec2 center)
        {
            float x = 0, y = 0;
            int n = 0;
            foreach (var u in Units)
            {
                if (u.Side != side || u.Group != g || !u.Alive) continue;
                x += u.Pos.X;
                y += u.Pos.Y;
                n++;
            }
            center = n > 0 ? new Vec2(x / n, y / n) : Vec2.Zero;
            return n > 0;
        }

        public bool TryCenter(int side, out Vec2 center)
        {
            float x = 0, y = 0;
            int n = 0;
            foreach (var u in Units)
            {
                if (u.Side != side || !u.Alive) continue;
                x += u.Pos.X;
                y += u.Pos.Y;
                n++;
            }
            center = n > 0 ? new Vec2(x / n, y / n) : Vec2.Zero;
            return n > 0;
        }

        public BattleSummary Summary(int side)
        {
            var s = new BattleSummary();
            void Add(BattleUnit u)
            {
                if (u.Side != side) return;
                if (u.IsHero)
                {
                    s.HeroDead = u.State == UnitState.Dead;
                    return;
                }
                if (!s.Stacks.TryGetValue(u.StackKey, out var r))
                {
                    r = new StackResult { Key = u.StackKey, Troop = u.Troop };
                    s.Stacks[u.StackKey] = r;
                }
                if (u.State == UnitState.Dead)
                {
                    r.Dead++;
                    s.Dead++;
                }
                else
                {
                    r.Survived++;
                    s.Survived++;
                }
                r.Xp += u.Xp;
            }
            foreach (var u in Units) Add(u);
            foreach (var u in Reserves[side]) Add(u);
            return s;
        }

        void Reinforce()
        {
            for (int side = 0; side < 2; side++)
            {
                if (Routed[side] || Reserves[side].Count == 0) continue;
                int free = Options.MaxOnField - ActiveCount(side);
                var touched = new HashSet<Group>();
                var forward = Forward(side);
                while (free-- > 0 && Reserves[side].Count > 0)
                {
                    var u = Reserves[side][0];
                    Reserves[side].RemoveAt(0);
                    float x = -forward.X * (BattleRules.FieldLength / 2f - rng.Range(1f, 5f));
                    float y = rng.Range(-BattleRules.FieldWidth / 3f, BattleRules.FieldWidth / 3f);
                    u.Pos = new Vec2(x, y);
                    u.Facing = forward;
                    Units.Add(u);
                    touched.Add(u.Group);
                }
                foreach (var g in touched)
                {
                    var hold = holds[side, (int)g];
                    if (orders[side, (int)g] == Order.Hold && hold != null && hold.Block) AssignBlock(side, g, hold.Center, hold.Facing);
                }
            }
        }

        void CheckEnd()
        {
            for (int side = 0; side < 2; side++)
            {
                if (Routed[side] || Morale[side] > 0) continue;
                Routed[side] = true;
                foreach (var u in Units)
                    if (u.Side == side && u.Alive && !u.Troop.Has(Traits.Berserk)) u.Routed = true;
                Events.Add(new BattleEvent(BattleEventKind.Rout, Vec2.Zero, side));
            }

            if (Time > Options.TimeLimit && !Routed[0] && !Routed[1])
            {
                int loser = Morale[0] < Morale[1] ? 0 : 1;
                Morale[loser] = 0;
            }

            for (int side = 0; side < 2; side++)
            {
                int standing;
                if (Routed[side])
                {
                    standing = 0;
                    if (Time <= Options.TimeLimit + BattleRules.StandoffGrace)
                        foreach (var u in Units)
                            if (u.Side == side && u.Alive && !u.Routed) standing++;
                }
                else standing = ActiveCount(side) + Reserves[side].Count;

                if (standing > 0) continue;
                Winner = 1 - side;
                Routed[side] = true;
                foreach (var u in Units)
                    if (u.Side == side && u.Alive) u.Routed = true;
                return;
            }
        }
    }
}
