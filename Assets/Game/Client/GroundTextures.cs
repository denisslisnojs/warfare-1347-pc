using System.Collections.Generic;
using UnityEngine;

namespace Warfare.Client
{
    public static class GroundTextures
    {
        const int Size = 256;
        static readonly Dictionary<string, Texture2D> cache = new Dictionary<string, Texture2D>();

        public static float TileMeters(string kind) => kind switch
        {
            "wheat" => 5f,
            "barley" => 5f,
            "flax" => 5f,
            "plowed" => 6f,
            "road" => 6f,
            _ => 9f,
        };

        public static Texture2D Get(string kind, Color baseColor)
        {
            string key = kind + ColorUtility.ToHtmlStringRGB(baseColor);
            if (cache.TryGetValue(key, out var t) && t != null) return t;
            t = new Texture2D(Size, Size, TextureFormat.RGBA32, true)
            {
                name = "ground_" + key,
                wrapMode = TextureWrapMode.Repeat,
                filterMode = FilterMode.Trilinear,
                anisoLevel = 8,
            };
            var px = new Color[Size * Size];
            int seed = (key.GetHashCode() & 0x3ff) + 1;
            for (int y = 0; y < Size; y++)
            for (int x = 0; x < Size; x++)
            {
                float u = (float)x / Size, v = (float)y / Size;
                var c = baseColor * Shade(kind, u, v, seed);
                float f = Hash(x, y, seed);
                if (kind == "meadow" || kind == "grass")
                {
                    if (f > 0.9975f) c = Color.Lerp(c, new Color(0.95f, 0.9f, 0.55f), 0.7f);
                    else if (f > 0.9955f) c = Color.Lerp(c, new Color(0.92f, 0.92f, 0.96f), 0.6f);
                }
                else if (kind == "road" && f > 0.992f) c = Color.Lerp(c, new Color(0.62f, 0.6f, 0.56f), 0.8f);
                c.a = 1f;
                px[y * Size + x] = c;
            }
            t.SetPixels(px);
            t.Apply(true, true);
            cache[key] = t;
            return t;
        }

        static float Shade(string kind, float u, float v, int seed)
        {
            float n = Fbm(u, v, 4, seed) - 0.5f;
            float fine = Fbm(u, v, 32, seed + 3) - 0.5f;
            switch (kind)
            {
                case "wheat":
                case "barley":
                case "flax":
                    return 0.86f + (Mathf.Sin(u * Mathf.PI * 2f * 22f) * 0.5f + 0.5f) * 0.16f + n * 0.22f + fine * 0.18f;
                case "plowed":
                    return 0.88f + Mathf.Sin(u * Mathf.PI * 2f * 14f + n * 2f) * 0.14f + n * 0.25f + fine * 0.22f;
                case "road":
                    return 0.92f - (1f - Mathf.Abs(Mathf.Sin(u * Mathf.PI * 2f))) * 0.08f + n * 0.2f + fine * 0.25f;
                default:
                    return 0.95f + n * 0.3f + (Fbm(u, v, 2, seed + 11) - 0.5f) * 0.25f + fine * 0.16f;
            }
        }

        static float Fbm(float u, float v, int baseFreq, int seed)
        {
            float sum = 0, amp = 0.5f, norm = 0;
            for (int i = 0; i < 4; i++)
            {
                int f = baseFreq << i;
                sum += amp * Tileable(u * f, v * f, f, seed + i * 17);
                norm += amp;
                amp *= 0.5f;
            }
            return sum / norm;
        }

        static float Tileable(float x, float y, int period, int seed)
        {
            float ox = seed * 0.37f, oy = seed * 0.71f;
            float u = x / period, v = y / period;
            float a = Mathf.PerlinNoise(x + ox, y + oy);
            float b = Mathf.PerlinNoise(x - period + ox, y + oy);
            float c = Mathf.PerlinNoise(x + ox, y - period + oy);
            float d = Mathf.PerlinNoise(x - period + ox, y - period + oy);
            return Mathf.Lerp(Mathf.Lerp(a, b, u), Mathf.Lerp(c, d, u), v);
        }

        static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)(x * 374761393 + y * 668265263 + seed * 362437);
                h = (h ^ (h >> 13)) * 1274126177u;
                return ((h ^ (h >> 16)) & 0xffffff) / 16777216f;
            }
        }
    }
}
