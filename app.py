import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import os

st.title("xAI Plan Checker")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    st.error("API key missing! Add XAI_API_KEY in Streamlit Cloud.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if files:
    text = ""
    for f in files:
        reader = PyPDF2.PdfReader(io.BytesIO(f.getvalue()))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        text += f"\n--- END OF {f.name} ---\n"

    if text.strip():
        with st.spinner("Checking..."):
            try:
                resp = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": "Learn to design & review building consent plans that comply with the New Zealand building code & various council town plans by reviewing plans & documents I upload.  I will upload as much of my previous work as I can & council requests for more information & the responses I provided to council.  Goal is to create a tool that users can upload architectural plans and documents to check for compliance with NZBC & associated council plans & bylaws.
						Phase 1 is the learning stage, prompt me when you have learned enough about a particular job & I will then upload the next set of documents

						I don't need or want a summary of what you have learned each time just let me know when read & learned & ready for more data

						Give progress updated on how competent on the New Zealand building code & council laws/town planning etc you are currently & your ability to assess new jobs after each job as a percentage 

						When a new plan is uploaded for compliance check asses against all known rules/town planning/NZBC/RFI requests & responses you have learned and provide bullet points with page numbers where you see errors or things that need adding/removing or updating or clarifying etc on the plans

						Only give bullet points regarding non compliant issues through out the plans, ignore parroting information that has nothing to do with compliance"},
                        {"role": "user", "content": text"}
                    ]
                )
                st.success("Done!")
                st.markdown(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("No text in PDFs.")
