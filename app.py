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
support_files = st.file_uploader("Upload geotech, H1, etc.", type="pdf", accept_multiple_files=True, key="support")

# Step 3: Upload RFI
st.header("Step 3: Upload RFI (Council Request)")
rfi_file = st.file_uploader("Upload RFI document", type="pdf", accept_multiple_files=False, key="rfi")

# Combine non-RFI files
files = plan_files + support_files

if files and st.button("Check Compliance"):
    # Extract text from plans
    plan_text = ""
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    plan_text += f"--- {f.name} - Page {page_num} ---\n{page_text}\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    # Extract RFI text
    rfi_text = ""
    if rfi_file:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(rfi_file.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    rfi_text += f"--- RFI: {rfi_file.name} - Page {page_num} ---\n{page_text}\n"
        except Exception as e:
            st.error(f"Failed to read RFI: {e}")

    if plan_text.strip() or rfi_text:
        with st.spinner("Analyzing..."):
            try:
                if rfi_text:
                    # RFI CHALLENGE MODE
                    system_prompt = """You are a NZBC compliance engineer defending the plans against council RFIs.

FOR EACH RFI POINT:
1. QUOTE THE RFI QUESTION
2. SEARCH THE PLANS HARD — find the exact page and text that answers it
3. IF ANSWERED: Say "ALREADY COMPLIANT" + quote the plan text + page
4. IF NOT ANSWERED: Give practical fix + alternative

Example:
- RFI.pdf Page 1: "No E1 overflow shown"
  - ALREADY COMPLIANT: "Overflow path shown on Page 5 (WD103): 'Secondary flow to boundary at 150mm freeboard'"
  - Fix: Add detail to Page 5 if needed

- RFI.pdf Page 2: "Setback breach"
  - Issue: Building 1.2m from boundary
  - Suggested: Apply for variation
  - Alternative: Fire-rate wall to FRL 60/60/60 (C6)

ONLY bullet points. NO summary."""
                else:
                    # FULL COMPLIANCE MODE
                    system_prompt = """You are a NZBC compliance auditor.

CHECK EVERY PAGE.

For EACH non-compliant issue:
- FILE + PAGE
- Clause
- Issue
- SUGGESTED FIX
- ALTERNATIVE (if main fix is impractical)

ONLY bullet points."""

                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"RFI:\n{rfi_text}\n\nPLANS:\n{plan_text}" if rfi_text else plan_text}
                    ]
                )
                st.success("Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found.")
