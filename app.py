import streamlit as st
import requests
from io import BytesIO
from PIL import Image

# Hugging Face Model API URL (Stable Diffusion 2)
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

def generate_image(prompt):
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None
    return Image.open(BytesIO(response.content))

# UI
st.title("🖼️ Text to Image Generator")
prompt = st.text_input("Enter your image prompt")

if st.button("Generate"):
    if prompt:
        with st.spinner("Generating image..."):
            image = generate_image(prompt)
            if image:
                st.image(image, caption=prompt, use_column_width=True)
    else:
        st.warning("Please enter a prompt.")