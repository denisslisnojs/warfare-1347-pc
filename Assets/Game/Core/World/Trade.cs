using System;
using System.Collections.Generic;

namespace Warfare.Core.World
{
    public sealed class Good
    {
        public string Id;
        public string Name;
        public int Price;
    }

    public sealed class Stock
    {
        readonly Dictionary<string, int> counts = new Dictionary<string, int>();

        public IEnumerable<string> Ids => counts.Keys;

        public int Count(string id) => id != null && counts.TryGetValue(id, out var n) ? n : 0;

        public Stock Clone()
        {
            var copy = new Stock();
            copy.CopyFrom(this);
            return copy;
        }

        public void CopyFrom(Stock other)
        {
            counts.Clear();
            foreach (var kv in other.counts) counts[kv.Key] = kv.Value;
        }

        public void Add(string id, int n)
        {
            int left = Count(id) + n;
            if (left < 0) throw new InvalidOperationException($"not enough {id}: {Count(id)} + {n}");
            if (left == 0) counts.Remove(id);
            else counts[id] = left;
        }
    }

    public static class Trade
    {
        public const float SellRatio = 0.8f;

        public static int BuyPrice(Good g) => Math.Max(1, g.Price);

        public static int SellPrice(Good g) => Math.Max(1, (int)Math.Round(g.Price * SellRatio));

        public static int Buy(Good g, Stock market, Stock party, ref int gold, int want)
        {
            int price = BuyPrice(g);
            int n = Math.Min(Math.Min(want, market.Count(g.Id)), gold / price);
            if (n <= 0) return 0;
            market.Add(g.Id, -n);
            party.Add(g.Id, n);
            gold -= n * price;
            return n;
        }

        public static int Sell(Good g, Stock market, Stock party, ref int gold, int want)
        {
            int n = Math.Min(want, party.Count(g.Id));
            if (n <= 0) return 0;
            party.Add(g.Id, -n);
            market.Add(g.Id, n);
            gold += n * SellPrice(g);
            return n;
        }
    }
}
