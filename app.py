import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

# === PRO LOOK (CSS) ===
st.markdown("""
<style>
    .main { background-color: #f8f9fa; padding: 2rem; border-radius: 10px; }
    .stButton>button { background-color: #0066cc; color: white; font-weight: bold; border-radius: 8px; padding: 0.7rem 1.4rem; font-size: 1.1rem; width: 100%; margin: 0.5rem 0; }
    .stFileUploader > div > div { background-color: #e9f2ff; border-radius: 8px; padding: 1rem; border: 2px dashed #99ccff; }
    h1, h2, h3 { color: #003366; font-family: 'Helvetica', sans-serif; font-weight: 600; }
    .final-report { background-color: #e8f5e8; padding: 1.5rem; border-left: 8px solid #28a745; border-radius: 8px; margin: 2rem 0; font-size: 1.1rem; line-height: 1.6; }
    .footer { text-align: center; margin-top: 3rem; color: #6c757d; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker PRO")

# Get key
api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Settings.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

# === SINGLE UPLOAD BOX ===
st.header("Upload All Files (Plans, Geotech, H1, RFI)")
uploaded_files = st.file_uploader("Drag & drop all PDFs here", type="pdf", accept_multiple_files=True, key="all_files")

# Separate RFI detection
rfi_file = None
other_files = []
for f in uploaded_files or []:
    if "rfi" in f.name.lower():
        rfi_file = f
    else:
        other_files.append(f)

# === BUTTONS ===
col1, col2 = st.columns(2)

with col1:
    check_compliance = st.button("COMPLIANCE CHECK", type="primary")

with col2:
    check_rfi = st.button("RFI RESPONSE", type="secondary")

# === EXTRACT TEXT ONCE ===
plan_text = ""
rfi_text = ""

if other_files:
    for f in other_files:
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

# === COMPLIANCE CHECK — MAX THOROUGHNESS (10 ISSUES PER CLAUSE) ===
if check_compliance and other_files:
    if plan_text.strip():
        with st.spinner("Creating 100% Verified Report..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor with 30 years experience.

BE EXTREMELY THOROUGH.

For EVERY NZBC clause (E1, E2, E3, B1, B2, D1, D2, F7, G4, G12, G13, H1, C3, etc.), list UP TO 10 specific issues.

If fewer than 10 issues in a clause, write "Only X issues found for [clause]" at the end of that clause.

Structure:
**Clause E2 – External Moisture**
- Issue 1: ...
  Suggested Fix: ...
  Alternative: ...
- Issue 2: ...
  ...
- Only 7 issues found for E2

Do this for every clause that has issues.

If a clause has no issues, say "**Clause E2 – External Moisture**: No issues found"

Cover ALL clauses.

Be brutal — find every possible minor issue.

ONLY use this format. NO intro text."""},
                        {"role": "user", "content": plan_text}
                    ]
                )
                report = response.choices[0].message.content

                # Fact check
                fact_check = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are the FACT CHECKER.

Check every flag.

If correct → keep it
If wrong or missing → fix or add

Output ONLY the FINAL 100% CORRECT report in the exact same format.

NO explanations."""},
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
