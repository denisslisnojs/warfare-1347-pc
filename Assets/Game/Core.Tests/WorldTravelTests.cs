using System;
using System.Collections.Generic;
using NUnit.Framework;
using Warfare.Core.World;

namespace Warfare.Core.Tests
{
    public class WorldTravelTests
    {
        static void AssertWalkable(WalkGrid grid, IReadOnlyList<Vec2> path)
        {
            for (int i = 1; i < path.Count; i++)
            {
                var a = path[i - 1];
                var b = path[i];
                int steps = Math.Max(1, (int)(Vec2.Distance(a, b) / 0.1f));
                for (int k = 0; k <= steps; k++)
                {
                    var p = a + (b - a) * (k / (float)steps);
                    bool near = grid.Walkable(p) || grid.Walkable(p + new Vec2(0.3f, 0.3f)) || grid.Walkable(p + new Vec2(-0.3f, 0.3f)) || grid.Walkable(p + new Vec2(0.3f, -0.3f)) || grid.Walkable(p + new Vec2(-0.3f, -0.3f));
                    Assert.That(near, Is.True, $"segment {i} passes blocked cell at {p}");
                }
            }
        }

        static float Length(IReadOnlyList<Vec2> path)
        {
            float d = 0;
            for (int i = 1; i < path.Count; i++) d += Vec2.Distance(path[i - 1], path[i]);
            return d;
        }

        [Test]
        public void RiverIsCrossedOnlyByTheBridge()
        {
            var grid = new WalkGrid(40, 20);
            for (int y = 0; y < 20; y++)
            for (int x = 19; x <= 21; x++)
                grid[x, y] = WalkGrid.Blocked;
            var a = new Vec2(17.5f, 16.5f);
            var b = new Vec2(22.5f, 13.5f);
            grid.AddCrossing(a, b, 1f, 0.7f);
            var path = new PathFinder(grid, 0.7f).Find(new Vec2(5, 5), new Vec2(35, 5));
            Assert.That(path, Is.Not.Null);
            Assert.That(path[0], Is.EqualTo(new Vec2(5, 5)));
            Assert.That(path[path.Count - 1], Is.EqualTo(new Vec2(35, 5)));
            int ia = path.IndexOf(a), ib = path.IndexOf(b);
            Assert.That(ia, Is.GreaterThan(0));
            Assert.That(ib, Is.EqualTo(ia + 1));
            AssertWalkable(grid, path.GetRange(0, ia + 1));
            AssertWalkable(grid, path.GetRange(ib, path.Count - ib));
            var back = new PathFinder(grid, 0.7f).Find(new Vec2(35, 5), new Vec2(5, 5));
            Assert.That(back.IndexOf(a), Is.EqualTo(back.IndexOf(b) + 1));
        }

        [Test]
        public void DiagonalRiverCannotBeSlippedThrough()
        {
            var grid = new WalkGrid(20, 20);
            for (int i = 0; i < 20; i++) grid[i, i] = WalkGrid.Blocked;
            Assert.That(grid.Region(2, 10), Is.Not.EqualTo(grid.Region(10, 2)));
            Assert.That(new PathFinder(grid, 1f).Find(new Vec2(2, 10), new Vec2(10, 2)), Is.Null);
        }

        [Test]
        public void ClickOnWaterSnapsToTheNearestReachableShore()
        {
            var grid = new WalkGrid(30, 10);
            for (int y = 0; y < 10; y++)
            for (int x = 15; x < 30; x++)
                grid[x, y] = WalkGrid.Blocked;
            int home = grid.Region(2, 2);
            Assert.That(grid.Nearest(new Vec2(19, 4), home, 20, out var shore), Is.True);
            Assert.That(shore, Is.EqualTo(new Vec2(14, 4)));
            Assert.That(grid.Nearest(new Vec2(29, 4), home, 5, out _), Is.False);
        }

        [Test]
        public void RoadIsTakenWhenItIsFaster()
        {
            var grid = new WalkGrid(60, 30);
            for (int x = 0; x < 60; x++) grid[x, 25] = 0.5f;
            var path = new PathFinder(grid, 0.5f).Find(new Vec2(5, 20), new Vec2(55, 20));
            Assert.That(path, Is.Not.Null);
            AssertWalkable(grid, path);
            Assert.That(path.Exists(p => p.Y >= 24.5f), Is.True);
        }

