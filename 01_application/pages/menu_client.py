# -*- coding: utf-8 -*-
"""Menu client : ouvert par le QR code de la table (/menu?table=TBL00001)."""
import streamlit as st

import db


def prix(x):
    return f"{x:.3f} DT".replace(".", ",")


def appareil():
    ua = (st.context.headers.get("User-Agent") or "").lower()
    if "iphone" in ua or "ipad" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    return "web"  # ordinateur : valeur propre à l'application, absente des données générées


table_id = st.query_params.get("table")
if not table_id:
    st.warning("Scannez le QR code de votre table pour ouvrir le menu.")
    st.stop()

info = db.table_et_etablissement(table_id)
if info is None:
    st.error("Ce QR code ne correspond à aucune table.")
    st.stop()
if info["statut_etablissement"] != "actif" or info["formule_id"] is None:
    st.error("Le menu de cet établissement n'est plus disponible.")
    st.stop()

etab = info["etablissement_id"]
peut_commander = bool(info["inclut_commande"])

# Une session par scan : on la crée une seule fois par onglet et par table.
etat = st.session_state
if etat.get("table") != table_id or etat.get("session_id") is None:
    etat.table = table_id
    etat.session_id = db.ouvrir_session(table_id, etab, appareil())
    etat.panier = {}
    etat.commande = None

st.title(info["nom_etablissement"])
st.caption(f"{info['nom_ville']} · table {info['numero_table']} ({info['zone']}) · formule {info['nom_formule']}")

if etat.commande:
    cid, total = etat.commande
    st.success(f"Commande {cid} envoyée en cuisine. Total : {prix(total)}.")
    if st.button("Nouvelle commande", type="primary"):
        etat.session_id = None  # une commande par session : une nouvelle commande ouvre une nouvelle session
        st.rerun()
    st.stop()

articles = db.menu(etab)
if not articles:
    st.info("Le menu est vide pour le moment.")
    st.stop()
noms = {a["article_id"]: a for a in articles}


def ajouter(article_id):
    etat.panier[article_id] = etat.panier.get(article_id, 0) + 1
    db.journaliser(etat.session_id, etab, "ajout_panier", article_id, 1)


def retirer(article_id):
    q = etat.panier.get(article_id, 0)
    if q:
        etat.panier[article_id] = q - 1
        if etat.panier[article_id] == 0:
            del etat.panier[article_id]
        db.journaliser(etat.session_id, etab, "retrait_panier", article_id, 1)


categories = list(dict.fromkeys(a["nom_categorie"] for a in articles))
onglets = st.tabs(categories)
for onglet, cat in zip(onglets, categories):
    with onglet:
        for a in (x for x in articles if x["nom_categorie"] == cat):
            c1, c2, c3 = st.columns([5, 2, 2], vertical_alignment="center")
            c1.write(a["nom_article"])
            c2.write(prix(a["prix_ttc"]))
            if peut_commander:
                q = etat.panier.get(a["article_id"], 0)
                c3.button(f"＋ {q}" if q else "＋", key=f"aj_{a['article_id']}", on_click=ajouter, args=(a["article_id"],))

if not peut_commander:
    st.info("Menu consultable uniquement : la commande depuis la table n'est pas proposée par cet établissement.")
    st.stop()

st.divider()
st.subheader("Mon panier")
if not etat.panier:
    st.caption("Votre panier est vide.")
else:
    total = 0
    for aid, q in list(etat.panier.items()):
        a = noms[aid]
        c1, c2, c3 = st.columns([5, 2, 2], vertical_alignment="center")
        c1.write(f"{q} × {a['nom_article']}")
        c2.write(prix(q * a["prix_ttc"]))
        c3.button("－", key=f"re_{aid}", on_click=retirer, args=(aid,))
        total += q * a["prix_ttc"]
    st.markdown(f"**Total : {prix(total)}**")
    if st.button("Envoyer la commande", type="primary", use_container_width=True):
        try:
            etat.commande = db.passer_commande(etat.session_id, table_id, etab, dict(etat.panier))
            etat.panier = {}
        except ValueError as e:
            st.error(str(e))
        st.rerun()

if st.button("🔔 Appeler le serveur"):
    db.journaliser(etat.session_id, etab, "appel_serveur")
    st.toast("Le serveur a été prévenu.")
