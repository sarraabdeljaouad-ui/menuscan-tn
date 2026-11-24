# -*- coding: utf-8 -*-
"""Écran de l'équipe, selon le rôle du compte connecté.

Gérant : ouverture des commandes, indicateurs, appels, commandes en direct, meilleures ventes, plan de salle.
Serveur : appels, commandes en direct et plan de salle, sans chiffre d'affaires ni réglages.
Plan de salle cliquable (lot 1) : une table ouvre une fenêtre avec ses appels, ses commandes et l'encaissement.
Les droits sont vérifiés ici à chaque exécution, et chaque écriture est limitée à l'établissement du compte.
"""
import streamlit as st

from commun import db
from commun.theme import BLEU, CASES, CLAIR, GRIS, MARINE, e, kpis, prix

MODES = {"Espèces": "especes", "Carte bancaire": "carte_bancaire", "Ticket restaurant": "ticket_restaurant"}
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
ZONES = {"terrasse": "Terrasse", "salle": "Salle", "etage": "Étage"}
MOTIFS = {"serveur": "appelle le serveur", "addition": "demande l'addition", "eau": "demande de l'eau"}
STATUTS = {"nouvelle": ("Nouvelle", CLAIR, MARINE), "en_prepa": ("En préparation", "#FEF3C7", "#92400E"),
           "prete": ("Prête", "#DCFCE7", "#166534"), "servie": ("Servie, à encaisser", "#EDE9FE", "#5B21B6")}
