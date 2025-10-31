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

st.header("Step 1: Upload Plans")
plan_files = st.file_uploader("Upload plans", type="pdf", accept_multiple_files=True, key="plans")

st.header("Step 2: Upload Supporting Docs")
support_files = st.file_uploader("Upload geotech, H1, RFIs", type="pdf", accept_multiple_files=True, key="support")

files = plan_files + support_files

if files and st.button("Check Compliance"):
    text = ""
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    text += f"--- {f.name} - Page {page_num} ---\n{t}\n"
        except:
            st.error(f"Failed to read {f.name}")

    if text.strip():
        with st.spinner("Full Compliance Check..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC expert. For every non-compliant issue:
- FILE NAME + PAGE NUMBER
- Clause (e.g., E1.3.1)
- Issue description
- POTENTIAL FIX (be specific)

Example:
- 85 CAPE HILL.pdf Page 1: H6.5 non-compliant for HIRB G (building height 90.59m exceeds limit)
  - Clause: H6.5
  - Issue: Height exceeds HIRB G limit of 90m
  - Fix: Reduce height to 89.9m or apply for variation with engineer justification

ONLY bullet points. NO summary."""},
                        {"role": "user", "content": text}
                    ]
                )
                st.success("Compliance Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found.")
