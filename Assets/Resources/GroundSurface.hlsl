#ifndef WARFARE_GROUND_SURFACE
#define WARFARE_GROUND_SURFACE
#include "MeadowNoise.hlsl"
CBUFFER_START(UnityPerMaterial)
    float4 _BaseMap_ST;
    float _Tile;
    float _DetailStrength;
    float _ReliefStrength;
    float4 _RockHeight;
    float _Meadow;
    float4 _RockColor;
    float4 _CanopyFade;
    float4 _RoadColor;

    float4 _MapSize;
    float4 _TipColor;
    float4 _DryColor;
    float _RootShade;
    float _FadeStart;
    float _FadeEnd;
    float _Height;
    float _Density;
    float _Shell;
    float _TipLight;
    float4 _Area;
    float _SteppeCover;
    float4 _Smooth;
    float4 _HabitatArea;
    float _GroundVariation;
    float _FarDensity;
    float4 _LodRange;
    float _NormalBend;
    float4 _PaveColor;
    float _PaveTile;
CBUFFER_END

TEXTURE2D(_BaseMap); SAMPLER(sampler_trilinear_clamp);
TEXTURE2D(_Relief);
TEXTURE2D(_Splat0);
TEXTURE2D(_Splat1);
TEXTURE2D(_Grass); SAMPLER(sampler_trilinear_repeat);
TEXTURE2D(_Forest);
TEXTURE2D(_Taiga);
TEXTURE2D(_ForestFloor);
TEXTURE2D(_TaigaFloor);
TEXTURE2D(_RoadMask);
TEXTURE2D(_YardMask);
TEXTURE2D(_Paving);
TEXTURE2D(_Farm);
TEXTURE2D(_Steppe);
TEXTURE2D(_Desert);
TEXTURE2D(_Tundra);
TEXTURE2D(_Snow);
TEXTURE2D(_Rock);

float3 ReliefNormal(float2 uv, float3 n)
{
    float2 g = (SAMPLE_TEXTURE2D(_Relief, sampler_trilinear_clamp, uv).rg - 0.5) * 4.0 * _ReliefStrength;
    return normalize(n + float3(-g.x, 0.0, -g.y));
}

TEXTURE2D(_Habitat); SAMPLER(sampler_Habitat);
TEXTURE2D(_MeadowGround);
float GrassInstanceRandom(float2 p)
{
    uint h = asuint(p.x) * 747796405u ^ asuint(p.y) * 2891336453u;
    h ^= h >> 16;
    h *= 2246822519u;
    h ^= h >> 13;
    return (h & 0x00ffffffu) * (1.0 / 16777216.0);
}
float4 Detail(TEXTURE2D_PARAM(tex, smp), float2 uv, float far, float farScale)
{
    return lerp(SAMPLE_TEXTURE2D(tex, smp, uv), SAMPLE_TEXTURE2D(tex, smp, uv * farScale), far);
}

float4 Triplanar(TEXTURE2D_PARAM(tex, smp), float3 p, float3 nrm, float scale, float far)
{
    float3 bw = pow(abs(nrm), 4.0);
    bw /= bw.x + bw.y + bw.z;
    float4 x = Detail(TEXTURE2D_ARGS(tex, smp), p.zy * scale, far, 0.3);
    float4 y = Detail(TEXTURE2D_ARGS(tex, smp), p.xz * scale, far, 0.3);
    float4 z = Detail(TEXTURE2D_ARGS(tex, smp), p.xy * scale, far, 0.3);
    return x * bw.x + y * bw.y + z * bw.z;
}


