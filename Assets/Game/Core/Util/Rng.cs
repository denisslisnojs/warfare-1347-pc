namespace Warfare.Core
{
    public sealed class Rng
    {
        uint state;

        public Rng(uint seed)
        {
            state = seed;
        }

        public uint NextUInt()
        {
            unchecked
            {
                state += 0x6D2B79F5u;
                uint t = (state ^ (state >> 15)) * (state | 1u);
                t = (t + (t ^ (t >> 7)) * (t | 61u)) ^ t;
                return t ^ (t >> 14);
            }
        }

        public double Next() => NextUInt() / 4294967296.0;

        public float Value => (float)Next();

        public float Range(float min, float max) => min + (float)Next() * (max - min);

        public int Int(int maxExclusive) => (int)(Next() * maxExclusive);

        public bool Chance(double p) => Next() < p;
    }
}
