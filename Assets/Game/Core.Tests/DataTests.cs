using System.Linq;
using NUnit.Framework;

namespace Warfare.Core.Tests
{
    public class DataTests
    {
        [Test]
        public void TroopsLoad()
        {
            Assert.That(TestData.Troops.All.Count, Is.EqualTo(70));
        }

        [Test]
        public void EveryTroopHasNameAndStats()
        {
            foreach (var t in TestData.Troops.All)
            {
                Assert.That(t.Name, Is.Not.Empty, t.Id);
                Assert.That(t.Hp, Is.GreaterThan(0), t.Id);
                Assert.That(t.Damage, Is.GreaterThan(0), t.Id);
                Assert.That(t.AttackTime, Is.GreaterThan(0), t.Id);
                Assert.That(t.Speed, Is.GreaterThan(0), t.Id);
                Assert.That(t.Tier, Is.InRange(1, 4), t.Id);
            }
        }

        [Test]
        public void UpgradesPointToKnownTroops()
        {
            foreach (var t in TestData.Troops.All)
                foreach (var next in t.UpgradesTo)
                    Assert.That(TestData.Troops.TryGet(next, out _), Is.True, $"{t.Id} -> {next}");
        }

        [Test]
        public void EnumsAndTraitsParsed()
        {
            var knight = TestData.Troops.Get("aurelia_c4m");
            Assert.That(knight.Line, Is.EqualTo(TroopLine.Cavalry));
            Assert.That(knight.Role, Is.EqualTo(TroopRole.Melee));
            Assert.That(knight.Look.Weapon, Is.EqualTo("lance"));

            var spearman = TestData.Troops.Get("aurelia_i2");
            Assert.That(spearman.Has(Traits.Brace), Is.True);
            Assert.That(TestData.Troops.All.Any(t => t.Has(Traits.Gun)), Is.True);
        }

        [Test]
        public void UnknownTroopThrows()
        {
            Assert.Throws<System.Collections.Generic.KeyNotFoundException>(() => TestData.Troops.Get("nope"));
        }
    }
}
