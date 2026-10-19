using System;
using UnityEngine;

namespace Warfare.Client
{
    public sealed class UnitArt : ScriptableObject
    {
        [Serializable]
        public sealed class Clip
        {
            public string State;
            public float Length;
            public float SideSpeed;
            public float ForwardSpeed;
        }

        public GameObject Infantry;
        public GameObject Sword;
        public GameObject Shield;
        public GameObject Spear;
        public RuntimeAnimatorController Controller;
        public Clip[] Idle = Array.Empty<Clip>();
        public Clip[] Walk = Array.Empty<Clip>();
        public Clip[] Run = Array.Empty<Clip>();
        public Clip[] Attack = Array.Empty<Clip>();
        public Clip[] Impact = Array.Empty<Clip>();
        public Clip[] Death = Array.Empty<Clip>();
        public Clip[] Block = Array.Empty<Clip>();
        public Clip[] BlockIdle = Array.Empty<Clip>();
        public Clip[] Strafe = Array.Empty<Clip>();
        public float StrafeSpeed = 1.6f;
        public float WalkSpeed = 1.3f;
        public float RunSpeed = 3.2f;

        public bool Ready => Infantry != null && Controller != null && Idle.Length > 0;

        public static UnitArt Load() => Resources.Load<UnitArt>("UnitArt");
    }
}
