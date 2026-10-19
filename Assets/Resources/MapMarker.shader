Shader "Warfare/MapMarker"
{
    Properties
    {
        _Color ("Color", Color) = (1, 0.93, 0.72, 0.9)
        _Rim ("Rim color", Color) = (0.12, 0.09, 0.06, 0.85)
        _Size ("Dot size", Float) = 0.35
        _Grow ("Grow from distance", Float) = 80
    }

    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent+1" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Off
            Offset -2, -2

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _Color;
                float4 _Rim;
                float _Size;
                float _Grow;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
                float2 corner : TEXCOORD1;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
                float fogCoord : TEXCOORD1;
            };

            Varyings vert(Attributes input)
            {
                Varyings o;
                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                float d = distance(positionWS, _WorldSpaceCameraPos);
                positionWS.xz += input.corner * _Size * max(1.0, d / max(_Grow, 1.0));
                o.positionCS = TransformWorldToHClip(positionWS);
                o.color = input.color;
                o.uv = input.uv;
                o.fogCoord = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings input) : SV_Target
            {
                float r = length(input.uv * 2.0 - 1.0);
                float a = saturate((1.0 - r) * 6.0);
                float3 col = lerp(_Rim.rgb, _Color.rgb * input.color.rgb, saturate((0.72 - r) * 8.0));
                col = MixFog(col, input.fogCoord);
                return half4(col, a * lerp(_Rim.a, _Color.a, saturate((0.72 - r) * 8.0)) * input.color.a);
            }
            ENDHLSL
        }
    }
}
