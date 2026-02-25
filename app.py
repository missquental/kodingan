import os
import streamlit as st
import base64
from io import BytesIO
from datetime import datetime
from PIL import Image
from ollama import Client

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="AI Content & Coding Suite",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 AI Content & Coding Suite (Ollama Cloud)")

# =========================
# API KEY
# =========================

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

if not OLLAMA_API_KEY:
    st.error("⚠️ OLLAMA_API_KEY belum diset di Streamlit Secrets")
    st.stop()

# =========================
# CLIENT CLOUD
# =========================

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + OLLAMA_API_KEY}
)

# =========================
# SIDEBAR
# =========================

st.sidebar.header("⚙️ Pengaturan Artikel")

model_name = st.sidebar.selectbox(
    "Model Artikel",
    [
        "qwen3.5:cloud",
        "glm-5:cloud",
        "deepseek-v3.2:cloud",
        "mistral-large-3:675b-cloud",
        "gpt-oss",
        "gemma3"
    ]
)

article_length = st.sidebar.selectbox(
    "Panjang Artikel",
    ["500 kata", "1000 kata", "2000 kata"]
)

tone = st.sidebar.selectbox(
    "Gaya",
    ["Formal", "Santai", "SEO Friendly", "Storytelling"]
)

# =========================
# TABS
# =========================

tabs = st.tabs([
    "📝 Artikel",
    "💻 Coding Agent",
    "📺 Trending YouTube (via Ollama)"
])

# =========================
# TAB ARTIKEL
# =========================

with tabs[0]:
    st.subheader("📝 Generator Artikel")

    title = st.text_input("Judul Artikel")
    keywords = st.text_input("Keyword")

    if st.button("🚀 Generate Artikel") and title:

        prompt = f"""
        Buat artikel {article_length}, gaya {tone}.
        Judul: {title}
        Keyword: {keywords}

        Struktur:
        - Pendahuluan
        - Subjudul H2 & H3
        - Isi informatif
        - Kesimpulan
        """

        messages = [{"role": "user", "content": prompt}]

        container = st.empty()
        full_text = ""

        for part in client.chat(model=model_name, messages=messages, stream=True):
            if part.message.content:
                full_text += part.message.content
                container.markdown(full_text)

        st.download_button(
            "📥 Download Artikel",
            full_text,
            file_name=f"artikel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

# =========================
# TAB CODING CHAT AGENT (WITH MEMORY)
# =========================

with tabs[1]:
    st.subheader("💻 Coding Chat Agent (Revisi Mode)")

    coding_model = st.selectbox(
        "Model Coding",
        [
            "qwen3-coder-next",
            "qwen3-coder",
            "devstral-2",
            "deepseek-v3.1",
            "glm-5:cloud",
            "gpt-oss"
        ],
        key="coding_model"
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": """
                Kamu adalah Senior Software Engineer dan AI Coding Assistant.
                Jawab profesional.
                Jika membuat code:
                - Berikan code lengkap
                - Gunakan best practice
                - Tambahkan komentar
                """
            }
        ]

    for msg in st.session_state.chat_history[1:]:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

    user_input = st.chat_input("Tulis instruksi / revisi code...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.chat_message("user").markdown(user_input)

        response_container = st.chat_message("assistant")
        full_response = ""

        with response_container:
            placeholder = st.empty()
            for part in client.chat(model=coding_model, messages=st.session_state.chat_history, stream=True):
                if part.message.content:
                    full_response += part.message.content
                    placeholder.markdown(full_response)

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    if st.button("🔄 Reset Chat"):
        st.session_state.chat_history = [st.session_state.chat_history[0]]
        st.success("Chat berhasil direset")

# =========================
# TAB YOUTUBE TRENDING VIA OLLAMA
# =========================

with tabs[2]:
    st.subheader("📺 Rekomendasi Video Populer via Ollama")

    st.info("💡 Masukkan info seperti negara dan topik untuk mendapatkan rekomendasi video populer.")

    country_ollama = st.selectbox("🌍 Negara", ["Indonesia", "Amerika Serikat", "India", "Inggris"], index=0)
    topic = st.text_input("🏷️ Topik (Opsional)", placeholder="Misal: Teknologi, Musik, Hiburan...")
    num_recommendations = st.slider("🔢 Jumlah Rekomendasi", min_value=3, max_value=20, value=5)

    if st.button("🔍 Dapatkan Rekomendasi"):
        with st.spinner("Meminta rekomendasi dari AI..."):
            system_prompt = (
                "Kamu adalah asisten AI yang ahli dalam budaya digital dan media sosial. "
                "Berikutnya kamu akan diminta memberikan rekomendasi video YouTube yang sedang populer "
                "di suatu negara dan/atau topik tertentu."
            )

            user_prompt = (
                f"Saat ini, berikan saya daftar {num_recommendations} video YouTube yang sedang populer "
                f"di negara {country_ollama}."
            )
            if topic.strip():
                user_prompt += f" Fokus pada topik '{topic}'."

            user_prompt += "\n\nFormat balasan:\n1. Judul Video - Channel\n2. Judul Video - Channel\n..."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response_container = st.empty()
            full_response = ""

            try:
                for part in client.chat(model=model_name, messages=messages, stream=True):
                    if part.message.content:
                        full_response += part.message.content
                        response_container.markdown(full_response)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat menghubungi Ollama: {str(e)}")
