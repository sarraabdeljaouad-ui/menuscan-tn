# -*- coding: utf-8 -*-
"""Espace gérant : commandes en cours, appels du serveur, activité du jour.

Démonstration : le choix de l'établissement est libre, sans authentification.
"""
import streamlit as st

import db

MODES = {"Espèces": "especes", "Carte bancaire": "carte_bancaire", "Ticket restaurant": "ticket_restaurant"}


def prix(x):
    return f"{x:.3f} DT".replace(".", ",")


st.title("Espace gérant")
etabs = db.etablissements_commande()
if not etabs:
    st.info("Aucun établissement actif avec la commande depuis la table.")
    st.stop()
libelles = {e["etablissement_id"]: f"{e['nom_etablissement']} ({e['nom_ville']})" for e in etabs}
choix = st.selectbox("Établissement", list(libelles), format_func=libelles.get, key="etab_gerant")
st.caption("Démonstration : sans authentification. La restriction par établissement arrive avec la sécurité par ligne (phase 6).")


def servir(commande_id):
    db.servir(commande_id, MODES[st.session_state[f"m_{commande_id}"]])


@st.fragment(run_every="10s")
def tableau():
    act = db.activite_du_jour(choix)
    c1, c2, c3 = st.columns(3)
    c1.metric("Commandes servies aujourd'hui", act["servies"])
    c2.metric("Annulées", act["annulees"])
    c3.metric("Chiffre servi", prix(act["chiffre"]))

    appels = db.appels_recents(choix)
    if appels:
        st.warning("🔔 " + " · ".join(f"table {a['numero_table']} à {a['horodatage']:%H:%M}" for a in appels))

    st.subheader("Commandes en cours")
    cmds = db.commandes_en_cours(choix)
    if not cmds:
        st.caption("Aucune commande en attente. Mise à jour automatique toutes les 10 secondes.")
    for c in cmds:
        with st.container(border=True):
            st.markdown(f"**Table {c['numero_table']}** ({c['zone']}) · {c['date_heure_commande']:%H:%M} · {c['commande_id']} · **{prix(c['montant_total_ttc'])}**")
            st.write(c["detail"])
            k1, k2, k3 = st.columns([2, 1, 1], vertical_alignment="bottom")
            k1.selectbox("Règlement", list(MODES), key=f"m_{c['commande_id']}")
            k2.button("Servie", key=f"s_{c['commande_id']}", type="primary", on_click=servir, args=(c["commande_id"],))
            k3.button("Annuler", key=f"a_{c['commande_id']}", on_click=db.annuler, args=(c["commande_id"],))


tableau()
