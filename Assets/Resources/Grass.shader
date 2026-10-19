Shader "Warfare/Grass"
{
    Properties
    {
        _BaseMap ("Terrain color", 2D) = "white" {}
        _Grass ("Grass detail", 2D) = "gray" {}
        _SteppeTex ("Steppe detail", 2D) = "gray" {}
        _Splat0 ("Splat 0", 2D) = "black" {}
        _Splat1 ("Splat 1", 2D) = "black" {}
        _Tile ("Detail tile size", Float) = 7
        _DetailStrength ("Detail strength", Range(0, 1)) = 0.9
        _MapSize ("Map width, height", Vector) = (1765, 1176, 0, 0)
        _TipColor ("Tip tint", Color) = (1.14, 1.16, 0.95, 1)
        _DryColor ("Dry tip tint", Color) = (1.25, 1.15, 0.8, 1)
        _RootShade ("Root shade", Range(0, 1)) = 0.62
        _NormalBend ("Blade normal bend", Range(0, 1)) = 0.055
        _Meadow ("Meadow variation", Range(0, 1)) = 1
        _FadeStart ("Shrink start distance", Float) = 45
        _FadeEnd ("Shrink end distance", Float) = 80
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Off

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
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
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float3 rootColor : TEXCOORD2;
                float4 blade : TEXCOORD3;
                float fogCoord : TEXCOORD4;
                float4 color : COLOR;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 origin = float3(UNITY_MATRIX_M._m03, UNITY_MATRIX_M._m13, UNITY_MATRIX_M._m23);
                float3 p = TransformObjectToWorld(input.positionOS.xyz);
                float d = distance(origin, _WorldSpaceCameraPos);
                float s = 1.0 - smoothstep(_FadeStart, _FadeEnd, d);
                s *= smoothstep(0.0, 0.2, s);
                float thinning = smoothstep(_LodRange.x, _LodRange.y, d);
                float keep = lerp(1.08, _FarDensity, thinning);
                s *= 1.0 - smoothstep(keep - 0.08, keep, GrassInstanceRandom(origin.xz));
                p.y = origin.y + (p.y - origin.y) * s;
                float2 rootXZ = p.xz;
                o.rootColor = origin;
                o.positionWS = p;
                o.positionCS = TransformWorldToHClip(p);
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.blade = float4(input.uv, MeadowFbm(rootXZ * 0.045), 0);
                o.fogCoord = ComputeFogFactor(o.positionCS.z);
                o.color = input.color;
                return o;
            }

            half4 frag(Varyings input, bool front : SV_IsFrontFace) : SV_Target
            {
                float h = input.blade.y;
                float2 uv = float2((input.rootColor.x + _MapSize.x * 0.5) / (_MapSize.x - 1.0), 1.0 - (_MapSize.y * 0.5 - input.rootColor.z) / (_MapSize.y - 1.0));
                float2 huv = (input.rootColor.xz - _HabitatArea.xy) / _HabitatArea.zw;
                float4 habitat = SAMPLE_TEXTURE2D(_Habitat, sampler_Habitat, huv);
                float3 n; float snow;
                float3 ground = GroundSurface(uv, input.rootColor, normalize(habitat.rgb * 2.0 - 1.0), n, snow);
                float dry = smoothstep(0.5, 0.78, input.blade.z) * _Meadow;
                float3 tip = ground * lerp(_TipColor.rgb, float3(1.02, 1.02, 1.02), dry * 0.5);
                float3 albedo = lerp(ground * _RootShade, tip, smoothstep(0.0, 1.0, h));
                float3 bladeNormal = normalize(input.normalWS);
                bladeNormal *= front ? 1.0 : -1.0;
                n = normalize(n + bladeNormal * (_NormalBend * smoothstep(0.0, 0.35, h)));
                InputData inputData = (InputData)0;
                inputData.positionWS = input.positionWS;
                inputData.positionCS = input.positionCS;
                inputData.normalWS = n;
                inputData.viewDirectionWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
                float3 sunDir = GetMainLight().direction;
                inputData.shadowCoord = TransformWorldToShadowCoord(input.positionWS + float3(0, 0.06, 0) + sunDir * 0.03);
                inputData.fogCoord = input.fogCoord;
                inputData.bakedGI = SampleSH(n);
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                inputData.shadowMask = half4(1, 1, 1, 1);
                SurfaceData surf = (SurfaceData)0;
                surf.albedo = albedo;
                surf.smoothness = 0.05;
                surf.occlusion = 1.0;
                surf.alpha = 1.0;
                half4 color = UniversalFragmentPBR(inputData, surf);
                return half4(MixFog(color.rgb, input.fogCoord), 1);
            }
            ENDHLSL
        }
    }
}
