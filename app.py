import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.title("xAI Plan Checker")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing!")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

files = st.file_uploader("Upload PDFs (< 2MB)", type="pdf", accept_multiple_files=True)

if files:
    text = ""
    for f in files:
        
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            text += f"\n--- END OF {f.name} ---\n"
        except:
            st.error(f"Failed to read {f.name}")

    # Token limit
    if len(text) > 30000:
        st.error("Too much text! Upload 1-2 pages at a time.")
        st.stop()

    with st.spinner("Checking..."):
        try:
            resp = client.chat.completions.create(
                model="grok-3-mini",  # 32K tokens
                messages=[
                    {"role": "system", "content": "You are a NZBC expert. Give ONLY bullet points for non-compliant issues with PAGE NUMBERS. Example: '- Page 3: E1 missing'"},
                    {"role": "user", "content": text}
                ]
            )
            st.success("Done!")
            st.markdown(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"API Error: {e}")
