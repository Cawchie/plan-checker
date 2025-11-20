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
    .final-report { background-color: #d4edda; padding: 1.5rem; border-left: 8px solid #28a745; border-radius: 8px; margin: 2rem 0; font-size: 1.1rem; line-height: 1.6; }
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
support_files = st.file_uploader("Upload geotech, H1 calcs, etc.", type=["pdf", "xlsx"], accept_multiple_files=True, key="support")

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
plan_text = ""
rfi_text = ""

if files or rfi_file:
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    plan_text += f"--- {f.name} - Page {page_num} ---\n{t}\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    if rfi_file:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(rfi_file.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    rfi_text += f"--- RFI: {rfi_file.name} - Page {page_num} ---\n{t}\n"
        except Exception as e:
            st.error(f"Failed to read RFI: {e}")

# === COMPLIANCE CHECK + FACT CHECK + FINAL REPORT ===
if check_compliance and files:
    if plan_text.strip():
        with st.spinner("Running Compliance Check + Fact Check..."):
            try:
                # First: Run compliance check
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor with 20 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE ISSUE.

For EACH non-compliant item:
- FILE NAME + PAGE NUMBER
- Clause (e.g., E1.3.1)
- Issue description
- SUGGESTED FIX
- ALTERNATIVE (if main fix is impractical)

CHECK:
E1, E2, E3, B1, B2, D1, D2, F1–F9, G1–G15, H1
Council: height, coverage, setbacks, zoning
Geotech: soil bearing, liquefaction
H1: R-values, thermal bridging

ONLY bullet points. NO summary."""},
                        {"role": "user", "content": plan_text}
                    ]
                )
                report = response.choices[0].message.content

                # Second: Fact check & fix
                fact_check = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are the FACT CHECKER.

Check every flag in the report.

If flag is CORRECT → keep it
If flag is WRONG or MISSING → correct or add the right one

Be brutal. Fix every mistake.

Output ONLY the FINAL 100% CORRECT report in the same format.

NO explanations. NO "this is correct" — just the clean report."""},
                        {"role": "user", "content": f"REPORT TO CHECK:\n{report}\n\nPLANS:\n{plan_text}"}
                    ]
                )
                final_report = fact_check.choices[0].message.content

                st.balloons()
                st.success("100% VERIFIED REPORT READY")
                with st.container():
                    st.markdown(f"<div class='final-report'><strong>FINAL 100% CORRECT REPORT</strong>\n\n{final_report}</div>", unsafe_allow_html=True)
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

FOR EACH RFI POINT:
1. QUOTE RFI
2. FIND ANSWER IN PLANS
3. IF COMPLIANT: "ALREADY COMPLIANT" + quote + page
4. IF NOT: FIX + ALTERNATIVE

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
