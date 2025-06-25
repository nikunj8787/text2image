import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import os
import time  # Added for timing

# Get HF token ONLY from Streamlit secrets
HF_TOKEN = st.secrets.get("HF_TOKEN", None)

# Initialize client only if token exists
if HF_TOKEN:
    client = InferenceClient(token=HF_TOKEN)
else:
    client = None
    st.warning("Hugging Face token not set. Using public endpoints only.")

st.set_page_config(
    page_title="FLUX.1 Image Generator",
    page_icon="🎨",
    layout="centered"
)

# ... (keep your existing styling code) ...

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # ADD MODEL SELECTION
    model_options = {
        "Stable Diffusion XL (Public)": "stabilityai/stable-diffusion-xl-base-1.0",
        "OpenJourney (Public)": "prompthero/openjourney",
        "FLUX.1-dev (Requires Token)": "black-forest-labs/FLUX.1-dev"
    }
    selected_model = st.selectbox("AI Model", list(model_options.keys()), index=0)
    
    width = st.slider("Image Width", 512, 1024, 768, 64)
    height = st.slider("Image Height", 512, 1024, 768, 64)
    
    # ADD ADVANCED OPTIONS
    with st.expander("Advanced Options"):
        num_inference_steps = st.slider("Quality Steps", 20, 100, 50, 10)
        guidance_scale = st.slider("Creativity", 1.0, 20.0, 7.5, 0.5)
    
    st.markdown("---")
    st.info("ℹ️ Powered by [Hugging Face](https://huggingface.co)")

# Main content
prompt = st.text_area(
    "Describe what you want to see:",
    placeholder="A futuristic cityscape at sunset with flying cars...",
    height=120
)

# ADD NEGATIVE PROMPT
negative_prompt = st.text_input(
    "Exclude from image (optional):",
    placeholder="blurry, deformed, ugly..."
)

generate_btn = st.button("✨ Generate Image", use_container_width=True)

# Placeholder for image display
image_placeholder = st.empty()
status_area = st.empty()
download_placeholder = st.empty()

if generate_btn:
    if not prompt.strip():
        st.warning("Please enter an image description")
    else:
        with st.spinner("Generating your image... (20-60 seconds)"):
            start_time = time.time()
            try:
                model_id = model_options[selected_model]
                
                # VERIFY FLUX.1 ACCESS
                if "FLUX.1" in selected_model and not HF_TOKEN:
                    raise Exception("FLUX.1 requires Hugging Face token in secrets")
                
                # GENERATE IMAGE
                image_bytes = client.text_to_image(
                    prompt,
                    model=model_id,
                    negative_prompt=negative_prompt or None,
                    parameters={
                        "width": width,
                        "height": height,
                        "num_inference_steps": num_inference_steps,
                        "guidance_scale": guidance_scale
                    }
                )
                
                # CONVERT TO PIL IMAGE
                image = Image.open(io.BytesIO(image_bytes))
                gen_time = time.time() - start_time
                
                # Display image
                image_placeholder.image(image, caption=prompt, use_column_width=True)
                status_area.success(f"✅ Generated in {gen_time:.1f} seconds")
                
                # Prepare download
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                
                # Download button
                download_placeholder.download_button(
                    "💾 Download Image",
                    data=buf.getvalue(),
                    file_name=f"image_{prompt[:20]}.png",
                    mime="image/png",
                    use_container_width=True
                )
                
            except Exception as e:
                error_msg = str(e)
                status_area.error(f"❌ Error: {error_msg}")
                
                # SPECIAL HANDLING FOR FLUX.1
                if "FLUX.1" in selected_model:
                    status_area.info("""
                    **To use FLUX.1:**
                    1. Request access: [huggingface.co/black-forest-labs/FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev)
                    2. Add token in Streamlit secrets
                    """)
                else:
                    status_area.info("Try a different model or check your network connection")

# Footer
st.markdown("---")
st.caption("Built with [Hugging Face Inference API](https://huggingface.co/docs/huggingface_hub) | [Streamlit](https://streamlit.io)")
