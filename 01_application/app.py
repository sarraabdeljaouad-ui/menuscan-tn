# -*- coding: utf-8 -*-
"""MenuScan TN : application de menu numérique et de commande depuis la table.

Lancement, depuis le dossier 01_application, environnement Python activé :
    streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="MenuScan TN", page_icon="🍽️", layout="centered")

pages = [
    st.Page("pages/accueil.py", title="Accueil", icon=":material/home:", url_path="accueil", default=True),
    st.Page("pages/menu_client.py", title="Menu client", icon=":material/restaurant_menu:", url_path="menu"),
    st.Page("pages/espace_gerant.py", title="Espace gérant", icon=":material/storefront:", url_path="gerant"),
]
st.navigation(pages).run()
