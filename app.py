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

# Session state for files
if 'all_files' not in st.session_state:
    st.session_state.all_files = []

# Step 1: Upload plans
st.header("Step 1: Upload Plans")
plan_files = st.file_uploader("Upload architectural/structural plans", type="pdf", accept_multiple_files=True, key="plans")

# Step 2: Upload supporting docs
st.header("Step 2: Upload Supporting Docs (Geotech, H1, etc.)")
support_files = st.file_uploader("Upload geotech, H1 calcs, RFIs, etc.", type="pdf", accept_multiple_files=True, key="support")

# Combine files
files = plan_files + support_files
if files:
    st.session_state.all_files = files

if st.button("Check Compliance") or st.session_state.all_files:
    files = st.session_state.all_files
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
        with st.spinner("Checking all documents..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3-mini",
                    messages=[
                        {"role": "system", "content": "You are a NZBC expert. Check ALL uploaded files (plans + geotech + H1). Give ONLY bullet points for non-compliant issues with FILE NAME + PAGE NUMBER. Example: '- THRUPP.pdf Page 3: E1 missing'"},
                        {"role": "user", "content": text}
                    ]
                )
                st.success("Compliance Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found in PDFs.")
