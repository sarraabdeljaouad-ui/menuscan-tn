# -*- coding: utf-8 -*-
"""Espace gérant : indicateurs, commandes en direct (nouvelles, en préparation, prêtes), meilleures ventes, plan des tables.

Démonstration : le choix de l'établissement est libre, sans authentification.
"""
import streamlit as st

import db
from theme import BLEU, CLAIR, GRIS, MARINE, ORANGE, e, kpis, prix

st.set_page_config(layout="wide")
MODES = {"Espèces": "especes", "Carte bancaire": "carte_bancaire", "Ticket restaurant": "ticket_restaurant"}
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

etabs = db.etablissements_commande()
if not etabs:
    st.info("Aucun établissement actif avec la commande depuis la table.")
    st.stop()
par_id = {x["etablissement_id"]: x for x in etabs}
with st.sidebar:
    st.divider()
    choix = st.selectbox("Établissement", list(par_id), format_func=lambda i: f"{par_id[i]['nom_etablissement']} ({par_id[i]['nom_ville']})",
                         key="etab_gerant", help="Démonstration sans authentification : chaque gérant ne verra que son établissement (phase 6).")
    x = par_id[choix]
    nb_tables = db.un("SELECT COUNT(*) AS n FROM tables_salle WHERE etablissement_id = :e", e=choix)["n"]
    st.markdown(f"""<div style="background:rgba(255,255,255,.1);border-radius:16px;padding:12px 14px;font-size:14px">
      Formule <b>{e(x['nom_formule'])}</b><br><span style="color:#C7D7F5">{nb_tables} tables</span></div>""", unsafe_allow_html=True)

n = db.maintenant()
h1, h2 = st.columns([3, 1], vertical_alignment="center")
h1.markdown(f'<div class="titre" style="font-size:32px">Bonjour {e(x["gerant_prenom"])}</div>'
            f'<div style="color:{GRIS}">{e(x["nom_etablissement"])} · {JOURS[n.weekday()]} {n.day} {MOIS[n.month - 1]} · {n:%H:%M}</div>',
            unsafe_allow_html=True)
ouvert = h2.toggle("Commandes ouvertes", value=bool(x["commandes_ouvertes"]), key=f"ouvert_{choix}")
if ouvert != bool(x["commandes_ouvertes"]):
    db.ouvrir_commandes(choix, ouvert)
    st.rerun()


def servir(cid):
    db.avancer(cid, MODES[st.session_state[f"mode_{cid}"]])


