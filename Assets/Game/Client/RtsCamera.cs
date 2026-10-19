using System;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Warfare.Client
{
    public sealed class RtsCamera : MonoBehaviour
    {
        public Vector3 Focus = new Vector3(-30f, 0f, 0f);
        public float Yaw = 90f;
        public float Distance = 60f;
        public float MinDistance = 8f;
        public float MaxDistance = 160f;
        public float MinPitch = 32f;
        public float MaxPitch = 72f;
        public float PanSpeed = 1.1f;
        public float RotateSpeed = 100f;
        public float ZoomStep = 0.12f;
        public Vector2 Bounds = new Vector2(150f, 110f);
        public Func<float, float, float> Ground;

        Vector3 focusTarget;
        float yawTarget;
        float distanceTarget;
        bool showcase;
        float showPitch, showShift, spin, blend, lift;
        Vector3 keepFocus;
        float keepYaw, keepDistance;

        public bool Showcasing => showcase;

        void Start()
        {
            focusTarget = Focus;
            yawTarget = Yaw;
            distanceTarget = Distance;
            Apply();
        }

        public float ManualAt { get; private set; } = -1f;

        public void Track(Vector3 point)
        {
            if (!showcase) focusTarget = point;
        }

        public void Showcase(Vector3 point, float distance, float pitch, float shift, float spinSpeed)
        {
            if (!showcase)
            {
                keepFocus = focusTarget;
                keepYaw = yawTarget;
                keepDistance = distanceTarget;
            }
            showcase = true;
            focusTarget = point;
            distanceTarget = distance;
            showPitch = pitch;
            showShift = shift;
            spin = spinSpeed;
        }

        public void EndShowcase()
        {
            if (!showcase) return;
            showcase = false;
            focusTarget = keepFocus;
            yawTarget = keepYaw;
            distanceTarget = keepDistance;
        }

        public void LookAt(Vector3 point, float yaw, float distance)
        {
            ManualAt = Time.unscaledTime;
            focusTarget = Focus = new Vector3(point.x, 0f, point.z);
            yawTarget = Yaw = yaw;
            distanceTarget = Distance = Mathf.Clamp(distance, MinDistance, MaxDistance);
        }

        void Update()
        {
            var kb = Keyboard.current;
            var mouse = Mouse.current;
            float dt = Time.unscaledDeltaTime;

            if (showcase) yawTarget += spin * dt;
            if (kb != null && !showcase)
            {
                Vector2 move = Vector2.zero;
                if (kb.wKey.isPressed || kb.upArrowKey.isPressed) move.y += 1;
                if (kb.sKey.isPressed || kb.downArrowKey.isPressed) move.y -= 1;
                if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) move.x += 1;
                if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) move.x -= 1;
                float boost = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed ? 2.5f : 1f;
                if (move != Vector2.zero)
                {
                    var rot = Quaternion.Euler(0f, yawTarget, 0f);
                    var delta = rot * new Vector3(move.x, 0f, move.y).normalized * (distanceTarget * PanSpeed * boost * dt);
                    focusTarget += delta;
                    ManualAt = Time.unscaledTime;
                }
                if (kb.qKey.isPressed) yawTarget -= RotateSpeed * dt;
                if (kb.eKey.isPressed) yawTarget += RotateSpeed * dt;
            }

            if (mouse != null && !showcase)
            {
                float scroll = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(scroll) > 0.01f)
                {
                    float notches = scroll / 120f;
                    if (Mathf.Abs(notches) < 0.5f) notches = Mathf.Sign(scroll);
                    distanceTarget *= Mathf.Pow(1f - ZoomStep, notches);
                }
                if (mouse.middleButton.isPressed) yawTarget += mouse.delta.ReadValue().x * 0.25f;
            }

            distanceTarget = Mathf.Clamp(distanceTarget, showcase ? 1f : MinDistance, MaxDistance);
            focusTarget.x = Mathf.Clamp(focusTarget.x, -Bounds.x, Bounds.x);
            focusTarget.z = Mathf.Clamp(focusTarget.z, -Bounds.y, Bounds.y);

            blend = Mathf.MoveTowards(blend, showcase ? 1f : 0f, dt * 0.8f);
            bool flying = blend > 0f && blend < 1f;
            float k = 1f - Mathf.Exp(-(flying ? 3.5f : 12f) * dt);
            Focus = Vector3.Lerp(Focus, focusTarget, k);
            Yaw = Mathf.LerpAngle(Yaw, yawTarget, k);
            Distance = Mathf.Lerp(Distance, distanceTarget, k);
            Apply(dt);
        }

        void Apply(float dt = 0f)
        {
            float t = Mathf.InverseLerp(MinDistance, MaxDistance, Distance);
            float b = Mathf.SmoothStep(0f, 1f, blend);
            float pitch = Mathf.Lerp(Mathf.Lerp(MinPitch, MaxPitch, Mathf.Sqrt(t)), showPitch, b);
            if (b > 0f && Ground != null)
            {
                float need = Mathf.Max(ClearPitch(pitch, Yaw, b), ClearPitch(pitch, Yaw + spin * 4f, b)) - pitch;
                lift = need > lift ? Mathf.Lerp(lift, need, 1f - Mathf.Exp(-10f * dt)) : Mathf.Lerp(lift, need, 1f - Mathf.Exp(-1.5f * dt));
                if (dt <= 0f) lift = need;
                pitch += lift;
            }
            else lift = 0f;
            transform.SetPositionAndRotation(Place(pitch, Yaw, b, out var rot), rot);
        }

        Vector3 Place(float pitch, float yaw, float b, out Quaternion rot)
        {
            rot = Quaternion.Euler(pitch, yaw, 0f);
            return Focus - rot * Vector3.forward * Distance + rot * Vector3.left * (showShift * b);
        }

        float ClearPitch(float pitch, float yaw, float b)
        {
            float margin = 2f + Distance * 0.06f;
            for (float p = pitch; p < 80f; p += 2f)
            {
                var cam = Place(p, yaw, b, out _);
                bool clear = true;
                for (float s = 0.2f; s <= 1.001f && clear; s += 0.05f)
                {
                    var q = Vector3.Lerp(Focus, cam, s);
                    if (Ground(q.x, q.z) + margin * s > q.y) clear = false;
                }
                if (clear) return p;
            }
            return 80f;
        }
    }
}
