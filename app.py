import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os
import pandas as pd

# === PRO LOOK (CSS) ===
st.markdown("""
<style>
    .main { background-color: #f8f9fa; padding: 2rem; border-radius: 10px; }
    .stButton>button { background-color: #007bff; color: white; font-weight: bold; border-radius: 8px; padding: 0.6rem 1.2rem; font-size: 1.1rem; width: 100%; margin: 0.5rem 0; }
    .stFileUploader > div > div { background-color: #e9ecef; border-radius: 8px; padding: 1rem; border: 2px dashed #ced4da; }
    h1, h2, h3 { color: #343a40; font-family: 'Helvetica', sans-serif; font-weight: 600; }
    .report { background-color: #fff3cd; padding: 1.2rem; border-left: 6px solid #ffc107; border-radius: 8px; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.6; }
    .h1-calc { background-color: #d4edda; padding: 1.2rem; border-left: 6px solid #28a745; border-radius: 8px; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.6; }
    .initial-check { background-color: #cce5ff; padding: 1.2rem; border-left: 6px solid #007bff; border-radius: 8px; margin: 1.5rem 0; font-size: 1.05rem; line-height: 1.6; }
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

# === BUTTONS ===
col1, col2, col3, col4 = st.columns(4)

with col1:
    initial_check = st.button("INITIAL JOB CHECK", type="secondary")

with col2:
    check_compliance = st.button("COMPLIANCE CHECK", type="primary")

with col3:
    check_rfi = st.button("RFI RESPONSE", type="secondary")

with col4:
    calc_h1 = st.button("H1 CALCULATION", type="secondary")

# === EXTRACT TEXT ONCE ===
plan_text = ""
h1_data = None
rfi_text = ""

if plan_files or support_files or rfi_file:
    for f in (plan_files or []) + (support_files or []):
        if f.name.lower().endswith('.xlsx'):
            try:
                h1_data = pd.ExcelFile(io.BytesIO(f.getvalue()))
                st.success(f"H1 Excel {f.name} loaded.")
            except Exception as e:
                st.error(f"Failed to read Excel {f.name}: {e}")
        else:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
                for page_num, page in enumerate(reader.pages, 1):
                    t = page.extract_text() or ""
                    if t.strip():
                        plan_text += f"--- Page {page_num} ---\n{t}\n"
            except Exception as e:
                st.error(f"Failed to read {f.name}: {e}")

    if rfi_file:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(rfi_file.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                t = page.extract_text() or ""
                if t.strip():
                    rfi_text += f"--- RFI Page {page_num} ---\n{t}\n"
        except Exception as e:
            st.error(f"Failed to read RFI: {e}")

# === INITIAL JOB CHECK ===
if initial_check and plan_text:
    with st.spinner("Running Initial Job Check..."):
        try:
            response = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": """You are a NZBC compliance expert.

EXTRACT FROM PLANS:
- Address
- Council authority
- Planning zone
- Wind zone
- Earthquake zone
- Corrosion zone

CHECK IF:
- Address matches council/zone
- Zones match site (e.g., rural zone setbacks 20m front, 10m side/rear; height 10m, coverage 10%)
- Sound (e.g., Waikato Rural Zone: front 20m, side/rear 10m, height 10m, coverage 10%)

GIVE:
- PASS/FAIL
- Required vs Actual
- Fix if failed

ONLY bullet points. Example:
- Address: 85 Barnaby Road, Tuakau → PASS
- Council: Waikato → PASS
- Zone: Rural (Franklin) → PASS (setbacks 20m front, 10m side/rear)
- Wind Zone: Very High → FAIL (plans show Low)
  - Fix: Upgrade fixings per NZS3604 Table 5.1"""},
                    {"role": "user", "content": plan_text}
                ]
            )
            st.success("Initial Job Check Complete")
            with st.container():
                st.markdown(f"<div class='initial-check'>{response.choices[0].message.content}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"API Error: {e}")
elif initial_check:
    st.warning("No plans found.")

# === H1 CALCULATION ===
if calc_h1 and h1_data:
    with st.spinner("Calculating H1 Compliance..."):
        try:
            project_details = h1_data.parse("Project Details")
            territorial_authority = project_details.iloc[0, 14] if len(project_details) > 0 else "Unknown"
            climate_zone = project_details.iloc[0, 15] if len(project_details) > 0 else "Unknown"

            def extract_r_values(df, r_col=2):
                r_vals = []
                for i in range(len(df)):
                    val = df.iloc[i, r_col]
                    if pd.notna(val) and str(val).strip() and str(val).strip() != "No":
                        try:
                            r_vals.append(float(val))
                        except:
                            pass
                return r_vals

            slab_r = extract_r_values(h1_data.parse("Slab Floors"))
            other_r = extract_r_values(h1_data.parse("Other Floors"))
            roof_r = extract_r_values(h1_data.parse("Roof"))
            walls_r = extract_r_values(h1_data.parse("Walls"))

            st.success("H1 Calculation Complete")
            with st.container():
                st.markdown(f"""
                <div class='h1-calc'>
                <strong>Project:</strong> {territorial_authority}<br>
                <strong>Climate Zone:</strong> {climate_zone}<br><br>
                <strong>Slab R:</strong> {slab_r}<br>
                <strong>Other Floors R:</strong> {other_r}<br>
                <strong>Roof R:</strong> {roof_r}<br>
                <strong>Walls R:</strong> {walls_r}<br>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"H1 Error: {e}")
elif calc_h1:
    st.warning("No H1 Excel found.")

# === COMPLIANCE CHECK (MAX DETAIL) ===
if check_compliance and (plan_files or support_files):
    if plan_text.strip():
        with st.spinner("Running Full Compliance Check (Maximum Detail)..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC E2 weathertightness auditor with 30 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE E2 ISSUE.

MUST FIND:
- 135° corners (internal/external)
- Window/door penetrations
- Pipe penetrations
- Roof/wall junctions
- Base details
- Flashing (head, sill, jamb, apron)
- Cavity battens
- Soffit junctions
- Brick to Stria transitions
- Pipe penetration sealing
- Meter box flashing
- Balustrade junctions
- Garage door jambs

FLAG EVERY MISSING DETAIL.

For EACH issue:
- Page X
- Clause (e.g., E2.3.2)
- Issue
- SUGGESTED FIX
- ALTERNATIVE

BE EXTREMELY THOROUGH. DO NOT MISS ANYTHING.

Example:
- Page 4
  - Clause: E2.3.2 (External Moisture - 135° Corners)
  - Issue: 135° internal corner at north-east wall has no flashing detail
  - Suggested Fix: Add 135° corner flashing with 150mm upstand and stop-end
  - Alternative: Use pre-formed 135° flashing with sealant

ONLY bullet points. NO FILE NAME. NO ADDRESS."""},
                        {"role": "user", "content": plan_text}
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
