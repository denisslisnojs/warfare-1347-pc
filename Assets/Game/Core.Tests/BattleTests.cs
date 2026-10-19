using System.Linq;
using NUnit.Framework;
using Warfare.Core.Battle;

namespace Warfare.Core.Tests
{
    public class BattleTests
    {
        static ArmyDef Veterans(int n = 30) => TestData.Army("aurelia", ("aurelia_i4m", n));
        static ArmyDef Peasants(int n = 30) => TestData.Army("outlaw", ("aurelia_i1", n));

        static ArmyDef Mixed(string f) => TestData.Army(f, ($"{f}_i3m", 14), ($"{f}_i3r", 8), ($"{f}_c3m", 6));

        [Test]
        public void ArmorReducesDamageByType()
        {
            var knight = TestData.Troops.Get("aurelia_c4m");
            Assert.That(BattleSim.ArmorFactor(knight, DamageType.Cut), Is.LessThan(BattleSim.ArmorFactor(knight, DamageType.Blunt)));
            var peasant = TestData.Troops.Get("aurelia_i1");
            Assert.That(BattleSim.ArmorFactor(peasant, DamageType.Cut), Is.GreaterThan(BattleSim.ArmorFactor(knight, DamageType.Cut)));
        }

        [Test]
        public void DeploysBothArmiesFacingEachOther()
        {
            var b = TestData.Battle(Mixed("aurelia"), Mixed("nordmark"));
            Assert.That(b.ActiveCount(0), Is.EqualTo(28));
            Assert.That(b.ActiveCount(1), Is.EqualTo(28));
            Assert.That(b.Active(0).All(u => u.Pos.X < 0), Is.True);
            Assert.That(b.Active(1).All(u => u.Pos.X > 0), Is.True);
        }

        [Test]
        public void BattleEndsWithWinner()
        {
            var b = TestData.Battle(Mixed("aurelia"), Mixed("nordmark"), seed: 3);
            b.RunToEnd();
            Assert.That(b.Finished, Is.True);
            Assert.That(b.Time, Is.LessThan(BattleRules.TimeLimit));
        }

        [Test]
        public void VeteransBeatPeasants()
        {
            int wins = 0;
            for (uint seed = 1; seed <= 20; seed++)
            {
                var b = TestData.Battle(Veterans(), Peasants(), seed);
                b.RunToEnd();
                if (b.Winner == 0) wins++;
            }
            Assert.That(wins, Is.GreaterThanOrEqualTo(19));
        }

        [Test]
        public void SameSeedSameOutcome()
        {
            BattleSim Run()
            {
                var b = TestData.Battle(Mixed("aurelia"), Mixed("nordmark"), seed: 11);
                b.RunToEnd();
                return b;
            }
            var a = Run();
            var c = Run();
            Assert.That(c.Winner, Is.EqualTo(a.Winner));
            Assert.That(c.Time, Is.EqualTo(a.Time));
            Assert.That(c.Summary(0).Dead, Is.EqualTo(a.Summary(0).Dead));
            Assert.That(c.Summary(1).Dead, Is.EqualTo(a.Summary(1).Dead));
        }

        [Test]
        public void MoraleFallsWithLossesAndLoserRoutsBeforeAnnihilation()
        {
            var b = TestData.Battle(Veterans(), Peasants(), seed: 5);
            b.RunToEnd();
            Assert.That(b.Winner, Is.EqualTo(0));
            Assert.That(b.Morale[1], Is.EqualTo(0));
            Assert.That(b.Routed[1], Is.True);
            var lost = b.Summary(1);
            Assert.That(lost.Dead, Is.GreaterThan(0));
            Assert.That(lost.Survived, Is.GreaterThan(0), "someone should flee instead of dying");
        }

        [Test]
        public void VeteransHaveMoreResolve()
        {
            var b = TestData.Battle(Veterans(), Peasants());
            Assert.That(b.Resolve[0], Is.GreaterThan(b.Resolve[1]));
        }

        [Test]
        public void FieldCapAndReinforcements()
        {
            var b = TestData.Battle(TestData.Army("aurelia", ("aurelia_i4m", 200)), Peasants(200), seed: 2);
            Assert.That(b.ActiveCount(0), Is.EqualTo(BattleRules.MaxOnField));
            Assert.That(b.Reserves[0].Count, Is.EqualTo(50));
            bool reinforced = false;
            for (int i = 0; i < 30 * 240 && !b.Finished; i++)
            {
                b.Step(1f / 30f);
                Assert.That(b.ActiveCount(1), Is.LessThanOrEqualTo(BattleRules.MaxOnField));
                if (b.Reserves[1].Count < 50) reinforced = true;
            }
            Assert.That(reinforced, Is.True);
        }

