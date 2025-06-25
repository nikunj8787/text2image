import streamlit as st
import requests

st.title("Replicate: Formula Image to LaTeX")

# Use the API key from Streamlit secrets
API_KEY = st.secrets["REPLICATE_API_TOKEN"]

# Model version for image-to-latex
MODEL_VERSION = "fbf6eb41957601528aab2b3f6d37a287015d9f486c3ac4ec6e80f04744ac1a32"

st.write("This demo uses Replicate's API to convert a formula image to LaTeX code.")

image_url = st.text_input(
    "Image URL",
    value="https://replicate.delivery/pbxt/MR7VaVSjxG96N6hB8frEioG1sBaqsbV0Velueqh8yr7H9piP/equation.png"
)
question = st.text_input("Question", value="Convert the formula into latex code.")

if st.button("Get LaTeX Code"):
    with st.spinner("Querying Replicate..."):
        api_url = "https://api.replicate.com/v1/predictions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Prefer": "wait"
        }
        payload = {
            "version": MODEL_VERSION,
            "input": {
                "image": image_url,
                "question": question
            }
        }
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 201:
            output = response.json()
            answer = output.get("output")
            st.success("LaTeX Code:")
            st.code(answer)
        else:
            st.error(f"Error: {response.status_code}\n{response.text}")

if image_url:
    st.image(image_url, caption="Input Image", width=300)
