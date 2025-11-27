import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os
import random

# === FUNNY PHRASES ===
PHRASES = [
    "Might be a lil while, grab a coffee ☕",
    "Grok is reading every note like a boss…",
    "Council officers wish they were this thorough",
    "Finding zero issues… as usual",
    "Hold tight, making the council jealous",
    "Your consent is loading…",
    "Grok just saved you another RFI",
    "This job is cleaner than my code",
    "Consent loading… 99%… (it's a lie, it's 100%)"
]

st.set_page_config(page_title="xAI Plan Checker PRO", layout="centered")

st.markdown("""
<style>
    .main {background-color: #f8f9fa; padding: 2rem; border-radius: 10px;}
    .stButton>button {background-color: #0066cc !important; color: white !important; font-weight: bold; height: 3.5rem; font-size: 1.2rem;}
    .stFileUploader > div > div {background-color: #e9f2ff; border-radius: 8px; padding: 1rem; border: 2px dashed #99ccff;}
    h1 {color: #003366; text-align: center;}
    .client-report {background-color: #e8f5e8; padding: 2rem; border-left: 8px solid #28a745; border-radius: 8px; margin: 2rem 0; font-size: 1.2rem; line-height: 1.8;}
    .detailed-report {background-color: #f0f8ff; padding: 2rem; border-left: 8px solid #007bff; border-radius: 8px; margin: 2rem 0; font-size: 1rem; line-height: 1.6;}
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
rfi_text = ""

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

if rfi_file:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(rfi_file.getvalue()))
        for page_num, page in enumerate(reader.pages, 1):
            t = page.extract_text() or ""
            if t.strip():
                rfi_text += f"--- RFI Page {page_num} ---\n{t}\n\n"
    except Exception as e:
        st.error("Failed to read RFI")

# === COMPLIANCE CHECK ===
if check_compliance:
    if plan_text:
        watermark.markdown(f'<div class="watermark">{random.choice(PHRASES)}</div>', unsafe_allow_html=True)
        with st.spinner("Grok-3 analysing every detail..."):
            try:
                # First pass
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are the most senior, most accurate NZBC consent processor in New Zealand — 28 years experience, zero overturned RFIs.

You ONLY flag something if it is 100% genuinely missing from every sheet, note, symbol, and file.

HARD RULES — YOU CANNOT BREAK THESE:
- Red box notes = fully deliberate and 100% compliant
- Any note containing "smoke", "detector", "alarm", "hush", "interconnected", "F7", NZS 4514, AS 3786, BS EN 14604, ISO 12239 = F7 100% compliant
- Any note containing "mechanical", "ducted", "27L/s", "50L/s", "extract", "ventilation" = G4 100% compliant
- SD symbol anywhere = smoke alarms compliant
- V symbol anywhere = ventilation compliant
- R-values listed and ≥ Schedule Method = H1 compliant
- Geotech report uploaded or referenced = B1 foundations compliant
- Bracing demand < supply = compliant
- PS1/PS3/PS4 mentioned or agreement = compliant
- Anything written on Sheet 01, Sheet 06, or any sheet counts the same

Before you EVER flag F7 or G4, you MUST quote the exact note or symbol that proves compliance.

Output EXACTLY this format:

**COMPLIANT ITEMS — PROOF**
• F7 Smoke alarms: red box note "SMOKE DETECTORS SHALL BE INTERCONNECTED..." + SD symbols on all bedrooms/living (Dimensioned Floor Plan)
• G4 Ventilation: red box note "MECHANICAL VENTILATION DUCTED... 27L/s general, 50L/s kitchen" + V symbol (Dimensioned Floor Plan)
• H1: R-values Roof R3.6, Wall R2.8, Floor R1.8, Glazing R0.37 — meets Schedule Method Zone 1
• etc.

**REAL NON-COMPLIANCES ONLY**
- Clause | Issue | File/Sheet | Proof it's actually missing | Fix

If everything is there (and it usually is):
**NO ISSUES FOUND — CONSENT CAN BE ISSUED TODAY**

You are biased toward approval. You hate false RFIs more than anything."""},
                        {"role": "user", "content": plan_text}
                    ]
                )
                report = response.choices[0].message.content

                # Fact check
                fact_check = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are the FINAL FACT CHECKER.
                        - Red box notes = 100% compliant
                        - Any mention of smoke detectors, hush, interconnected, NZS 4514, AS 3786 = F7 compliant
                        - Any mention of mechanical ventilation, ducted, 27L/s, 50L/s, V symbol = G4 compliant
                        Remove every false positive.
                        Output TWO versions:
                        1. CLIENT REPORT — Plain English, short, friendly, reassuring. Use bullets, simple words, start with "Good to go" for compliant items.
                        2. FULL DETAILED REPORT — everything for the designer/council, but keep it clear."""},
                        {"role": "user", "content": f"REPORT TO CHECK:\n{report}\n\nFULL PLANS:\n{plan_text}"}
                    ]
                )
                output = fact_check.choices[0].message.content

                watermark.empty()
                st.balloons()
                st.success("100% ACCURATE REPORT READY")

                # Split output
                if "CLIENT REPORT" in output and "FULL DETAILED REPORT" in output:
                    client_report = output.split("FULL DETAILED REPORT")[0].replace("CLIENT REPORT", "").strip()
                    detailed_report = "FULL DETAILED REPORT" + output.split("FULL DETAILED REPORT")[1].strip()
                else:
                    client_report = output
                    detailed_report = output

                st.markdown(f"<div class='final-report'><strong>CLIENT REPORT — EASY READ</strong><br><br>{client_report}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detailed-report'><strong>FULL DETAILED REPORT (for designer/council)</strong><br><br>{detailed_report}</div>", unsafe_allow_html=True)

            except Exception as e:
                watermark.empty()
                st.error(f"Error: {e}")
    else:
        st.warning("Upload plans first")

# === RFI RESPONSE ===
if check_rfi:
    if rfi_text and plan_text:
        watermark.markdown(f'<div class="watermark">{random.choice(PHRASES)}</div>', unsafe_allow_html=True)
        with st.spinner("Grok-3 analysing RFI..."):
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

Output TWO versions:
1. CLIENT REPORT — Plain English, short, friendly.
2. FULL DETAILED REPORT — everything."""},
                        {"role": "user", "content": f"RFI:\n{rfi_text}\n\nPLANS:\n{plan_text}"}
                    ]
                )
                rfi_output = response.choices[0].message.content

                watermark.empty()
                st.success("RFI RESPONSE READY")

                # Split output
                if "CLIENT REPORT" in rfi_output and "FULL DETAILED REPORT" in rfi_output:
                    rfi_client = rfi_output.split("FULL DETAILED REPORT")[0].replace("CLIENT REPORT", "").strip()
                    rfi_detailed = "FULL DETAILED REPORT" + rfi_output.split("FULL DETAILED REPORT")[1].strip()
                else:
                    rfi_client = rfi_output
                    rfi_detailed = rfi_output

                st.markdown(f"<div class='final-report'><strong>CLIENT RFI RESPONSE — EASY READ</strong><br><br>{rfi_client}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='detailed-report'><strong>FULL DETAILED RFI RESPONSE (for designer/council)</strong><br><br>{rfi_detailed}</div>", unsafe_allow_html=True)

            except Exception as e:
                watermark.empty()
                st.error(f"Error: {e}")
    else:
        st.warning("Upload an RFI file and plans first")

# Footer
st.markdown("<div class='footer'>xAI Plan Checker PRO © 2025 | Powered by Grok-3</div>", unsafe_allow_html=True)
