# -*- coding: utf-8 -*-
"""Plats recommandés (gérant, formule Pro ; EF-12, EF-14) : les plats « souvent pris avec » chaque plat de la carte,
issus des règles d'association de la phase 7. Copiés depuis l'entrepôt par 02_oltp/copier_resultats_ml.py."""
import pandas as pd
import streamlit as st

from commun import db
from commun.theme import GRIS, e, kpis

u = st.session_state.get("utilisateur")
if not u or u["role"] != "gerant":
    st.warning("Page réservée au gérant.")
    st.stop()

st.markdown('<div class="titre" style="font-size:32px">Plats recommandés</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · plats que vos clients commandent souvent ensemble</div>',
            unsafe_allow_html=True)
if u["nom_formule"] != "Pro":
    st.info(f"Les plats recommandés font partie de la formule Pro. Votre formule actuelle : {e(u['nom_formule'] or '–')}.")
    st.stop()

copie = db.copie_ml()
reco = pd.DataFrame(db.recommandations(u["etablissement_id"]))
if not copie or copie["publie_le"] is None or reco.empty:
    st.info("Pas encore de recommandation pour votre carte : il faut assez de commandes contenant plusieurs plats. "
            "La liste est recalculée à chaque publication des modèles.")
    st.stop()

reco["rang"] = reco.groupby("plat").cumcount() + 1  # rangs continus après retrait des plats qui ne sont plus à la carte
mis_en_avant = reco.plat_recommande.value_counts().head(5)
kpis([("Plats avec une suggestion", str(reco.plat.nunique()), "plats de votre carte", None),
      ("Suggestions", str(len(reco)), "jusqu'à 3 par plat", None),
      ("Plat le plus suggéré", mis_en_avant.index[0], f"proposé avec {mis_en_avant.iloc[0]} plat(s)", None)])

st.markdown("### Plats à mettre en avant")
st.caption("Les plats qui reviennent le plus souvent comme accompagnement : à placer en évidence sur la carte ou à proposer par le serveur.")
st.markdown(" ".join(f'<span style="display:inline-block;background:#DBE7FF;color:#1E3A8A;border-radius:999px;padding:6px 12px;'
                     f'margin:0 6px 6px 0;font-weight:600">{e(p)} · {n}</span>' for p, n in mis_en_avant.items()),
            unsafe_allow_html=True)

st.markdown("### Souvent pris avec")
plats = sorted(reco.plat.unique())
choix = st.selectbox("Plat", ["Tous les plats"] + plats)
vue = reco if choix == "Tous les plats" else reco[reco.plat == choix]
MOTIFS = {"règle plat": "Ces deux plats sont souvent commandés ensemble",
          "règle catégorie": "Leurs catégories sont souvent commandées ensemble"}
st.dataframe(pd.DataFrame({"Plat": vue.plat, "Rang": vue.rang, "Souvent pris avec": vue.plat_recommande,
                           "Catégorie": vue.categorie_recommandee, "Pourquoi": vue.motif.map(MOTIFS).fillna(vue.motif)}),
             hide_index=True, width="stretch")
st.caption(f"Analyse des commandes de 2024 et 2025, vérifiée sur 2026 · publiée le {copie['publie_le']:%d/%m/%Y}. "
           "Une suggestion signale une habitude des clients, pas une garantie de vente. Données simulées.")
