import streamlit as st
import replicate

# Get your Replicate API token from Streamlit secrets
REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]

# Initialize Replicate client
client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# Model name for Stable Diffusion (change if you want a different model)
MODEL_NAME = "stability-ai/stable-diffusion"

def generate_image(prompt, size="512x512"):
    width, height = map(int, size.split("x"))
    # Replicate's stable diffusion model supports width/height parameters
    output = client.run(
        f"{MODEL_NAME}:db21e45b6b3e0c0e3a9c6c9b1c8b6b2b8a4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4",
        input={
            "prompt": prompt,
            "width": width,
            "height": height
        }
    )
    # Output is a list of image URLs
    return output[0]

st.title("Replicate Text-to-Image Demo")

prompt = st.text_area("Describe the image you want to generate:")
size = st.selectbox("Image Size:", ["256x256", "512x512", "1024x1024"], index=1)

if st.button("🎨 Generate Image"):
    if prompt.strip():
        with st.spinner("Generating image..."):
            image_url = generate_image(prompt, size)
            st.image(image_url, caption=prompt)
            st.download_button("Download Image", data=requests.get(image_url).content, file_name="image.png", mime="image/png")
    else:
        st.warning("Please enter a prompt.")
