import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import os
import time
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get HF token from Streamlit secrets
HF_TOKEN = st.secrets.get("HF_TOKEN", None)

# Initialize client with fallback
client = None
if HF_TOKEN:
    try:
        client = InferenceClient(token=HF_TOKEN)
        logger.info("Initialized InferenceClient with token")
    except Exception as e:
        logger.error(f"Client initialization failed: {str(e)}")
        client = None

# Public fallback models
PUBLIC_MODELS = {
    "Stable Diffusion XL": "stabilityai/stable-diffusion-xl-base-1.0",
    "OpenJourney (Art)": "prompthero/openjourney",
    "DreamShaper": "lykon/dreamshaper-8",
    "Anime Diffusion": "cagliostrolab/animagine-xl-3.1"
}

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
    .model-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4F46E5;
    }
    .error-card {
        background-color: #fff5f5;
        border-left: 4px solid #e53e3e;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<div class="header"><h1>🎨 AI Image Generator</h1><p>Transform text into stunning visuals</p></div>', unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Model selection with fallbacks
    model_options = {**PUBLIC_MODELS}
    if HF_TOKEN:
        model_options["FLUX.1-dev (Premium)"] = "black-forest-labs/FLUX.1-dev"
    
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
        seed = st.number_input("Random Seed", value=-1, help="-1 for random")
    
    st.markdown("---")
    st.markdown(f'<div class="model-card"><b>Current Model:</b> {selected_model}<br>'
                f'<b>Status:</b> {"🔒 Requires token" if "FLUX" in selected_model else "✅ Public access"}</div>', 
                unsafe_allow_html=True)

# Main content
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.text_area(
            "Describe what you want to see:",
            placeholder="A beautiful garden with colorful flowers and a stone path...",
            height=120
        )
    with col2:
        st.write("### Tips:")
        st.markdown("- Be specific: 'sunset garden' → 'vibrant sunset garden with roses'")
        st.markdown("- Add details: 'stone path, butterflies, wooden bench'")

negative_prompt = st.text_input(
    "Exclude from image (optional):",
    placeholder="blurry, deformed, ugly, text, watermark"
)

generate_btn = st.button("✨ Generate Image", use_container_width=True)

# Placeholders
image_placeholder = st.empty()
status_placeholder = st.empty()
download_placeholder = st.empty()

def generate_image_fallback(prompt, model_id, width, height):
    """Fallback to API request if client fails"""
    API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return None

if generate_btn:
    if not prompt.strip():
        st.warning("Please enter an image description")
    else:
        with st.spinner("🚀 Generating image... (20-60 seconds)"):
            start_time = time.time()
            try:
                model_id = model_options[selected_model]
                
                # Check for FLUX.1 access
                if "FLUX.1" in selected_model and not HF_TOKEN:
                    raise Exception("FLUX.1 requires Hugging Face token")
                
                # Attempt generation
                image_bytes = None
                
                if client:
                    try:
                        image_bytes = client.text_to_image(
                            prompt,
                            model=model_id,
                            negative_prompt=negative_prompt or None,
                            parameters={
                                "width": width,
                                "height": height,
                                "guidance_scale": guidance_scale,
                                "num_inference_steps": num_inference_steps,
                                "seed": seed
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Client failed: {str(e)} - Using fallback")
                        image_bytes = generate_image_fallback(prompt, model_id, width, height)
                else:
                    image_bytes = generate_image_fallback(prompt, model_id, width, height)
                
                if not image_bytes:
                    raise Exception("All generation methods failed")
                
                # Process and display image
                image = Image.open(io.BytesIO(image_bytes))
                gen_time = time.time() - start_time
                
                # Display image
                image_placeholder.image(image, caption=prompt, use_column_width=True)
                status_placeholder.success(f"✅ Generated in {gen_time:.1f} seconds | Model: {selected_model}")
                
                # Prepare download
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                
                # Download button
                download_placeholder.download_button(
                    "💾 Download Image",
                    data=buf.getvalue(),
                    file_name=f"ai_image_{prompt[:20]}.png",
                    mime="image/png",
                    use_container_width=True
                )
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Generation failed: {error_msg}")
                status_placeholder.markdown(
                    f'<div class="model-card error-card">'
                    f'<h4>❌ Generation Failed</h4>'
                    f'<p>{error_msg}</p>'
                    f'</div>', 
                    unsafe_allow_html=True
                )
                
                # Special handling for FLUX.1
                if "FLUX.1" in selected_model:
                    status_placeholder.info("""
                    **To use FLUX.1:**
                    1. Request access: [huggingface.co/black-forest-labs/FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev)
                    2. Add your Hugging Face token in Streamlit secrets
                    """)
                else:
                    status_placeholder.info("""
                    **Troubleshooting Tips:**
                    - Try a different model
                    - Simplify your prompt
                    - Reduce image dimensions
                    - Check your network connection
                    """)

# Footer
st.markdown("---")
st.caption("Powered by [Hugging Face](https://huggingface.co) | "
           "[Streamlit](https://streamlit.io) | "
           "Need help? [Contact Support](mailto:support@example.com)")
