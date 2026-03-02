import os
import streamlit as st
import base64
from io import BytesIO
from datetime import datetime
from PIL import Image
from ollama import Client
import sys
import subprocess
import json
import urllib.parse
import requests

# =========================
# INSTALL DEPENDENCIES
# =========================

try:
    import google.auth
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import Flow
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth", "google-auth-oauthlib", "google-api-python-client"])
    import google.auth
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import Flow

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
# YOUTUBE AUTH CONFIG
# =========================

PREDEFINED_OAUTH_CONFIG = {
    "web": {
        "client_id": "1086578184958-hin4d45sit9ma5psovppiq543eho41sl.apps.googleusercontent.com",
        "project_id": "anjelikakozme",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["https://redirect1x.streamlit.app"]
    }
}

# =========================
# YOUTUBE FUNCTIONS
# =========================

def generate_auth_url(client_config):
    """Generate OAuth authorization URL"""
    try:
        scopes = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
        
        # Create authorization URL
        auth_url = (
            f"{client_config['auth_uri']}?"
            f"client_id={client_config['client_id']}&"
            f"redirect_uri={urllib.parse.quote(client_config['redirect_uris'][0])}&"
            f"scope={urllib.parse.quote(' '.join(scopes))}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return auth_url
    except Exception as e:
        st.error(f"Error generating auth URL: {e}")
        return None

def exchange_code_for_tokens(client_config, auth_code):
    """Exchange authorization code for access and refresh tokens"""
    try:
        token_data = {
            'client_id': client_config['client_id'],
            'client_secret': client_config['client_secret'],
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': client_config['redirect_uris'][0]
        }
        
        response = requests.post(client_config['token_uri'], data=token_data)
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens
        else:
            st.error(f"Token exchange failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error exchanging code for tokens: {e}")
        return None

def create_youtube_service(credentials_dict):
    """Create YouTube API service from credentials"""
    try:
        if 'token' in credentials_dict:
            credentials = Credentials.from_authorized_user_info(credentials_dict)
        else:
            credentials = Credentials(
                token=credentials_dict.get('access_token'),
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=credentials_dict.get('client_id'),
                client_secret=credentials_dict.get('client_secret'),
                scopes=['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
            )
        service = build('youtube', 'v3', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Error creating YouTube service: {e}")
        return None

def get_channel_info(service):
    """Get channel information from YouTube API"""
    try:
        request = service.channels().list(
            part="snippet,statistics",
            mine=True
        )
        response = request.execute()
        return response.get('items', [])
    except Exception as e:
        st.error(f"Error fetching channel info: {e}")
        return []

def upload_video_to_youtube(service, video_path, title, description, tags, category_id, privacy_status, made_for_kids):
    """Upload video to YouTube"""
    try:
        # Define video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids
            }
        }

        # Call the API's videos.insert method to create and upload the video
        insert_request = service.videos().insert(
            part='snippet,status',
            body=body,
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )

        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    st.progress(progress, text=f"Uploading... {progress}%")
            except Exception as e:
                error = e
                if retry > 3:
                    raise e
                retry += 1
                st.warning(f"Retrying upload... Attempt {retry}")
        
        if 'id' in response:
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return video_id, video_url
        else:
            st.error("Failed to upload video")
            return None, None
            
    except Exception as e:
        st.error(f"Error uploading video: {e}")
        return None, None

def get_youtube_categories():
    """Get YouTube video categories"""
    return {
        "1": "Film & Animation",
        "2": "Autos & Vehicles", 
        "10": "Music",
        "15": "Pets & Animals",
        "17": "Sports",
        "19": "Travel & Events",
        "20": "Gaming",
        "22": "People & Blogs",
        "23": "Comedy",
        "24": "Entertainment",
        "25": "News & Politics",
        "26": "Howto & Style",
        "27": "Education",
        "28": "Science & Technology"
    }

def generate_video_metadata_with_ai(keywords, model_name):
    """Generate video title, description, and hashtags using AI based on keywords"""
    try:
        prompt = f"""
        Berdasarkan keyword: "{keywords}"
        Buatlah:
        1. Judul video yang menarik dan SEO-friendly (maks 100 karakter)
        2. Deskripsi video yang informatif dan engaging (200-300 kata)
        3. 5 hashtag yang relevan dan populer untuk meningkatkan reach
        
        Format jawaban:
        JUDUL: [judul video]
        DESKRIPSI: [deskripsi video]
        HASHTAG: [hashtag1, hashtag2, hashtag3, hashtag4, hashtag5]
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        full_response = ""
        for part in client.chat(model=model_name, messages=messages, stream=True):
            if part.message.content:
                full_response += part.message.content
        
        # Parse response
        lines = full_response.strip().split('\n')
        title = ""
        description = ""
        hashtags = []
        
        for line in lines:
            if line.startswith("JUDUL:"):
                title = line.replace("JUDUL:", "").strip()
            elif line.startswith("DESKRIPSI:"):
                description = line.replace("DESKRIPSI:", "").strip()
            elif line.startswith("HASHTAG:"):
                hashtags_str = line.replace("HASHTAG:", "").strip()
                hashtags = [tag.strip() for tag in hashtags_str.strip("[]").split(",")]
        
        return title, description, hashtags
    except Exception as e:
        st.error(f"Error generating metadata with AI: {e}")
        return "", "", []

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
    "📺 Trending YouTube (via Ollama)",
    "📤 Upload YouTube"
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

# =========================
# TAB UPLOAD YOUTUBE
# =========================

with tabs[3]:
    st.subheader("📤 Upload Video ke YouTube")

    # OAuth Section
    st.markdown("### 🔐 Autentikasi YouTube")
    
    # Predefined Auth Button
    if st.button("🔑 Gunakan Konfigurasi OAuth Bawaan"):
        st.session_state['oauth_config'] = PREDEFINED_OAUTH_CONFIG['web']
        st.success("✅ Konfigurasi OAuth bawaan dimuat!")
        st.rerun()
    
    # Manual OAuth Config Upload
    st.markdown("### 📁 Atau Upload Konfigurasi OAuth")
    oauth_json = st.file_uploader("Upload file JSON OAuth", type=['json'])
    
    if oauth_json:
        try:
            config = json.load(oauth_json)
            if 'web' in config:
                st.session_state['oauth_config'] = config['web']
                st.success("✅ Konfigurasi OAuth dimuat dari file!")
                st.rerun()
            else:
                st.error("❌ Format file JSON tidak valid!")
        except Exception as e:
            st.error(f"❌ Error membaca file: {e}")
    
    # Authorization Process
    if 'oauth_config' in st.session_state:
        oauth_config = st.session_state['oauth_config']
        
        # Generate authorization URL
        auth_url = generate_auth_url(oauth_config)
        if auth_url:
            st.markdown("### 🔗 Link Autorisasi")
            st.markdown(f"[Klik di sini untuk autorisasi]({auth_url})")
            
            # Instructions
            with st.expander("💡 Petunjuk Autorisasi"):
                st.write("1. Klik link autorisasi di atas")
                st.write("2. Login ke akun YouTube Anda")
                st.write("3. Berikan akses yang diperlukan")
                st.write("4. Salin kode autorisasi dari URL")
            
            # Manual authorization code input
            st.markdown("### 🔑 Masukkan Kode Autorisasi")
            auth_code = st.text_input("Kode Autorisasi", type="password", 
                                    placeholder="Paste kode autorisasi di sini...")
            
            if st.button("🔄 Tukar Kode dengan Token"):
                if auth_code:
                    with st.spinner("Menukar kode dengan token..."):
                        tokens = exchange_code_for_tokens(oauth_config, auth_code)
                        if tokens:
                            st.success("✅ Token berhasil didapat!")
                            st.session_state['youtube_tokens'] = tokens
                            
                            # Create credentials for YouTube service
                            creds_dict = {
                                'access_token': tokens['access_token'],
                                'refresh_token': tokens.get('refresh_token'),
                                'token_uri': oauth_config['token_uri'],
                                'client_id': oauth_config['client_id'],
                                'client_secret': oauth_config['client_secret']
                            }
                            
                            # Test the connection
                            service = create_youtube_service(creds_dict)
                            if service:
                                channels = get_channel_info(service)
                                if channels:
                                    channel = channels[0]
                                    st.session_state['youtube_service'] = service
                                    st.session_state['channel_info'] = channel
                                    st.success(f"🎉 Terhubung ke: {channel['snippet']['title']}")
                                    st.rerun()
                                else:
                                    st.error("❌ Tidak dapat mengambil informasi channel")
                            else:
                                st.error("❌ Gagal membuat layanan YouTube")
                        else:
                            st.error("❌ Gagal menukar kode dengan token")
                else:
                    st.error("Silakan masukkan kode autorisasi")
    
    # Upload Section
    if 'youtube_service' in st.session_state:
        st.markdown("---")
        st.markdown("### 🎬 Upload Video")
        
        # Channel Info
        channel = st.session_state['channel_info']
        st.info(f"📺 Terhubung ke channel: **{channel['snippet']['title']}**")
        
        # Video Upload
        video_file = st.file_uploader("Pilih video untuk diupload", type=['mp4', '.mov', '.avi', '.flv'])
        
        if video_file:
            # Save uploaded file temporarily
            temp_video_path = f"temp_{video_file.name}"
            with open(temp_video_path, "wb") as f:
                f.write(video_file.getbuffer())
            
            st.success(f"✅ Video {video_file.name} siap diupload!")
            
            # AI Metadata Generation
            st.markdown("### 🤖 Generasi Metadata dengan AI")
            st.info("Masukkan keyword untuk menghasilkan judul, deskripsi, dan hashtag yang optimal")
            
            # Keyword Input
            keywords = st.text_input(".Keyword untuk Video", placeholder="Contoh: tutorial python, masak enak, review gadget")
            
            # AI Metadata Generation Button
            use_ai_metadata = False
            ai_title, ai_description, ai_hashtags = "", "", []
            
            if keywords:
                if st.button("🧠 Hasilkan Metadata dengan AI"):
                    with st.spinner("Menghasilkan metadata dengan AI berdasarkan keyword..."):
                        ai_title, ai_description, ai_hashtags = generate_video_metadata_with_ai(keywords, model_name)
                    
                    if ai_title and ai_description:
                        st.success("✅ Metadata berhasil dihasilkan dengan AI!")
                        use_ai_metadata = True
                    else:
                        st.warning("⚠️ Gagal menghasilkan metadata dengan AI")
            
            # Display AI Results if available
            if use_ai_metadata and ai_title:
                st.markdown("#### Hasil Generasi AI:")
                st.write(f"**Judul:** {ai_title}")
                st.write(f"**Deskripsi:** {ai_description}")
                st.write(f"**Hashtag:** {', '.join(ai_hashtags)}")
            
            # Video Details
            st.markdown("### 📝 Detail Video")
            
            # Title Input
            if use_ai_metadata and ai_title:
                video_title = st.text_input("Judul Video", value=ai_title)
            else:
                video_title = st.text_input("Judul Video", value=video_file.name.split('.')[0])
            
            # Description Input
            if use_ai_metadata and ai_description:
                video_description = st.text_area("Deskripsi Video", value=ai_description, height=150)
            else:
                video_description = st.text_area("Deskripsi Video", height=150)
            
            # Tags Input
            if use_ai_metadata and ai_hashtags:
                default_tags = ", ".join(ai_hashtags)
                tags_input = st.text_input("Tag (pisahkan dengan koma)", value=default_tags, placeholder="tag1, tag2, tag3")
            else:
                tags_input = st.text_input("Tag (pisahkan dengan koma)", placeholder="tag1, tag2, tag3")
            
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
            
            # Category
            categories = get_youtube_categories()
            category_names = list(categories.values())
            selected_category_name = st.selectbox("Kategori", category_names, index=category_names.index("Entertainment"))
            category_id = [k for k, v in categories.items() if v == selected_category_name][0]
            
            # Privacy Settings
            privacy_status = st.selectbox("Privasi", ["public", "unlisted", "private"], index=0)
            made_for_kids = st.checkbox("Dibuat untuk anak-anak", value=False)
            
            # Upload Button
            if st.button("🚀 Upload ke YouTube", type="primary"):
                if not video_title:
                    st.error("❌ Judul video harus diisi!")
                else:
                    with st.spinner("Mengupload video... Mohon tunggu, ini bisa memakan waktu beberapa menit."):
                        service = st.session_state['youtube_service']
                        video_id, video_url = upload_video_to_youtube(
                            service,
                            temp_video_path,
                            video_title,
                            video_description,
                            tags,
                            category_id,
                            privacy_status,
                            made_for_kids
                        )
                        
                        if video_id:
                            st.success("🎉 Video berhasil diupload!")
                            st.markdown(f"### 📺 Video Anda:")
                            st.markdown(f"[Lihat Video]({video_url})")
                            st.video(video_url)
                            
                            # Cleanup temp file
                            if os.path.exists(temp_video_path):
                                os.remove(temp_video_path)
                        else:
                            st.error("❌ Upload video gagal!")
                            # Cleanup temp file
                            if os.path.exists(temp_video_path):
                                os.remove(temp_video_path)
    else:
        st.info("🔐 Silakan autentikasi terlebih dahulu untuk mengupload video ke YouTube")
