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
col1, col2, col3 = st.columns(3)

with col1:
    check_compliance = st.button("COMPLIANCE CHECK", type="primary")

with col2:
    check_rfi = st.button("RFI RESPONSE", type="secondary")

with col3:
    calc_h1 = st.button("H1 CALCULATION", type="secondary")

# === EXTRACT TEXT ONCE ===
plan_text = ""
h1_data = None
rfi_text = ""

# Only extract if files are uploaded
if plan_files or support_files or rfi_file:
    # Extract plans + support
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
if calc_h1 and h1_data:
    with st.spinner("Calculating H1 Compliance..."):
        try:
            # Parse sheets
            project_details = h1_data.parse("Project Details")
            slab_floors = h1_data.parse("Slab Floors")
            other_floors = h1_data.parse("Other Floors")
            roof = h1_data.parse("Roof")
            skylights = h1_data.parse("Skylights")
            walls = h1_data.parse("Walls")
            glazing = h1_data.parse("Glazing (walls & doors)")
            doors = h1_data.parse("Doors (opaque)")
            results = h1_data.parse("Results")

            # Extract key values
            territorial_authority = project_details.iloc[0, 14] if len(project_details) > 0 else "Unknown"
            climate_zone = project_details.iloc[0, 15] if len(project_details) > 0 else "Unknown"

            # Function to extract R-values
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

            slab_r = extract_r_values(slab_floors)
            other_r = extract_r_values(other_floors)
            roof_r = extract_r_values(roof)
            skylights_r = extract_r_values(skylights)
            walls_r = extract_r_values(walls)
            glazing_r = extract_r_values(glazing)
            doors_r = extract_r_values(doors)

            # Results summary
            result_summary = ""
            for i in range(len(results)):
                row = results.iloc[i]
                if len(row) > 1 and pd.notna(row[1]):
                    result_summary += f"{row[0] if pd.notna(row[0]) else ''}: {row[1]}\n"

            # Display
            st.success("H1 Calculation Complete")
            with st.container():
                st.markdown(f"""
                <div class='h1-calc'>
                <strong>Project:</strong> {territorial_authority}<br>
                <strong>Climate Zone:</strong> {climate_zone}<br><br>
                <strong>Slab Floors R-Values:</strong> {slab_r}<br>
                <strong>Other Floors R-Values:</strong> {other_r}<br>
                <strong>Roof R-Values:</strong> {roof_r}<br>
                <strong>Skylights R-Values:</strong> {skylights_r}<br>
                <strong>Walls R-Values:</strong> {walls_r}<br>
                <strong>Glazing R-Values:</strong> {glazing_r}<br>
                <strong>Doors R-Values:</strong> {doors_r}<br><br>
                <strong>Results Summary:</strong><br>
                {result_summary.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"H1 Error: {e}")
elif calc_h1:
    st.warning("No H1 Excel found in supporting docs.")

# === COMPLIANCE CHECK ===
if check_compliance and (plan_files or support_files):
    if plan_text.strip():
        with st.spinner("Running Full Compliance Check..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor with 20 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE ISSUE.

LOOK FOR:
- KEY/LEGEND items (smoke alarms, vents, fire doors, etc.)
- SYMBOLS on the plan (SD, FD, V, H, etc.)

For EACH non-compliant item:
- FILE NAME + PAGE NUMBER
- Clause (e.g., E1.3.1)
- Issue description
- SUGGESTED FIX
- ALTERNATIVE (if main fix is impractical)

DO NOT SKIP ANYTHING. BE DETAILED.

Example:
- PLAN.pdf Page 6: F7.3.1 smoke detectors
  - Clause: F7.3.1
  - Issue: KEY says "SD required" but no SD in bedrooms
  - Suggested: Add SD within 3m of bedroom doors
  - Alternative: Note "to be installed per F7/AS1"

ONLY bullet points. NO summary."""},
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
                        {"role": "system", "content": """You are a NZBC compliance engineer defending the plans against council RFIs.

FOR EACH RFI POINT:
1. QUOTE THE RFI QUESTION
2. SEARCH THE PLANS HARD — find the exact page and text that answers it
3. IF ANSWERED: Say "ALREADY COMPLIANT" + quote the plan text + page
4. IF NOT ANSWERED: Give practical fix + alternative

Example:
- RFI.pdf Page 1: "No E1 overflow shown"
  - ALREADY COMPLIANT: "Overflow path shown on Page 5 (WD103): 'Secondary flow to boundary at 150mm freeboard'"
  - Fix: Add detail to Page 5 if needed

- RFI.pdf Page 2: "Setback breach"
  - Issue: Building 1.2m from boundary
  - Suggested: Apply for resource consent variation
  - Alternative: Fire-rate wall to FRL 60/60/60 (C6)

ONLY bullet points. NO summary."""},
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
