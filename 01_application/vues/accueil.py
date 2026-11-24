# -*- coding: utf-8 -*-
"""Page d'accueil : présentation, chiffres de la base, étapes, formules et tables de démonstration."""
import streamlit as st

import db
from theme import BORD, BLEU, CLAIR, FOND, GRIS, MARINE, TEXTE, e, kpis

st.set_page_config(layout="wide")

QR = "1111111100000110111011010101101110110000011111111"
cases = "".join(f'<div style="border-radius:3px;background:{MARINE if b == "1" else (BLEU if i * 7 % 5 == 0 else FOND)}"></div>'
                for i, b in enumerate(QR))
st.markdown(f"""
<div style="background:{MARINE};border-radius:28px;padding:40px;display:flex;flex-wrap:wrap;gap:32px;align-items:center;color:#fff">
  <div style="flex:999 1 400px;min-width:0;display:flex;flex-direction:column;gap:16px">
    <span style="align-self:flex-start;font-size:13px;font-weight:600;color:{CLAIR};background:rgba(255,255,255,.12);border-radius:999px;padding:6px 12px">Cafés et restaurants tunisiens · projet de portfolio, données fictives</span>
    <div class="titre" style="font-size:44px;line-height:1.08;color:#fff">Le menu de votre café, dans la poche de vos clients.</div>
    <div style="font-size:18px;line-height:1.55;color:{CLAIR};max-width:560px">Le client scanne le QR code de sa table, choisit dans le menu du jour aux prix en vigueur et commande sans attendre. Le gérant suit chaque commande, de la cuisine à la table.</div>
  </div>
  <div style="flex:1 1 230px;display:flex;justify-content:center">
    <div style="width:230px;background:#fff;border-radius:24px;padding:20px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;gap:12px;box-shadow:0 24px 48px rgba(2,6,23,.35)">
      <span style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{BLEU}">Scannez pour commander</span>
      <div role="img" aria-label="Illustration d'un QR code" style="width:150px;height:150px;padding:8px;border:2px solid {BORD};border-radius:14px;display:grid;grid-template-columns:repeat(7,1fr);gap:4px">{cases}</div>
      <span class="titre" style="font-size:20px">Table 1</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

st.write("")
n = db.un("""SELECT (SELECT COUNT(*) FROM etablissements WHERE statut_etablissement = 'actif') AS actifs,
                    (SELECT COUNT(*) FROM etablissements) AS signes, (SELECT COUNT(*) FROM ref_villes) AS villes,
                    (SELECT COUNT(*) FROM commandes) AS commandes, (SELECT COUNT(*) FROM sessions) AS sessions""")
f = lambda x: f"{x:,}".replace(",", " ")
kpis([("Établissements actifs", f(n["actifs"]), f"sur {f(n['signes'])} signés depuis 2024", None),
      ("Villes couvertes", str(n["villes"]), "de Tunis Centre à Sfax", None),
      ("Commandes depuis la table", f(n["commandes"]), "depuis janvier 2024", None),
      ("Scans de QR code", f(n["sessions"]), "sessions de consultation du menu", None)], 170)

st.markdown("## De la table à la cuisine, en quatre temps")
ETAPES = [("Scanner", "Le client scanne le QR code de sa table. Le menu s'ouvre dans son navigateur, en français ou en arabe.", CLAIR),
          ("Commander", "Il remplit son panier aux prix du jour, ajoute une note pour le serveur et envoie la commande.", "#FEF3C7"),
          ("Préparer", "La commande arrive dans l'espace gérant. L'équipe l'accepte et la fait avancer jusqu'à « prête ».", "#DCFCE7"),
          ("Servir", "Le serveur apporte la commande et note le règlement. Le client suit chaque étape sur son téléphone.", "#EDE9FE")]
cartes = "".join(f"""<div style="background:#fff;border:1px solid {BORD};border-radius:20px;padding:20px;display:flex;flex-direction:column;gap:10px">
  <span class="titre" style="width:40px;height:40px;border-radius:12px;background:{c};display:flex;align-items:center;justify-content:center;font-size:18px">{i}</span>
  <span class="titre" style="font-size:18px">{t}</span><span style="font-size:15px;line-height:1.55;color:#334155">{d}</span></div>"""
                 for i, (t, d, c) in enumerate(ETAPES, 1))
st.markdown(f'<div class="grille" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))">{cartes}</div>', unsafe_allow_html=True)

st.markdown("## Trois formules, trois tables de démonstration")
st.caption("Chaque bouton imite le scan du QR code de la table 1 d'un établissement actif.")
demos = db.lire("""
    SELECT DISTINCT ON (a.formule_id) a.formule_id, f.nom_formule, f.prix_mensuel_ht, f.description, e.nom_etablissement,
           v.ville AS nom_ville, t.table_id
    FROM etablissements e JOIN ref_villes v USING (ville_id)
    JOIN abonnements a ON a.etablissement_id = e.etablissement_id
         AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
    JOIN formules f ON f.formule_id = a.formule_id
    JOIN tables_salle t ON t.etablissement_id = e.etablissement_id
    WHERE e.statut_etablissement = 'actif' AND t.numero_table = 1
    ORDER BY a.formule_id, e.etablissement_id""", j=db.maintenant().date())
BADGES = {"FRM01": ("Menu seul", FOND, "#334155"), "FRM02": ("Commande à table", BLEU, "#fff"), "FRM03": ("Statistiques", "#FEF3C7", "#92400E")}
cartes = ""
for d in demos:
    lib, bf, bt = BADGES.get(d["formule_id"], ("", FOND, TEXTE))
    vedette = d["formule_id"] == "FRM02"
    cartes += f"""<div style="background:#fff;border:2px solid {BLEU if vedette else BORD};border-radius:22px;padding:24px;display:flex;flex-direction:column;gap:12px">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><span class="titre" style="font-size:22px">{e(d['nom_formule'])}</span>
  <span style="font-size:12px;font-weight:700;background:{bf};color:{bt};border-radius:999px;padding:5px 10px">{lib}</span></div>
  <div><span class="titre" style="font-size:38px;color:{MARINE}">{int(d['prix_mensuel_ht'])}</span> <span style="font-size:14px;color:{GRIS}">DT HT par mois</span></div>
  <span style="font-size:15px;line-height:1.5;color:#334155;min-height:66px">{e(d['description'])}</span>
  <div style="background:{FOND};border-radius:14px;padding:10px 14px"><b>{e(d['nom_etablissement'])}</b><br><span style="font-size:13px;color:{GRIS}">{e(d['nom_ville'])} · table 1</span></div>
  <a href="/menu?table={e(d['table_id'])}" target="_self" style="display:flex;align-items:center;justify-content:center;min-height:46px;border-radius:14px;background:{BLEU if vedette else FOND};color:{'#fff' if vedette else MARINE};font-weight:700;text-decoration:none">Ouvrir le menu de la table</a>
</div>"""
st.markdown(f'<div class="grille" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">{cartes}</div>', unsafe_allow_html=True)

st.divider()
st.caption("MenuScan TN · projet de portfolio de Sarra Abdeljaouad · entreprise et données fictives · chiffres lus dans la base à chaque visite")
