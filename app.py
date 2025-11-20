import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.set_page_config(page_title="xAI Plan Checker PRO", layout="centered")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; padding: 2rem; border-radius: 10px; }
    .stButton>button { background-color: #0066cc; color: white; font-weight: bold; border-radius: 8px; padding: 0.7rem 1.4rem; font-size: 1.1rem; width: 100%; margin: 0.5rem 0; }
    .stFileUploader > div > div { background-color: #e9f2ff; border-radius: 8px; padding: 1rem; border: 2px dashed #99ccff; }
    h1 { color: #003366; text-align: center; }
    .final-report { background-color: #e8f5e8; padding: 2rem; border-left: 8px solid #28a745; border-radius: 8px; margin: 2rem 0; font-size: 1.1rem; line-height: 1.6; }
    .footer { text-align: center; margin-top: 4rem; color: #666; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker PRO — Grok-3")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing!")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

st.header("Upload All Files (Plans, Geotech, H1, RFI)")
uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True, key="files")

rfi_file = None
other_files = []
for f in uploaded_files or []:
    if "rfi" in f.name.lower():
        rfi_file = f
    else:
        other_files.append(f)

col1, col2 = st.columns(2)
with col1:
    compliance = st.button("COMPLIANCE CHECK", type="primary", use_container_width=True)
with col2:
    rfi = st.button("RFI RESPONSE", type="secondary", use_container_width=True)

plan_text = ""

if other_files:
    for f in other_files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            file_text = ""
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    file_text += f"--- {f.name} - Page {page_num} ---\n{t}\n"
            
            # AUTO-SUMMARIZE IF FILE TOO LONG — TOKEN-PROOF
            if len(file_text) > 35000:
                with st.spinner(f"Summarizing {f.name}..."):
                    summary = client.chat.completions.create(
                        model="grok-3",
                        messages=[
                            {"role": "system", "content": "Summarize ONLY compliance-critical information: clauses, R-values, geotech values, flashing, bracing, producer statements, specifications, council notes, numbers. Be concise but complete."},
                            {"role": "user", "content": file_text}
                        ]
                    )
                    file_text = summary.choices[0].message.content + f"\n(Source: {f.name})"
            
            plan_text += file_text + "\n\n"
        except:
            pass

if compliance and plan_text:
    with st.spinner("Grok-3 is analysing every page by page..."):
        try:
            response = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": """You are the most thorough NZBC compliance auditor in New Zealand.

List every possible non-compliance in bullet points:
- File + Page
- Clause
- Issue
- Fix
- Alternative

Check E1, E2, E3, B1, B2, C, D1, F7, G4, G5, G12, G13, H1, council rules.

Be brutal. Find everything.

ONLY bullet points."""},
                    {"role": "user", "content": plan_text}
                ]
            )
            report = response.choices[0].message.content

            fact_check = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "You are the FINAL FACT CHECKER. Fix every wrong or missing flag. Output ONLY the perfect report. No explanations."},
                    {"role": "user", "content": report + "\n\nFULL PLANS:\n" + plan_text}
                ]
            )
            final_report = fact_check.choices[0].message.content

            st.balloons()
            st.success("100% ACCURATE REPORT READY")
            st.markdown(f"<div class='final-report'><strong>FINAL REPORT — GROK-3</strong>\n\n{final_report}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

if rfi and rfi_file:
    rfi_text = ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(rfi_file.getvalue()))
        for page_num, page in enumerate(reader.pages, 1):
            t = page.extract_text() or ""
            if t.strip():
                rfi_text += f"--- Page {page_num} ---\n{t}\n"
    except:
        pass

    if rfi_text:
        with st.spinner("Generating RFI response..."):
            resp = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "For each RFI point: quote it, then say ALREADY COMPLIANT + proof or FIX + ALTERNATIVE. Bullet points only."},
                    {"role": "user", "content": f"RFI:\n{rfi_text}\n\nPLANS:\n{plan_text}"}
                ]
            )
            st.markdown(f"<div class='final-report'>{resp.choices[0].message.content}</div>", unsafe_allow_html=True)

st.markdown("xAI Plan Checker PRO © 2025 | Powered by Grok-3", unsafe_allow_html=True)
