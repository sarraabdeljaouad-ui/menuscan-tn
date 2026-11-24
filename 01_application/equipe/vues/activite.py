# -*- coding: utf-8 -*-
"""Activité des tables (gérant, lot 2) : recherche d'une table, comparaison des tables sur une période,
puis historique détaillé de la table choisie (commandes, encaissements, appels)."""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from commun import db
from commun.theme import GRIS, e, kpis, prix

ZONES = {"terrasse": "Terrasse", "salle": "Salle", "etage": "Étage"}
STATUTS = {"nouvelle": "Nouvelle", "en_prepa": "En préparation", "prete": "Prête", "servie": "Servie", "annulee": "Annulée"}
MODES = {"especes": "Espèces", "carte_bancaire": "Carte bancaire", "ticket_restaurant": "Ticket restaurant"}
MOTIFS = {"serveur": "Serveur", "addition": "Addition", "eau": "Eau"}
ANNULATIONS = {"article_indisponible": "Annulée : article indisponible"}
# Format « localized » : nombres affichés selon la langue du navigateur (73,5 en français, et non 73.500, qui se lit 73 mille)
ARGENT = st.column_config.NumberColumn(format="localized")

u = st.session_state.get("utilisateur")
if not u or u["role"] != "gerant":
    st.warning("Page réservée au gérant.")
    st.stop()
etab = u["etablissement_id"]


def nombre(x, unite=""):
    return "–" if x is None else f"{float(x):.1f}{unite}".replace(".", ",")


st.markdown(f'<div class="titre" style="font-size:32px">Activité des tables</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · cherchez une table, puis ouvrez son historique</div>',
            unsafe_allow_html=True)

# ---------- Période et recherche ----------
n = db.maintenant()
jour = datetime.combine(n.date(), datetime.min.time())
PERIODES = {"Aujourd'hui": jour, "7 jours": jour - timedelta(days=6), "30 jours": jour - timedelta(days=29),
            "Ce mois": jour.replace(day=1), "Période…": None}
c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
choix = c1.pills("Période", list(PERIODES), default="7 jours", key="periode") or "7 jours"
if choix == "Période…":
    dates = c2.date_input("Du … au …", value=(n.date() - timedelta(days=13), n.date()), max_value=n.date(), format="DD/MM/YYYY")
    if not isinstance(dates, tuple) or len(dates) != 2:
        st.info("Choisissez la date de fin.")
        st.stop()
    debut, fin = datetime.combine(dates[0], datetime.min.time()), datetime.combine(dates[1], datetime.max.time())
else:
    debut, fin = PERIODES[choix], n
recherche = c2.text_input("Rechercher", placeholder="Numéro de table ou zone (ex. 5, terrasse)", icon=":material/search:",
                          label_visibility="collapsed") if choix != "Période…" else st.text_input(
    "Rechercher", placeholder="Numéro de table ou zone (ex. 5, terrasse)", icon=":material/search:", label_visibility="collapsed")
st.caption(f"Du {debut:%d/%m/%Y} au {min(fin, n):%d/%m/%Y à %H:%M}. Seules les commandes jusqu'à maintenant sont comptées.")

lignes = db.activite_tables(etab, debut, fin)
q = (recherche or "").strip().lower().removeprefix("table").strip()
if q:
    lignes = [l for l in lignes if q == str(l["numero_table"]) or q in l["zone"].lower() or q in ZONES.get(l["zone"], "").lower()]
if not lignes:
    st.info("Aucune table ne correspond à la recherche.")
    st.stop()

# ---------- Synthèse et tableau comparatif ----------
servies = sum(l["servies"] for l in lignes)
chiffre = sum(float(l["chiffre"]) for l in lignes)
meilleure = max(lignes, key=lambda l: l["chiffre"])
kpis([("Chiffre servi", prix(chiffre), f"{len(lignes)} table{'s' if len(lignes) > 1 else ''}", None),
      ("Commandes servies", str(servies), f"{sum(l['annulees'] for l in lignes)} annulée(s)", None),
      ("Panier moyen", prix(chiffre / servies) if servies else "–", "par commande servie", None),
      ("Table la plus rentable", f"Table {meilleure['numero_table']}" if meilleure["chiffre"] else "–",
       prix(meilleure["chiffre"]) if meilleure["chiffre"] else "aucune vente", None)], 190)