@st.fragment(run_every="10s")
def tableau():
    i = db.indicateurs(choix)
    actives = db.commandes_actives(choix)
    if i["ca_semaine"]:
        ecart = round((i["ca_jour"] / i["ca_semaine"] - 1) * 100)
        comp = (f"{'+' if ecart >= 0 else '−'}{abs(ecart)} % vs {JOURS[i['jour_semaine'].weekday()]} "
                f"{i['jour_semaine']:%d/%m}, même heure", "#166534" if ecart >= 0 else "#B45309")
    else:
        comp = ("pas de vente le même jour la semaine dernière", None)
    periode = f"depuis le 1er {MOIS[n.month - 1]}"
    kpis([("Chiffre servi aujourd'hui", prix(i["ca_jour"]), comp[0], comp[1]),
          ("Commandes servies", str(i["n_jour"]), f"{len(actives)} en cours", None),
          ("Panier moyen", prix(i["panier"]) if i["panier"] else "–", periode, None),
          ("Délai de service", f"{i['delai']:.1f} min".replace(".", ",") if i["delai"] else "–", periode, None),
          ("Taux de commande", f"{100 * float(i['taux']):.1f} %".replace(".", ",") if i["taux"] is not None else "–", f"des scans, {periode}", None)], 160)

    tables = db.etat_tables(choix)
    appels = [t for t in tables if t["appel"]]
    if appels:
        st.warning("Appel du serveur : " + ", ".join(f"table {t['numero_table']}" for t in appels))

    st.markdown('<div class="titre" style="font-size:22px;margin-top:14px">Commandes en direct</div>', unsafe_allow_html=True)
    colonnes = [("nouvelle", "Nouvelles", CLAIR, MARINE), ("en_prepa", "En préparation", "#FEF3C7", "#92400E"), ("prete", "Prêtes à servir", "#DCFCE7", "#166534")]
    for col, (statut, titre, fond, txt) in zip(st.columns(3), colonnes):
        cartes = [c for c in actives if c["statut_commande"] == statut]
        with col.container(key=f"colonne_{statut}"):
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:16px">{titre}</b>'
                        f'<span style="min-width:28px;height:28px;border-radius:999px;background:{fond};color:{txt};font-weight:700;display:flex;align-items:center;justify-content:center">{len(cartes)}</span></div>',
                        unsafe_allow_html=True)
            if not cartes:
                st.caption("Aucune commande.")
            for c in cartes:
                cid = c["commande_id"]
                minutes = int((n - c["date_heure_commande"]).total_seconds() // 60)
                note = (f'<div style="font-size:13px;color:#92400E;background:#FEF3C7;border-radius:8px;padding:6px 8px;margin-top:6px">« {e(c["note"])} »</div>'
                        if c["note"] else "")
                with st.container(key=f"carte_{cid}"):
                    st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:baseline"><b>Table {c['numero_table']} <span style="font-weight:500;color:#64748B;font-size:13px">· {e(c['zone'])}</span></b>
                      <span style="font-size:13px;font-weight:600;color:{'#B45309' if minutes >= 10 else '#64748B'}">{minutes} min</span></div>
                      <div style="font-size:14px;color:#334155;margin-top:4px">{e(c['detail'])}</div>{note}
                      <div style="display:flex;justify-content:space-between;margin-top:6px"><b style="color:{BLEU}">{prix(c['montant_total_ttc'])}</b><span style="font-size:12px;color:#64748B">{cid}</span></div>""",
                                unsafe_allow_html=True)
                    if statut == "nouvelle":
                        b1, b2 = st.columns([3, 2])
                        b1.button("Accepter", key=f"acc_{cid}", type="primary", on_click=db.avancer, args=(cid,), use_container_width=True)
                        b2.button("Annuler", key=f"ann_{cid}", on_click=db.annuler, args=(cid,), use_container_width=True)
                    elif statut == "en_prepa":
                        st.button("Marquer prête", key=f"pre_{cid}", type="primary", on_click=db.avancer, args=(cid,), use_container_width=True)
                    else:
                        st.selectbox("Règlement", list(MODES), key=f"mode_{cid}", label_visibility="collapsed")
                        st.button("Servie", key=f"ser_{cid}", type="primary", on_click=servir, args=(cid,), use_container_width=True)

    g, d = st.columns(2)
    with g.container(key="carte_ventes"):
        st.markdown(f'<div class="titre" style="font-size:19px">Meilleures ventes du mois</div><div style="font-size:13px;color:#64748B;margin-bottom:8px">{periode}</div>',
                    unsafe_allow_html=True)
        ventes = db.meilleures_ventes(choix)
        if not ventes:
            st.caption("Pas encore de vente ce mois-ci.")
        haut = max([v["q"] for v in ventes] or [1])
        st.markdown("".join(f"""<div style="margin:8px 0"><div style="display:flex;justify-content:space-between;font-size:15px"><b style="font-weight:600">{e(v['nom_article'])}</b><span style="color:{GRIS}">{v['q']} servis</span></div>
          <div style="height:8px;border-radius:4px;background:#E8EEFA;margin-top:4px"><div style="height:8px;border-radius:4px;width:{round(100 * v['q'] / haut)}%;background:{BLEU}"></div></div></div>"""
                            for v in ventes), unsafe_allow_html=True)
    with d.container(key="carte_tables"):
        occ = sum(1 for t in tables if t["appel"] or t["commande"] or t["ouvert"])
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline"><span class="titre" style="font-size:19px">Tables</span>'
                    f'<span style="font-size:13px;color:#64748B">{occ} occupées sur {len(tables)}</span></div>', unsafe_allow_html=True)
        html = ""
        for zone in dict.fromkeys(t["zone"] for t in tables):
            cases = ""
            for t in (t for t in tables if t["zone"] == zone):
                lib, fond, txt = (("Appel", ORANGE, "#422006") if t["appel"] else ("Commande", BLEU, "#fff") if t["commande"]
                                  else ("Menu", CLAIR, MARINE) if t["ouvert"] else ("Libre", "#F1F5F9", "#64748B"))
                cases += (f'<div style="height:52px;border-radius:12px;background:{fond};color:{txt};display:flex;flex-direction:column;align-items:center;justify-content:center">'
                          f'<span class="titre" style="font-size:17px;color:{txt} !important;line-height:1">{t["numero_table"]}</span><span style="font-size:10px;font-weight:600">{lib}</span></div>')
            html += (f'<div style="font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#64748B;margin:10px 0 6px">{e(zone)}</div>'
                     f'<div style="display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px">{cases}</div>')
        legende = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px"><span style="width:12px;height:12px;border-radius:3px;background:{c}"></span>{l}</span>'
                          for l, c in [("Commande en cours", BLEU), ("Menu ouvert (30 min)", CLAIR), ("Appel (15 min)", ORANGE), ("Libre", "#F1F5F9")])
        st.markdown(html + f'<div style="font-size:13px;color:#334155;margin-top:12px">{legende}</div>', unsafe_allow_html=True)


tableau()
