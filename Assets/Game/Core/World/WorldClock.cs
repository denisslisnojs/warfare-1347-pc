using System;

namespace Warfare.Core.World
{
    public enum DayPart
    {
        Night,
        Morning,
        Day,
        Evening,
    }

    public sealed class WorldClock
    {
        public const int StartYear = 1347;
        const int StartDayOfYear = 31 + 28;
        static readonly int[] MonthDays = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

        public double Days { get; private set; }
        public float SecondsPerDay = 10f;
        public int Speed = 1;

        public WorldClock(double days = 0)
        {
            Days = days;
        }

        public double Advance(float realSeconds)
        {
            if (realSeconds <= 0f || SecondsPerDay <= 0f) return 0;
            double d = realSeconds / SecondsPerDay * Speed;
            Days += d;
            return d;
        }

        public int Hour => (int)((Days - Math.Floor(Days)) * 24.0);

        public DayPart Part
        {
            get
            {
                int h = Hour;
                if (h < 5) return DayPart.Night;
                if (h < 11) return DayPart.Morning;
                if (h < 17) return DayPart.Day;
                if (h < 21) return DayPart.Evening;
                return DayPart.Night;
            }
        }

        public (int day, int month, int year) Date
        {
            get
            {
                int d = (int)Math.Floor(Days) + StartDayOfYear;
                int year = StartYear;
                while (d >= 365)
                {
                    d -= 365;
                    year++;
                }
                int m = 0;
                while (d >= MonthDays[m])
                {
                    d -= MonthDays[m];
                    m++;
                }
                return (d + 1, m, year);
            }
        }
    }
}