        [Test]
        public void HoldInPlaceKeepsGroupStill()
        {
            var b = TestData.Battle(TestData.Army("aurelia", ("aurelia_i3m", 20)), TestData.Army("aurelia", ("aurelia_i3m", 20)));
            b.AiEnabled[1] = false;
            b.SetOrder(0, Group.Infantry, Order.Hold);
            b.SetOrder(1, Group.Infantry, Order.Hold);
            b.TryGroupCenter(0, Group.Infantry, out var before);
            for (int i = 0; i < 300; i++) b.Step(1f / 30f);
            b.TryGroupCenter(0, Group.Infantry, out var after);
            Assert.That(Vec2.Distance(before, after), Is.LessThan(1f));
        }

        [Test]
        public void HoldAtMovesGroupToPoint()
        {
            var b = TestData.Battle(TestData.Army("aurelia", ("aurelia_i3m", 20)), TestData.Army("aurelia", ("aurelia_i3m", 20)));
            b.AiEnabled[1] = false;
            b.SetOrder(1, Group.Infantry, Order.Hold);
            var point = new Vec2(-40f, 30f);
            b.HoldAt(0, new[] { Group.Infantry }, point);
            for (int i = 0; i < 30 * 20; i++) b.Step(1f / 30f);
            b.TryGroupCenter(0, Group.Infantry, out var c);
            Assert.That(Vec2.Distance(c, point), Is.LessThan(4f));
            Assert.That(b.OrderOf(0, Group.Infantry), Is.EqualTo(Order.Hold));
        }

        [Test]
        public void AdvanceShiftsHoldTowardEnemy()
        {
            var b = TestData.Battle(TestData.Army("aurelia", ("aurelia_i3m", 20)), TestData.Army("aurelia", ("aurelia_i3m", 20)));
            b.AiEnabled[1] = false;
            b.SetOrder(1, Group.Infantry, Order.Hold);
            b.SetOrder(0, Group.Infantry, Order.Hold);
            b.TryGroupCenter(0, Group.Infantry, out var before);
            b.Advance(0, Group.Infantry, BattleRules.AdvanceStep);
            for (int i = 0; i < 30 * 10; i++) b.Step(1f / 30f);
            b.TryGroupCenter(0, Group.Infantry, out var after);
            Assert.That(after.X - before.X, Is.EqualTo(BattleRules.AdvanceStep).Within(1.5f));
        }

        [Test]
        public void RetreatLeavesField()
        {
            var b = TestData.Battle(Mixed("aurelia"), Mixed("nordmark"));
            b.AiEnabled[1] = false;
            foreach (var g in BattleRules.AllGroups) b.SetOrder(1, g, Order.Hold);
            b.SetOrder(0, Group.Cavalry, Order.Retreat);
            for (int i = 0; i < 30 * 30; i++) b.Step(1f / 30f);
            Assert.That(b.Units.Where(u => u.Side == 0 && u.Group == Group.Cavalry).All(u => u.State == UnitState.Fled), Is.True);
            Assert.That(b.GroupCount(0, Group.Cavalry), Is.EqualTo(0));
        }

        [Test]
        public void RangedShootAndRunOutOfAmmo()
        {
            var b = TestData.Battle(TestData.Army("nordmark", ("nordmark_i3r", 10)), TestData.Army("aurelia", ("aurelia_i3m", 10)));
            b.AiEnabled[1] = false;
            b.SetOrder(1, Group.Infantry, Order.Hold);
            b.SetOrder(0, Group.Ranged, Order.Attack);
            int shots = 0;
            for (int i = 0; i < 30 * 90 && !b.Finished; i++)
            {
                b.Step(1f / 30f);
                shots += b.Events.Count(e => e.Kind == BattleEventKind.Shoot);
            }
            Assert.That(shots, Is.GreaterThan(20));
            Assert.That(b.Summary(1).Dead, Is.GreaterThan(0));
        }

        [Test]
        public void HeroDeathHurtsMorale()
        {
            var army = Veterans(10);
            var hero = TestData.Troops.Get("aurelia_i1").Clone();
            hero.Hp = 1;
            army.Hero = hero;
            var b = TestData.Battle(army, Veterans(10), seed: 4);
            for (int i = 0; i < 30 * 120 && !b.HeroDown; i++) b.Step(1f / 30f);
            Assert.That(b.HeroDown, Is.True);
        }
    }
}
