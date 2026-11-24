# -*- coding: utf-8 -*-
"""Tables et QR codes (gérant) : un QR code par table, à télécharger un par un ou en planche PDF à imprimer.

Gestion des tables (lot 2, migration 006) : ajouter une table (QR code disponible tout de suite), changer son numéro,
sa zone ou ses places, la retirer du service ou l'y remettre. Le QR code encode l'identifiant de la table, pas son numéro :
renuméroter une table ne demande pas de réimprimer son QR code.
"""
from urllib.parse import urlparse

import streamlit as st

from commun import db, qr
from commun.theme import GRIS, e

ZONES = {"terrasse": "Terrasse", "salle": "Salle", "etage": "Étage"}

u = st.session_state.get("utilisateur")
if not u or u["role"] != "gerant":
    st.warning("Page réservée au gérant.")
    st.stop()
etab = u["etablissement_id"]

if "message_tables" in st.session_state:
    st.toast(st.session_state.pop("message_tables"), icon=":material/check_circle:")

base = db.url_client()
toutes = db.tables_gestion(etab)
tables = [t for t in toutes if not t["retiree"]]
retirees = [t for t in toutes if t["retiree"]]


def retirer(t, oui):
    try:
        db.retirer_table(etab, t["table_id"], oui)
        st.session_state.message_tables = f"Table {t['numero_table']} {'retirée du service' if oui else 'remise en service'}"
    except ValueError as err:
        st.session_state.message_tables = f"Table {t['numero_table']} : {err}"


st.markdown(f'<div class="titre" style="font-size:32px">Tables et QR codes</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · {len(tables)} tables en service · adresse encodée : <code>{e(base)}/?table=…</code></div>',
            unsafe_allow_html=True)
if urlparse(base).hostname in ("localhost", "127.0.0.1"):
    st.warning("Les QR codes pointent vers localhost : ils ne s'ouvriront que sur ce PC. Pour un téléphone, mettre l'adresse réseau du PC "
               "dans CLIENT_URL (fichier .env, par exemple http://192.168.1.222:8501), puis relancer l'application équipe.")

# ---------- Ajouter une table ----------
with st.expander("＋ Ajouter une table", expanded=False):
    with st.form("ajout_table", border=False):
        c1, c2, c3 = st.columns(3)
        numero = c1.number_input("Numéro", min_value=1, max_value=999, step=1,
                                 value=max([t["numero_table"] for t in tables] or [0]) + 1)
        zone = c2.selectbox("Zone", list(ZONES), format_func=ZONES.get)
        places = c3.number_input("Places", min_value=1, max_value=20, step=1, value=4)
        if st.form_submit_button("Créer la table et son QR code", type="primary", icon=":material/add:"):
            try:
                st.session_state.nouvelle_table = db.ajouter_table(etab, numero, zone, places)
                st.session_state.message_tables = f"Table {numero} créée : son QR code est prêt"
                st.rerun()
            except ValueError as err:
                st.error(str(err))

nouvelle = st.session_state.get("nouvelle_table")
t_new = next((t for t in tables if t["table_id"] == nouvelle), None)
if t_new:
    lien = qr.url_table(base, t_new["table_id"])
    with st.container(key="carte_nouvelle"):
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        c1.image(qr.png(lien, 360), width="stretch")
        c2.markdown(f'<div class="titre" style="font-size:22px">Table {t_new["numero_table"]} créée</div>'
                    f'<div style="color:{GRIS}">{ZONES.get(t_new["zone"], e(t_new["zone"]))} · {t_new["capacite"]} places. '
                    f'Imprimez ce QR code et posez-le sur la table : il s\'ouvre dès maintenant.</div>', unsafe_allow_html=True)
        c2.download_button("Télécharger le QR code (PNG)", data=qr.png(lien, 1000), file_name=f"QR_{t_new['table_id']}.png",
                           mime="image/png", type="primary", icon=":material/download:")
        if c2.button("Fermer", type="tertiary"):
            st.session_state.pop("nouvelle_table", None)
            st.rerun()

nom = u["nom_etablissement"]
st.download_button("Télécharger la planche à imprimer (PDF, 6 cartes par page A4)", data=qr.planche_pdf(nom, tables, base),
                   file_name=f"QR_{etab}.pdf", mime="application/pdf", icon=":material/print:")
st.write("")

# ---------- Tables en service ----------
for debut in range(0, len(tables), 4):
    for col, t in zip(st.columns(4), tables[debut:debut + 4]):
        tid = t["table_id"]
        with col.container(key=f"carte_qr_{tid}"):
            lien = qr.url_table(base, tid)
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline"><span class="titre" style="font-size:20px">Table {t["numero_table"]}</span>'
                        f'<span style="font-size:13px;color:{GRIS}">{ZONES.get(t["zone"], e(t["zone"]))} · {t["capacite"]} places</span></div>',
                        unsafe_allow_html=True)
            st.image(qr.png(lien, 360), width="stretch")
            st.markdown(f'<div style="font-size:12px;color:{GRIS};word-break:break-all"><a href="{e(lien)}" target="_blank">{e(lien)}</a></div>',
                        unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            b1.download_button("PNG", data=qr.png(lien, 1000), file_name=f"QR_{tid}.png", mime="image/png",
                               key=f"png_{tid}", icon=":material/download:", width="stretch")
            with b2.popover("", icon=":material/edit:", help="Modifier ou retirer la table", width="stretch"):
                with st.form(f"modif_{tid}", border=False):
                    n2 = st.number_input("Numéro", min_value=1, max_value=999, step=1, value=t["numero_table"])
                    z2 = st.selectbox("Zone", list(ZONES), index=list(ZONES).index(t["zone"]) if t["zone"] in ZONES else 0, format_func=ZONES.get)
                    p2 = st.number_input("Places", min_value=1, max_value=20, step=1, value=int(t["capacite"] or 4))
                    st.caption("Le QR code ne change pas : inutile de le réimprimer.")
                    if st.form_submit_button("Enregistrer", type="primary", width="stretch"):
                        try:
                            db.modifier_table(etab, tid, n2, z2, p2)
                            st.session_state.message_tables = f"Table {n2} enregistrée"
                            st.rerun()
                        except ValueError as err:
                            st.error(str(err))
                st.button("Retirer du service", key=f"ret_{tid}", on_click=retirer, args=(t, True), width="stretch",
                          disabled=t["en_cours"], help="Impossible : une commande est en cours ou à encaisser." if t["en_cours"] else
                          "Son QR code ne s'ouvrira plus. L'historique de la table est conservé.")

if retirees:
    with st.expander(f"Tables retirées du service ({len(retirees)})"):
        for t in retirees:
            c1, c2 = st.columns([4, 1.5], vertical_alignment="center")
            c1.markdown(f"**Table {t['numero_table']}** · {ZONES.get(t['zone'], e(t['zone']))} · {t['capacite']} places · "
                        f"retirée le {t['date_retrait']:%d/%m/%Y}")
            c2.button("Remettre en service", key=f"rem_{t['table_id']}", on_click=retirer, args=(t, False), width="stretch")
