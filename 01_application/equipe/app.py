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

COOKIE = "menuscan_equipe"
etat = st.session_state


def poser_cookie(valeur, age):
    """Écrit le cookie de connexion dans le navigateur (Streamlit sait lire les cookies, pas les écrire)."""
    st.html(f"<script>document.cookie = '{COOKIE}={valeur}; path=/; max-age={age}; SameSite=Strict';</script>",
            unsafe_allow_javascript=True, width=1)


# Connexion gardée 30 jours sans utilisation : le cookie porte un jeton aléatoire, la base n'en garde que l'empreinte.
if etat.get("utilisateur") is None and not etat.get("deconnecte"):
    jeton = st.context.cookies.get(COOKIE)
    compte = db.compte_par_jeton(jeton)
    if compte:
        etat.utilisateur, etat.jeton, etat.cookie_a_poser = compte, jeton, jeton
if etat.get("cookie_a_poser"):  # connexion ou retour sur la page : la validité de 30 jours repart de maintenant
    poser_cookie(etat.pop("cookie_a_poser"), db.DUREE_CONNEXION_JOURS * 86400)
if etat.pop("cookie_a_effacer", False):
    poser_cookie("", 0)


def deconnecter(tous=False):
    u = etat.utilisateur
    if tous:
        db.deconnecter_etablissement(u["etablissement_id"])
    else:
        db.supprimer_jeton(etat.get("jeton"))
    etat.clear()
    etat.deconnecte, etat.cookie_a_effacer = True, True  # le cookie lu au chargement de la page ne doit plus servir


u = etat.get("utilisateur")
accueil = st.Page("vues/accueil.py", title="Accueil", icon=":material/home:", default=u is None)
if u is None:
    pages = [accueil, st.Page("vues/connexion.py", title="Se connecter", icon=":material/login:", url_path="connexion")]
else:
    titre = "Tableau de bord" if u["role"] == "gerant" else "Service"
    pages = [st.Page("vues/tableau.py", title=titre, icon=":material/dashboard:" if u["role"] == "gerant" else ":material/room_service:",
                     url_path="tableau", default=True),
             st.Page("vues/menu.py", title="Menu", icon=":material/restaurant_menu:", url_path="menu")]
    if u["role"] == "gerant":
        pages.append(st.Page("vues/activite.py", title="Activité des tables", icon=":material/table_restaurant:", url_path="activite"))
        pages.append(st.Page("vues/qr_codes.py", title="Tables et QR codes", icon=":material/qr_code_2:", url_path="qr"))
    with st.sidebar:
        role = "Gérant" if u["role"] == "gerant" else "Serveur"
        st.markdown(f"""<div style="background:rgba(255,255,255,.1);border-radius:16px;padding:12px 14px;font-size:14px;margin-top:8px">
          <b>{e(u['nom_etablissement'])}</b><br><span style="color:#C7D7F5">{e(u['nom_ville'])} · formule {e(u['nom_formule'] or '–')}</span><br>
          <span style="color:#C7D7F5">{role} · {e(u['identifiant'])}</span></div>""", unsafe_allow_html=True)
        st.button("Se déconnecter", icon=":material/logout:", width="stretch", on_click=deconnecter)
        if u["role"] == "gerant":
            with st.popover("Déconnecter partout", icon=":material/devices:", width="stretch"):
                st.caption("Tous les téléphones et tablettes connectés aux comptes de l'établissement (gérant et serveur) "
                           "devront se reconnecter. À utiliser si un appareil est perdu ou si un serveur part.")
                st.button("Confirmer", type="primary", on_click=deconnecter, kwargs=dict(tous=True), width="stretch")

st.navigation(pages).run()
