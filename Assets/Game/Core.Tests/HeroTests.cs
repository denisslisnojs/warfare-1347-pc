using System.Linq;
using NUnit.Framework;
using Warfare.Core.Battle;

namespace Warfare.Core.Tests
{
    public class HeroTests
    {
        const float Dt = 1f / 30f;

        static BattleSim Battle(ArmyDef blue, ArmyDef red, bool deploy = false, uint seed = 1)
        {
            var b = new BattleSim(blue, red, TestData.Troops, new BattleOptions { Seed = seed, Deployment = deploy, ManualHero = true });
            b.AiEnabled[1] = false;
            return b;
        }

        static ArmyDef WithHero(params (string, int)[] stacks)
        {
            var a = TestData.Army("aurelia", stacks);
            var hero = TestData.Troops.Get("aurelia_i3m").Clone();
            hero.Hp *= 3;
            a.Hero = hero;
            return a;
        }

        static void Run(BattleSim b, float seconds)
        {
            for (int i = 0; i < seconds / Dt; i++) b.Step(Dt);
        }

        [Test]
        public void DeploymentFreezesTime()
        {
            var b = Battle(WithHero(("aurelia_i3m", 10)), TestData.Army("nordmark", ("nordmark_i3m", 10)), deploy: true);
            var before = b.Units.Select(u => u.Pos).ToArray();
            Run(b, 3);
            Assert.That(b.Time, Is.EqualTo(0));
            Assert.That(b.Units.Select(u => u.Pos).ToArray(), Is.EqualTo(before));
            b.Begin();
            Run(b, 1);
            Assert.That(b.Time, Is.GreaterThan(0.9f));
        }

        [Test]
        public void PlaceGroupsStaysInsideOwnZone()
        {
            var b = Battle(WithHero(("aurelia_i3m", 20)), TestData.Army("nordmark", ("nordmark_i3m", 10)), deploy: true);
            b.PlaceGroups(0, new[] { Group.Infantry }, new Vec2(-30, 25));
            b.TryGroupCenter(0, Group.Infantry, out var c);
            Assert.That(Vec2.Distance(c, new Vec2(-30, 25)), Is.LessThan(4f));
            b.PlaceGroups(0, new[] { Group.Infantry }, new Vec2(60, 0));
            foreach (var u in b.Units.Where(u => u.Side == 0 && u.Group == Group.Infantry))
                Assert.That(b.InDeployZone(0, u.Pos), Is.True, u.Pos.ToString());
        }

        [Test]
        public void HeroWalksWhereTold()
        {
            var b = Battle(WithHero(("aurelia_i3m", 5)), TestData.Army("nordmark", ("nordmark_i3m", 5)));
            var hero = b.Hero(0);
            var start = hero.Pos;
            b.HeroInput = new HeroInput { Move = new Vec2(0, 1), Aim = new Vec2(1, 0) };
            Run(b, 2);
            Assert.That(hero.Pos.Y - start.Y, Is.GreaterThan(4f));
            Assert.That(System.Math.Abs(hero.Pos.X - start.X), Is.LessThan(1.5f));
        }

        [Test]
        public void HeroStrikesFoeInFront()
        {
            var b = Battle(WithHero(), TestData.Army("nordmark", ("aurelia_i1", 1)));
            var hero = b.Hero(0);
            var foe = b.Units.First(u => u.Side == 1);
            b.SetOrder(1, Group.Infantry, Order.Hold);
            foe.Pos = hero.Pos + new Vec2(1.2f, 0);
            b.HeroInput = new HeroInput { Aim = new Vec2(1, 0), Attack = true };
            Run(b, 6);
            Assert.That(foe.Hp, Is.LessThan(foe.MaxHp));
        }

        [Test]
        public void HeroMissesFoeBehind()
        {
            var b = Battle(WithHero(), TestData.Army("nordmark", ("aurelia_i1", 1)));
            var hero = b.Hero(0);
            var foe = b.Units.First(u => u.Side == 1);
            foe.Troop = foe.Troop.Clone();
            foe.Troop.Damage = 0.01f;
            b.SetOrder(1, Group.Infantry, Order.Hold);
            foe.Pos = hero.Pos + new Vec2(-1.2f, 0);
            b.HeroInput = new HeroInput { Aim = new Vec2(1, 0), Attack = true };
            Run(b, 3);
            Assert.That(foe.Hp, Is.EqualTo(foe.MaxHp));
        }

        [Test]
        public void BlockingReducesDamageTaken()
        {
            float Taken(bool block)
            {
                float total = 0;
                for (uint seed = 1; seed <= 6; seed++)
                {
                    var b = Battle(WithHero(), TestData.Army("outlaw", ("nordmark_i3m", 3)), seed: seed);
                    b.AiEnabled[1] = true;
                    var hero = b.Hero(0);
                    foreach (var e in b.Units.Where(u => u.Side == 1)) e.Pos = hero.Pos + new Vec2(2f, 0);
                    b.HeroInput = new HeroInput { Aim = new Vec2(1, 0), Block = block };
                    Run(b, 8);
                    total += hero.MaxHp - hero.Hp;
                }
                return total;
            }
            Assert.That(Taken(true), Is.LessThan(Taken(false) * 0.5f));
        }

        [Test]
        public void FollowKeepsGroupBehindHero()
        {
            var b = Battle(WithHero(("aurelia_i3m", 12)), TestData.Army("nordmark", ("nordmark_i3m", 5)));
            b.SetOrder(1, Group.Infantry, Order.Hold);
            b.SetOrder(0, Group.Infantry, Order.Follow);
            var hero = b.Hero(0);
            b.HeroInput = new HeroInput { Move = new Vec2(0, 1), Aim = new Vec2(0, 1) };
            Run(b, 6);
            b.HeroInput = default;
            Run(b, 6);
            b.TryGroupCenter(0, Group.Infantry, out var c);
            Assert.That(Vec2.Distance(c, hero.Pos), Is.LessThan(BattleRules.FollowDistance + 5f));
            Assert.That(b.OrderOf(0, Group.Infantry), Is.EqualTo(Order.Follow));
        }

        [Test]
        public void AutoBattleIgnoresManualHero()
        {
            var b = Battle(WithHero(("aurelia_i3m", 10)), TestData.Army("nordmark", ("nordmark_i1", 10)), deploy: true);
            b.RunToEnd();
            Assert.That(b.Finished, Is.True);
            Assert.That(b.Winner, Is.EqualTo(0));
        }
    }
}
