# -*- coding: utf-8 -*-
"""Connexion de l'équipe : identifiant et mot de passe, vérifiés par PostgreSQL (bcrypt)."""
import time

import streamlit as st

from commun import db
from commun.theme import BORD, GRIS

_, centre, _ = st.columns([1, 1.3, 1])
with centre:
    st.markdown('<div class="titre" style="font-size:30px">Espace équipe</div>'
                f'<div style="color:{GRIS};margin-bottom:12px">Serveurs et gérants des établissements clients de MenuScan TN.</div>',
                unsafe_allow_html=True)
    with st.form("connexion", border=True):
        identifiant = st.text_input("Identifiant", placeholder="gerant.etb0005")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        envoyer = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
    if envoyer:
        u = db.authentifier(identifiant, mot_de_passe)
        if u:
            st.session_state.utilisateur = u
            st.rerun()
        time.sleep(1)  # ralentit les essais en série
        st.error("Identifiant ou mot de passe incorrect.")
    st.markdown(f"""<div style="background:#fff;border:1px dashed {BORD};border-radius:16px;padding:14px 16px;font-size:14px;color:#334155;margin-top:12px">
      <b>Comptes de démonstration</b><br>
      Gérant : <code>gerant.etb0005</code> · Serveur : <code>serveur.etb0005</code> (Café Les Arcades)<br>
      Mot de passe : <code>Demo2026!</code><br>
      <span style="color:{GRIS}">Même principe pour chaque établissement : <code>gerant.etbXXXX</code>, <code>serveur.etbXXXX</code>.</span></div>""",
                unsafe_allow_html=True)
