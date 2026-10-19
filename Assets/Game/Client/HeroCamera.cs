using UnityEngine;
using UnityEngine.InputSystem;

namespace Warfare.Client
{
    public sealed class HeroCamera : MonoBehaviour
    {
        public Transform Target;
        public float Yaw = 0f;
        public float Distance = 26f;
        public float MinDistance = 14f;
        public float MaxDistance = 45f;
        public float NearPitch = 50f;
        public float FarPitch = 58f;
        public float RotateSpeed = 90f;
        public float FocusHeight = 1f;
        public float Follow = 10f;

        float distanceTarget;
        float yawTarget;
        Vector3 focus;

        void OnEnable()
        {
            distanceTarget = Distance;
            yawTarget = Yaw;
            if (Target != null) focus = Target.position;
        }

        public void Snap(float yaw)
        {
            Yaw = yawTarget = yaw;
            if (Target != null) focus = Target.position;
        }

        public Vector2 FlatForward => new Vector2(Mathf.Sin(Yaw * Mathf.Deg2Rad), Mathf.Cos(Yaw * Mathf.Deg2Rad));

        void LateUpdate()
        {
            if (Target == null) return;
            float dt = Time.unscaledDeltaTime;
            var kb = Keyboard.current;
            var mouse = Mouse.current;
            if (kb != null)
            {
                if (kb.qKey.isPressed) yawTarget -= RotateSpeed * dt;
                if (kb.eKey.isPressed) yawTarget += RotateSpeed * dt;
            }
            if (mouse != null)
            {
                float scroll = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(scroll) > 0.01f)
                {
                    float notches = Mathf.Abs(scroll) >= 60f ? scroll / 120f : Mathf.Sign(scroll);
                    distanceTarget = Mathf.Clamp(distanceTarget * Mathf.Pow(0.88f, notches), MinDistance, MaxDistance);
                }
            }
            float k = 1f - Mathf.Exp(-12f * dt);
            Distance = Mathf.Lerp(Distance, distanceTarget, k);
            Yaw = Mathf.LerpAngle(Yaw, yawTarget, k);
            focus = Vector3.Lerp(focus, Target.position, 1f - Mathf.Exp(-Follow * dt));
            float pitch = Mathf.Lerp(NearPitch, FarPitch, Mathf.InverseLerp(MinDistance, MaxDistance, Distance));
            var rot = Quaternion.Euler(pitch, Yaw, 0f);
            transform.SetPositionAndRotation(focus + Vector3.up * FocusHeight - rot * Vector3.forward * Distance, rot);
        }
    }
}