df = pd.DataFrame([{
    "Table": l["numero_table"], "Zone": ZONES.get(l["zone"], l["zone"]), "Places": l["capacite"], "Visites": l["visites"],
    "Servies": l["servies"], "Annulées": l["annulees"], "Chiffre (DT)": float(l["chiffre"]),
    "Panier moyen (DT)": float(l["panier"]) if l["panier"] is not None else None,
    "Délai moyen (min)": round(float(l["delai"]), 1) if l["delai"] is not None else None, "Appels": l["appels"],
    "Dernière commande": l["derniere"]} for l in lignes])
st.markdown('<div class="titre" style="font-size:20px;margin-top:16px">Tables</div>', unsafe_allow_html=True)
st.caption("Cliquez sur une ligne pour ouvrir l'historique de la table. Les colonnes se trient en cliquant sur leur titre.")
sel = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", key="tableau_tables",
                   column_config={
                       "Chiffre (DT)": ARGENT, "Panier moyen (DT)": ARGENT, "Délai moyen (min)": ARGENT,
                       "Dernière commande": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")})
rangs = sel.selection.rows
if not rangs and len(lignes) == 1:
    rangs = [0]
if not rangs:
    st.stop()

# ---------- Historique de la table choisie ----------
t = lignes[rangs[0]]
st.markdown(f'<div class="titre" style="font-size:24px;margin-top:18px">Table {t["numero_table"]} '
            f'<span style="font-size:16px;color:{GRIS};font-weight:600">· {ZONES.get(t["zone"], e(t["zone"]))} · {t["capacite"]} places</span></div>',
            unsafe_allow_html=True)
taux = t["servies"] / t["visites"] if t["visites"] else None
kpis([("Chiffre servi", prix(t["chiffre"]), f"{t['servies']} commande{'s' if t['servies'] > 1 else ''}", None),
      ("Panier moyen", prix(t["panier"]) if t["panier"] else "–", "par commande servie", None),
      ("Délai de service", nombre(t["delai"], " min"), "de l'envoi au service", None),
      ("Visites", str(t["visites"]), f"{nombre(100 * taux, ' %')} avec commande" if taux is not None else "aucun scan", None),
      ("Appels", str(t["appels"]), "sur la période", None)], 185)

hist = db.historique_table(etab, t["table_id"], debut, fin)
onglets = st.tabs(["Commandes", "Appels"])
with onglets[0]:
    if not hist:
        st.caption("Aucune commande sur la période.")
    else:
        h = pd.DataFrame([{
            "Heure": c["date_heure_commande"], "Commande": c["commande_id"], "Articles": c["detail"],
            "Montant (DT)": float(c["montant_total_ttc"]), "Statut": STATUTS.get(c["statut_commande"], c["statut_commande"]),
            "Délai (min)": float(c["delai"]) if c["delai"] is not None else None, "Règlement": MODES.get(c["mode_reglement"], "À encaisser" if c["statut_commande"] == "servie" else ""),
            "Note": c["note"] or ANNULATIONS.get(c["motif_annulation"], c["motif_annulation"] or "")} for c in hist])
        st.dataframe(h, hide_index=True, width="stretch", column_config={
            "Heure": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Montant (DT)": ARGENT, "Délai (min)": ARGENT})
        if len(hist) == 300:
            st.caption("Les 300 commandes les plus récentes sont affichées : réduisez la période pour voir les plus anciennes.")
        st.download_button("Exporter en CSV", h.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           file_name=f"table_{t['numero_table']}_{debut:%Y%m%d}_{min(fin, n):%Y%m%d}.csv", mime="text/csv",
                           icon=":material/download:")
with onglets[1]:
    ap = db.appels_table(etab, t["table_id"], debut, fin)
    st.caption("Détail des appels passés depuis l'application (motif et délai de prise en charge). "
               "Les appels des données historiques sont comptés plus haut, sans ce détail.")
    if not ap:
        st.caption("Aucun appel détaillé sur la période.")
    else:
        st.dataframe(pd.DataFrame([{
            "Heure": a["date_heure_appel"], "Motif": MOTIFS.get(a["motif"], a["motif"]),
            "Pris en charge": a["date_heure_prise"], "Attente (min)": float(a["attente"]) if a["attente"] is not None else None} for a in ap]),
            hide_index=True, width="stretch", column_config={
                "Heure": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                "Pris en charge": st.column_config.DatetimeColumn(format="HH:mm")})
