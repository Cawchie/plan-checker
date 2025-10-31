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
    .saved-job { background-color: #e7f3ff; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

st.title("xAI Plan Checker")

# Get key
api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Settings.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

# === SAVE JOBS (SESSION STATE) ===
if 'saved_jobs' not in st.session_state:
    st.session_state.saved_jobs = {}

# === UPLOADS ===
st.header("Upload Plans (Required)")
plan_files = st.file_uploader("Upload plans", type="pdf", accept_multiple_files=True, key="plans")

st.header("Upload Supporting Docs (Geotech, H1, etc.)")
support_files = st.file_uploader("Upload geotech, H1 calcs, etc.", type="pdf", accept_multiple_files=True, key="support")

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
    save_job = st.button("SAVE JOB", type="secondary")

# === EXTRACT TEXT ONCE ===
text = ""
rfi_text = ""
geotech_text = ""

if files or rfi_file:
    # Extract plans + support
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    if any(keyword in f.name.lower() for keyword in ["geotech", "geotechnical", "soil"]):
                        geotech_text += f"--- GEOTECH: {f.name} - Page {page_num} ---\n{t}\n"
                    else:
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

# === SAVE JOB ===
if save_job and files:
    job_name = st.text_input("Job Name (e.g., 146 Martyn Wright)", key="save_job_name")
    if job_name and st.button("Confirm Save"):
        st.session_state.saved_jobs[job_name] = {
            "files": files,
            "text": text,
            "rfi_text": rfi_text,
            "geotech_text": geotech_text
        }
        st.success(f"Job '{job_name}' saved!")

# === LOAD JOB ===
if st.session_state.saved_jobs:
    st.header("Saved Jobs")
    load_job = st.selectbox("Load a saved job", [""] + list(st.session_state.saved_jobs.keys()))
    if load_job:
        job = st.session_state.saved_jobs[load_job]
        text = job["text"]
        rfi_text = job["rfi_text"]
        geotech_text = job["geotech_text"]
        st.markdown(f"<div class='saved-job'><strong>{load_job}</strong> loaded. Use buttons below.</div>", unsafe_allow_html=True)

# === COMPLIANCE CHECK ===
if check_compliance and (files or load_job):
    if text.strip():
        with st.spinner("Running Full Compliance Check..."):
            try:
                full_context = ""
                if geotech_text:
                    full_context += f"GEOTECH REPORT:\n{geotech_text}\n"
                full_context += f"PLANS & CALCS:\n{text}"

                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor with 20 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE ISSUE.

GEOTECH INTEGRATION (CRITICAL):
- GEOTECH REPORT IS UPLOADED — USE IT FOR ALL B1.3.1 CHECKS
- Verify soil bearing (Cu=70 kPa), liquefaction, slope stability
- IF GEOTECH MATCHES CALCS: CLEAR THE FLAG
- IF NOT: FLAG + quote geotech data

For EACH non-compliant item:
- FILE NAME + PAGE NUMBER
- Clause (e.g., B1.3.1)
- Issue description
- SUGGESTED FIX
- ALTERNATIVE (if main fix is impractical)

CHECK:
E1, E2, E3, B1, B2, D1, D2, F1–F9, G1–G15, H1
Council: height, coverage, setbacks, zoning
Weathertightness: flashing, cladding, junctions

DO NOT FLAG GEOTECH IF REPORT IS UPLOADED AND MATCHES.

ONLY bullet points. NO summary."""},
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
if check_rfi and (rfi_file or load_job):
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
