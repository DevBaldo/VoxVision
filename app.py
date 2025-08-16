# app.py
import streamlit as st
from io import BytesIO
import time
from gtts import gTTS
import pdfplumber
from groq import Groq
import os
import fitz
from PIL import Image
import pytesseract
from google import genai

# ---------------- CONFIGURACIÓN ---------------- #

# Configuración de Tesseract (ajusta la ruta según tu SO)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# API keys
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------- FUNCIONES ---------------- #

# -------------------------------
# Función: Detectar idioma con Groq
# -------------------------------
def detectar_idioma(texto: str) -> str:
    prompt = f"""
    Detecta el idioma de este texto y responde solo con el código ISO 639-1 (ej. 'en', 'es', 'fr', etc).
    Texto: \"{texto.strip()[:500]}\"
    """
    response = groq_client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=10,
        top_p=1,
        stream=False
    )
    idioma = response.choices[0].message.content.strip().lower()
    return idioma

# Extraer texto de PDF
def extraer_texto_pdf(file_bytes):
    texto = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ""
    return texto.strip()

# -------------------------------
# Función: Extraer imágenes de PDF
# -------------------------------
def extraer_imagenes(file_bytes):
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    imagenes = []
    for p in range(len(pdf)):
        page = pdf[p]
        for img in page.get_images(full=True):
            xref = img[0]
            base = pdf.extract_image(xref)
            imagenes.append({
                "page": p + 1,
                "bytes": base["image"],
                "ext": base["ext"]
            })
    return imagenes

# -------------------------------
# Función: Describir imagen con Gemini o fallback Tesseract
# -------------------------------
def describir_imagen(image_bytes, file_ext):
    try:
        # Guardar imagen temporal
        with open(f"temp.{file_ext}", "wb") as f:
            f.write(image_bytes)

        # Subir a Gemini Files API
        file_ref = genai_client.files.upload(file=f"temp.{file_ext}")

        # Solicitar descripción a Gemini
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_ref, "Con la menor cantidad de caracteres posibles, describe esta imagen de forma accesible. El texto sera leido por gTTs, hazlo compatible"]
        )

        return response.text.strip()

    except Exception as e:
        st.warning(f"⚠️ Gemini falló, usando OCR Tesseract. Error: {e}")
        try:
            img = Image.open(BytesIO(image_bytes))
            text = pytesseract.image_to_string(img, lang="spa+eng")
            return text if text.strip() else "[No se pudo extraer texto con OCR]"
        except Exception as e2:
            st.error(f"Error también en Tesseract: {e2}")
            return ""

# Convertir texto a voz
def texto_a_voz(texto, idioma):
    tts = gTTS(text=texto, lang=idioma)
    temp = BytesIO()
    tts.write_to_fp(temp)
    temp.seek(0)
    return temp

# -------------------------------
# Interfaz Streamlit
# -------------------------------
st.set_page_config(page_title="VoxVision")
st.title("🧠 VoxVision: PDF o Texto ➜ Voz Accesible")

# Subida de archivo
uploaded = st.file_uploader("📄 Sube tu archivo PDF o TXT", type=["pdf", "txt"])

if uploaded:
    uploaded_bytes = uploaded.getvalue()
    text = ""
    descripciones = []

    # Caso TXT
    if uploaded.type == "text/plain":
        text = uploaded_bytes.decode("utf-8")

    # Caso PDF
    else:
        with pdfplumber.open(BytesIO(uploaded_bytes)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        # Extraer imágenes
        imagenes = extraer_imagenes(uploaded_bytes)
        if imagenes:
            with st.spinner("🔎 Analizando imágenes del PDF..."):
                for i, img in enumerate(imagenes):
                    desc = describir_imagen(img["bytes"], img["ext"])
                    if desc:
                        # Almacenamos la imagen y la descripción juntas
                        descripciones.append((img, desc))
                    else:
                        st.warning(f"⚠️ No se pudo describir la imagen en la página {img['page']}")

        # Mostrar las imágenes y descripciones con un expander si hay más de una
        if descripciones:
            if len(descripciones) > 1:
                with st.expander("🖼️ Ver descripciones e imágenes"):
                    # Iteramos sobre la lista que contiene la imagen y la descripción
                    for img_data, desc in descripciones:
                        st.image(img_data["bytes"], caption=f"📷 Imagen página {img_data['page']}", use_container_width=True)
                        st.write(f"📝 Descripción accesible: {desc}")
            else:
                img_data, desc = descripciones[0]
                st.image(img_data["bytes"], caption=f"📷 Imagen página {img_data['page']}", use_container_width=True)
                st.write(f"📝 Descripción accesible: {desc}")

    # Texto final con descripciones
    texto_completo = text + "\n\n" + "\n\n".join(
    f"Descripción imagen página {d[0]['page']}: {d[1]}" for d in descripciones
)

    # Mostrar texto extraído
    st.text_area("📝 Texto extraído", value=texto_completo, height=300)

    # Convertir a voz
    if st.button("🗣️ Convertir a voz"):
        if not texto_completo.strip():
            st.warning("⚠️ No hay texto para convertir.")
        else:
            with st.spinner("🌐 Detectando idioma..."):
                lang = detectar_idioma(texto_completo)
                if lang not in ["en", "es", "de", "fr", "it", "pt"]:
                    st.warning(f"Idioma detectado: {lang}. Puede que no esté soportado por gTTS.")
                else:
                    st.success(f"🌐 Idioma detectado: {lang}")

            with st.spinner("🎙️ Generando audio..."):
                tts = gTTS(text=texto_completo, lang=lang)
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