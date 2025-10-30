import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.title("xAI Plan Checker")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Streamlit Cloud.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if files:
    text = ""
    for f in files:
        reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        text += f"\n--- END OF {f.name} ---\n"

    if text.strip():
        with st.spinner("Checking..."):
            try:
                resp = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": "You are a New Zealand Building Code expert. Check E1, D1, B1, H1, geotech, etc. List passes, flags, fixes."},
                        {"role": "user", "content": text}
                    ]
                )
                st.success("Done!")
                st.markdown(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("No text in PDFs.")
