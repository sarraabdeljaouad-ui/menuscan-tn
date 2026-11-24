# -*- coding: utf-8 -*-
"""MenuScan TN : application de menu numérique et de commande depuis la table.

Lancement, depuis le dossier 01_application, environnement Python activé :
    streamlit run app.py
"""
import streamlit as st

import db
import theme

st.set_page_config(page_title="MenuScan TN", page_icon=":material/qr_code_2:", layout="centered")
theme.appliquer()

try:
    db.moteur()
except db.MigrationManquante as e:
    st.error(str(e))
    st.stop()

pages = [
    st.Page("vues/accueil.py", title="Accueil", icon=":material/home:", default=True),
    st.Page("vues/menu_client.py", title="Menu client", icon=":material/restaurant_menu:", url_path="menu"),
    st.Page("vues/espace_gerant.py", title="Espace gérant", icon=":material/storefront:", url_path="gerant"),
]
st.navigation(pages).run()
