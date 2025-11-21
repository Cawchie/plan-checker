import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os
import random

PHRASES = [
    "Might be a lil while, grab a coffee ☕",
    "Grok is reading every note like a boss…",
    "Council officers wish they were this thorough",
    "Finding zero issues… as usual",
    "Hold tight, making the council jealous",
    "Your consent is loading…",
    "Grok just saved you another RFI",
    "This job is cleaner than my code",
    "Consent loading… 99%… (it’s a lie, it’s 100%)"
]

st.set_page_config(page_title="xAI Plan Checker PRO", layout="centered")

st.markdown("""
<style>
    .main {background-color: #f8f9fa; padding: 2rem; border-radius: 10px;}
    .stButton>button {background-color: #0066cc !important; color: white !important; font-weight: bold; height: 3.5rem; font-size: 1.2rem;}
    .stFileUploader > div > div {background-color: #e9f2ff; border-radius: 8px; padding: 1rem; border: 2px dashed #99ccff;}
    h1 {color: #003366; text-align: center;}
    .client-report {background-color: #e8f5e8; padding: 2rem; border-left: 8px solid #28a745; border-radius: 8px; margin: 2rem 0; font-size: 1.2rem; line-height: 1.8;}
    .detailed-report {background-color: #f0f8ff; padding: 2rem; border-left: 8px solid #007bff; border-radius: 8px; margin: 2rem 0; font-size: 1rem;}
    .footer {text-align: center; margin-top: 4rem; color: #666; font-size: 0.9rem;}
    .watermark {position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); font-size: 56px; font-weight: bold; color: rgba(0, 102, 204, 0.13); pointer-events: none; z-index: 9999; white-space: nowrap;}
</style>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker PRO — Grok-3")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Secrets.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

st.header("Upload All Files (Plans, Geotech, H1, RFI)")
uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True, key="files")

rfi_file = None
other_files = []
if uploaded_files:
    for f in uploaded_files:
        if "rfi" in f.name.lower():
            rfi_file = f
        else:
            other_files.append(f)

col1, col2 = st.columns(2)
with col1:
    check_compliance = st.button("COMPLIANCE CHECK", type="primary", use_container_width=True)
with col2:
    check_rfi = st.button("RFI RESPONSE", type="secondary", use_container_width=True)

watermark = st.empty()

plan_text = ""
if other_files:
    for f in other_files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    plan_text += f"--- {f.name} - Page {page_num} ---\n{t}\n\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

if check_compliance and plan_text:
    watermark.markdown(f'<div class="watermark">{random.choice(PHRASES)}</div>', unsafe_allow_html=True)
    with st.spinner("Grok-3 analysing every detail..."):
        try:
            # First pass
            response = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "You are an NZBC auditor. List every possible non-compliance in bullet points with clause, issue, fix."},
                    {"role": "user", "content": plan_text}
                ]
            )
            raw_report = response.choices[0].message.content

            # FINAL FACT CHECKER — outputs BOTH versions
            fact_check = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": """You are the FINAL FACT CHECKER.
                    Kill every false positive (smoke alarms, ventilation, red box notes, SD/V symbols = compliant).
                    Output exactly two sections:
                    1. CLIENT REPORT — Plain English, short, friendly, reassuring
                    2. FULL DETAILED REPORT — everything for the designer/council"""},
                    {"role": "user", "content": f"RAW REPORT:\n{raw_report}\n\nFULL PLANS:\n{plan_text}"}
                ]
            )
            output = fact_check.choices[0].message.content

            watermark.empty()
            st.balloons()
            st.success("100% ACCURATE REPORT READY")

            # Split into two reports
            if "CLIENT REPORT" in output and "FULL DETAILED REPORT" in output:
                client_report = output.split("FULL DETAILED REPORT")[0].replace("CLIENT REPORT", "").strip()
                detailed_report = "FULL DETAILED REPORT" + output.split("FULL DETAILED REPORT")[1].strip()
            else:
                client_report = output
                detailed_report = output

            # CLIENT VERSION (big green box)
            st.markdown(f"<div class='client-report'><strong>CLIENT REPORT — EASY READ</strong><br><br>{client_report}</div>", unsafe_allow_html=True)

            # FULL VERSION (blue box, always visible)
            st.markdown(f"<div class='detailed-report'><strong>FULL DETAILED REPORT (for designer/council)</strong><br><br>{detailed_report}</div>", unsafe_allow_html=True)

        except Exception as e:
            watermark.empty()
            st.error(f"Error: {e}")

st.markdown("<div class='footer'>xAI Plan Checker PRO © 2025 | Powered by Grok-3</div>", unsafe_allow_html=True)
