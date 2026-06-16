<div align="center">

# 🎙️ VoxVision

### *Convierte documentos e imágenes en voz, al instante.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/Groq_API-Compound_Beta-F55036?style=for-the-badge)](https://groq.com/)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

**VoxVision** es una aplicación web diseñada para ayudar a personas con **discapacidad visual** a acceder a documentos, textos e imágenes de forma comprensible, convirtiendo su contenido a audio de manera automática.


</div>

---

##  ¿Qué hace VoxVision?

Sube un archivo, presiona un botón y escucha su contenido. Así de simple.

| Tipo de archivo | ¿Qué hace VoxVision? |
|---|---|
| 📄 **PDF** | Extrae el texto de todas las páginas y describe cada imagen que encuentre |
| 🖼️ **Imagen** (PNG/JPG) | Usa IA para generar una descripción accesible del contenido visual |
| 📝 **TXT** | Lee y convierte el texto directamente a audio |

Todo el contenido procesado se convierte a **audio MP3 descargable**, detectando automáticamente el idioma del documento.

---

##  Funcionalidades

- 📖 **Extracción de texto de PDFs** – compatibilidad con documentos complejos usando `pdfplumber`
- 🖼️ **Descripción de imágenes con IA** – Google Gemini 2.5 Flash describe el contenido visual de forma accesible
- 🔄 **Fallback inteligente a OCR** – si Gemini falla, Tesseract OCR extrae el texto de la imagen automáticamente
- 🌐 **Detección de idioma automática** – Groq (compound-beta) identifica el idioma del documento
- 🔊 **Síntesis de voz natural** – `gTTS` genera audio en el idioma detectado (ES, EN, DE, FR, IT, PT)
- 💾 **Descarga del audio generado** – exporta el resultado como `.mp3`

---

## 🛠️ Stack tecnológico

| Categoría | Tecnología |
|---|---|
| **Interfaz web** | [Streamlit](https://streamlit.io/) |
| **Extracción de PDF** | [pdfplumber](https://github.com/jsvine/pdfplumber) + [PyMuPDF](https://pymupdf.readthedocs.io/) |
| **Descripción de imágenes** | [Google Gemini 2.5 Flash](https://ai.google.dev/) |
| **OCR (fallback)** | [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via [pytesseract](https://github.com/madmaze/pytesseract) |
| **Detección de idioma** | [Groq API](https://groq.com/) (compound-beta) |
| **Síntesis de voz** | [gTTS (Google Text-to-Speech)](https://gtts.readthedocs.io/) |
| **Procesamiento de imágenes** | [Pillow](https://pillow.readthedocs.io/) |

---

##  Instalación y configuración

### Requisitos previos

- Python 3.10 o superior
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract#installing-tesseract) instalado en el sistema
- Claves de API de [Groq](https://console.groq.com/) y [Google Gemini](https://ai.google.dev/)

### 1. Clonar el repositorio

```bash
git clone https://github.com/DevBaldo/VoxVision.git
cd VoxVision
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Configurar las credenciales (Streamlit Secrets)

Copia el archivo de ejemplo y rellena tus claves de API:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

```toml
GROQ_API_KEY = "tu_clave_groq_aqui"
GEMINI_API_KEY = "tu_clave_gemini_aqui"
```

> **Nota:** Para despliegues en Streamlit Cloud, añade estas claves directamente en **Settings → Secrets**.

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

Abre [http://localhost:8501](http://localhost:8501) en tu navegador.

---

##  Estructura del proyecto

```
VoxVision/
├── app.py              # Aplicación principal (lógica + interfaz Streamlit)
├── requirements.txt    # Dependencias del proyecto
├── .env.example        # Plantilla de variables de entorno
├── .gitignore
└── README.md
```

---

##  Variables de entorno

| Variable | Descripción | Dónde obtenerla |
|---|---|---|
| `GROQ_API_KEY` | Clave de la API de Groq (detección de idioma) | [console.groq.com](https://console.groq.com/) |
| `GEMINI_API_KEY` | Clave de la API de Google Gemini (descripción de imágenes) | [ai.google.dev](https://ai.google.dev/) |

---

##  Flujo de la aplicación

```
Archivo subido (PDF / TXT / Imagen)
        │
        ▼
┌───────────────────────────────────────┐
│  Extracción de contenido              │
│  ├── PDF:    texto + imágenes         │
│  ├── TXT:    texto directo            │
│  └── Imagen: descripción IA (Gemini)  │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Detección de idioma (Groq)           │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Síntesis de voz (gTTS)               │
│  → Audio MP3 reproducible y           │
│    descargable                        │
└───────────────────────────────────────┘
```


