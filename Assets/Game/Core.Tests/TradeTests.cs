using NUnit.Framework;
using Warfare.Core.World;

namespace Warfare.Core.Tests
{
    public class TradeTests
    {
        static readonly Good Grain = new Good { Id = "grain", Name = "Зерно", Price = 20 };

        static Stock With(string id, int n)
        {
            var s = new Stock();
            s.Add(id, n);
            return s;
        }

        [Test]
        public void BuyingMovesGoodsAndPaysFullPrice()
        {
            var market = With("grain", 10);
            var party = new Stock();
            int gold = 100;
            int got = Trade.Buy(Grain, market, party, ref gold, 3);
            Assert.That(got, Is.EqualTo(3));
            Assert.That(gold, Is.EqualTo(40));
            Assert.That(market.Count("grain"), Is.EqualTo(7));
            Assert.That(party.Count("grain"), Is.EqualTo(3));
        }

        [Test]
        public void BuyingStopsWhenGoldRunsOut()
        {
            var market = With("grain", 10);
            var party = new Stock();
            int gold = 50;
            Assert.That(Trade.Buy(Grain, market, party, ref gold, 5), Is.EqualTo(2));
            Assert.That(gold, Is.EqualTo(10));
        }

        [Test]
        public void BuyingStopsWhenStockRunsOut()
        {
            var market = With("grain", 2);
            var party = new Stock();
            int gold = 1000;
            Assert.That(Trade.Buy(Grain, market, party, ref gold, 5), Is.EqualTo(2));
            Assert.That(market.Count("grain"), Is.EqualTo(0));
            Assert.That(market.Ids, Is.Empty);
        }

        [Test]
        public void SellingPaysEightyPercent()
        {
            var market = new Stock();
            var party = With("grain", 4);
            int gold = 0;
            Assert.That(Trade.SellPrice(Grain), Is.EqualTo(16));
            Assert.That(Trade.Sell(Grain, market, party, ref gold, 2), Is.EqualTo(2));
            Assert.That(gold, Is.EqualTo(32));
            Assert.That(market.Count("grain"), Is.EqualTo(2));
            Assert.That(party.Count("grain"), Is.EqualTo(2));
        }

        [Test]
        public void ResetRestoresStockFromCopy()
        {
            var party = With("grain", 3);
            var saved = party.Clone();
            party.Add("grain", 5);
            party.Add("salt", 2);
            Assert.That(saved.Count("grain"), Is.EqualTo(3));
            party.CopyFrom(saved);
            Assert.That(party.Count("grain"), Is.EqualTo(3));
            Assert.That(party.Count("salt"), Is.EqualTo(0));
        }

        [Test]
        public void CannotSellMoreThanOwned()
        {
            var market = new Stock();
            var party = With("grain", 1);
            int gold = 0;
            Assert.That(Trade.Sell(Grain, market, party, ref gold, 10), Is.EqualTo(1));
            Assert.That(gold, Is.EqualTo(16));
            Assert.That(party.Count("grain"), Is.EqualTo(0));
        }
    }
}