float3 GroundSurface(float2 uv, float3 positionWS, float3 normalWS, out float3 n, out float snow)
{
    float3 macro = SAMPLE_TEXTURE2D(_BaseMap, sampler_trilinear_clamp, uv).rgb;
    float4 s0 = SAMPLE_TEXTURE2D(_Splat0, sampler_trilinear_clamp, uv);
    float4 s1 = SAMPLE_TEXTURE2D(_Splat1, sampler_trilinear_clamp, uv);
    n = ReliefNormal(uv, normalize(normalWS));
    float2 meadowUV = (positionWS.xz - _HabitatArea.xy) / max(_HabitatArea.zw, 1.0);
    float habitat = SAMPLE_TEXTURE2D(_Habitat, sampler_Habitat, meadowUV).a;

    float dist = distance(positionWS, _WorldSpaceCameraPos);
    float far = saturate((dist - 120.0) / 600.0);
    float2 w = positionWS.xz / _Tile;

    float4 d[9];
    d[0] = Detail(TEXTURE2D_ARGS(_Grass, sampler_trilinear_repeat), w, far, 0.19);
    [branch] if (habitat > 0.001)
        d[0] = lerp(d[0], Detail(TEXTURE2D_ARGS(_MeadowGround, sampler_trilinear_repeat), w, far, 0.19), habitat * _GroundVariation);
    float canopy = smoothstep(_CanopyFade.x, _CanopyFade.y, dist);
    d[1] = lerp(Detail(TEXTURE2D_ARGS(_ForestFloor, sampler_trilinear_repeat), w, far, 0.19), Detail(TEXTURE2D_ARGS(_Forest, sampler_trilinear_repeat), w * 1.3, far, 0.19), canopy);
    d[2] = lerp(Detail(TEXTURE2D_ARGS(_TaigaFloor, sampler_trilinear_repeat), w, far, 0.19), Detail(TEXTURE2D_ARGS(_Taiga, sampler_trilinear_repeat), w * 1.3, far, 0.19), canopy);
    d[3] = Detail(TEXTURE2D_ARGS(_Farm, sampler_trilinear_repeat), mul(float2x2(0.876, -0.482, 0.482, 0.876), w) * 0.5, far * 0.6, 0.62);
    d[4] = Detail(TEXTURE2D_ARGS(_Steppe, sampler_trilinear_repeat), w, far, 0.19);
    d[5] = Detail(TEXTURE2D_ARGS(_Desert, sampler_trilinear_repeat), w * 0.6, far, 0.19);
    d[6] = Detail(TEXTURE2D_ARGS(_Tundra, sampler_trilinear_repeat), w, far, 0.19);
    d[7] = Detail(TEXTURE2D_ARGS(_Snow, sampler_trilinear_repeat), w * 0.7, far, 0.19);
    d[8] = Triplanar(TEXTURE2D_ARGS(_Rock, sampler_trilinear_repeat), positionWS, normalize(normalWS), 0.6 / _Tile, far);

    float slope = 1.0 - n.y;
    float slopeRock = smoothstep(0.24, 0.5, slope) * saturate(0.25 + positionWS.y / 16.0);
    float rockT = saturate(max(slopeRock, smoothstep(_RockHeight.x, _RockHeight.y, positionWS.y)) * (1.0 - s1.a));
    float wts[9] = { s0.r, s0.g, s0.b, s0.a, s1.r, s1.g, s1.b, s1.a, 0.0 };
    for (int k = 0; k < 8; k++) wts[k] *= 1.0 - rockT;
    wts[8] = rockT;

    float hmax = -1.0;
    float hs[9];
    for (int j = 0; j < 9; j++)
    {
        hs[j] = wts[j] > 0.002 ? wts[j] + d[j].a * 0.45 : -1.0;
        hmax = max(hmax, hs[j]);
    }
    float3 acc = 0.0;
    float bsum = 0.0;
    for (int m = 0; m < 9; m++)
    {
        float b = max(hs[m] - (hmax - 0.18), 0.0);
        acc += d[m].rgb * b;
        bsum += b;
    }
    float3 detail = bsum > 0.0 ? acc / bsum : 0.5;

    float3 base = lerp(macro, _RockColor.rgb, slopeRock * (1.0 - s1.a) * 0.55);
    float3 albedo = base * lerp(1.0, detail * 2.0, _DetailStrength);
    albedo = MeadowTint(albedo, positionWS.xz, _Meadow * saturate(wts[0] + wts[4] * 0.6) * (1.0 - far * 0.5));
    [branch] if (habitat > 0.001)
    {
    float meadow = habitat * _GroundVariation * saturate(wts[0] + wts[4] * 0.06);
    float patch = MeadowFbm(positionWS.xz * 0.17 + 6.4);
    float tuft = MeadowFbm(positionWS.xz * 1.15 + MeadowValue(positionWS.xz * 0.31) * 1.3);
    float fullness = smoothstep(0.24, 0.72, tuft);
    float dryPatch = smoothstep(0.55, 0.77, patch);
    float3 turfTint = lerp(float3(0.82, 0.89, 0.78), float3(1.10, 1.07, 0.99), fullness);
    turfTint = lerp(turfTint, float3(1.07, 1.015, 0.85), dryPatch * 0.5);
    albedo *= lerp(float3(1, 1, 1), turfTint, meadow);
    float barePatch = smoothstep(0.66, 0.84, MeadowFbm(positionWS.xz * 0.55 + 89.1));
    albedo = lerp(albedo, albedo * float3(1.06, 0.95, 0.77), barePatch * meadow * 0.45);
    }
    float road = SAMPLE_TEXTURE2D(_RoadMask, sampler_trilinear_clamp, uv).r * smoothstep(0.12, 0.42, positionWS.y);
    float3 dirt = _RoadColor.rgb * lerp(1.0, d[4].r * 2.0, 0.5);
    albedo = lerp(albedo, dirt, road * 0.92);
    float2 yard = SAMPLE_TEXTURE2D(_YardMask, sampler_trilinear_clamp, uv).rg * smoothstep(0.12, 0.42, positionWS.y);
    float3 trodden = lerp(albedo * float3(1.1, 1.0, 0.68), dirt, 0.25 + 0.35 * MeadowFbm(positionWS.xz * 0.9 + 17.3));
    albedo = lerp(albedo, trodden, yard.r * 0.85);
    float stones = SAMPLE_TEXTURE2D(_Paving, sampler_trilinear_repeat, positionWS.xz * _PaveTile).r;
    albedo = lerp(albedo, _PaveColor.rgb * lerp(0.62, 1.2, stones), yard.g * 0.95);


    snow = s1.a;
    return albedo;
}
#endif
