# app.py
import streamlit as st
from io import BytesIO
import time
from gtts import gTTS
import pdfplumber
from groq import Groq
import os
import fitz
import base64
import requests
from PIL import Image

# API key
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
AIK_API_KEY = st.secrets.get("AIKEYWORDING_API_KEY") or os.getenv("AIKEYWORDING_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Detectar idioma automáticament API
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

# Detectar imágenes
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

def describir_imagen_api(image_bytes, api_key):
    try:
        # Step 1: Pre-process the image
        img = Image.open(BytesIO(image_bytes))
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG")
        processed_image_bytes = output_buffer.getvalue()

        # Step 2: Request a signed URL from the API
        signed_url_payload = {
            "filename": "img.jpg"
        }
        res_signed_url = requests.post(
            "https://aikeywording.com/api/customer-api/signed-url", # <<< Replace with the correct endpoint
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json=signed_url_payload
        )
        res_signed_url.raise_for_status()
        signed_url_data = res_signed_url.json()
        signed_url = signed_url_data.get("signedUrl")
        public_url = signed_url_data.get("publicUrl")

        if not signed_url or not public_url:
            st.error("Error: No se pudo obtener la URL firmada de la API.")
            return ""

        # Step 3: Upload the image to the signed URL using a PUT request
        headers = {'Content-Type': 'image/jpeg'}
        upload_response = requests.put(signed_url, data=processed_image_bytes, headers=headers)
        upload_response.raise_for_status()

        # Step 4: Submit the job with the public URL
        payload = {
            "modelVersion": "v1",
            "imagesUrls": [public_url],
            "options": {
                "enforcedKeywords": [],
                "excludedKeywords": [],
                "maxKeywords": 10,
                "excludeMultiWordKeywords": False,
                "maxTitleCharacterLength": 40,
                "maxDescriptionCharacterLength": 200,
                "titleCasing": "sentence case",
                "descriptionStyle": "default"
            }
        }
        res_job = requests.post(
            "https://aikeywording.com/api/customer-api/keyword",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json=payload
        )
        res_job.raise_for_status()
        data = res_job.json()
        job_id = data.get("jobId")

        if not job_id:
            st.error("Error: No se pudo obtener el ID del trabajo.")
            return ""

        # Step 5: Poll for results
        with st.spinner(f"Generando descripción para la imagen... (Job ID: {job_id})"):
            max_retries = 10
            for i in range(max_retries):
                time.sleep(2)
                get_url = f"https://aikeywording.com/api/customer-api/keyword/{job_id}"
                get_res = requests.get(get_url, headers={"X-API-KEY": api_key})
                
                if get_res.status_code == 200:
                    get_data = get_res.json()
                    description = get_data.get("description", "")
                    if description:
                        return description
                
                st.info(f"Intento {i + 1}/{max_retries}: Esperando la descripción...")

        st.warning("No se pudo obtener la descripción de la imagen después de varios intentos.")
        return ""

    except requests.exceptions.HTTPError as http_err:
        st.warning(f"Error de API: {http_err} - Comprueba tu clave de API y el formato de la imagen.")
        return ""
    except Exception as e:
        st.warning(f"Se omitió una imagen debido a un error: {e}")
        return ""

# Interfaz
st.set_page_config(page_title="VoxVision")
st.title("🧠 VoxVision: PDF o Texto ➜ Voz Accesible")

# Subida de archivo
uploaded = st.file_uploader("📄 Sube tu archivo PDF o TXT", type=["pdf", "txt"])
if uploaded:
    uploaded_bytes = uploaded.getvalue()
    text = ""
    descripciones = []
    
    if uploaded.type == "text/plain":
        text = uploaded_bytes.decode("utf-8")
    else:
        with pdfplumber.open(BytesIO(uploaded_bytes)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        imagenes = extraer_imagenes(uploaded_bytes)
        with st.spinner("Analizando imágenes del PDF..."):
            for img in imagenes:
                desc = describir_imagen_api(img["bytes"], AIK_API_KEY)
                
                if desc:
                    descripciones.append((img["page"], desc))
                    st.image(img["bytes"], caption=f"Imagen página {img['page']}", use_column_width=True)
                    st.write(f"📝 Descripción para no videntes: {desc}")
                else:
                    st.warning(f"Se omitió una imagen en la página {img['page']} debido a un error.")

    st.text_area("📝 Texto extraído", value=text, height=300)

    texto_completo = text + "\n\n" + "\n\n".join(
        f"Descripción imagen página {p}: {d}" for p, d in descripciones
    )

    # Convertir a voz
    if st.button("🗣️ Convertir a voz"):
        if not texto_completo.strip():
            st.warning("No hay texto para convertir.")
        else:
            with st.spinner("🔎 Detectando idioma..."):
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