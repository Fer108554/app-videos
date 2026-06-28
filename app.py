import streamlit as st
import tempfile
import requests
import os
from pathlib import Path
import replicate

# ── Configuración de la página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Generador de Videos con IA",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Generador de Videos con IA")
st.caption("Powered by Replicate · Zeroscope v2 XL")

# ── Token de Replicate ───────────────────────────────────────────────────────
replicate_token = st.secrets.get("REPLICATE_API_TOKEN", "") if hasattr(st, "secrets") else ""

if not replicate_token:
    with st.sidebar:
        st.subheader("🔑 Configuración")
        replicate_token = st.text_input(
            "Token de Replicate",
            type="password",
            placeholder="r8_xxxxxxxxxxxxxxxxxxxx",
            help="Obtén tu token gratis en replicate.com → Account → API tokens",
        )
        st.markdown("[Crear token gratuito →](https://replicate.com/account/api-tokens)")
else:
    with st.sidebar:
        st.subheader("🔑 Configuración")
        st.success("Token cargado desde Secrets ✓")

# ── Parámetros del modelo ────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("⚙️ Parámetros")
    num_frames = st.slider("Número de fotogramas", min_value=8, max_value=24, value=16, step=4)
    num_inference_steps = st.slider("Pasos de inferencia", min_value=10, max_value=50, value=25, step=5,
                                     help="Más pasos = más calidad, pero más lento")
    guidance_scale = st.slider("Escala de guía", min_value=1.0, max_value=15.0, value=7.5, step=0.5,
                                help="Qué tan fiel es al texto. Valores altos = más literal")

# ── Formulario principal ─────────────────────────────────────────────────────
st.subheader("📝 Describe tu video")

with st.form("video_form"):
    prompt = st.text_area(
        "Prompt (en inglés da mejores resultados)",
        placeholder="A fluffy golden retriever running on a beach at sunset, cinematic, 4k",
        height=100,
    )
    negative_prompt = st.text_input(
        "Prompt negativo (opcional)",
        placeholder="blurry, low quality, distorted",
        value="blurry, low quality, worst quality, deformed",
    )
    submitted = st.form_submit_button("🎬 Generar Video", use_container_width=True, type="primary")

# ── Generación ───────────────────────────────────────────────────────────────
if submitted:
    if not prompt.strip():
        st.error("Por favor escribe un prompt para generar el video.")
    elif not replicate_token:
        st.error("Necesitas ingresar tu token de Replicate en el panel lateral.")
    else:
        with st.spinner("⏳ Generando tu video… esto puede tardar 1-3 minutos"):
            try:
                os.environ["REPLICATE_API_TOKEN"] = replicate_token

                output = replicate.run(
                    "anotherjesse/zeroscope-v2-xl:9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351",
                    input={
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "num_frames": num_frames,
                        "num_inference_steps": num_inference_steps,
                        "guidance_scale": guidance_scale,
                        "width": 576,
                        "height": 320,
                        "fps": 8,
                    }
                )

                # output es una lista de URLs o un FileOutput
                video_url = output[0] if isinstance(output, list) else str(output)
                video_bytes = requests.get(video_url).content

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_bytes)
                    tmp_path = tmp.name

                st.success("¡Video generado con éxito! 🎉")
                st.video(tmp_path)

                with open(tmp_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Descargar video",
                        data=f.read(),
                        file_name="video_generado.mp4",
                        mime="video/mp4",
                        use_container_width=True,
                    )

                Path(tmp_path).unlink(missing_ok=True)

            except Exception as e:
                import traceback
                error_msg = str(e)
                full_trace = traceback.format_exc()
                if "401" in error_msg or "authorization" in error_msg.lower():
                    st.error("❌ Token inválido. Verifica tu token de Replicate.")
                elif "429" in error_msg:
                    st.error("❌ Límite de peticiones alcanzado. Espera unos minutos.")
                else:
                    st.error(f"❌ Error: {error_msg}")
                    st.code(full_trace, language="text")

# ── Consejos ─────────────────────────────────────────────────────────────────
with st.expander("💡 Consejos para mejores resultados"):
    st.markdown("""
    **Escribe prompts en inglés** — el modelo fue entrenado principalmente con texto en inglés.

    **Prompts que funcionan bien:**
    - `A cat playing with a ball of yarn, cozy living room, warm lighting`
    - `Ocean waves crashing on rocks at sunset, timelapse, cinematic`
    - `A red sports car driving on a mountain road, aerial view`

    **Incluye detalles de estilo:**
    - `cinematic`, `4k`, `high quality`, `smooth motion`
    - Iluminación: `golden hour`, `soft light`, `dramatic lighting`
    - Tipo de cámara: `aerial shot`, `close-up`, `wide angle`

    **Prompt negativo útil:** `blurry, low quality, static, no motion, distorted faces`
    """)

st.divider()
st.caption("Modelo: [Zeroscope v2 XL](https://replicate.com/anotherjesse/zeroscope-v2-xl) · "
           "Hosting gratuito en [Streamlit Community Cloud](https://streamlit.io/cloud)")
