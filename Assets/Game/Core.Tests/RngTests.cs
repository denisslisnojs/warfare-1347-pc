using NUnit.Framework;

namespace Warfare.Core.Tests
{
    public class RngTests
    {
        [Test]
        public void SameSeedSameSequence()
        {
            var a = new Rng(42);
            var b = new Rng(42);
            for (int i = 0; i < 1000; i++) Assert.That(a.NextUInt(), Is.EqualTo(b.NextUInt()));
        }

        [Test]
        public void DifferentSeedsDiffer()
        {
            var a = new Rng(1);
            var b = new Rng(2);
            int same = 0;
            for (int i = 0; i < 100; i++)
                if (a.NextUInt() == b.NextUInt()) same++;
            Assert.That(same, Is.LessThan(3));
        }

        [Test]
        public void ValuesInRange()
        {
            var r = new Rng(7);
            double sum = 0;
            for (int i = 0; i < 10000; i++)
            {
                double v = r.Next();
                Assert.That(v, Is.GreaterThanOrEqualTo(0).And.LessThan(1));
                sum += v;
            }
            Assert.That(sum / 10000, Is.EqualTo(0.5).Within(0.02));
        }
    }
}
