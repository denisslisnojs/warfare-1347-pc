using System.Collections.Generic;

namespace Warfare.Core.Battle
{
    public static class BattleRules
    {
        public const int MaxOnField = 150;
        public const float TimeLimit = 600f;
        public const float StandoffGrace = 30f;

        public const float FieldLength = 240f;
        public const float FieldWidth = 160f;
        public const float FleeMargin = 6f;
        public const float DeployFront = 40f;
        public const float BlockGap = 4f;
        public const float InfantrySpacing = 1.7f;
        public const float CavalrySpacing = 3.0f;
        public const int MaxBlockColumns = 40;

        public const float SpeedK = 3.5f;
        public const float RouteSpeedK = 0.92f;
        public const float RangeK = 0.48f;

        public const float ReachShort = 1.6f;
        public const float ReachPole = 2.3f;
        public const float ReachCavalry = 2.5f;
        public const float BraceExtraReach = 1.1f;
        public const float StrikeSlack = 1.0f;

        public const float SpaceLine = 1.5f;
        public const float SpaceCavalry = 2.6f;
        public const float SpaceEnemy = 1.4f;
        public const float SteerSeparation = 1.8f;
        public const float AnchorTolerance = 0.6f;
        public const float FaceEnemyRadius = 40f;

        public const float ChargeDistance = 11f;
        public const float BusyTargetPenalty = 1.8f;
        public const int MaxMeleeAttackers = 3;
        public const float FullTargetPenalty = 25f;
        public const float WaitBehindGap = 1.4f;
        public const float HeroBehindFront = 1.9f;
        public const float HeroEngageDistance = 5.6f;
        public const float RangedAdvanceGap = 48f;
        public const float AdvanceStep = 10f;
        public const float DeployEdge = 4f;
        public const float DeployFrontLimit = 12f;
        public const float FollowDistance = 5f;
        public const float FollowRefresh = 0.5f;
        public const float HeroWindup = 0.22f;
        public const float HeroBlockSpeed = 0.45f;
        public const float HeroBackSpeed = 0.6f;
        public const float HeroStrafeSpeed = 0.85f;
        public const float HeroSwingSpeed = 0.6f;
        public const float HeroStrikeCone = 0.2f;
        public const float HeroBlockShield = 0.92f;
        public const float HeroBlockParry = 0.7f;
        public const float HeroBlockRanged = 0.2f;

        public const float ArrowSpeed = 41.6f;
        public const float BulletSpeed = 208f;
        public const float ProjectileHitRadius = 2.7f;
        public const float MissSpread = 3.2f;
        public const float MaxArc = 10f;
        public const float ShotHeight = 1.5f;
        public const float HitHeight = 1.1f;

        public const float MoraleLossPerArmy = 118f;
        public const float HeroDeathMorale = 15f;
        public const float KillMoraleGain = 0.5f;
        public const float OutnumberedDrain = 0.6f;
        public const float RearHitMorale = 0.15f;
        public const float GunShake = 0.3f;

        public static readonly HashSet<string> PoleWeapons = new HashSet<string>
        {
            "spear", "pitchfork", "halberd", "glaive", "daneaxe", "pollaxe", "bardiche",
        };

        public static readonly Group[] AllGroups = { Group.Hero, Group.Infantry, Group.Ranged, Group.Cavalry };

        public static Group[] DepthOrder(Formation f) => f switch
        {
            Formation.ArchersFront => new[] { Group.Ranged, Group.Infantry, Group.Hero, Group.Cavalry },
            Formation.CavCharge => new[] { Group.Cavalry, Group.Hero, Group.Infantry, Group.Ranged },
            _ => new[] { Group.Infantry, Group.Hero, Group.Ranged, Group.Cavalry },
        };

        public static Group GroupOf(TroopDef t)
        {
            if (t.IsCavalry) return Group.Cavalry;
            return t.IsRanged ? Group.Ranged : Group.Infantry;
        }

        public static bool IsPole(TroopDef t) => t.Look?.Weapon != null && PoleWeapons.Contains(t.Look.Weapon);

        public static int StartingAmmo(TroopDef t)
        {
            if (!t.IsRanged) return 0;
            if (t.Has(Traits.Firepot)) return t.Tier >= 4 ? 6 : 5;
            if (t.Has(Traits.Gun)) return 12;
            return t.IsCavalry ? 10 : 18;
        }
    }
}
