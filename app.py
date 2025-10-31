import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.title("xAI Plan Checker")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing!")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

files = st.file_uploader("Upload Full Plans", type="pdf", accept_multiple_files=True)

if files:
    all_issues = []
    for f in files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                if not text.strip():
                    continue

                # Add page header
                chunk = f"--- {f.name} - Page {page_num} ---\n{text}"

                with st.spinner(f"Checking {f.name} Page {page_num}..."):
                    try:
                        resp = client.chat.completions.create(
                            model="grok-3-mini",
                            messages=[
                                {"role": "system", "content": "You are a NZBC expert. Give ONLY bullet points for non-compliant issues with PAGE NUMBERS. Example: '- Page {page_num}: E1 missing'"},
                                {"role": "user", "content": chunk}
                            ]
                        )
                        issues = resp.choices[0].message.content.strip()
                        if issues:
                            all_issues.append(issues)
                    except Exception as e:
                        st.error(f"Error on {f.name} Page {page_num}: {e}")

        except Exception as e:
            st.error(f"Failed to read {f.name}: {e}")

    if all_issues:
        st.success("Full Compliance Check Complete")
        st.markdown("\n\n".join(all_issues))
    else:
        st.success("No non-compliant issues found!")
