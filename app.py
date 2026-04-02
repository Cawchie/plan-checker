import streamlit as st

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
    if size <= 70:
        st.success("**Yes – your site looks perfect for a NOHO cabin under 70 m².**\nA place to stay, to sit, to dwell, to live.")
        st.info("Next steps: Hand the plans to your Licensed Building Practitioner, notify council via PIM, and build with confidence.")
    else:
        st.error("**Āroha mai** – This size may need full consent.\nThe 2026 exemption is for dwellings 70 m² or under.")
        st.info("We can still help with thoughtful custom designs that honour your whenua.")

st.caption("This is a helpful guide only. Always confirm with your LBP and local council.")
