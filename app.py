import streamlit as st
from huggingface_hub import InferenceClient, login
from PIL import Image
import io
import os
import time

# Check if we're in Streamlit sharing environment
IS_STREAMLIT_CLOUD = os.getenv('IS_STREAMLIT_CLOUD') == 'true'

# Get HF token from Streamlit secrets or environment
HF_TOKEN = st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN", ""))

# Authenticate with Hugging Face
if HF_TOKEN:
    try:
        login(token=HF_TOKEN)
        st.session_state.hf_auth = True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        st.session_state.hf_auth = False
else:
    st.warning("Hugging Face token not found. Public models only.")
    st.session_state.hf_auth = False

# Initialize client with fallback options
if IS_STREAMLIT_CLOUD:
    client = InferenceClient()  # Use default for Streamlit Cloud
else:
    client = InferenceClient()  # Will auto-route requests

st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="centered"
)

# Custom styling
st.markdown("""
<style>
    .header {
        background: linear-gradient(90deg, #4F46E5, #7C3AED);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .generate-btn {
        background-color: #4F46E5 !important;
        color: white !important;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: none;
        width: 100%;
        margin-top: 1rem;
    }
    .download-btn {
        background-color: #10B981 !important;
        color: white !important;
        margin-top: 1rem;
    }
    .model-info {
        background-color: #f0f9ff;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<div class="header"><h1>🎨 AI Image Generator</h1><p>Transform text into stunning visuals</p></div>', unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Model selection
    model_options = {
        "Stable Diffusion XL": "stabilityai/stable-diffusion-xl-base-1.0",
        "OpenJourney (Art)": "prompthero/openjourney",
        "FLUX.1-dev (Request access)": "black-forest-labs/FLUX.1-dev"
    }
    selected_model = st.selectbox(
        "AI Model",
        list(model_options.keys()),
        index=0
    )
    
    # Image dimensions
    width = st.slider("Image Width", 512, 1024, 768, 64)
    height = st.slider("Image Height", 512, 1024, 768, 64)
    
    # Advanced options
    with st.expander("Advanced Options"):
        guidance_scale = st.slider("Creativity", 1.0, 20.0, 7.5, 0.5)
        num_inference_steps = st.slider("Quality Steps", 20, 100, 50, 10)
    
    st.markdown("---")
    st.markdown('<div class="model-info">'
                f'<b>Current Model:</b> {selected_model}<br>'
                f'<b>Status:</b> {"🔒 Access needed" if "FLUX" in selected_model and not st.session_state.get("hf_auth", False) else "✅ Ready"}'
                '</div>', unsafe_allow_html=True)

# Main content
prompt = st.text_area(
    "Describe what you want to see:",
    placeholder="A futuristic cityscape at sunset with flying cars...",
    height=120
)

negative_prompt = st.text_input(
    "Exclude from image (optional):",
    placeholder="blurry, deformed, ugly..."
)

col1, col2 = st.columns(2)
with col1:
    generate_btn = st.button("✨ Generate Image", key="generate", use_container_width=True)

# Placeholder for image display
image_placeholder = st.empty()
download_placeholder = st.empty()
status_area = st.empty()

if generate_btn:
    if not prompt.strip():
        st.warning("Please enter an image description")
    else:
        with st.spinner("🚀 Generating image... (20-60 seconds)"):
            start_time = time.time()
            try:
                model_id = model_options[selected_model]
                
                # Check for FLUX.1 access
                if "FLUX" in selected_model and not st.session_state.get("hf_auth", False):
                    raise Exception("FLUX.1 requires Hugging Face access. Add token in secrets.")
                
                # Generate image
                image = client.text_to_image(
                    prompt,
                    model=model_id,
                    negative_prompt=negative_prompt if negative_prompt else None,
                    parameters={
                        "width": width,
                        "height": height,
                        "guidance_scale": guidance_scale,
                        "num_inference_steps": num_inference_steps
                    }
                )
                
                gen_time = time.time() - start_time
                
                # Display image
                image_placeholder.image(image, caption=prompt, use_column_width=True)
                status_area.success(f"✅ Generated in {gen_time:.1f} seconds | Model: {selected_model}")
                
                # Prepare download
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                # Download button
                download_placeholder.download_button(
                    "💾 Download Image",
                    data=byte_im,
                    file_name=f"ai_image_{prompt[:20]}.png",
                    mime="image/png",
                    use_container_width=True,
                    key="download"
                )
                
            except Exception as e:
                error_msg = str(e)
                status_area.error(f"❌ Error: {error_msg}")
                
                # Suggest alternatives for FLUX.1 access issues
                if "FLUX" in selected_model:
                    status_area.info("""
                    **To use FLUX.1:**
                    1. Request access at [huggingface.co/black-forest-labs/FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev)
                    2. Add your Hugging Face token in Streamlit secrets
                    """)

# Footer
st.markdown("---")
st.caption("Powered by [Hugging Face Inference API](https://huggingface.co/docs/huggingface_hub) | "
           "[Streamlit](https://streamlit.io)")
