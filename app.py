import streamlit as st

st.set_page_config(page_title="NOHO Site Checker", page_icon="🌿", layout="centered")

st.image("https://brad21005.wixsite.com/noho/NOHO-logo.png", width=180)  # replace with your actual logo URL if needed
st.title("Check if your site can use the 2026 exemption")
st.markdown("**Tiny homes. Enormous living.**  \nA calm, simple check for the new building consent exemption in Aotearoa.")

st.write("---")

size = st.number_input("Approx. size of building you want (m²)", min_value=10, max_value=200, value=55, step=1)

single_storey = st.checkbox("It is single-storey")
standalone = st.checkbox("It is detached / standalone")
self_contained = st.checkbox("It will be fully self-contained (kitchen, bathroom, living, sleeping)")

if st.button("Check My Site", type="primary"):
    if size > 70:
        st.error("**Āroha mai** – This size may need full consent. The 2026 exemption is for dwellings 70 m² or under.")
        st.info("We can still help with thoughtful custom designs that honour your whenua.")
    elif not single_storey:
        st.warning("**Almost** – The exemption requires single-storey only.")
    elif not standalone:
        st.warning("**Almost** – The exemption requires a detached, standalone dwelling.")
    elif not self_contained:
        st.warning("**Almost** – The exemption requires a fully self-contained dwelling.")
    else:
        st.success("**Yes – your site looks perfect for a NOHO cabin under 70 m².**  \nA place to stay, to sit, to dwell, to live.")
        st.info("Next steps: Hand the plans to your Licensed Building Practitioner, notify council via PIM, and build with confidence.")

st.caption("This is a helpful guide only. You and your LBP are responsible for confirming site-specific compliance with the Building and Construction (Small Stand-alone Dwellings) Amendment Act 2025.")
