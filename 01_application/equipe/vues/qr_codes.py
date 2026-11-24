# -*- coding: utf-8 -*-
"""Tables et QR codes (gérant) : un QR code par table, à télécharger un par un ou en planche PDF à imprimer."""
from urllib.parse import urlparse

import streamlit as st

from commun import db, qr
from commun.theme import GRIS, e

u = st.session_state.get("utilisateur")
if not u or u["role"] != "gerant":
    st.warning("Page réservée au gérant.")
    st.stop()

base = db.url_client()
tables = db.lire("SELECT table_id, numero_table, zone, capacite FROM tables_salle WHERE etablissement_id = :e ORDER BY numero_table",
                 e=u["etablissement_id"])

st.markdown(f'<div class="titre" style="font-size:32px">Tables et QR codes</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · {len(tables)} tables · adresse encodée : <code>{e(base)}/?table=…</code></div>',
            unsafe_allow_html=True)
if urlparse(base).hostname in ("localhost", "127.0.0.1"):
    st.warning("Les QR codes pointent vers localhost : ils ne s'ouvriront que sur ce PC. Pour un téléphone, mettre l'adresse réseau du PC "
               "dans CLIENT_URL (fichier .env, par exemple http://192.168.1.222:8501), puis relancer l'application équipe.")

nom = u["nom_etablissement"]
st.download_button("Télécharger la planche à imprimer (PDF, 6 cartes par page A4)", data=qr.planche_pdf(nom, tables, base),
                   file_name=f"QR_{u['etablissement_id']}.pdf", mime="application/pdf", type="primary", icon=":material/print:")
st.write("")

for debut in range(0, len(tables), 4):
    for col, t in zip(st.columns(4), tables[debut:debut + 4]):
        with col.container(key=f"carte_qr_{t['table_id']}"):
            lien = qr.url_table(base, t["table_id"])
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline"><span class="titre" style="font-size:20px">Table {t["numero_table"]}</span>'
                        f'<span style="font-size:13px;color:{GRIS}">{qr.ZONES.get(t["zone"], e(t["zone"]))} · {t["capacite"]} places</span></div>',
                        unsafe_allow_html=True)
            st.image(qr.png(lien, 360), width="stretch")
            st.markdown(f'<div style="font-size:12px;color:{GRIS};word-break:break-all"><a href="{e(lien)}" target="_blank">{e(lien)}</a></div>',
                        unsafe_allow_html=True)
            st.download_button("PNG", data=qr.png(lien, 1000), file_name=f"QR_{t['table_id']}.png", mime="image/png",
                               key=f"png_{t['table_id']}", icon=":material/download:", width="stretch")