ACTIONS = {"nouvelle": "Accepter", "en_prepa": "Marquer prête", "prete": "Servie"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

u = st.session_state.get("utilisateur")
if not u:
    st.warning("Connexion requise.")
    st.stop()
choix = u["etablissement_id"]
gerant = u["role"] == "gerant"

n = db.maintenant()
h1, h2 = st.columns([3, 1], vertical_alignment="center")
h1.markdown(f'<div class="titre" style="font-size:32px">Bonjour {e(u["prenom"] if gerant else "l’équipe")}</div>'
            f'<div style="color:{GRIS}">{e(u["nom_etablissement"])} · {JOURS[n.weekday()]} {n.day} {MOIS[n.month - 1]} · {n:%H:%M}</div>',
            unsafe_allow_html=True)
ouvert_bd = db.commandes_ouvertes(choix)
if gerant:
    ouvert = h2.toggle("Commandes ouvertes", value=ouvert_bd, key="ouvert")
    if ouvert != ouvert_bd:
        db.ouvrir_commandes(choix, ouvert)
        st.rerun()
else:
    h2.markdown(f'<span style="background:{"#DCFCE7" if ouvert_bd else "#F1F5F9"};color:{"#166534" if ouvert_bd else GRIS};border-radius:999px;padding:8px 14px;font-weight:600">'
                f'{"Commandes ouvertes" if ouvert_bd else "Commandes fermées"}</span>', unsafe_allow_html=True)


def ouvrir_table(table_id):
    """Appelée depuis le tableau rafraîchi toutes les 10 s : relance toute la page pour afficher la fenêtre."""
    st.session_state.table_ouverte = table_id
    st.rerun(scope="app")


def fermer_table():
    st.session_state.pop("table_ouverte", None)


def prendre(appel_id):
    db.prendre_appel(choix, appel_id, u["utilisateur_id"])


def encaisser(table_id):
    """Appelée dans la fenêtre. La fermer depuis l'intérieur casse l'affichage (page blanche) :
    on relance donc toute la page, sans la fenêtre, et le message s'affiche ensuite sur le tableau."""
    mode = st.session_state.get(f"mode_{table_id}")
    if not mode:
        st.error("Choisissez le mode de règlement.")
        return
    montant = db.encaisser(choix, table_id, MODES[mode])
    st.session_state.message = f"Table encaissée : {prix(montant)} ({mode.lower()})"
    fermer_table()
    st.rerun(scope="app")


def minutes_depuis(h):
    return int((db.maintenant() - h).total_seconds() // 60)


def fenetre_table(t):
    """Fenêtre d'une table : appels, commandes en cours, encaissement. Elle reste ouverte après chaque action."""
    @st.dialog(f"Table {t['numero_table']} · {ZONES.get(t['zone'], t['zone'])}", width="medium", on_dismiss=fermer_table)
    def contenu():
        d = db.detail_table(choix, t["table_id"])
        for a in d["appels"]:
            with st.container(key=f"appel_f_{a['appel_id']}"):
                c1, c2 = st.columns([3, 2], vertical_alignment="center")
                c1.markdown(f"**Le client {MOTIFS[a['motif']]}** · {minutes_depuis(a['date_heure_appel'])} min")
                c2.button("Je m'en occupe", key=f"pf_{a['appel_id']}", on_click=prendre, args=(a["appel_id"],), type="primary", width="stretch")
        en_cours = [c for c in d["commandes"] if not c["a_encaisser"]]
        a_regler = [c for c in d["commandes"] if c["a_encaisser"]]
        if not d["commandes"] and not d["appels"]:
            st.caption("Rien en cours à cette table.")
        for c in en_cours + a_regler:
            lib, fond, txt = STATUTS[c["statut_commande"]]
            note = f'<div style="font-size:13px;color:#92400E;margin-top:4px">« {e(c["note"])} »</div>' if c["note"] else ""
            with st.container(key=f"carte_f_{c['commande_id']}"):
                st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b>{c['commande_id']}
                  <span style="font-weight:500;color:#64748B;font-size:13px">· {c['date_heure_commande']:%H:%M}</span></b>
                  <span style="background:{fond};color:{txt};border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700">{lib}</span></div>
                  <div style="font-size:14px;color:#334155;margin-top:4px">{e(c['detail'])}</div>{note}
                  <div style="font-weight:700;color:{BLEU};margin-top:4px">{prix(c['montant_total_ttc'])}</div>""", unsafe_allow_html=True)
                if c["statut_commande"] in ACTIONS:
                    b1, b2 = st.columns([3, 2])
                    b1.button(ACTIONS[c["statut_commande"]], key=f"fa_{c['commande_id']}", type="primary", on_click=db.avancer,
                              args=(choix, c["commande_id"]), width="stretch")
                    if c["statut_commande"] == "nouvelle":
                        b2.button("Annuler", key=f"fn_{c['commande_id']}", on_click=db.annuler, args=(choix, c["commande_id"]), width="stretch")
        if a_regler:
            total = sum(c["montant_total_ttc"] for c in a_regler)
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:6px">
              <b>À encaisser ({len(a_regler)} commande{"s" if len(a_regler) > 1 else ""})</b>
              <span class="titre" style="font-size:24px;color:{MARINE}">{prix(total)}</span></div>""", unsafe_allow_html=True)
            st.pills("Règlement", list(MODES), key=f"mode_{t['table_id']}", label_visibility="collapsed")
            if st.button(f"Encaisser {prix(total)}", key=f"enc_{t['table_id']}", type="primary", icon=":material/payments:", width="stretch"):
                encaisser(t["table_id"])
        elif en_cours:
            st.caption("Les commandes seront à encaisser une fois servies.")
    contenu()


@st.fragment(run_every="10s")
def tableau():
    actives = db.commandes_actives(choix)
    periode = f"depuis le 1er {MOIS[n.month - 1]}"
    if gerant:
        i = db.indicateurs(choix)
        if i["ca_semaine"]:
            ecart = round((i["ca_jour"] / i["ca_semaine"] - 1) * 100)
            comp = (f"{'+' if ecart >= 0 else '−'}{abs(ecart)} % vs {JOURS[i['jour_semaine'].weekday()]} "
                    f"{i['jour_semaine']:%d/%m}, même heure", "#166534" if ecart >= 0 else "#B45309")
        else:
            comp = ("pas de vente le même jour la semaine dernière", None)
        kpis([("Chiffre servi aujourd'hui", prix(i["ca_jour"]), comp[0], comp[1]),
              ("Commandes servies", str(i["n_jour"]), f"{len(actives)} en cours", None),
              ("Panier moyen", prix(i["panier"]) if i["panier"] else "–", periode, None),
              ("Délai de service", f"{i['delai']:.1f} min".replace(".", ",") if i["delai"] else "–", periode, None),
              ("Taux de commande", f"{100 * float(i['taux']):.1f} %".replace(".", ",") if i["taux"] is not None else "–", f"des scans, {periode}", None)], 160)
    tables = db.etat_tables(choix)
    if not gerant:
        compte = {s: sum(1 for c in actives if c["statut_commande"] == s) for s in ("nouvelle", "en_prepa", "prete")}
        enc = sum(1 for t in tables if t["a_encaisser"])
        kpis([("Nouvelles", str(compte["nouvelle"]), "à accepter", None), ("En préparation", str(compte["en_prepa"]), "en cuisine", None),
              ("Prêtes", str(compte["prete"]), "à servir", "#166534" if compte["prete"] else None),
              ("À encaisser", str(enc), f"table{'s' if enc > 1 else ''}", "#5B21B6" if enc else None)], 160)

    appels = db.appels_en_attente(choix)
    if appels:
        st.markdown(f'<div class="titre" style="font-size:20px;margin-top:14px">Appels <span style="font-size:15px;color:#92400E">· {len(appels)} en attente</span></div>',
                    unsafe_allow_html=True)
        for a in appels:
            with st.container(key=f"appel_{a['appel_id']}"):
                c1, c2, c3 = st.columns([5, 2, 2], vertical_alignment="center")
                c1.markdown(f"**Table {a['numero_table']}** · {e(a['zone'])} · {MOTIFS[a['motif']]} · "
                            f"<span style='color:#92400E'>{minutes_depuis(a['date_heure_appel'])} min</span>", unsafe_allow_html=True)
                if c2.button("Voir la table", key=f"va_{a['appel_id']}", width="stretch"):
                    ouvrir_table(a["table_id"])
                c3.button("Je m'en occupe", key=f"pa_{a['appel_id']}", on_click=prendre, args=(a["appel_id"],), type="primary", width="stretch")

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
                        b1.button("Accepter", key=f"acc_{cid}", type="primary", on_click=db.avancer, args=(choix, cid), width="stretch")
                        b2.button("Annuler", key=f"ann_{cid}", on_click=db.annuler, args=(choix, cid), width="stretch")
                    elif statut == "en_prepa":
                        st.button("Marquer prête", key=f"pre_{cid}", type="primary", on_click=db.avancer, args=(choix, cid), width="stretch")
                    else:
                        st.button("Servie", key=f"ser_{cid}", type="primary", on_click=db.avancer, args=(choix, cid), width="stretch")

    if gerant:
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
    else:
        d = st.container()
    with d.container(key="carte_tables"):
        occ = sum(1 for t in tables if t["appel"] or t["commande"] or t["a_encaisser"] or t["ouvert"])
        st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline"><span class="titre" style="font-size:19px">Tables</span>'
                    f'<span style="font-size:13px;color:#64748B">{occ} occupée{"s" if occ > 1 else ""} sur {len(tables)}</span></div>', unsafe_allow_html=True)
        st.caption("Touchez une table pour voir ses commandes, prendre un appel ou encaisser.")
        with st.container(key="plan"):
            for zone in dict.fromkeys(t["zone"] for t in tables):
                st.markdown(f'<div style="font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#64748B;margin:6px 0 0">{ZONES.get(zone, e(zone))}</div>',
                            unsafe_allow_html=True)
                de_zone = [t for t in tables if t["zone"] == zone]
                for i in range(0, len(de_zone), 7):
                    for col, t in zip(st.columns(7), de_zone[i:i + 7]):
                        cle = ("appel" if t["appel"] else "commande" if t["commande"] else "encaisser" if t["a_encaisser"]
                               else "menu" if t["ouvert"] else "libre")
                        with col.container(key=f"case_{cle}_{t['table_id']}"):
                            if st.button(f"**{t['numero_table']}**  \n{CASES[cle][0]}", key=f"t_{t['table_id']}", width="stretch"):
                                ouvrir_table(t["table_id"])
        legende = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px"><span style="width:12px;height:12px;border-radius:3px;background:{f}"></span>{l}</span>'
                          for l, f, _ in CASES.values())
        st.markdown(f'<div style="font-size:13px;color:#334155;margin-top:8px">{legende}</div>', unsafe_allow_html=True)


if "message" in st.session_state:
    st.toast(st.session_state.pop("message"), icon=":material/check_circle:")
tableau()
ouverte = st.session_state.get("table_ouverte")
if ouverte:
    t = next((t for t in db.etat_tables(choix) if t["table_id"] == ouverte), None)  # seulement une table de l'établissement du compte
    if t:
        fenetre_table(t)
