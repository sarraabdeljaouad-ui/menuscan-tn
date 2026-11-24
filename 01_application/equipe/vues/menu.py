# -*- coding: utf-8 -*-
"""Menu (lot 2) : gestion de la carte par l'équipe.

Serveur et gérant : mettre un article en rupture pour aujourd'hui (il disparaît du menu client), ou le rendre disponible.
Gérant seulement : changer un prix, modifier une description, retirer ou remettre un article, ajouter un article.
Règle des prix (décision D-27) : voir db.changer_prix.
"""
import streamlit as st

from commun import db
from commun.theme import BLEU, GRIS, e, icone_categorie, kpis, prix

u = st.session_state.get("utilisateur")
if not u:
    st.warning("Connexion requise.")
    st.stop()
etab, gerant = u["etablissement_id"], u["role"] == "gerant"

if "message_menu" in st.session_state:
    st.toast(st.session_state.pop("message_menu"), icon=":material/check_circle:")


def rupture(article_id):
    db.signaler_rupture(etab, article_id, st.session_state[f"rup_{article_id}"], u["utilisateur_id"])


def retirer(article_id, nom, oui):
    db.retirer_article(etab, article_id, oui)
    st.session_state.message_menu = f"{nom} : {'retiré de la carte' if oui else 'remis sur la carte'}"


articles = db.carte(etab)
actifs = [a for a in articles if not a["retire"] and not a["a_venir"]]
retires = [a for a in articles if a["retire"]]
a_venir = [a for a in articles if a["a_venir"] and not a["retire"]]
ruptures = [a for a in actifs if a["rupture"]]

st.markdown(f'<div class="titre" style="font-size:32px">Menu</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · '
            f'{"prix, ruptures et carte" if gerant else "signalez les articles en rupture : ils disparaissent du menu des clients"}</div>',
            unsafe_allow_html=True)
kpis([("Sur la carte", str(len(actifs)), "articles proposés aujourd'hui", None),
      ("En rupture", str(len(ruptures)), ", ".join(a["nom_article"] for a in ruptures[:3]) or "aucune aujourd'hui", "#B45309" if ruptures else None),
      ("Retirés", str(len(retires)), "hors carte", None)], 190)

# ---------- Ajouter un article (gérant) ----------
if gerant:
    with st.expander("＋ Ajouter un article"):
        cats = db.categories(etab)
        with st.form("ajout", clear_on_submit=True, border=False):
            c1, c2, c3 = st.columns([2, 3, 1.4])
            cat = c1.selectbox("Catégorie", cats, format_func=lambda c: c["nom_categorie"])
            nom = c2.text_input("Nom", max_chars=40, placeholder="Ex. : Café glacé")
            p = c3.number_input("Prix TTC (DT)", min_value=0.0, max_value=500.0, step=0.1, format="%.3f")
            desc = st.text_input("Description (facultative)", max_chars=120, placeholder="Ex. : Express, glaçons et lait frais")
            if st.form_submit_button("Ajouter à la carte", type="primary", icon=":material/add:"):
                try:
                    db.ajouter_article(etab, cat["categorie_id"], nom, desc, p)
                    st.session_state.message_menu = f"{nom.strip()} ajouté à la carte à {prix(p)}"
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

# ---------- Liste des articles ----------
c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
noms_cat = list(dict.fromkeys(a["nom_categorie"] for a in actifs))
cat = c1.pills("Catégorie", ["Toutes"] + noms_cat, default="Toutes", key="cat_menu", label_visibility="collapsed") or "Toutes"
q = c2.text_input("Rechercher", placeholder="Rechercher un article", icon=":material/search:", label_visibility="collapsed").strip().lower()
liste = [a for a in actifs if (cat == "Toutes" or a["nom_categorie"] == cat)
         and (not q or q in a["nom_article"].lower() or q in (a["description"] or "").lower())]
rangs = {c: i for i, c in enumerate(noms_cat)}
if not liste:
    st.caption("Aucun article ne correspond.")

