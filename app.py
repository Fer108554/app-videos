import streamlit as st
import tempfile
import requests
import os
from pathlib import Path
import fal_client

# ── Configuración de la página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Generador de Videos con IA",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Generador de Videos con IA")
st.caption("Powered by fal.ai · AnimateDiff Lightning")

# ── Token de fal.ai ──────────────────────────────────────────────────────────
fal_token = st.secrets.get("FAL_KEY", "") if hasattr(st, "secrets") else ""

if not fal_token:
    with st.sidebar:
        st.subheader("🔑 Configuración")
        fal_token = st.text_input(
            "API Key de fal.ai",
            type="password",
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:xxxx",
            help="Obtén tu key gratis en fal.ai → Dashboard → API Keys",
        )
        st.markdown("[Crear cuenta gratuita →](https://fal.ai)")
else:
    with st.sidebar:
        st.subheader("🔑 Configuración")
        st.success("API Key cargada desde Secrets ✓")

# ── Parámetros del modelo ────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("⚙️ Parámetros")
    num_frames = st.slider("Número de fotogramas", min_value=8, max_value=24, value=16, step=4)
    num_inference_steps = st.slider("Pasos de inferencia", min_value=4, max_value=8, value=4, step=1,
                                     help="AnimateDiff Lightning es muy rápido con pocos pasos")
    guidance_scale = st.slider("Escala de guía", min_value=1.0, max_value=5.0, value=1.0, step=0.5)

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
    elif not fal_token:
        st.error("Necesitas ingresar tu API Key de fal.ai en el panel lateral.")
    else:
        with st.spinner("⏳ Generando tu video… esto puede tardar 30-60 segundos"):
            try:
                os.environ["FAL_KEY"] = fal_token

                result = fal_client.run(
                    "fal-ai/fast-animatediff/text-to-video",
                    arguments={
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "num_inference_steps": num_inference_steps,
                        "guidance_scale": guidance_scale,
                        "video_size": "landscape_16_9",
                        "num_frames": num_frames,
                    }
                )

                video_url = result["video"]["url"]
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
                if "401" in error_msg or "unauthorized" in error_msg.lower():
                    st.error("❌ API Key inválida. Verifica tu key de fal.ai.")
                elif "402" in error_msg or "credit" in error_msg.lower():
                    st.error("❌ Sin crédito. Ve a fal.ai/dashboard/billing para recargar.")
                elif "429" in error_msg:
                    st.error("❌ Límite de peticiones. Espera unos minutos.")
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
    """)

st.divider()
st.caption("Modelo: [AnimateDiff Lightning](https://fal.ai/models/fal-ai/fast-animatediff) · "
           "Hosting gratuito en [Streamlit Community Cloud](https://streamlit.io/cloud)")
