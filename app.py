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
    st.write("**Grok is checking your site against the 2026 exemption rules...**")
    
    if size > 70:
        st.error("**Āroha mai** – This size is over 70 m² so it does not qualify for the exemption.")
        st.info("You will likely need full building consent. We can still help with custom NOHO designs that honour your whenua.")
    else:
        st.success("**Yes – your site looks perfect for a NOHO cabin under 70 m².**")
        st.info("A place to stay, to sit, to dwell, to live.")
        
        if not single or not detached or not self_contained:
            st.warning("**One small thing:** Make sure it is single-storey, standalone, and fully self-contained. Double-check with your LBP and council.")

st.caption("This is a helpful guide only. Always confirm with your Licensed Building Practitioner and local council.")
