using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace Warfare.Core
{
    public enum TroopLine { Infantry, Cavalry }

    public enum TroopRole { Melee, Ranged }

    public enum DamageType { Cut, Pierce, Blunt }

    public static class Traits
    {
        public const string Brace = "brace";
        public const string Shieldwall = "shieldwall";
        public const string Javelin = "javelin";
        public const string Twohand = "twohand";
        public const string Skirmish = "skirmish";
        public const string Pavise = "pavise";
        public const string Gun = "gun";
        public const string Berserk = "berserk";
        public const string Feint = "feint";
        public const string Firepot = "firepot";
        public const string Camel = "camel";
        public const string Lasso = "lasso";
    }

    public sealed class ArmorValues
    {
        public float Cut { get; set; }
        public float Pierce { get; set; }
        public float Blunt { get; set; }

        public float this[DamageType type] => type switch
        {
            DamageType.Cut => Cut,
            DamageType.Pierce => Pierce,
            _ => Blunt,
        };
    }

    public sealed class TroopLook
    {
        public string Helmet { get; set; }
        public string Cloth { get; set; }
        public string Armor { get; set; }
        public string Weapon { get; set; }
        public bool Shield { get; set; }
        public string Body { get; set; }
        public bool Tabard { get; set; }
        public bool Camel { get; set; }
    }

    public sealed class TroopDef
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Faction { get; set; }
        public int Tier { get; set; }
        public TroopLine Line { get; set; }
        public TroopRole Role { get; set; }
        public float Hp { get; set; }
        public ArmorValues Armor { get; set; } = new ArmorValues();
        public float Damage { get; set; }
        public DamageType DamageType { get; set; }
        public float AttackTime { get; set; }
        public float Range { get; set; }
        public float Speed { get; set; }
        public float Crit { get; set; }
        public float Dodge { get; set; }
        public float Block { get; set; }
        public int HireCost { get; set; }
        public int UpgradeCost { get; set; }
        public int XpToUpgrade { get; set; }
        public List<string> UpgradesTo { get; set; } = new List<string>();
        public List<string> Traits { get; set; } = new List<string>();
        public TroopLook Look { get; set; } = new TroopLook();
        public string Description { get; set; }

        [JsonIgnore] HashSet<string> traitSet;

        public bool Has(string trait)
        {
            traitSet ??= new HashSet<string>(Traits ?? new List<string>(), StringComparer.Ordinal);
            return traitSet.Contains(trait);
        }

        [JsonIgnore] public bool IsCavalry => Line == TroopLine.Cavalry;
        [JsonIgnore] public bool IsRanged => Role == TroopRole.Ranged;

        public TroopDef Clone()
        {
            var c = (TroopDef)MemberwiseClone();
            c.Armor = new ArmorValues { Cut = Armor.Cut, Pierce = Armor.Pierce, Blunt = Armor.Blunt };
            c.UpgradesTo = new List<string>(UpgradesTo);
            c.Traits = new List<string>(Traits);
            c.traitSet = null;
            return c;
        }
    }
}
