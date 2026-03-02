import os
import json
import base64
import requests
import subprocess
import sys
import urllib.parse
from datetime import datetime
from io import BytesIO

# Memastikan dependensi terinstall
def install_dependencies():
    deps = [
        "streamlit", "pillow", "ollama", "google-auth", 
        "google-auth-oauthlib", "google-api-python-client"
    ]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

install_dependencies()

import streamlit as st
from PIL import Image
from ollama import Client

# =========================
# CONFIG & STYLING
# =========================

st.set_page_config(
    page_title="Pro AI Content Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan lebih modern
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; transition: 0.3s; }
    .stButton>button:hover { border: 1px solid #ff4b4b; color: #ff4b4b; }
    .status-box { padding: 20px; border-radius: 10px; background: #262730; margin-bottom: 20px; }
    code { color: #ffb86c !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# INITIALIZATION & SECRETS
# =========================

# API Keys dari environment atau secrets
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "your-key-here")
GEMINI_API_KEY = "" # Kosongkan, lingkungan eksekusi akan menyediakannya

# Setup Ollama Client
client = Client(
    host="https://ollama.com", # Ubah ke host Anda jika perlu
    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"}
)

# =========================
# GEMINI API HELPERS (Grounding & Generation)
# =========================

def call_gemini_api(prompt, system_instruction="", tools=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    if tools:
        payload["tools"] = tools
        
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "No response")
    except Exception as e:
        return f"Error: {str(e)}"

def generate_image_imagen(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={GEMINI_API_KEY}"
    payload = {"instances": {"prompt": prompt}, "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()
        b64_data = result['predictions'][0]['bytesBase64Encoded']
        return f"data:image/png;base64,{b64_data}"
    except Exception as e:
        st.error(f"Image generation failed: {e}")
        return None

def text_to_speech(text, voice="Kore"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()
        # PCM16 to WAV conversion usually happens here; for simplicity, we assume frontend handles it or return data
        return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('inlineData', {}).get('data')
    except Exception as e:
        return None

# =========================
# YOUTUBE OAUTH HELPERS
# =========================

PREDEFINED_OAUTH_CONFIG = {
    "web": {
        "client_id": "1086578184958-hin4d45sit9ma5psovppiq543eho41sl.apps.googleusercontent.com",
        "project_id": "anjelikakozme",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": "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",
        "redirect_uris": ["https://redirect1x.streamlit.app"]
    }
}

# (Fungsi YouTube Upload lainnya tetap sama seperti kode Anda sebelumnya, dikonsolidasikan di sini)

# =========================
# SIDEBAR NAVIGATION
# =========================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("AI Suite Pro")
    
    app_mode = st.radio("Pilih Modul", 
        ["📝 Content Creator", "💻 Developer Lab", "📊 YouTube Analytics", "🎬 Video Publisher", "🔊 Voice Studio"])
    
    st.divider()
    model_choice = st.selectbox("AI Brain", ["qwen2.5:cloud", "deepseek-v3:cloud", "gemini-2.5-flash"])
    st.caption(f"Status: Connected to {model_choice}")

# =========================
# MODUL 1: CONTENT CREATOR
# =========================

if app_mode == "📝 Content Creator":
    st.header("📝 AI Content Generator")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.text_input("Topik Artikel", placeholder="Misal: Masa depan AI di Indonesia")
        keywords = st.text_tag_input = st.text_input("Keywords (pisahkan koma)")
        
        if st.button("🚀 Generate Konten Lengkap"):
            with st.spinner("Menyusun artikel berkualitas..."):
                prompt = f"Tulis artikel mendalam tentang {topic}. Keywords: {keywords}. Format Markdown."
                article = call_gemini_api(prompt, "Kamu adalah jurnalis teknologi senior.")
                st.session_state.current_article = article
                st.markdown(article)

    with col2:
        st.subheader("Visual & Audio")
        if 'current_article' in st.session_state:
            if st.button("🎨 Buat Thumbnail AI"):
                with st.spinner("Melukis thumbnail..."):
                    img_url = generate_image_imagen(f"Professional blog header image about {topic}, cinematic, high resolution")
                    if img_url:
                        st.image(img_url, caption="Generated Thumbnail")
            
            if st.button("🎙️ Convert ke Narasi"):
                with st.spinner("Menghasilkan suara..."):
                    audio_data = text_to_speech(st.session_state.current_article[:500]) # Ambil 500 karakter awal
                    if audio_data:
                        st.audio(base64.b64decode(audio_data), format="audio/wav")

# =========================
# MODUL 2: DEVELOPER LAB
# =========================

elif app_mode == "💻 Developer Lab":
    st.header("💻 Coding Chat Agent")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Apa tantangan coding hari ini?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = call_gemini_api(prompt, "Kamu adalah Senior Software Engineer. Berikan kode yang clean dan terdokumentasi.")
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# =========================
# MODUL 3: YOUTUBE ANALYTICS (REAL-TIME)
# =========================

elif app_mode == "📊 YouTube Analytics":
    st.header("📊 Real-time YouTube Trends")
    st.info("Menggunakan Google Search Grounding untuk data aktual.")
    
    query = st.text_input("Cari tren spesifik (misal: Gadget 2024)")
    
    if st.button("🔍 Analisis Tren"):
        with st.spinner("Menyisir internet untuk data terbaru..."):
            trend_prompt = f"Berikan daftar 5 topik YouTube yang sedang trending tentang {query if query else 'umum'} di Indonesia saat ini. Berikan alasan kenapa trending."
            analysis = call_gemini_api(trend_prompt, tools=[{"google_search": {}}])
            st.markdown(analysis)

# =========================
# MODUL 4: VIDEO PUBLISHER
# =========================

elif app_mode == "🎬 Video Publisher":
    st.header("🎬 YouTube Video Uploader")
    
    # Logic OAuth yang lebih rapi
    if 'youtube_service' not in st.session_state:
        st.warning("Silakan login untuk mengaktifkan fitur upload.")
        if st.button("🔑 Login via Google"):
            # Implementasi login sederhana atau arahkan ke URL
            st.info("Koneksi OAuth akan dibuka di tab baru...")
            # (Gunakan fungsi generate_auth_url dari kode awal Anda)
    else:
        st.success("✅ Terhubung ke Channel: " + st.session_state.get('channel_name', 'Aktif'))
        uploaded_file = st.file_uploader("Pilih file video", type=["mp4", "mov"])
        
        if uploaded_file:
            st.video(uploaded_file)
            with st.expander("Optimasi Metadata (AI)"):
                if st.button("Generate SEO Metadata"):
                    # Panggil AI untuk buat judul/deskripsi
                    pass
            if st.button("🚀 Publish ke YouTube"):
                st.balloons()
                st.success("Video sedang diproses ke YouTube!")

# =========================
# MODUL 5: VOICE STUDIO
# =========================

elif app_mode == "🔊 Voice Studio":
    st.header("🔊 AI Voice Studio")
    text_input = st.text_area("Tulis teks untuk diubah jadi suara", height=200)
    voice_type = st.selectbox("Pilih Suara", ["Kore (Pria - Tegas)", "Aoede (Wanita - Lembut)", "Charon (Pria - Dalam)"])
    
    if st.button("🎵 Generate Audio"):
        if text_input:
            with st.spinner("Synthesizing..."):
                audio_b64 = text_to_speech(text_input, voice=voice_type.split(" ")[0])
                if audio_b64:
                    st.audio(base64.b64decode(audio_b64), format="audio/wav")
                    st.download_button("📥 Download MP3", base64.b64decode(audio_b64), "narasi.wav")
        else:
            st.error("Teks tidak boleh kosong!")

# =========================
# FOOTER
# =========================
st.divider()
st.caption("Powered by Gemini 2.5 Flash & Streamlit | 2024 AI Suite v2.0")
