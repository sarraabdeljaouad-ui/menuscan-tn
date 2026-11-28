# -*- coding: utf-8 -*-
"""Espace MenuScan (rôle menuscan, migration 010) : établissements à risque de résiliation (K19, EF-10, EF-14)
et candidats à la formule Commande (EF-13). Résultats de la phase 7, copiés depuis l'entrepôt par 02_oltp/copier_resultats_ml.py."""
import pandas as pd
import streamlit as st

from commun import db
from commun.theme import GRIS, e, kpis

u = st.session_state.get("utilisateur")
if not u or u["role"] != "menuscan":
    st.warning("Page réservée à l'équipe MenuScan.")
    st.stop()


def fr(d):
    return lambda x: "–" if x is None or pd.isna(x) else f"{float(x):,.{d}f}".replace(",", " ").replace(".", ",")


def pct(x):
    return "–" if x is None or pd.isna(x) else f"{100 * float(x):.1f} %".replace(".", ",")


copie = db.copie_ml()
st.markdown('<div class="titre" style="font-size:32px">Établissements à risque</div>'
            f'<div style="color:{GRIS}">Succès client · probabilité de résiliation le mois suivant et ses 3 facteurs principaux</div>',
            unsafe_allow_html=True)
if not copie or copie["publie_le"] is None:
    st.info("Aucun résultat copié. Lancer `python 02_oltp/copier_resultats_ml.py` après la publication du schéma ml.")
    st.stop()

scores = db.scores_resiliation()
mois = scores[0]["mois_observe"]
st.caption(f"Scores calculés sur les données jusqu'à fin {mois:%m/%Y} · modèle {e(scores[0]['version_modele'])} · "
           f"publiés le {copie['publie_le']:%d/%m/%Y}, copiés le {copie['copie_le']:%d/%m/%Y}. "
           "Les scores ne bougent pas d'ici la prochaine publication.")

onglets = st.tabs(["À risque de résiliation", "Candidats à la formule Commande"])
with onglets[0]:
    df = pd.DataFrame(scores)
    c1, c2, c3 = st.columns([1.2, 1.2, 1], vertical_alignment="bottom")
    villes = c1.multiselect("Ville", sorted(df.nom_ville.unique()), placeholder="Toutes")
    formules = c2.multiselect("Formule", sorted(df.nom_formule.dropna().unique()), placeholder="Toutes")
    seulement = c3.toggle("Alertes seulement", value=True)
    if villes:
        df = df[df.nom_ville.isin(villes)]
    if formules:
        df = df[df.nom_formule.isin(formules)]
    alertes = df[df.alerte]
    mrr = float(alertes.mrr_ht.fillna(0).sum())
    kpis([("Établissements en alerte", f"{len(alertes)} / {len(df)}", "10 % les plus à risque de tout le parc", None),
          ("MRR menacé", f"{mrr:,.0f} DT HT".replace(",", " "), "revenu mensuel des établissements en alerte", None),
          ("Résiliations attendues", fr(1)(df.probabilite.astype(float).sum()), "somme des probabilités, le mois suivant", None)])
    vue = alertes if seulement else df
    facteurs = vue[["facteur_1", "facteur_2", "facteur_3"]].apply(lambda r: " · ".join(x for x in r if isinstance(x, str)), axis=1)
    tableau = pd.DataFrame({
        "Établissement": vue.nom_etablissement + " · " + vue.nom_ville, "Code": vue.etablissement_id,
        "Formule": vue.nom_formule, "Risque": vue.probabilite.astype(float), "MRR (DT HT)": vue.mrr_ht.astype(float),
        "Ce qui augmente le risque": facteurs, "Gérant": vue.gerant_prenom})
    st.dataframe(tableau.style.format({"Risque": pct, "MRR (DT HT)": fr(0)}, na_rep="–"), hide_index=True, width="stretch",
                 placeholder="–", height=min(38 + 35 * max(len(tableau), 1), 560))
    st.download_button("Exporter en CSV", tableau.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name=f"etablissements_a_risque_{mois:%Y%m}.csv", mime="text/csv", icon=":material/download:")
    with st.expander("Comment lire ce score"):
        st.markdown(
            "- **Risque** : probabilité que l'établissement résilie le mois suivant. En moyenne, environ 3 établissements sur 100 "
            "résilient chaque mois.\n"
            "- **Alerte** : les 10 % les plus à risque. Sur 2026, une alerte sur sept a été suivie d'une résiliation, "
            "et les alertes ont repéré près de la moitié des résiliations.\n"
            "- **Facteurs** : ce qui éloigne le plus l'établissement du risque moyen (usage du menu, retards de paiement, "
            "échéance de l'engagement annuel…). C'est une piste pour l'appel, pas un diagnostic.\n"
            "- Données simulées : le modèle retrouve les règles du générateur de données.")

with onglets[1]:
    cand = pd.DataFrame(db.candidats_commande())
    if cand.empty:
        st.info("Aucun candidat dans la dernière publication.")
    else:
        st.caption(f"Formule Essentiel, usage du menu au moins égal à la médiane des établissements en formule Commande "
                   f"({fr(3)(cand.seuil_usage.iloc[0])} session par table et par jour), hors alerte de résiliation.")
        t = pd.DataFrame({"Établissement": cand.nom_etablissement + " · " + cand.nom_ville, "Code": cand.etablissement_id,
                          "Sessions / table / jour (3 mois)": cand.sessions_table_jour_3m.astype(float), "Tables": cand.nb_tables,
                          "Risque de résiliation": cand.probabilite_resiliation.astype(float)})
        st.dataframe(t.style.format({"Sessions / table / jour (3 mois)": fr(3), "Risque de résiliation": pct}, na_rep="–"),
                     hide_index=True, width="stretch", placeholder="–")
