import streamlit as st
import tempfile
import requests
from pathlib import Path
from huggingface_hub import InferenceClient

# ── Configuración de la página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Generador de Videos con IA",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Generador de Videos con IA")
st.caption("Powered by Hugging Face · router.huggingface.co")

# ── Token de Hugging Face ────────────────────────────────────────────────────
hf_token = st.secrets.get("HF_TOKEN", "") if hasattr(st, "secrets") else ""

if not hf_token:
    with st.sidebar:
        st.subheader("🔑 Configuración")
        hf_token = st.text_input(
            "Token de Hugging Face",
            type="password",
            placeholder="hf_xxxxxxxxxxxxxxxxxxxx",
        )
        st.markdown("[Obtener token gratuito →](https://huggingface.co/settings/tokens)")
else:
    with st.sidebar:
        st.subheader("🔑 Configuración")
        st.success("Token cargado desde Secrets ✓")

# ── Parámetros del modelo ────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("⚙️ Parámetros")
    num_frames = st.slider("Número de fotogramas", min_value=8, max_value=24, value=16, step=4)
    num_inference_steps = st.slider("Pasos de inferencia", min_value=10, max_value=50, value=25, step=5)
    guidance_scale = st.slider("Escala de guía", min_value=1.0, max_value=15.0, value=7.5, step=0.5)

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
        value="blurry, low quality, worst quality, deformed",
    )
    submitted = st.form_submit_button("🎬 Generar Video", use_container_width=True, type="primary")

# ── Generación ───────────────────────────────────────────────────────────────
if submitted:
    if not prompt.strip():
        st.error("Por favor escribe un prompt para generar el video.")
    elif not hf_token:
        st.error("Necesitas ingresar tu token de Hugging Face en el panel lateral.")
    else:
        with st.spinner("⏳ Generando tu video… esto puede tardar 1-3 minutos"):
            try:
                client = InferenceClient(
                    provider="hf-inference",
                    api_key=hf_token,
                )

                video = client.text_to_video(
                    prompt,
                    model="damo-vilab/text-to-video-ms-1.7b",
                    guidance_scale=guidance_scale,
                    num_inference_steps=num_inference_steps,
                )

                # video es un objeto de tipo bytes o similar
                if hasattr(video, "read"):
                    video_bytes = video.read()
                elif isinstance(video, bytes):
                    video_bytes = video
                else:
                    video_bytes = bytes(video)

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
                full_trace = traceback.format_exc()
                error_msg = str(e)
                if "401" in error_msg or "authorization" in error_msg.lower():
                    st.error("❌ Token inválido.")
                elif "429" in error_msg:
                    st.error("❌ Límite de peticiones. Espera unos minutos.")
                else:
                    st.error(f"❌ Error: {error_msg}")
                    st.code(full_trace, language="text")

# ── Consejos ─────────────────────────────────────────────────────────────────
with st.expander("💡 Consejos para mejores resultados"):
    st.markdown("""
    **Escribe prompts en inglés** para mejores resultados.

    **Ejemplos:**
    - `A cat playing with a ball of yarn, cozy living room, warm lighting`
    - `Ocean waves crashing on rocks at sunset, cinematic`
    - `A red sports car driving on a mountain road, aerial view`
    """)

st.divider()
st.caption("Modelo: [damo-vilab/text-to-video-ms-1.7b](https://huggingface.co/damo-vilab/text-to-video-ms-1.7b) · "
           "Hosting gratuito en [Streamlit Community Cloud](https://streamlit.io/cloud)")
