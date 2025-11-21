import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os
import random

# === FUNNY RANDOM PHRASES ===
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

# === CSS + WATERMARK THAT ONLY APPEARS DURING SPINNER ===
st.markdown(f"""
<style>
    .main {{
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
    }}
    .stButton>button {{
        background-color: #0066cc !important;
        color: white !important;
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
    h1 {{ color: #003366; text-align: center; }}
    .final-report {{
        background-color: #e8f5e8;
        padding: 2rem;
        border-left: 8px solid #28a745;
        border-radius: 8px;
        margin: 2rem 0;
        font-size: 1.1rem;
        line-height: 1.6;
    }}
    .footer {{ text-align: center; margin-top: 4rem; color: #666; font-size: 0.9rem; }}
    .thinking-watermark {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 52px;
        font-weight: bold;
        color: rgba(0, 102, 204, 0.12);
        pointer-events: none;
        white-space: nowrap;
        z-index: 9999;
        font-family: 'Helvetica Neue', sans-serif;
    }}
</style>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker PRO — Grok-3")

# Header and uploader
st.header("Upload All Files (Plans, Geotech, H1, RFI)")
uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True, key="files")

# === FORCE BUTTONS TO SHOW ===
col1, col2 = st.columns(2)
with col1:
    check_compliance = st.button("**COMPLIANCE CHECK**", type="primary", use_container_width=True)
with col2:
    check_rfi = st.button("**RFI RESPONSE**", type="secondary", use_container_width=True)

# Show thinking watermark only when spinner is active
thinking_placeholder = st.empty()

# Your existing extraction code here (unchanged)
# ... [all your file reading, plan_text, rfi_text code] ...

if check_compliance and other_files:
    if plan_text.strip():
        # Show random watermark during processing
        thinking_placeholder.markdown(
            f'<div class="thinking-watermark">{random.choice(PHRASES)}</div>',
            unsafe_allow_html=True
        )
        with st.spinner("Grok-3 is analysing every page..."):
            try:
                # ... your Grok calls ...
                # after final_report is ready:
                thinking_placeholder.empty()  # remove watermark when done
                st.balloons()
                st.success("100% ACCURATE REPORT READY")
                st.markdown(f"<div class='final-report'><strong>FINAL REPORT — GROK-3</strong>\n\n{final_report}</div>", unsafe_allow_html=True)
            except Exception as e:
                thinking_placeholder.empty()
                st.error(f"Error: {e}")
    else:
        st.warning("No text found in plans.")
else:
    thinking_placeholder.empty()  # make sure it's gone when idle

# Footer
st.markdown("<div class='footer'>xAI Plan Checker PRO © 2025 | Powered by Grok-3</div>", unsafe_allow_html=True)
