# app.py
import streamlit as st
from io import BytesIO
from gtts import gTTS
import tempfile
import pdfplumber
from groq import Groq
import os

# API key
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Detectar idioma automaticamiente
def detectar_idioma(texto: str) -> str:
    prompt = f"""
Detecta el idioma de este texto y responde solo con el código ISO 639-1 (ej. 'en', 'es', 'fr', etc).
Texto: \"{texto.strip()[:500]}\"
"""
    response = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=10,
        top_p=1,
        stream=False
    )
    idioma = response.choices[0].message.content.strip().lower()
    return idioma

# Interfaz
st.set_page_config(page_title="VoxVision")
st.title("🧠 VoxVision: PDF o Texto ➜ Voz Accesible")

# Subida de archivo
uploaded = st.file_uploader("📄 Sube tu archivo PDF o TXT", type=["pdf", "txt"])
if uploaded:
    text = ""
    if uploaded.type == "text/plain":
        text = uploaded.read().decode("utf-8")
    else:
        with pdfplumber.open(uploaded) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    
    st.text_area("📝 Texto extraído", value=text, height=300)

    # Convertir a voz
    if st.button("🗣️ Convertir a voz"):
        if not text.strip():
            st.warning("No hay texto para convertir.")
        else:
            with st.spinner("🔎 Detectando idioma..."):
                lang = detectar_idioma(text)
            if lang not in ["en", "es", "de", "fr", "it", "pt"]:
                st.warning(f"Idioma detectado: {lang}. Puede que no esté soportado por gTTS.")
            else:
                st.success(f"🌐 Idioma detectado: {lang}")

                with st.spinner("🎙️ Generando audio..."):
                    tts = gTTS(text=text, lang=lang)
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    audio_bytes = fp.read()
                    st.session_state.audio_bytes = audio_bytes
                    st.session_state.lang = lang

# Mostrar audio
if "audio_bytes" in st.session_state and st.session_state.audio_bytes:
    st.audio(st.session_state.audio_bytes, format="audio/mp3")
    st.download_button(
        label="📥 Descargar MP3 generado",
        data=st.session_state.audio_bytes,
        file_name=f"voz_{st.session_state.lang}.mp3",
        mime="audio/mpeg",
    )  