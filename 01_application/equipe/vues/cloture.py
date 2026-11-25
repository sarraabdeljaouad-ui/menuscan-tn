# -*- coding: utf-8 -*-
"""Clôture de la journée (gérant, lot 3) : encaissements par mode de règlement, commandes servies et annulées,
tables encore à encaisser, appels, avis, ruptures et ventes par article avec la marge quand le coût de revient est saisi.
Le bilan est borné à maintenant : le jeu simulé contient des commandes datées après aujourd'hui."""
from datetime import timedelta

import pandas as pd
import streamlit as st

from commun import db
from commun.theme import GRIS, e, kpis, prix

MODES = {"especes": "Espèces", "carte_bancaire": "Carte bancaire", "ticket_restaurant": "Ticket restaurant"}
MOTIFS = {"article_indisponible": "Article indisponible", "client_parti": "Client parti", "erreur_commande": "Erreur de commande"}

u = st.session_state.get("utilisateur")
if not u or u["role"] != "gerant":
    st.warning("Page réservée au gérant.")
    st.stop()
etab = u["etablissement_id"]
n = db.maintenant()


def dt(x, d=3):
    """Nombre à la française (virgule, espace des milliers), tiret si vide."""
    return "–" if x is None or pd.isna(x) else f"{float(x):,.{d}f}".replace(",", " ").replace(".", ",")


c1, c2 = st.columns([3, 1.2], vertical_alignment="bottom")
c1.markdown(f'<div class="titre" style="font-size:32px">Clôture de la journée</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · bilan de caisse et de service</div>', unsafe_allow_html=True)
jour = c2.date_input("Journée", value=n.date(), max_value=n.date(), min_value=n.date() - timedelta(days=730), format="DD/MM/YYYY")
if jour == n.date():
    st.caption(f"Journée en cours : bilan arrêté à {n:%H:%M}. Il se complète au fil du service.")

r = db.cloture(etab, jour)
k = r["commandes"]
encaisse = sum(float(x["montant"]) for x in r["reglements"])
kpis([("Encaissé", prix(encaisse), f"{sum(x['n'] for x in r['reglements'])} commande(s) réglée(s)", "#166534" if encaisse else None),
      ("Chiffre servi", prix(k["chiffre"]), f"{k['servies']} commande(s) servie(s)", None),
      ("Panier moyen", prix(float(k["chiffre"]) / k["servies"]) if k["servies"] else "–", "par commande servie", None),
      ("Annulées", str(k["annulees"]), prix(k["montant_annule"]) + " non vendus" if k["annulees"] else "aucune", "#B91C1C" if k["annulees"] else None),
      ("Délai de service", f"{dt(k['delai'], 1)} min" if k["delai"] is not None else "–", "de l'envoi au service", None)], 170)
st.caption("« Encaissé » compte les règlements faits ce jour-là ; « Chiffre servi » compte les commandes passées ce jour-là et servies. "
           "Les deux diffèrent quand une table est encaissée plus tard, ou encore à encaisser.")

if r["a_encaisser"]:
    total = sum(float(x["montant"]) for x in r["a_encaisser"])
    st.warning(f"Reste à encaisser : {prix(total)} sur " + ", ".join(f"table {x['numero_table']} ({prix(x['montant'])})" for x in r["a_encaisser"])
               + ". À régler dans la fenêtre de la table avant de fermer la caisse.")
if k["en_cours"] and jour == n.date():
    st.info(f"{k['en_cours']} commande(s) encore en cours de préparation ou de service.")

g, d = st.columns(2)
with g:
    st.markdown('<div class="titre" style="font-size:20px">Encaissements par mode de règlement</div>', unsafe_allow_html=True)
    if r["reglements"]:
        st.dataframe(pd.DataFrame([{"Mode": MODES.get(x["mode_reglement"], x["mode_reglement"] or "–"), "Commandes": x["n"],
                                    "Montant (DT)": dt(x["montant"]), "Part": f"{100 * float(x['montant']) / encaisse:.0f} %"}
                                   for x in r["reglements"]]), hide_index=True, width="stretch", placeholder="–")
    else:
        st.caption("Aucun règlement ce jour-là.")
