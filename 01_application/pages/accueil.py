# -*- coding: utf-8 -*-
"""Page d'accueil : présentation et liens de test vers des tables."""
import streamlit as st

import db

st.title("MenuScan TN")
st.caption("Menu numérique à QR code et commande depuis la table · projet de portfolio, données fictives")

st.markdown(
    "Le client scanne le QR code de sa table : il arrive sur le **menu client**, avec le code de sa table dans l'adresse "
    "(par exemple `/menu?table=TBL00001`). Le gérant suit les commandes dans l'**espace gérant**."
)

st.subheader("Tables de démonstration")
st.caption("Une table par formule, choisie parmi les établissements actifs. Le lien imite le scan du QR code.")
exemples = db.lire("""
    SELECT DISTINCT ON (a.formule_id) a.formule_id, f.nom_formule, e.nom_etablissement, v.ville AS nom_ville, t.table_id, t.numero_table
    FROM etablissements e
    JOIN ref_villes v USING (ville_id)
    JOIN abonnements a ON a.etablissement_id = e.etablissement_id
         AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
    JOIN formules f ON f.formule_id = a.formule_id
    JOIN tables_salle t ON t.etablissement_id = e.etablissement_id
    WHERE e.statut_etablissement = 'actif'
    ORDER BY a.formule_id, e.etablissement_id, t.numero_table""", j=db.maintenant().date())
for x in exemples:
    st.page_link("pages/menu_client.py", query_params={"table": x["table_id"]},
                 label=f"{x['nom_etablissement']} ({x['nom_ville']}) · table {x['numero_table']} · formule {x['nom_formule']}")

st.subheader("Base de données")
n = db.lire("""SELECT (SELECT COUNT(*) FROM etablissements WHERE statut_etablissement = 'actif') AS actifs,
                      (SELECT COUNT(*) FROM commandes) AS commandes,
                      (SELECT COUNT(*) FROM commandes WHERE statut_commande = 'en_cours') AS en_cours""")[0]
c1, c2, c3 = st.columns(3)
c1.metric("Établissements actifs", f"{n['actifs']:,}".replace(",", " "))
c2.metric("Commandes enregistrées", f"{n['commandes']:,}".replace(",", " "))
c3.metric("Commandes en cours", n["en_cours"])
