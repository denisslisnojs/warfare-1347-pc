using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Warfare.Client
{
    public sealed class HeroPreview : MonoBehaviour
    {
        const int Layer = 31;
        const float FrontYaw = 15f;
        static readonly Vector3 Stage = new Vector3(60000f, 1500f, 60000f);

        public RenderTexture Texture { get; private set; }
        Camera cam;
        Transform turntable;
        GameObject current;
        float yaw = FrontYaw;

        public static HeroPreview Create()
        {
            var p = new GameObject("HeroPreview").AddComponent<HeroPreview>();
            p.Setup();
            return p;
        }

        static void SetLayer(Transform t)
        {
            t.gameObject.layer = Layer;
            for (int i = 0; i < t.childCount; i++) SetLayer(t.GetChild(i));
        }

        void Setup()
        {
            transform.position = Stage;
            turntable = new GameObject("Turntable").transform;
            turntable.SetParent(transform, false);
            Texture = new RenderTexture(640, 900, 24, RenderTextureFormat.ARGB32) { name = "HeroPreview", antiAliasing = 4 };
            cam = new GameObject("HeroPreviewCam").AddComponent<Camera>();
            cam.transform.SetParent(transform, false);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0f, 0f, 0f, 0f);
            cam.cullingMask = 1 << Layer;
            cam.fieldOfView = 24f;
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 1000f;
            cam.targetTexture = Texture;
            var data = cam.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = false;
            data.renderShadows = false;
            if (Camera.main != null) Camera.main.cullingMask &= ~(1 << Layer);
            Show(false);
        }

        public void SetFigure(GameObject figure)
        {
            if (current != null) Destroy(current);
            current = figure;
            yaw = FrontYaw;
            if (figure == null) return;
            turntable.localRotation = Quaternion.identity;
            figure.transform.SetParent(turntable, false);
            figure.transform.localPosition = Vector3.zero;
            figure.transform.localRotation = Quaternion.LookRotation(Vector3.back) * Quaternion.Euler(0f, 90f, 0f);
            SetLayer(figure.transform);
            var banner = figure.transform.Find("Banner");
            if (banner != null) banner.gameObject.SetActive(false);
            var renderers = figure.GetComponentsInChildren<Renderer>();
            var bounds = renderers.Length > 0 ? renderers[0].bounds : new Bounds(Stage, Vector3.one);
            foreach (var r in renderers)
            {
                bounds.Encapsulate(r.bounds);
                r.shadowCastingMode = ShadowCastingMode.Off;
            }
            figure.transform.position += new Vector3(Stage.x - bounds.center.x, Stage.y - bounds.min.y, Stage.z - bounds.center.z);
            float h = Mathf.Max(bounds.size.y, 0.01f);
            float w = Mathf.Sqrt(bounds.size.x * bounds.size.x + bounds.size.z * bounds.size.z);
            float tanV = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
            float d = Mathf.Max(h * 0.58f / tanV, w * 0.55f / (tanV * Texture.width / Texture.height));
            var target = Stage + Vector3.up * (h * 0.48f);
            cam.transform.position = target + Quaternion.Euler(6f, 0f, 0f) * (Vector3.back * d);
            cam.transform.LookAt(target);
        }

        public void Show(bool on)
        {
            if (cam != null) cam.enabled = on;
            if (!on) yaw = FrontYaw;
        }

        public void Spin(float dx) => yaw -= dx * 0.5f;

        void Update()
        {
            if (turntable != null) turntable.localRotation = Quaternion.Euler(0f, yaw, 0f);
        }
    }
}
