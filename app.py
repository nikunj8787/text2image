import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import os

# Get HF token from Streamlit secrets or environment
HF_TOKEN = st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN", ""))

# Initialize Hugging Face client
if HF_TOKEN:
    client = InferenceClient(
        provider="nebius",
        api_key=HF_TOKEN
    )
else:
    client = None

st.set_page_config(
    page_title="FLUX.1 Image Generator",
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
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<div class="header"><h1>🎨 FLUX.1 Image Generator</h1><p>Transform text into stunning visuals using AI</p></div>', unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    width = st.slider("Image Width", 256, 1024, 512, 64)
    height = st.slider("Image Height", 256, 1024, 512, 64)
    st.markdown("---")
    st.info("ℹ️ Powered by [FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev) model")

# Main content
prompt = st.text_area(
    "Describe what you want to see:",
    placeholder="A futuristic cityscape at sunset with flying cars...",
    height=120
)

col1, col2 = st.columns(2)
with col1:
    generate_btn = st.button("✨ Generate Image", key="generate", use_container_width=True)

# Placeholder for image display
image_placeholder = st.empty()
download_placeholder = st.empty()

if generate_btn:
    if not prompt.strip():
        st.warning("Please enter an image description")
    elif not client:
        st.error("Hugging Face API token not found. Please set HF_TOKEN in secrets or environment variables.")
    else:
        with st.spinner("Generating your image... (this may take 20-40 seconds)"):
            try:
                # Generate image
                image = client.text_to_image(
                    prompt,
                    model="black-forest-labs/FLUX.1-dev",
                    parameters={"width": width, "height": height}
                )
                
                # Display image
                image_placeholder.image(image, caption=prompt, use_column_width=True)
                
                # Prepare download
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                # Download button
                download_placeholder.download_button(
                    "💾 Download Image",
                    data=byte_im,
                    file_name=f"flux_image_{prompt[:20]}.png",
                    mime="image/png",
                    use_container_width=True,
                    key="download"
                )
                
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
                st.info("This model requires Nebius provider access. Contact Hugging Face for access.")

# Footer
st.markdown("---")
st.caption("Built with [Hugging Face Inference API](https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client) | "
           "[FLUX.1-dev model](https://huggingface.co/black-forest-labs/FLUX.1-dev)")
