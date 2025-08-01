# app.py
import streamlit as st
from io import BytesIO
from gtts import gTTS
import tempfile
import pdfplumber
from groq import Groq
import os

# Interfaz #
st.set_page_config(page_title="VoxVision")
st.title("🧠 VoxVision: PDF o Texto ➜ Voz Accesible")

uploaded = st.file_uploader("Sube tu archivo PDF o .txt", type=["pdf","txt"])
if uploaded:
    text = ""
    if uploaded.type == "text/plain":
        text = uploaded.read().decode("utf-8")
    else:
        # PDF
        with pdfplumber.open(uploaded) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    st.text_area("Texto extraído", value=text, height=300)

    lang = st.selectbox("Idioma de salida", options=["es", "en", "de"], index=0)
    if st.button("Convertir a voz"):
        if not text.strip():
            st.warning("No hay texto para convertir.")
        else:
            tts = gTTS(text=text, lang=lang)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            st.audio(fp.read(), format="audio/mp3")

            # guardar opcionalmente
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.write_to_fp(tmp)
            tmp.flush()
            st.markdown(f"Descarga: 📥 [MP3 generado]({tmp.name})")
