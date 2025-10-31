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

# Step 1: Upload Plans
st.header("Step 1: Upload Plans")
plan_files = st.file_uploader("Upload plans", type="pdf", accept_multiple_files=True, key="plans")

# Step 2: Upload Supporting Docs
st.header("Step 2: Upload Supporting Docs (Geotech, H1, etc.)")
support_files = st.file_uploader("Upload geotech, H1 calcs, etc.", type="pdf", accept_multiple_files=True, key="support")

# Step 3: Upload RFIs (SEPARATE)
st.header("Step 3: Upload RFI (Council Request for Information)")
rfi_files = st.file_uploader("Upload RFI document", type="pdf", accept_multiple_files=False, key="rfi")

# Combine non-RFI files
files = plan_files + support_files

if files and st.button("Check Compliance"):
    text = ""
    rfi_text = ""

    # Process non-RFI files
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text += f"--- {f.name} - Page {page_num} ---\n{page_text}\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    # Process RFI if uploaded
    if rfi_files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(rfi_files.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    rfi_text += f"--- RFI: {rfi_files.name} - Page {page_num} ---\n{page_text}\n"
        except Exception as e:
            st.error(f"Failed to read RFI: {e}")

    if text.strip() or rfi_text:
        with st.spinner("Checking..."):
            try:
                if rfi_text:
                    # RFI MODE
                    system_prompt = """You are a NZBC compliance engineer responding to council RFIs.

ONLY address the RFI questions.

For each RFI point:
- RFI FILE + PAGE
- Question
- **SUGGESTED SOLUTION** (practical, cost-effective)
- **ALTERNATIVE** if main fix is impractical (e.g., can't move building → fire-rate wall instead)

Example:
- RFI.pdf Page 1: Setback breach
  - Question: Building 1.2m from boundary
  - Suggested: Apply for resource consent variation
  - Alternative: Fire-rate wall to FRL 60/60/60 (Clause C6)"""
                else:
                    # FULL COMPLIANCE MODE
                    system_prompt = """You are a NZBC compliance auditor.

CHECK EVERY PAGE.

For EACH non-compliant issue:
- FILE + PAGE
- Clause
- Issue
- **SUGGESTED FIX**
- **ALTERNATIVE** if main fix is impractical

Example:
- Plan.pdf Page 3: E1 overflow missing
  - Clause: E1. Jahrhundert
  - Issue: No secondary flow path
  - Suggested: Add 150mm freeboard
  - Alternative: Direct to council drain with consent"""

                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": rfi_text + text if rfi_text else text}
                    ]
                )
                st.success("Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found.")
