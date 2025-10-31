import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

# === PRO LOOK (CSS) ===
st.markdown("""
<style>
    .main { background-color: #f8f9fa; padding: 2rem; border-radius: 10px; }
    .stButton>button { background-color: #007bff; color: white; font-weight: bold; border-radius: 8px; padding: 0.6rem 1.2rem; font-size: 1.1rem; width: 100%; margin: 0.5rem 0; }
    .stFileUploader > div > div { background-color: #e9ecef; border-radius: 8px; padding: 1rem; border: 2px dashed #ced4da; }
    h1, h2, h3 { color: #343a40; font-family: 'Helvetica', sans-serif; font-weight: 600; }
    .report { background-color: #fff3cd; padding: 1.2rem; border-left: 6px solid #ffc107; border-radius: 8px; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.6; }
    .footer { text-align: center; margin-top: 3rem; color: #6c757d; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker")

# Get key
api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Settings.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

# Upload Plans
st.header("Upload Plans (Required)")
plan_files = st.file_uploader("Upload plans", type="pdf", accept_multiple_files=True, key="plans")

# Upload Supporting Docs
st.header("Upload Supporting Docs (Geotech, H1, etc.)")
support_files = st.file_uploader("Upload geotech, H1 calcs, etc.", type="pdf", accept_multiple_files=True, key="support")

# Upload RFI
st.header("Upload RFI (Optional)")
rfi_file = st.file_uploader("Upload RFI document", type="pdf", accept_multiple_files=False, key="rfi")

# Combine non-RFI files
files = plan_files + support_files

# === BUTTONS ===
col1, col2 = st.columns(2)

with col1:
    check_compliance = st.button("COMPLIANCE CHECK", type="primary")

with col2:
    check_rfi = st.button("RFI RESPONSE", type="secondary")

# === EXTRACT TEXT ONCE ===
text = ""
rfi_text = ""

if files or rfi_file:
    # Extract plans + support
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    text += f"--- {f.name} - Page {page_num} ---\n{t}\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    # Extract RFI
    if rfi_file:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(rfi_file.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    rfi_text += f"--- RFI: {rfi_file.name} - Page {page_num} ---\n{t}\n"
        except Exception as e:
            st.error(f"Failed to read RFI: {e}")

# === COMPLIANCE CHECK ===
if check_compliance and files:
    if text.strip():
        with st.spinner("Running Full Compliance Check..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor with 20 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE ISSUE.

LOOK FOR:
- KEY/LEGEND items (smoke alarms, vents, fire doors, etc.)
- SYMBOLS on the plan (SD, FD, V, H, etc.)

For EACH non-compliant item:
- FILE NAME + PAGE NUMBER
- Clause (e.g., E1.3.1)
- Issue description
- SUGGESTED FIX
- ALTERNATIVE (if main fix is impractical)

LINK KEY TO PLAN:
- If KEY says "SD = Smoke Detector" → Find SD symbols
- If symbol missing → FLAG IT

DO NOT SKIP ANYTHING. BE DETAILED.

Example:
- PLAN.pdf Page 6: F7.3.1 smoke detectors
  - Clause: F7.3.1
  - Issue: KEY says "SD required" but no SD in bedrooms
  - Suggested: Add SD within 3m of bedroom doors
  - Alternative: Note "to be installed per F7/AS1"

ONLY bullet points. NO summary."""},
                        {"role": "user", "content": text}
                    ]
                )
                st.success("Compliance Check Complete")
                with st.container():
                    st.markdown(f"<div class='report'>{response.choices[0].message.content}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found in plans.")

# === RFI RESPONSE ===
if check_rfi and rfi_file:
    if rfi_text:
        with st.spinner("Analyzing RFI..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance engineer defending the plans against council RFIs.

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
  - Suggested: Apply for resource consent variation
  - Alternative: Fire-rate wall to FRL 60/60/60 (C6)

ONLY bullet points. NO summary."""},
                        {"role": "user", "content": f"RFI:\n{rfi_text}\n\nPLANS:\n{text}"}
                    ]
                )
                st.success("RFI Response Complete")
                with st.container():
                    st.markdown(f"<div class='report'>{response.choices[0].message.content}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found in RFI.")

# Footer
st.markdown("<div class='footer'>xAI Plan Checker © 2025 | Powered by grok-3</div>", unsafe_allow_html=True)
