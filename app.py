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
    .h1-calc { background-color: #d4edda; padding: 1.2rem; border-left: 6px solid #28a745; border-radius: 8px; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.6; }
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
col1, col2, col3 = st.columns(3)

with col1:
    check_compliance = st.button("COMPLIANCE CHECK", type="primary")

with col2:
    check_rfi = st.button("RFI RESPONSE", type="secondary")

with col3:
    calc_h1 = st.button("H1 CALCULATION", type="secondary")

# === EXTRACT TEXT ONCE ===
plan_text = ""
h1_text = ""
rfi_text = ""

if files or rfi_file:
    # Extract plans + support
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    if any(keyword in f.name.lower() for keyword in ["h1", "energy"]):
                        h1_text += f"--- H1: {f.name} - Page {page_num} ---\n{t}\n"
                    else:
                        plan_text += f"--- {f.name} - Page {page_num} ---\n{t}\n"
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

# === H1 CALCULATION (SEPARATE BUTTON) ===
if calc_h1 and files:
    if plan_text.strip() or h1_text.strip():
        with st.spinner("Calculating H1 Compliance..."):
            try:
                full_context = ""
                if h1_text:
                    full_context += f"H1 CALCS:\n{h1_text}\n"
                full_context += f"PLANS:\n{plan_text}"

                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are an H1 energy efficiency expert.

EXTRACT FROM PLANS:
- Floor area (m²)
- Wall area (m²)
- Roof area (m²)
- Glazing area (m²)
- R-values (wall, roof, floor, glazing U-value)
- Climate zone

CALCULATE:
- Construction R-value
- Schedule Method compliance
- Glazing % of floor area

GIVE:
- PASS/FAIL
- Required vs Actual R-values
- Fix if failed

Example:
- Floor Area: 218.40 m²
- Glazing: 32 m² (14.6%)
- Wall R-value: 2.4 (Required: 2.0) → PASS
- Roof R-value: 3.8 (Required: 3.0) → PASS
- Glazing U-value: 5.8 (Required: 5.5) → FAIL
  - Fix: Upgrade to double glazing (U=4.8)"""},
                        {"role": "user", "content": full_context}
                    ]
                )
                st.success("H1 Calculation Complete")
                with st.container():
                    st.markdown(f"<div class='h1-calc'>{response.choices[0].message.content}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found in plans.")

# === COMPLIANCE CHECK ===
if check_compliance and files:
    if plan_text.strip():
        with st.spinner("Running Full Compliance Check..."):
            try:
                full_context = ""
                if h1_text:
                    full_context += f"H1 CALCS:\n{h1_text}\n"
                full_context += f"PLANS:\n{plan_text}"

                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor.

CHECK EVERY PAGE.

INCLUDE H1 FROM CALCS.

For EACH non-compliant item:
- FILE + PAGE
- Clause
- Issue
- SUGGESTED FIX
- ALTERNATIVE

ONLY bullet points."""},
                        {"role": "user", "content": full_context}
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
                        {"role": "system", "content": """You are a NZBC compliance engineer.

ANSWER RFI USING PLANS + H1 CALCS.

ONLY bullet points."""},
                        {"role": "user", "content": f"RFI:\n{rfi_text}\n\nPLANS:\n{plan_text}"}
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
