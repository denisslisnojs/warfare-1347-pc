Shader "Warfare/Water"
{
    Properties
    {
        _Shallow ("Shallow", Color) = (0.22, 0.6, 0.62, 1)
        _Deep ("Deep", Color) = (0.04, 0.17, 0.32, 1)
        _DepthRange ("Depth range", Float) = 4
        _FoamColor ("Foam", Color) = (0.9, 0.95, 0.94, 1)
        _FoamWidth ("Foam width", Float) = 0.3
        _Waves ("Waves", 2D) = "gray" {}
        _WaveScale ("Wave scale", Float) = 0.06
        _WaveStrength ("Wave strength", Float) = 0.6
        _Flow ("Flow speed", Vector) = (0.018, 0.011, -0.014, 0.009)
        _MinAlpha ("Edge alpha", Range(0, 1)) = 0.3
        _MaxAlpha ("Deep alpha", Range(0, 1)) = 1
        _ShoreFade ("Shore fade", Float) = 6
    }

    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" "RenderPipeline" = "UniversalPipeline" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Off

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _Shallow;
                float4 _Deep;
                float _DepthRange;
                float4 _FoamColor;
                float _FoamWidth;
                float4 _Waves_ST;
                float _WaveScale;
                float _WaveStrength;
                float4 _Flow;
                float _MinAlpha;
                float _MaxAlpha;
                float _ShoreFade;
            CBUFFER_END

            TEXTURE2D(_Waves); SAMPLER(sampler_trilinear_repeat);

            struct Attributes
            {
                float4 positionOS : POSITION;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float4 screenPos : TEXCOORD1;
                float fogCoord : TEXCOORD2;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(input.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.screenPos = ComputeScreenPos(p.positionCS);
                o.fogCoord = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float2 suv = input.screenPos.xy / input.screenPos.w;
                float sceneEye = LinearEyeDepth(SampleSceneDepth(suv), _ZBufferParams);
                float waterEye = LinearEyeDepth(input.positionCS.z, _ZBufferParams);
                float3 view = GetWorldSpaceNormalizeViewDir(input.positionWS);
                float depth = max(sceneEye - waterEye, 0.0) * saturate(abs(view.y) + 0.15);

                float2 uvA = input.positionWS.xz * _WaveScale + _Time.y * _Flow.xy;
                float2 uvB = input.positionWS.xz * _WaveScale * 1.9 + _Time.y * _Flow.zw;
                float4 wa = SAMPLE_TEXTURE2D(_Waves, sampler_trilinear_repeat, uvA);
                float4 wb = SAMPLE_TEXTURE2D(_Waves, sampler_trilinear_repeat, uvB);
                float2 slope = ((wa.xy * 2.0 - 1.0) + (wb.xy * 2.0 - 1.0)) * _WaveStrength;
                float3 n = normalize(float3(slope.x, 1.0, slope.y));

                Light light = GetMainLight(TransformWorldToShadowCoord(input.positionWS), input.positionWS, half4(1, 1, 1, 1));
                float3 h = normalize(light.direction + view);
                float spec = pow(saturate(dot(n, h)), 220.0) * 3.0 * light.shadowAttenuation;
                float fresnel = pow(1.0 - saturate(dot(n, view)), 4.0);
                float3 sky = SampleSH(float3(0.0, 1.0, 0.0));

                float t = saturate(depth / _DepthRange);
                float3 col = lerp(_Shallow.rgb, _Deep.rgb, sqrt(t));
                col *= 0.62 + 0.38 * saturate(dot(n, light.direction)) * light.color * lerp(0.6, 1.0, light.shadowAttenuation);
                col = lerp(col, sky, fresnel * 0.45) + spec * light.color;

                float foamNoise = wa.a * 0.6 + wb.a * 0.4;
                float edge = saturate(1.0 - depth / _FoamWidth);
                float foam = edge * edge * smoothstep(0.5, 0.7, foamNoise + 0.18 * sin(_Time.y * 1.3 + depth * 9.0));
                col = lerp(col, _FoamColor.rgb, foam * 0.45);

                float alpha = lerp(_MinAlpha, _MaxAlpha, saturate(depth / (_DepthRange * 0.4)));
                alpha = max(alpha, foam * 0.6) * saturate(depth * _ShoreFade + 0.05);
                col = MixFog(col, ComputeFogFactor(TransformWorldToHClip(input.positionWS).z));
                return half4(col, alpha);
            }
            ENDHLSL
        }
    }
}
