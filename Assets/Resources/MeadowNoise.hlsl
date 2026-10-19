#ifndef W1347_MEADOW_NOISE
#define W1347_MEADOW_NOISE

float MeadowHash(float2 p)
{
    p = frac(p * float2(0.1031, 0.1030));
    p += dot(p, p.yx + 33.33);
    return frac((p.x + p.y) * p.x);
}

float MeadowValue(float2 p)
{
    float2 i = floor(p);
    float2 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = MeadowHash(i);
    float b = MeadowHash(i + float2(1, 0));
    float c = MeadowHash(i + float2(0, 1));
    float d = MeadowHash(i + float2(1, 1));
    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}

float MeadowFbm(float2 p)
{
    return MeadowValue(p) * 0.55 + MeadowValue(p * 2.13 + 17.1) * 0.3 + MeadowValue(p * 4.7 + 41.3) * 0.15;
}

float3 MeadowTint(float3 albedo, float2 xz, float strength)
{
    float dry = smoothstep(0.5, 0.78, MeadowFbm(xz * 0.045));
    float lush = smoothstep(0.55, 0.85, MeadowFbm(xz * 0.07 + 91.7));
    float bare = smoothstep(0.8, 0.9, MeadowFbm(xz * 0.11 + 213.4));
    float3 c = albedo;
    c = lerp(c, c * float3(1.18, 1.08, 0.72), dry * 0.55 * strength);
    c = lerp(c, c * float3(0.88, 1.04, 0.86), lush * 0.4 * strength);
    c = lerp(c, float3(0.42, 0.34, 0.24) * (0.8 + MeadowValue(xz * 1.3) * 0.4), bare * 0.6 * strength);
    return c;
}

float MeadowBare(float2 xz)
{
    return smoothstep(0.8, 0.9, MeadowFbm(xz * 0.11 + 213.4));
}

#endif
