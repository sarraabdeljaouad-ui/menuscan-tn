# -*- coding: utf-8 -*-
"""Application équipe MenuScan TN (back-office) : accueil public, connexion, puis écran selon le rôle (gérant ou serveur).

Lancement, depuis le dossier 01_application/equipe, environnement Python activé :
    streamlit run app.py          (port 8502, défini dans .streamlit/config.toml)
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from commun import db, theme  # noqa: E402
from commun.theme import e  # noqa: E402

st.set_page_config(page_title="MenuScan TN · Équipe", page_icon=":material/storefront:", layout="wide")
theme.appliquer()
try:
    db.moteur()
except db.MigrationManquante as err:
    st.error(str(err))
    st.stop()

u = st.session_state.get("utilisateur")
accueil = st.Page("vues/accueil.py", title="Accueil", icon=":material/home:", default=u is None)
if u is None:
    pages = [accueil, st.Page("vues/connexion.py", title="Se connecter", icon=":material/login:", url_path="connexion")]
else:
    titre = "Tableau de bord" if u["role"] == "gerant" else "Service"
    pages = [st.Page("vues/tableau.py", title=titre, icon=":material/dashboard:" if u["role"] == "gerant" else ":material/room_service:",
                     url_path="tableau", default=True)]
    with st.sidebar:
        role = "Gérant" if u["role"] == "gerant" else "Serveur"
        st.markdown(f"""<div style="background:rgba(255,255,255,.1);border-radius:16px;padding:12px 14px;font-size:14px;margin-top:8px">
          <b>{e(u['nom_etablissement'])}</b><br><span style="color:#C7D7F5">{e(u['nom_ville'])} · formule {e(u['nom_formule'] or '–')}</span><br>
          <span style="color:#C7D7F5">{role} · {e(u['identifiant'])}</span></div>""", unsafe_allow_html=True)
        if st.button("Se déconnecter", icon=":material/logout:", use_container_width=True):
            st.session_state.clear()
            st.rerun()

st.navigation(pages).run()
