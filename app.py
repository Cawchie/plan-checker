import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.title("xAI Plan Checker")

# Get key from secret
api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Settings.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

# Step 1: Upload plans
st.header("Step 1: Upload Plans")
plan_files = st.file_uploader("Upload plans", type="pdf", accept_multiple_files=True, key="plans")

# Step 2: Upload supporting docs
st.header("Step 2: Upload Supporting Docs")
support_files = st.file_uploader("Upload geotech, H1, RFIs", type="pdf", accept_multiple_files=True, key="support")

# Combine files
files = plan_files + support_files

if files and st.button("Check Compliance"):
    text = ""
    rfi_mode = False
    rfi_content = ""

    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    if "RFI" in f.name.upper() or "REQUEST FOR INFORMATION" in page_text.upper():
                        rfi_mode = True
                        rfi_content += f"--- RFI: {f.name} - Page {page_num} ---\n{page_text}\n"
                    else:
                        text += f"--- {f.name} - Page {page_num} ---\n{page_text}\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    if text.strip() or rfi_content:
        with st.spinner("Checking..."):
            try:
                if rfi_mode:
                    # RFI MODE: Only answer the RFI
                    system_prompt = """You are a NZBC compliance engineer responding to council RFIs.

ONLY address the RFI questions from the uploaded RFI document.

For each RFI point:
- RFI FILE + PAGE
- Question
- Direct answer with NZBC clause and fix
- No other compliance checks

Example:
- RFI.pdf Page 1: E1 overflow path
  - Question: No secondary flow path shown
  - Answer: Add 150mm freeboard to tank (E1.3.1). See updated plan Page 3."""
                else:
                    # FULL COMPLIANCE MODE
                    system_prompt = """You are a NZBC compliance auditor with 20 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE ISSUE.

For EACH non-compliant item:
- FILE NAME + PAGE NUMBER
- Clause (e.g., E1.3.1)
- Issue description
- POTENTIAL FIX

CHECK:
E1, E2, E3, B1, B2, D1, D2, F1–F9, G1–G15, H1
Council: height, coverage, setbacks, zoning
Geotech: soil bearing, liquefaction
H1: R-values, thermal bridging

ONLY bullet points. NO summary."""

                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": rfi_content + text if rfi_mode else text}
                    ]
                )
                st.success("Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found.")
