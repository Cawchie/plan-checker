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

# Upload files
files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if files:
    text = ""
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            text += f"\n--- END OF {f.name} ---\n"
        except Exception as e:
            st.error(f"Error reading {f.name}: {e}")

    if text.strip():
        with st.spinner("Checking compliance..."):
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": """COMPLIANCE CHECK MODE ONLY

You are a New Zealand Building Code expert. DO NOT LEARN — ONLY CHECK COMPLIANCE.

For the uploaded plans:
- Check against ALL known NZBC clauses (E1, D1, B1, H1, etc.)
- Check against council rules, RFIs, and past responses
- Give ONLY bullet points for NON-COMPLIANT issues
- Include PAGE NUMBERS
- No learning summary, no progress %, no "ready for more data"
- Example: "- Page 5: E1 surface water missing (Clause E1.3.1)"""},
                        {"role": "user", "content": text}
                    ]
                )
                st.success("Compliance Check Complete")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"API Error: {e}")
    else:
        st.warning("No readable text in the PDF(s).")
