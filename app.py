import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.title("xAI Plan Checker")

# Get key from secret
api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Settings.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

# Step 1: Upload plans
st.header("Step 1: Upload Plans")
plan_files = st.file_uploader("Upload plans", type="pdf", accept_multiple_files=True, key="plans")

# Step 2: Upload supporting docs
st.header("Step 2: Upload Supporting Docs")
support_files = st.file_uploader("Upload geotech, H1, RFIs", type="pdf", accept_multiple_files=True, key="support")

# Combine files
files = plan_files + support_files

if files and st.button("Check Compliance"):
    text = ""
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text += f"--- {f.name} - Page {page_num} ---\n{page_text}\n"
        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    if text.strip():
        with st.spinner("Full Compliance Check..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """You are a NZBC compliance auditor with 20 years experience.

CHECK EVERY SINGLE PAGE FOR EVERY POSSIBLE ISSUE.

For EACH non-compliant item:
- FILE NAME + PAGE NUMBER
- Clause (e.g., E1.3.1)
- Issue description
- POTENTIAL FIX

CHECK THESE CLAUSES:
E1, E2, E3, B1, B2, D1, D2, F1–F9, G1–G15, H1
Council: height, coverage, setbacks, zoning, RFI responses
Geotech: soil bearing, liquefaction, slope stability
H1: R-values, thermal bridging, glazing U-values

DO NOT SKIP ANYTHING. BE DETAILED.

Example:
- 85 CAPE HILL.pdf Page 3: E1.3.1 non-compliant
  - Clause: E1.3.1
  - Issue: No overflow path for 1:100 year storm
  - Fix: Add 150mm freeboard or secondary flow path to boundary

ONLY bullet points. NO summary. NO "ready for more data"."""},
                        {"role": "user", "content": text}
                    ]
                )
                st.success("Compliance Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No text found in PDFs.")
