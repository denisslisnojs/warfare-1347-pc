Shader "Warfare/GrassShell"
{
    Properties
    {
        _BaseMap ("Terrain color", 2D) = "white" {}
        _Splat0 ("Splat 0", 2D) = "black" {}
        _Splat1 ("Splat 1", 2D) = "black" {}
        _RoadMask ("Road mask", 2D) = "black" {}
        _Grass ("Grass detail", 2D) = "gray" {}
        _SteppeTex ("Steppe detail", 2D) = "gray" {}
        _Tile ("Detail tile size", Float) = 7
        _DetailStrength ("Detail strength", Range(0, 1)) = 0.9
        _Meadow ("Meadow variation", Range(0, 1)) = 1
        _Height ("Carpet height", Float) = 0.22
        _Density ("Strands per unit", Float) = 34
        _Shell ("Shell 0..1", Float) = 0
        _FadeStart ("Fade start distance", Float) = 90
        _FadeEnd ("Fade end distance", Float) = 150
        _RootShade ("Root shade", Range(0, 1)) = 0.84
        _TipLight ("Tip light", Float) = 1.1
        _Area ("Test area x, z, radius, on", Vector) = (0, 0, 0, 0)
        _RockHeight ("Rock height from-to", Vector) = (15, 25, 0, 0)
        _SteppeCover ("Steppe cover", Range(0, 1)) = 0.5
        _Smooth ("Smooth from-to distance", Vector) = (35, 85, 0, 0)
    }

    SubShader
    {
        Tags { "RenderType" = "TransparentCutout" "RenderPipeline" = "UniversalPipeline" "Queue" = "AlphaTest" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Back

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "MeadowNoise.hlsl"

            #include "GroundSurface.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv : TEXCOORD1;
                float fade : TEXCOORD2;
                float fogCoord : TEXCOORD3;
                float3 normalWS : TEXCOORD4;
                float far : TEXCOORD5;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                float3 p = TransformObjectToWorld(input.positionOS.xyz);
                float d = distance(p, _WorldSpaceCameraPos);
                float fade = 1.0 - smoothstep(_FadeStart, _FadeEnd, d);
                p.y += _Shell * _Height * fade;
                o.positionWS = p;
                o.positionCS = TransformWorldToHClip(p);
                o.uv = input.uv;
                o.fade = fade;
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.far = smoothstep(_Smooth.x, _Smooth.y, d);
                o.fogCoord = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                if (input.fade <= 0.001 || input.positionWS.y - _Shell * _Height * input.fade < 0.28) discard;
                if (_Area.w > 0.5 && distance(input.positionWS.xz, _Area.xy) > _Area.z) discard;
                float2 xz = input.positionWS.xz;
                float4 s0 = SAMPLE_TEXTURE2D(_Splat0, sampler_trilinear_clamp, input.uv);
                float4 s1 = SAMPLE_TEXTURE2D(_Splat1, sampler_trilinear_clamp, input.uv);
                if (s1.g > 0.1 || s1.a > 0.1) discard;
                float road = SAMPLE_TEXTURE2D(_RoadMask, sampler_trilinear_clamp, input.uv).r;
                float2 yard = SAMPLE_TEXTURE2D(_YardMask, sampler_trilinear_clamp, input.uv).rg;
                float3 nrm = normalize(input.normalWS);
                float2 huv = (input.positionWS.xz - _HabitatArea.xy) / _HabitatArea.zw;
                float habitat = SAMPLE_TEXTURE2D(_Habitat, sampler_Habitat, huv).a;
                float wobble = (MeadowValue(xz * 1.7 + 3.1) - 0.5) * 0.12;
                float slopeRock = smoothstep(0.24, 0.5, 1.0 - nrm.y + wobble) * saturate(0.25 + input.positionWS.y / 16.0);
                float heightRock = smoothstep(_RockHeight.x, _RockHeight.y, input.positionWS.y + wobble * 8.0);
                float cover = saturate(s0.r + s1.r * _SteppeCover + s0.g * 0.3) * (1.0 - smoothstep(0.05, 0.4, road)) * (1.0 - max(slopeRock, heightRock)) * (1.0 - s1.a) * (1.0 - saturate(yard.g * 1.5)) * (1.0 - yard.r * 0.6);
                cover *= habitat * (1.0 - MeadowBare(xz) * 0.9);
                float clump = MeadowFbm(xz * 0.9 + 5.3);
                float tall = saturate(cover * lerp(0.55, 1.15, clump));

                float2 cell = xz * _Density;
                float2 id = floor(cell);
                float2 f = frac(cell) - 0.5;
                float r = MeadowHash(id);
                if (MeadowHash(id + 19.7) > input.fade * 1.15) discard;
                float2 off = (float2(MeadowHash(id + 7.1), MeadowHash(id + 3.7)) - 0.5) * 0.5;
                float far = input.far;
                float strand = lerp(r * tall, tall * 0.85, far);
                float radius = 0.46 * (1.0 - _Shell / max(strand, 0.001));
                if (_Shell > strand || length(f - off) > radius) discard;

                float3 lightN; float snow;
                float3 root = input.positionWS - float3(0, _Shell * _Height * input.fade, 0);
                float3 ground = GroundSurface(input.uv, root, nrm, lightN, snow);
                float3 albedo = ground * lerp(_RootShade, _TipLight, _Shell * (1.0 - input.far));
                InputData inputData = (InputData)0;
                inputData.positionWS = input.positionWS;
                inputData.positionCS = input.positionCS;
                inputData.normalWS = lightN;
                inputData.viewDirectionWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
                float3 sunDir = GetMainLight().direction;
                inputData.shadowCoord = TransformWorldToShadowCoord(input.positionWS + float3(0, 0.06, 0) + sunDir * 0.03);
                inputData.fogCoord = input.fogCoord;
                inputData.bakedGI = SampleSH(lightN);
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                inputData.shadowMask = half4(1, 1, 1, 1);
                SurfaceData surf = (SurfaceData)0;
                surf.albedo = albedo;
                surf.smoothness = 0.05;
                surf.occlusion = 1.0;
                surf.alpha = 1.0;
                half4 color = UniversalFragmentPBR(inputData, surf);
                color.rgb = MixFog(color.rgb, input.fogCoord);
                return half4(color.rgb, 1);
            }
            ENDHLSL
        }
    }
}
