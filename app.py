import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os
import random

# === RANDOM FUNNY PHRASES ===
PHRASES = [
    "Might be a lil while, grab a coffee ☕",
    "Grok is reading every note like a boss…",
    "Council officers wish they were this thorough",
    "Finding zero issues… as usual",
    "This one’s clean — consent incoming",
    "Hold tight, making the council jealous",
    "Analysing 400 pages so you don’t have to",
    "False flags? Not on my watch",
    "Brewing perfection… almost done",
    "Your consent is being fast-tracked",
    "Grok just saved you another RFI",
    "Checking red boxes like a pro",
    "This job is cleaner than my search history",
    "Consent loading… 99%… (it’s a lie, it’s 100%)"
]

# === PRO LOOK + 45° WATERMARK ===
st.markdown(f"""
<style>
    .main {{
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        position: relative;
        overflow: hidden;
    }}
    .stButton>button {{
        background-color: #0066cc;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.7rem 1.4rem;
        font-size: 1.1rem;
        width: 100%;
        margin: 0.5rem 0;
    }}
    .stFileUploader > div > div {{
        background-color: #e9f2ff;
        border-radius: 8px;
        padding: 1rem;
        border: 2px dashed #99ccff;
    }}
    h1 {{
        color: #003366;
        text-align: center;
    }}
    .final-report {{
        background-color: #e8f5e8;
        padding: 2rem;
        border-left: 8px solid #28a745;
        border-radius: 8px;
        margin: 2rem 0;
        font-size: 1.1rem;
        line-height: 1.6;
    }}
    .footer {{
        text-align: center;
        margin-top: 4rem;
        color: #666;
        font-size: 0.9rem;
    }}
    .watermark {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 48px;
        font-weight: bold;
        color: rgba(0, 102, 204, 0.1);
        pointer-events: none;
        white-space: nowrap;
        z-index: 1;
        font-family: 'Helvetica Neue', sans-serif;
    }}
</style>
<div class="watermark">{random.choice(PHRASES)}</div>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker PRO — Grok-3")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing!")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

st.header("Upload All Files (Plans, Geotech, H1, RFI)")
uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True, key="files")

# ... [rest of your code exactly the same as the last working version] ...
# (extraction, RFI detection, compliance check, fact-check, etc.)

# Keep everything else unchanged — just added the watermark above

# Footer
st.markdown("<div class='footer'>xAI Plan Checker PRO © 2025 | Powered by Grok-3</div>", unsafe_allow_html=True)