        [Test]
        public void OpenFieldPathIsNearlyStraight()
        {
            var grid = new WalkGrid(100, 100);
            var from = new Vec2(10, 10);
            var to = new Vec2(90, 40);
            var path = new PathFinder(grid, 1f).Find(from, to);
            Assert.That(path, Is.Not.Null);
            Assert.That(path.Count, Is.LessThanOrEqualTo(4));
            Assert.That(Length(path), Is.LessThan(Vec2.Distance(from, to) * 1.03f));
        }

        [Test]
        public void PartyMovesAtItsSpeedAndSlowsOnRoughGround()
        {
            var grid = new WalkGrid(200, 10);
            for (int x = 100; x < 200; x++) grid[x, 5] = 2f;
            var party = new MapParty(new Vec2(10, 5), 10f);
            party.SetPath(new[] { new Vec2(10, 5), new Vec2(60, 5) });
            party.Advance(1.0, grid);
            Assert.That(party.Position.X, Is.EqualTo(20f).Within(1e-3f));
            var slow = new MapParty(new Vec2(110, 5), 10f);
            slow.SetPath(new[] { new Vec2(190, 5) });
            slow.Advance(1.0, grid);
            Assert.That(slow.Position.X, Is.EqualTo(115f).Within(1e-3f));
        }

        [Test]
        public void PartyStopsAtTheEndOfThePath()
        {
            var grid = new WalkGrid(50, 50);
            var party = new MapParty(new Vec2(0, 0), 10f);
            party.SetPath(new[] { new Vec2(0, 0), new Vec2(6, 0), new Vec2(6, 8) });
            Assert.That(party.RemainingDistance(), Is.EqualTo(14f).Within(1e-4f));
            party.Advance(5.0, grid);
            Assert.That(party.Moving, Is.False);
            Assert.That(party.Position, Is.EqualTo(new Vec2(6, 8)));
            Assert.That(party.Heading.Y, Is.EqualTo(1f).Within(1e-4f));
        }

        [Test]
        public void TimeFlowsOnlyOnTheRoadOrWhileWaiting()
        {
            var rules = new TravelRules { SecondsPerDay = 10f, Speeds = new[] { 1, 2, 4 }, PartySpeed = 10f, StartHour = 0f };
            var travel = new WorldTravel(new WalkGrid(100, 10), rules, new Vec2(5, 5));
            travel.Tick(10f);
            Assert.That(travel.Clock.Days, Is.EqualTo(0));
            travel.ToggleWait();
            travel.Tick(10f);
            Assert.That(travel.Clock.Days, Is.EqualTo(1).Within(1e-9));
            travel.ChangeSpeed(+5);
            Assert.That(travel.Clock.Speed, Is.EqualTo(4));
            travel.Order(new[] { new Vec2(95, 5) });
            Assert.That(travel.Waiting, Is.False);
            travel.Tick(5f);
            Assert.That(travel.Clock.Days, Is.EqualTo(3).Within(1e-9));
            Assert.That(travel.Party.Position.X, Is.EqualTo(25f).Within(1e-3f));
            travel.ChangeSpeed(-1);
            Assert.That(travel.Clock.Speed, Is.EqualTo(2));
        }

        [Test]
        public void CalendarStartsOnTheFirstOfMarch1347()
        {
            var clock = new WorldClock(8.0 / 24.0);
            Assert.That(clock.Date, Is.EqualTo((1, 2, 1347)));
            Assert.That(clock.Hour, Is.EqualTo(8));
            Assert.That(clock.Part, Is.EqualTo(DayPart.Morning));
            Assert.That(new WorldClock(31).Date, Is.EqualTo((1, 3, 1347)));
            Assert.That(new WorldClock(306).Date, Is.EqualTo((1, 0, 1348)));
            Assert.That(new WorldClock(0.9).Part, Is.EqualTo(DayPart.Night));
        }
    }
}