for a in liste:
    aid = a["article_id"]
    badge = ('<span class="badge" style="background:#FEF3C7;color:#92400E">Rupture aujourd\'hui</span>' if a["rupture"] else "")
    prochain = ""
    if a["prochain_prix"] is not None:  # prix programmé par le gérant (l'article avait déjà été vendu le jour du changement)
        prochain = (f' <span style="font-size:13px;color:#92400E;font-weight:600">→ {prix(a["prochain_prix"])} '
                    f'à partir du {a["prochain_date"]:%d/%m}</span>')
    with st.container(key=f"carte_m_{aid}"):
        cols = st.columns([5, 2.2, 1.6] if gerant else [5, 2.2], vertical_alignment="center")
        cols[0].markdown(f"""<div style="display:flex;gap:12px;align-items:center;{'opacity:.55' if a['rupture'] else ''}">
          {icone_categorie(a['nom_categorie'], rangs.get(a['nom_categorie'], 0))}
          <div style="min-width:0"><div style="font-weight:700">{e(a['nom_article'])}{badge}</div>
          <div style="font-size:13px;color:#64748B">{e(a['description'] or '')}</div>
          <div style="font-weight:700;color:{BLEU}">{prix(a['prix_ttc']) if a['prix_ttc'] is not None else '–'}{prochain}</div></div></div>""",
                         unsafe_allow_html=True)
        cols[1].toggle("Rupture", value=a["rupture"], key=f"rup_{aid}", on_change=rupture, args=(aid,))
        if gerant:
            with cols[2].popover("Modifier", icon=":material/edit:", width="stretch"):
                with st.form(f"modif_{aid}", border=False):
                    nv = st.number_input("Nouveau prix TTC (DT)", min_value=0.1, max_value=500.0, step=0.1, format="%.3f",
                                         value=float(a["prix_ttc"] or 1))
                    desc = st.text_input("Description", value=a["description"] or "", max_chars=120)
                    st.caption("Si l'article a déjà été commandé aujourd'hui, le nouveau prix s'applique à partir de demain.")
                    if st.form_submit_button("Enregistrer", type="primary", width="stretch"):
                        msg = []
                        if (desc or "") != (a["description"] or ""):
                            db.modifier_description(etab, aid, desc)
                            msg.append("description mise à jour")
                        r = db.changer_prix(etab, aid, nv, u["utilisateur_id"])
                        if r:
                            effet, lignes, cmds = r
                            quand = "dès aujourd'hui" if effet == db.maintenant().date() else f"à partir du {effet:%d/%m}"
                            msg.append(f"prix {prix(nv)} {quand}" + (f" ({cmds} commande{'s' if cmds > 1 else ''} simulée{'s' if cmds > 1 else ''} recalculée{'s' if cmds > 1 else ''})" if cmds else ""))
                        st.session_state.message_menu = f"{a['nom_article']} : " + (", ".join(msg) if msg else "aucun changement")
                        st.rerun()
                st.button("Retirer de la carte", key=f"ret_{aid}", on_click=retirer, args=(aid, a["nom_article"], True),
                          icon=":material/remove_circle:", width="stretch")

if retires and gerant:
    with st.expander(f"Articles retirés ({len(retires)})"):
        for a in retires:
            c1, c2 = st.columns([4, 1.5], vertical_alignment="center")
            c1.markdown(f"**{e(a['nom_article'])}** · {e(a['nom_categorie'])} · retiré le {a['date_retrait']:%d/%m/%Y}")
            c2.button("Remettre", key=f"rem_{a['article_id']}", on_click=retirer, args=(a["article_id"], a["nom_article"], False), width="stretch")
if a_venir:
    st.caption(f"{len(a_venir)} article(s) du jeu simulé arrivent plus tard sur la carte : "
               + ", ".join(f"{a['nom_article']} ({a['date_ajout']:%d/%m})" for a in a_venir) + ".")
