import streamlit as st
import requests
import json
from datetime import datetime
import tempfile
import os

# Configuration
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]  # Read from Streamlit secrets
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/generate"
DAILY_LIMIT = 50
IMAGE_SIZES = ["256x256", "512x512", "1024x1024"]

# Initialize session state
def init_session_state():
    """Initialize session state variables for user tracking and image gallery."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'daily_requests' not in st.session_state:
        st.session_state.daily_requests = 0
    if 'last_request_date' not in st.session_state:
        st.session_state.last_request_date = datetime.now().date()
    if 'image_gallery' not in st.session_state:
        st.session_state.image_gallery = []

def reset_daily_counter():
    """Reset daily request counter if a new day has started."""
    today = datetime.now().date()
    if st.session_state.last_request_date != today:
        st.session_state.daily_requests = 0
        st.session_state.last_request_date = today

def check_request_limit():
    """Check if user has exceeded daily request limit."""
    reset_daily_counter()
    return st.session_state.daily_requests < DAILY_LIMIT

def generate_image(prompt, size="512x512"):
    """Generate image using Deep Seek API with error handling and request tracking."""
    if not check_request_limit():
        st.error(f"Daily limit of {DAILY_LIMIT} requests exceeded. Please try again tomorrow.")
        return None
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "size": size
    }
    
    try:
        with st.spinner("Generating image..."):
            response = requests.post(DEEPSEEK_API_URL, 
                                   headers=headers, 
                                   json=payload, 
                                   timeout=30)
            
            if response.status_code == 200:
                st.session_state.daily_requests += 1
                result = response.json()
                return result.get('data', {}).get('url')
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None

def add_to_gallery(image_url, prompt):
    """Add generated image to gallery, maintaining last 5 images."""
    gallery_item = {
        "url": image_url,
        "prompt": prompt,
        "timestamp": datetime.now().isoformat()
    }
    
    st.session_state.image_gallery.insert(0, gallery_item)
    if len(st.session_state.image_gallery) > 5:
        st.session_state.image_gallery = st.session_state.image_gallery[:5]

def display_image_with_download(image_url, prompt, key_suffix=""):
    """Display image with download button."""
    st.image(image_url, caption=f"Prompt: {prompt}", use_column_width=True)
    
    # Download button
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            st.download_button(
                label="📥 Download Image",
                data=response.content,
                file_name=f"generated_image_{key_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                key=f"download_{key_suffix}"
            )
    except Exception as e:
        st.error(f"Download error: {str(e)}")

def google_oauth_login():
    """Handle Google OAuth authentication (simplified implementation)."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Login with Google", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_email = "family@example.com"
            st.success("Successfully logged in!")
            st.rerun()

def main():
    """Main application function with UI layout and functionality."""
    st.set_page_config(
        page_title="Family Image Generator",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for theme colors
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f77b4, #d62728);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stButton > button {
            background-color: #1f77b4;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
        }
        .stButton > button:hover {
            background-color: #d62728;
        }
        .request-counter {
            background-color: #f0f0f0;
            padding: 0.5rem;
            border-radius: 5px;
            text-align: center;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header"><h1>🎨 Family Image Generator</h1><p>Convert text to amazing images!</p></div>', unsafe_allow_html=True)
    
    # Authentication section
    if not st.session_state.authenticated:
        st.markdown("### 🔐 Authentication")
        st.info("Login is optional but helps track your daily usage.")
        google_oauth_login()
        st.markdown("---")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"Welcome back! 👋 ({st.session_state.user_email})")
        with col2:
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.rerun()
    
    # Request counter
    remaining_requests = DAILY_LIMIT - st.session_state.daily_requests
    st.markdown(f'<div class="request-counter">📊 Daily requests: {st.session_state.daily_requests}/{DAILY_LIMIT} | Remaining: {remaining_requests}</div>', unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📝 Text Prompt", "🎤 Voice Prompt", "🖼️ Gallery"])
    
    with tab1:
        st.markdown("### Enter your text prompt")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            prompt = st.text_area(
                "Describe the image you want to generate:",
                placeholder="A beautiful sunset over mountains with a river flowing through...",
                height=100
            )
        with col2:
            image_size = st.selectbox("Image Size:", IMAGE_SIZES, index=1)
        
        if st.button("🎨 Generate Image", use_container_width=True, type="primary"):
            if prompt.strip():
                image_url = generate_image(prompt, image_size)
                if image_url:
                    add_to_gallery(image_url, prompt)
                    st.success("Image generated successfully!")
                    display_image_with_download(image_url, prompt, "text")
            else:
                st.warning("Please enter a text prompt.")
    
    with tab2:
        st.markdown("### Voice Input (Browser-based)")
        st.info("🎙️ Voice recording requires browser permissions. Click the microphone button below to record.")
        
        # Browser-based voice recording using Streamlit's experimental audio input
        try:
            audio_bytes = st.experimental_audio_input("Record your voice prompt:")
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
                st.warning("⚠️ Voice-to-text transcription requires additional setup. For now, please use the text input tab.")
        except AttributeError:
            st.info("📝 Voice recording is not available in this deployment. Please use the Text Prompt tab instead.")
            
        # Alternative: Manual text input for voice simulation
        st.markdown("### Alternative: Type your voice prompt")
        col1, col2 = st.columns([3, 1])
        with col1:
            voice_prompt = st.text_area(
                "Enter text as if speaking:",
                placeholder="Type what you would say... (e.g., 'Create a picture of a cat playing in the garden')",
                height=80
            )
        with col2:
            image_size_voice = st.selectbox("Size:", IMAGE_SIZES, index=1, key="voice_size")
        
        if st.button("🎨 Generate from Voice Text", use_container_width=True, type="primary"):
            if voice_prompt.strip():
                image_url = generate_image(voice_prompt, image_size_voice)
                if image_url:
                    add_to_gallery(image_url, voice_prompt)
                    st.success("Image generated from voice prompt!")
                    display_image_with_download(image_url, voice_prompt, "voice")
            else:
                st.warning("Please enter a voice prompt.")
    
    with tab3:
        st.markdown("### 🖼️ Recent Images Gallery")
        
        if st.session_state.image_gallery:
            for i, item in enumerate(st.session_state.image_gallery):
                with st.expander(f"Image {i+1}: {item['prompt'][:50]}...", expanded=(i==0)):
                    display_image_with_download(item['url'], item['prompt'], f"gallery_{i}")
                    st.caption(f"Generated: {item['timestamp']}")
        else:
            st.info("No images generated yet. Create your first image in the Text Prompt tab!")
    
    # Footer
    st.markdown("---")
    st.markdown("*Made with ❤️ for the family | Powered by Deep Seek API*")

if __name__ == "__main__":
    main()