with d:
    st.markdown('<div class="titre" style="font-size:20px">Service</div>', unsafe_allow_html=True)
    ap, av = r["appels"], r["avis"]
    lignes = [("Appels des clients", f"{ap['n']}" + (f" · prise en charge en {dt(ap['attente'], 1)} min en moyenne" if ap["attente"] is not None else "")),
              ("Avis", f"{av['n']}" + (f" · {dt(av['moyenne'], 1)} / 5" if av["moyenne"] is not None else "")),
              ("Annulations", ", ".join(f"{MOTIFS.get(x['motif'], x['motif'])} ({x['n']})" for x in r["annulations"]) or "aucune"),
              ("Ruptures", ", ".join(x["nom_article"] for x in r["ruptures"]) or "aucune")]
    st.markdown("".join(f'<div style="display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid #E2E8F5">'
                        f'<span style="color:{GRIS}">{a}</span><span style="text-align:right;font-weight:600">{e(b)}</span></div>'
                        for a, b in lignes), unsafe_allow_html=True)
    if jour < n.date():
        st.caption("Le détail des appels et des avis n'existe que pour l'activité passée par l'application.")

st.markdown('<div class="titre" style="font-size:20px;margin-top:16px">Ventes par article</div>', unsafe_allow_html=True)
if not r["ventes"]:
    st.caption("Aucune commande servie ce jour-là.")
else:
    v = pd.DataFrame([{"Article": x["nom_article"], "Catégorie": x["nom_categorie"], "Quantité": int(x["quantite"]),
                       "Chiffre (DT)": float(x["montant"]),
                       "Coût (DT)": float(x["cout"]) if x["cout"] is not None else None,
                       "Marge (DT)": float(x["montant"]) - float(x["cout"]) if x["cout"] is not None else None} for x in r["ventes"]])
    st.dataframe(v.style.format({"Chiffre (DT)": dt, "Coût (DT)": dt, "Marge (DT)": dt}, na_rep="–"), hide_index=True, width="stretch", placeholder="–")
    connus = v["Coût (DT)"].notna()
    if connus.any():
        marge, ca = v.loc[connus, "Marge (DT)"].sum(), v.loc[connus, "Chiffre (DT)"].sum()
        st.caption(f"Marge sur les {int(connus.sum())} article(s) dont le coût est saisi : {prix(marge)} ({100 * marge / ca:.0f} % de leur chiffre). "
                   "Les autres articles n'ont pas de coût de revient : le saisir dans la page Menu, bouton « Modifier ».")
    else:
        st.caption("Aucun coût de revient saisi : la marge s'affichera dès qu'un coût est renseigné dans la page Menu (bouton « Modifier »).")
    resume = pd.DataFrame([{"Indicateur": a, "Valeur": b} for a, b in [
        ("Journée", f"{jour:%d/%m/%Y}"), ("Encaissé (DT)", dt(encaisse)), ("Chiffre servi (DT)", dt(k["chiffre"])),
        ("Commandes servies", k["servies"]), ("Commandes annulées", k["annulees"]),
        ("Reste à encaisser (DT)", dt(sum(float(x["montant"]) for x in r["a_encaisser"]))),
        *[(f"Encaissé {MODES.get(x['mode_reglement'], x['mode_reglement'])} (DT)", dt(x["montant"])) for x in r["reglements"]]]])
    st.download_button("Exporter la clôture (CSV)", (resume.to_csv(index=False, sep=";") + "\n" + v.to_csv(index=False, sep=";", decimal=","))
                       .encode("utf-8-sig"), file_name=f"cloture_{etab}_{jour:%Y%m%d}.csv", mime="text/csv", icon=":material/download:")
