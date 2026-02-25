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

tab1, tab2, tab3 = st.tabs([
    "📝 Artikel",
    "🎨 Image",
    "💻 Coding Agent"
])

# =========================
# TAB ARTIKEL
# =========================

with tab1:

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
# TAB IMAGE
# =========================

with tab2:

    st.subheader("🎨 AI Image Generator")

    image_prompt = st.text_area("Prompt Gambar", "a sunset over mountains")

    image_model = st.selectbox(
        "Model Image",
        ["x/z-image-turbo"]
    )

    if st.button("🖼 Generate Image"):

        messages = [{"role": "user", "content": image_prompt}]
        final_image = None

        for part in client.chat(
            model=image_model,
            messages=messages,
            stream=True
        ):
            if part.get("message") and part["message"].get("images"):
                final_image = part["message"]["images"][0]

        if final_image:
            image_bytes = base64.b64decode(final_image)
            image = Image.open(BytesIO(image_bytes))
            st.image(image, use_column_width=True)

            st.download_button(
                "📥 Download Image",
                image_bytes,
                file_name="generated.png",
                mime="image/png"
            )
        else:
            st.error("❌ Gambar tidak dihasilkan")

# =========================
# TAB CODING CHAT AGENT (WITH MEMORY)
# =========================

with tab3:

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

    # =========================
    # SESSION MEMORY
    # =========================

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

    # =========================
    # TAMPILKAN CHAT HISTORY
    # =========================

    for msg in st.session_state.chat_history[1:]:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

    # =========================
    # INPUT CHAT
    # =========================

    user_input = st.chat_input("Tulis instruksi / revisi code...")

    if user_input:

        # Tambahkan pesan user ke memory
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )

        st.chat_message("user").markdown(user_input)

        # Streaming response
        response_container = st.chat_message("assistant")
        full_response = ""

        with response_container:
            placeholder = st.empty()

            for part in client.chat(
                model=coding_model,
                messages=st.session_state.chat_history,
                stream=True
            ):
                if part.message.content:
                    full_response += part.message.content
                    placeholder.markdown(full_response)

        # Simpan jawaban ke memory
        st.session_state.chat_history.append(
            {"role": "assistant", "content": full_response}
        )

    # =========================
    # RESET BUTTON
    # =========================

    if st.button("🔄 Reset Chat"):
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
        st.success("Chat berhasil direset")
