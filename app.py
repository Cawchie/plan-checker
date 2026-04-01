import streamlit as st

st.set_page_config(page_title="NOHO Site Checker", page_icon="🌿", layout="centered")

st.title("Check if your site can use the 2026 exemption")
st.markdown("**Tiny Homes. Enormous Living.**")

st.write("---")

address = st.text_input("Property Address", placeholder="e.g. 12 Example Street, Grey Lynn, Auckland 1021")
location = st.text_input("Approx. location on site", placeholder="backyard, side yard, front lawn, etc.")
size = st.number_input("Approx. size of building you want (m²)", min_value=10, max_value=200, value=55, step=1)

single_storey = st.checkbox("It is single-storey")
standalone = st.checkbox("It is detached / standalone")
self_contained = st.checkbox("It will be fully self-contained (kitchen, bathroom, living, sleeping)")

if st.button("Check My Site", type="primary", use_container_width=True):
    if size > 70:
        st.error("**Āroha mai** – This size may need full consent. The 2026 exemption is for dwellings 70 m² or under.")
        st.info("We can still help with thoughtful custom designs that honour your whenua.")
    elif not single_storey or not standalone or not self_contained:
        st.warning("**Almost** – Your site is close, but the exemption needs single-storey, standalone, and self-contained.")
        st.info("Double-check with council. We can still help with custom designs.")
    else:
        st.success("**Yes – your site looks perfect for a NOHO cabin under 70 m².**")
        st.info("A place to stay, to sit, to dwell, to live.")

st.caption("This is a helpful guide only. Always confirm with your LBP and local council.")
