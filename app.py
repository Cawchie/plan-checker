import streamlit as st
import requests

st.set_page_config(page_title="NOHO Site Checker", page_icon="🌿", layout="centered")

st.title("Check if your site can use the 2026 exemption")
st.markdown("**Tiny Homes. Enormous Living.**")

st.write("---")

address = st.text_input("Property Address", placeholder="e.g. 77a Helvetia road, Pukekohe")
location = st.text_input("Approx. location on site", placeholder="backyard, side yard, front lawn, etc.")
size = st.number_input("Approx. size of building you want (m²)", min_value=10, max_value=200, value=55, step=1)

st.write("---")

single = st.checkbox("It is single-storey", value=True)
detached = st.checkbox("It is detached / standalone", value=True)
self_contained = st.checkbox("It will be fully self-contained (kitchen, bathroom, living, sleeping)", value=True)

if st.button("Check My Site", type="primary", use_container_width=True):
    with st.spinner("Grok is checking the 2026 exemption rules for you..."):
        prompt = f"""
You are Grok helping a Kiwi check if their site qualifies for the 2026 building consent exemption for small stand-alone dwellings (max 70 m², single-storey, detached, self-contained).

Inputs:
- Address: {address}
- Location on site: {location}
- Proposed size: {size} m²
- Single-storey: {single}
- Detached: {detached}
- Self-contained: {self_contained}

Give a calm, warm, Kiwi-friendly answer. Use te reo where natural. Tell them clearly if it qualifies or not, and why. End with next steps.
"""

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['XAI_API_KEY']}"},
            json={
                "model": "grok-beta",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )

        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            st.markdown(answer)
        else:
            st.error("Something went wrong with the Grok API. Please check your secret key.")

st.caption("This tool uses Grok (xAI) for real checking. Always confirm with your LBP and local council.")
