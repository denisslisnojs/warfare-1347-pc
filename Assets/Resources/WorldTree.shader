Shader "Warfare/WorldTree"
{
    Properties
    {
        _BaseColor ("Color", Color) = (1, 1, 1, 1)
        _Pattern ("Pattern", 2D) = "gray" {}
        _PatternScale ("Pattern repeats per unit", Float) = 3
        _PatternStrength ("Pattern strength", Range(0, 1)) = 0.8
        _AOStrength ("Baked occlusion", Range(0, 1)) = 0.9
        _Variation ("Tint variation", Range(0, 1)) = 0.25
        _Foliage ("Foliage (wind, light wrap)", Range(0, 1)) = 1
        _FadeStart ("Shrink start distance", Float) = 700
        _FadeEnd ("Shrink end distance", Float) = 950
        _Wind ("Wind sway", Float) = 0
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseColor;
            float4 _Pattern_ST;
            float _PatternScale;
            float _PatternStrength;
            float _AOStrength;
            float _Variation;
            float _Foliage;
            float _FadeStart;
            float _FadeEnd;
            float _Wind;
        CBUFFER_END

        TEXTURE2D(_Pattern); SAMPLER(sampler_trilinear_repeat);

        float Hash(float2 p)
        {
            return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
        }

        float3 TreeOrigin()
        {
            return float3(UNITY_MATRIX_M._m03, UNITY_MATRIX_M._m13, UNITY_MATRIX_M._m23);
        }

        float3 TreeWorld(float3 positionOS)
        {
            float3 origin = TreeOrigin();
            float3 p = TransformObjectToWorld(positionOS);
            float d = distance(origin, _WorldSpaceCameraPos);
            float s = 1.0 - smoothstep(_FadeStart, _FadeEnd, d);
            float h = max(p.y - origin.y, 0.0);
            float sway = sin(_Time.y * 1.4 + origin.x * 0.37 + origin.z * 0.21) * 0.025 * _Wind * h * h;
            p.xz += float2(sway, sway * 0.6);
            return origin + (p - origin) * s;
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float4 color : COLOR;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float4 color : TEXCOORD2;
                float3 tint : TEXCOORD3;
                float height : TEXCOORD4;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 origin = TreeOrigin();
                float3 p = TreeWorld(input.positionOS.xyz);
                o.positionWS = p;
                o.positionCS = TransformWorldToHClip(p);
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.color = input.color;
                float h1 = Hash(origin.xz);
                float h2 = Hash(origin.zx + 17.3);
                o.tint = 1.0 + float3(h1 - 0.5, (h2 - 0.5) * 0.7, (0.5 - h1) * 0.8) * _Variation * _Foliage + (h2 - 0.5) * _Variation * 0.6;
                o.height = saturate((p.y - origin.y) / max(length(UNITY_MATRIX_M._m01_m11_m21) * 1.2, 1e-3));
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float3 n = normalize(input.normalWS);
                float3 toEye = GetWorldSpaceNormalizeViewDir(input.positionWS);
                if (dot(n, toEye) < -0.05) n = -n;
                float3 bw = pow(abs(n), 4.0);
                bw /= max(bw.x + bw.y + bw.z, 1e-4);
                float3 q = input.positionWS * _PatternScale;
                float pat = SAMPLE_TEXTURE2D(_Pattern, sampler_trilinear_repeat, q.zy).r * bw.x
                          + SAMPLE_TEXTURE2D(_Pattern, sampler_trilinear_repeat, q.xz).r * bw.y
                          + SAMPLE_TEXTURE2D(_Pattern, sampler_trilinear_repeat, q.xy).r * bw.z;
                float ao = lerp(1.0, saturate(input.color.r * 1.25), _AOStrength);
                float top = lerp(1.0, lerp(0.78, 1.12, input.height), _Foliage);
                float3 albedo = _BaseColor.rgb * input.tint * lerp(1.0, pat * 2.0, _PatternStrength) * top;

                Light light = GetMainLight(TransformWorldToShadowCoord(input.positionWS), input.positionWS, half4(1, 1, 1, 1));
                float ndl = dot(n, light.direction);
                float wrap = saturate((ndl + 0.45) / 1.45);
                float lit = lerp(saturate(ndl), wrap, _Foliage);
                float3 diffuse = albedo * light.color * lit * lerp(0.35, 1.0, light.shadowAttenuation) * 1.1;
                float3 sh = SampleSH(n);
                float3 ambient = albedo * lerp(sh, dot(sh, float3(0.333, 0.333, 0.333)), 0.6) * ao;
                float3 col = diffuse * lerp(0.6, 1.0, ao) + ambient;
                col = MixFog(col, ComputeFogFactor(TransformWorldToHClip(input.positionWS).z));
                return half4(col, 1.0);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            float4 vert(Attributes input) : SV_POSITION
            {
                UNITY_SETUP_INSTANCE_ID(input);
                float3 p = TreeWorld(input.positionOS.xyz);
                float3 nrm = TransformObjectToWorldNormal(input.normalOS);
            #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                float3 dir = normalize(_LightPosition - p);
            #else
                float3 dir = _LightDirection;
            #endif
                float4 c = TransformWorldToHClip(ApplyShadowBias(p, nrm, dir));
            #if UNITY_REVERSED_Z
                c.z = min(c.z, UNITY_NEAR_CLIP_VALUE);
            #else
                c.z = max(c.z, UNITY_NEAR_CLIP_VALUE);
            #endif
                return c;
            }

            half4 frag() : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                o.positionCS = TransformWorldToHClip(TreeWorld(input.positionOS.xyz));
                return o;
            }

            half frag(Varyings input) : SV_Target { return input.positionCS.z; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            ZWrite On

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS : TEXCOORD0;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                o.positionCS = TransformWorldToHClip(TreeWorld(input.positionOS.xyz));
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float3 n = normalize(input.normalWS);
            #if defined(_GBUFFER_NORMALS_OCT)
                float2 oct = PackNormalOctQuadEncode(n);
                return half4(PackFloat2To888(saturate(oct * 0.5 + 0.5)), 0.0);
            #else
                return half4(n, 0.0);
            #endif
            }
            ENDHLSL
        }
    }
}
