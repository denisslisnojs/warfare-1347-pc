using NUnit.Framework;
using Warfare.Core.Battle;

namespace Warfare.Core.Tests
{
    [Explicit("Prints balance numbers to compare with the mobile dev/simtest.ts")]
    public class BalanceReport
    {
        static ArmyDef Army(float morale, params (string, int)[] stacks)
        {
            var a = TestData.Army("x", stacks);
            a.Morale = morale;
            return a;
        }

        static void Run(string name, ArmyDef a, ArmyDef b, int n = 20)
        {
            int w0 = 0, dead0 = 0, dead1 = 0;
            float time = 0;
            for (uint i = 1; i <= n; i++)
            {
                var bt = TestData.Battle(a, b, i);
                bt.RunToEnd();
                if (bt.Winner == 0) w0++;
                time += bt.Time;
                dead0 += bt.Summary(0).Dead;
                dead1 += bt.Summary(1).Dead;
            }
            TestContext.Progress.WriteLine($"{name,-42} win0 {w0 * 100 / n}% time {time / n:0}s dead {dead0 / (float)n:0.0} / {dead1 / (float)n:0.0}");
        }

        [Test]
        public void Print()
        {
            Run("10 peasants+3 landwehr vs 8 bandits", Army(100, ("aurelia_i1", 10), ("aurelia_i2", 3)), Army(75, ("outlaw_bandit", 8)));
            Run("10 peasants vs 10 bandits", Army(100, ("aurelia_i1", 10)), Army(75, ("outlaw_bandit", 10)));
            Run("10 imperial inf vs 10 hirdman", Army(100, ("aurelia_i3m", 10)), Army(100, ("nordmark_i3m", 10)));
            Run("10 knights vs 20 spearmen(sult i3m)", Army(100, ("aurelia_c4m", 10)), Army(100, ("sultanate_i3m", 20)));
            Run("15 horse archers vs 15 infantry t3", Army(100, ("horde_c3r", 15)), Army(100, ("aurelia_i3m", 15)));
            Run("30 mixed vs 30 mixed", Army(100, ("aurelia_i3m", 12), ("aurelia_i3r", 10), ("aurelia_c3m", 8)), Army(100, ("horde_i3m", 10), ("horde_i3r", 10), ("horde_c3r", 10)));
            Run("60 peasants vs 20 t3", Army(100, ("aurelia_i1", 60)), Army(100, ("nordmark_i3m", 20)));
            Run("mirror 28 vs 28", Army(100, ("aurelia_i3m", 14), ("aurelia_i3r", 8), ("aurelia_c3m", 6)), Army(100, ("aurelia_i3m", 14), ("aurelia_i3r", 8), ("aurelia_c3m", 6)));
            Run("150 vs 150 mixed", Army(100, ("aurelia_i3m", 80), ("aurelia_i3r", 40), ("aurelia_c3m", 30)), Army(100, ("nordmark_i3m", 80), ("nordmark_i3r", 40), ("nordmark_c3m", 30)), 5);
        }
    }
}
