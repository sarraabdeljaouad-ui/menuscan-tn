# -*- coding: utf-8 -*-
"""Application client MenuScan TN, ouverte par le QR code de la table (/?table=TBL00001) : menu, panier, suivi de la commande.

Lancement, depuis le dossier 01_application/client, environnement Python activé :
    streamlit run app.py          (port 8501, défini dans .streamlit/config.toml)
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from commun import db, theme  # noqa: E402
from commun.theme import BLEU, CLAIR, GRIS, MARINE, e, icone_categorie, prix  # noqa: E402

st.set_page_config(page_title="Menu · MenuScan TN", page_icon=":material/restaurant_menu:", layout="centered", initial_sidebar_state="collapsed")
theme.appliquer()
try:
    db.moteur()
except db.MigrationManquante as err:
    st.error(str(err))
    st.stop()

T = {
    "fr": dict(recherche="Rechercher un plat, une boisson…", panier="Voir le panier", ma_commande="Ma commande", envoyer="Envoyer la commande",
               note="Note pour le serveur", note_ex="Ex. : capucin bien chaud, sans sucre", appeler="Appeler le serveur",
               appel_ok="Le serveur a été prévenu.", total="Total TTC", sous_total="Sous-total", nouvelle="Nouvelle commande",
               envoyee="Commande envoyée", ou="Où en est ma commande ?", retour="Retour au menu", populaire="Populaire",
               vide="Votre panier est vide.", articles="articles", reglement="Règlement à table : espèces, carte ou ticket restaurant",
               ajouter_autres="Ajouter d'autres articles", recap="Récapitulatif", annulee="Commande annulée : un article n'était plus disponible. Le serveur passe à votre table.",
               etapes=["Reçue", "En préparation", "Prête", "Servie"], details=["Envoyée au café", "Acceptée par l'équipe", "Le serveur l'apporte", "Bon appétit !"],
               delai="Service en {m} min en moyenne ici (30 derniers jours)", ferme="Les commandes sont fermées pour le moment : le menu reste consultable.",
               essentiel="Menu consultable uniquement : cet établissement ne propose pas la commande depuis la table.",
               autre="Commander autre chose", mes_commandes="Mes commandes", total_visite="Total de la visite", suivre="Suivre ma commande",
               motifs={"serveur": "Appeler le serveur", "addition": "Demander l'addition", "eau": "De l'eau, s'il vous plaît"},
               appels_ok={"serveur": "Le serveur a été prévenu.", "addition": "L'addition arrive.", "eau": "Le serveur apporte de l'eau."},
               deja="Déjà demandé : le serveur arrive.", annulee_court="Annulée", reglee="Réglée", besoin="Besoin de quelque chose ?",
               options="Vos préférences", ajouter="Ajouter", maj="Mettre à jour", retirer_panier="Retirer du panier", unite="l'unité", qte="Quantité",
               estime="Servie vers {h}, dans environ {m} min", bientot="Servie d'un moment à l'autre",
               estime_note="Estimation d'après les commandes servies ici ces 30 derniers jours.",
               prete_titre="Votre commande est prête !", prete_txt="Le serveur vous l'apporte.", onglet_pret="Commande prête !",
               avis_titre="Votre avis", avis_q="Comment s'est passée votre commande ?", avis_com="Un commentaire ? (facultatif)",
               avis_env="Envoyer mon avis", merci="Merci pour votre avis !"),
    "ar": dict(recherche="ابحث عن طبق أو مشروب…", panier="عرض السلة", ma_commande="طلبي", envoyer="إرسال الطلب",
               note="ملاحظة للنادل", note_ex="مثال: كابوسان ساخن جدًا، بدون سكر", appeler="نداء النادل",
               appel_ok="تم إعلام النادل.", total="المجموع", sous_total="المجموع الفرعي", nouvelle="طلب جديد",
               envoyee="تم إرسال الطلب", ou="أين وصل طلبي؟", retour="العودة إلى القائمة", populaire="الأكثر طلبًا",
               vide="سلتك فارغة.", articles="عناصر", reglement="الدفع على الطاولة: نقدًا أو بالبطاقة أو بتذكرة المطعم",
               ajouter_autres="إضافة عناصر أخرى", recap="ملخص الطلب", annulee="أُلغي الطلب: أحد العناصر غير متوفر. سيأتي النادل إلى طاولتك.",
               etapes=["تم الاستلام", "قيد التحضير", "جاهز", "تم التقديم"], details=["أُرسل إلى المقهى", "قبله الفريق", "النادل في الطريق", "بالهناء والشفاء!"],
               delai="مدة التقديم هنا {m} دقيقة في المتوسط (آخر 30 يومًا)", ferme="الطلبات مغلقة حاليًا: يمكنك تصفح القائمة.",
               essentiel="القائمة للاطلاع فقط: هذا المحل لا يوفر الطلب من الطاولة.",
               autre="طلب شيء آخر", mes_commandes="طلباتي", total_visite="مجموع الزيارة", suivre="متابعة طلبي",
               motifs={"serveur": "نداء النادل", "addition": "طلب الحساب", "eau": "ماء من فضلك"},
               appels_ok={"serveur": "تم إعلام النادل.", "addition": "الحساب في الطريق.", "eau": "النادل سيحضر الماء."},
               deja="تم الطلب مسبقًا: النادل في الطريق.", annulee_court="ملغى", reglee="مدفوع", besoin="هل تحتاج شيئًا؟",
               options="تفضيلاتك", ajouter="إضافة", maj="تحديث", retirer_panier="حذف من السلة", unite="للوحدة", qte="الكمية",
               estime="يُقدَّم حوالي الساعة {h}، بعد {m} دقيقة تقريبًا", bientot="يُقدَّم بعد قليل",
               estime_note="تقدير حسب الطلبات المقدَّمة هنا خلال آخر 30 يومًا.",
               prete_titre="طلبك جاهز!", prete_txt="النادل في الطريق إليك.", onglet_pret="الطلب جاهز!",
               avis_titre="رأيك", avis_q="كيف كان طلبك؟", avis_com="تعليق؟ (اختياري)",
               avis_env="إرسال رأيي", merci="شكرًا على رأيك!"),
}

# Options sans effet sur le prix, par type de plat (enregistrées en français pour l'équipe, affichées dans la langue du client)
OPTIONS = {
    "Boissons chaudes": ["Sans sucre", "Peu sucré", "Bien chaud", "Lait à part"],
    "Thés et infusions": ["Sans sucre", "Peu sucré", "Menthe en plus"],
    "Boissons fraîches": ["Sans glaçons", "Sans sucre"], "Jus frais": ["Sans glaçons", "Sans sucre"],
    "Crêpes et gaufres": ["Sans chantilly"], "Desserts": ["Sans chantilly"],
    "Sandwichs": ["Sans oignon", "Sans piment"], "Burgers": ["Sans oignon", "Sans piment", "Bien cuit"],
    "Tacos": ["Sans oignon", "Sans piment"], "Grillades": ["Sans piment", "Bien cuit"], "Plats": ["Sans piment"],
    "Pizzas": ["Sans piment"], "Pâtes": ["Sans piment"], "Entrées": ["Sans oignon", "Sans piment"],
}
OPTIONS_AR = {"Sans sucre": "بدون سكر", "Peu sucré": "سكر قليل", "Bien chaud": "ساخن جدًا", "Lait à part": "الحليب على حدة",
              "Menthe en plus": "نعناع إضافي", "Sans glaçons": "بدون ثلج", "Sans chantilly": "بدون كريمة",
              "Sans oignon": "بدون بصل", "Sans piment": "بدون فلفل حار", "Bien cuit": "مطهو جيدًا"}


def appareil():
    ua = (st.context.headers.get("User-Agent") or "").lower()
    if "iphone" in ua or "ipad" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    return "web"  # ordinateur : valeur propre à l'application, absente des données générées


table_id = st.query_params.get("table")
if not table_id:
    st.warning("Scannez le QR code de votre table pour ouvrir le menu.")
    st.stop()
info = db.table_et_etablissement(table_id)
if info is None:
    st.error("Ce QR code ne correspond à aucune table.")
    st.stop()
if info["table_retiree"]:
    st.error("Cette table n'est plus en service. Demandez au serveur le QR code d'une autre table.")
    st.stop()
if info["statut_etablissement"] != "actif" or info["formule_id"] is None:
    st.error("Le menu de cet établissement n'est plus disponible.")
    st.stop()

etab = info["etablissement_id"]
etat = st.session_state
jeton = st.query_params.get("s")
# Le panier, la langue, la vue et la commande sont gardés en base (migration 003) et retrouvés grâce au jeton
# placé dans l'adresse : une actualisation de la page ne fait plus rien perdre, et ne compte plus comme un nouveau scan.
if etat.get("jeton") is None or etat.get("jeton") != jeton or etat.get("table") != table_id:
    ec = db.etat_client(jeton, table_id) or db.nouvel_etat_client(table_id, etab, appareil(), etat.get("langue", "fr"))
    etat.jeton, etat.table, etat.session_id = ec["jeton"], table_id, ec["session_id"]
    etat.panier = {k: int(v) for k, v in ec["panier"].items()}
    etat.langue, etat.vue, etat.commande = ec["langue"], ec["vue"], ec["commande_id"]
    etat.commandes = list(ec["commandes"] or [])
    etat.options = dict(ec.get("options") or {})
    if jeton != ec["jeton"]:
        st.query_params["s"] = ec["jeton"]
L = T[etat.get("langue", "fr")]
peut_commander = bool(info["inclut_commande"])
ouvert = peut_commander and bool(info["commandes_ouvertes"])


def sauver():
    db.sauver_etat_client(etat.jeton, etat.session_id, etat.panier, etat.langue, etat.vue, etat.commande, etat.commandes, etat.options)


def changer_langue():
    etat.langue = "fr" if etat.get("langue", "fr") == "ar" else "ar"
    db.changer_langue(etat.session_id, etat.langue)
    sauver()


def appeler(motif):
    if db.appeler(etat.session_id, table_id, etab, motif):
        st.toast(L["appels_ok"][motif])
    else:
        st.toast(L["deja"])


def bouton_appel(cle, plein=False):
    """Cloche : appel du serveur avec un motif (serveur, addition, eau)."""
    with st.popover("" if not plein else L["besoin"], icon=":material/notifications:", width="stretch", key=cle):
        for motif, texte in L["motifs"].items():
            if motif == "addition" and not etat.commandes:
                continue
            st.button(texte, key=f"{cle}_{motif}", on_click=appeler, args=(motif,), width="stretch",
                      type="primary" if motif == "addition" else "secondary")


def modifier(article_id, d):
    q = etat.panier.get(article_id, 0) + d
    if q > 0:
        etat.panier[article_id] = q
    else:
        etat.panier.pop(article_id, None)
        etat.options.pop(article_id, None)
    db.journaliser(etat.session_id, etab, "ajout_panier" if d > 0 else "retrait_panier", article_id, 1)
    sauver()


def ouvrir_fiche(article_id):
    """Ouvrir la fiche d'un article = l'avoir regardé : événement vue_article, comme dans les données générées."""
    etat.fiche = article_id
    db.journaliser(etat.session_id, etab, "vue_article", article_id)


def fermer_fiche():
    etat.pop("fiche", None)


def traduire(opts):
    return [OPTIONS_AR.get(o, o) for o in opts] if etat.get("langue", "fr") == "ar" else list(opts)


def aller(vue):
    etat.vue = vue
    sauver()


def commander_autre():
    """Une commande par session (DQ-12) : retour au menu après une commande = nouvelle session, même jeton, même visite."""
    if etat.commande:
        etat.session_id = db.ouvrir_session(table_id, etab, appareil(), etat.langue)
        etat.commande = None
    aller("menu")


initiales = "".join(m[0] for m in info["nom_etablissement"].split() if m[0].isupper())[:2] or "MS"
with st.container(key="entete"):
    c1, c2 = st.columns([3, 1], vertical_alignment="center")
    c1.markdown(f"""<div style="display:flex;align-items:center;gap:12px">
      <span class="titre" style="width:46px;height:46px;flex:none;border-radius:12px;background:#fff;color:{MARINE} !important;display:flex;align-items:center;justify-content:center;font-size:17px">{e(initiales)}</span>
      <div><div class="titre" style="font-size:21px;color:#fff">{e(info['nom_etablissement'])}</div>
      <div style="font-size:13px;color:#C7D7F5">{e(info['nom_ville'])} · table {info['numero_table']} · {e(info['zone'])}</div></div></div>""",
                unsafe_allow_html=True)
    c2.button("FR · ع" if etat.get("langue", "fr") == "fr" else "ع · FR", key="langue_btn", on_click=changer_langue,
              help="Français / العربية", width="stretch")

articles = db.menu(etab)
noms = {a["article_id"]: a for a in articles}
nb = sum(etat.panier.values())
total = sum(q * noms[a]["prix_ttc"] for a, q in etat.panier.items() if a in noms)


# ---------- Vue : suivi de la commande ----------
if etat.vue == "suivi" and etat.commandes:
    @st.fragment(run_every="10s")
    def afficher_suivi():
        c = db.suivi(etat.commandes[-1])
        st.markdown(f"""<div style="text-align:center;padding:12px 0 4px"><div style="width:58px;height:58px;margin:0 auto 8px;border-radius:50%;background:{CLAIR};display:flex;align-items:center;justify-content:center">
          <svg aria-hidden="true" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{BLEU}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
          <div class="titre" style="font-size:24px">{L['envoyee']}</div><div style="color:{GRIS};font-size:14px">{c['commande_id']}</div></div>""", unsafe_allow_html=True)
        statut = c["statut_commande"]
        if statut in ("nouvelle", "en_prepa"):
            est = db.estimation(etab, c)
            if est:
                reste = round((est[0] - db.maintenant()).total_seconds() / 60)
                texte = L["estime"].format(h=f"\u2066{est[0]:%H:%M}\u2069", m=reste) if reste > 0 else L["bientot"]
                st.markdown(f"""<div style="background:{CLAIR};border-radius:16px;padding:12px 16px;margin-bottom:10px;display:flex;gap:10px;align-items:center">
                  <span style="font-size:22px">⏱</span><div><div style="font-weight:700;color:{MARINE}">{texte}</div>
                  <div style="font-size:12px;color:#64748B">{L['estime_note']}</div></div></div>""", unsafe_allow_html=True)
        if statut == "prete":
            st.markdown(f"""<div style="background:#16A34A;border-radius:20px;padding:18px;margin-bottom:10px;text-align:center;color:#fff">
              <div class="titre" style="font-size:24px;color:#fff !important">🔔 {L['prete_titre']}</div>
              <div style="font-size:15px;color:#fff">{L['prete_txt']}</div></div>""", unsafe_allow_html=True)
        # titre de l'onglet : visible même quand le client regarde un autre onglet ; vibration sur Android (l'iPhone l'ignore)
        titre = f"✅ {L['onglet_pret']}" if statut == "prete" else "Menu · MenuScan TN"
        st.html(f"<script>document.title = {titre!r}; {'try{{navigator.vibrate&&navigator.vibrate([200,100,200])}}catch(e){{}}' if statut == 'prete' else ''}</script>",
                unsafe_allow_javascript=True, width=1)
        if statut == "servie" and not etat.get(f"avis_vu_{c['commande_id']}"):
            etat[f"avis_vu_{c['commande_id']}"] = True
            st.rerun(scope="app")  # affiche la carte « Votre avis », placée hors de la zone rafraîchie toutes les 10 s
        if statut == "annulee":
            st.error(L["annulee"])
        else:
            heures = [c["date_heure_commande"], c["date_heure_acceptation"], c["date_heure_prete"], c["date_heure_service"]]
            rang = ["nouvelle", "en_prepa", "prete", "servie"].index(c["statut_commande"])
            lignes = ""
            for i, (nom, det, h) in enumerate(zip(L["etapes"], L["details"], heures)):
                fait = i <= rang
                pastille = (f'<span style="width:26px;height:26px;border-radius:50%;background:{BLEU};display:flex;align-items:center;justify-content:center">'
                            f'<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span>'
                            if fait else '<span style="width:26px;height:26px;border-radius:50%;border:2px solid #CBD5E1;box-sizing:border-box;display:block"></span>')
                trait = f'<span style="width:2px;height:20px;background:{BLEU if i < rang else "#E2E8F5"};display:block;margin:2px auto"></span>' if i < 3 else ""
                lignes += (f'<div style="display:flex;gap:12px"><div style="width:26px">{pastille}{trait}</div>'
                           f'<div style="flex:1;display:flex;justify-content:space-between"><div><div style="font-weight:{700 if i == rang else 600};color:{"#0F172A" if fait else "#64748B"}">{nom}</div>'
                           f'<div style="font-size:13px;color:#64748B">{det}</div></div><span style="font-size:14px;color:{GRIS}">{h.strftime("%H:%M") if h else ""}</span></div></div>')
            st.markdown(f'<div style="background:#fff;border-radius:20px;padding:16px 18px"><div class="titre" style="font-size:17px;margin-bottom:10px">{L["ou"]}</div>{lignes}</div>',
                        unsafe_allow_html=True)
        recap = "".join(f'<div style="display:flex;justify-content:space-between"><span>{l["quantite"]} × {e(l["nom_article"])}'
                        + (f'<br><span style="font-size:13px;color:#92400E">{" · ".join(e(o) for o in traduire(l["options"].split(" · ")))}</span>' if l["options"] else "")
                        + f'</span><span>{prix(l["montant_ligne_ttc"])}</span></div>' for l in c["lignes"])
        note = f'<div style="font-size:13px;color:#64748B">« {e(c["note"])} »</div>' if c["note"] else ""
        st.markdown(f"""<div style="background:#fff;border-radius:20px;padding:16px 18px;margin-top:12px;display:flex;flex-direction:column;gap:6px">
          <div class="titre" style="font-size:17px">{L['recap']}</div>{recap}{note}
          <div style="border-top:1px solid #E2E8F5;padding-top:8px;display:flex;justify-content:space-between;align-items:baseline"><b>{L['total']}</b>
          <span class="titre" style="font-size:22px;color:{MARINE}">{prix(c['montant_total_ttc'])}</span></div></div>""", unsafe_allow_html=True)

    derniere = etat.commandes[-1]
    servie = db.suivi(derniere)["statut_commande"] == "servie"
    if servie:
        etat[f"avis_vu_{derniere}"] = True  # déjà servie à l'ouverture : pas de rechargement en plus
    afficher_suivi()

    @st.fragment(run_every="10s")
    def afficher_visite():
        if len(etat.commandes) < 2:
            return
        cs = db.commandes_visite(etat.commandes)
        etats = dict(zip(["nouvelle", "en_prepa", "prete", "servie"], L["etapes"]), annulee=L["annulee_court"])
        lignes = "".join(f"""<div style="display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-top:1px solid #E2E8F5">
          <span><b>{c['commande_id']}</b> <span style="color:#64748B;font-size:13px">· {c['date_heure_commande']:%H:%M} ·
          {L['reglee'] if c['date_heure_reglement'] else etats[c['statut_commande']]}</span></span>
          <span style="{'text-decoration:line-through;color:#94A3B8' if c['statut_commande'] == 'annulee' else ''}">{prix(c['montant_total_ttc'])}</span></div>""" for c in cs)
        total_visite = sum(c["montant_total_ttc"] for c in cs if c["statut_commande"] != "annulee")
        st.markdown(f"""<div style="background:#fff;border-radius:20px;padding:16px 18px;margin-top:12px">
          <div class="titre" style="font-size:17px;margin-bottom:6px">{L['mes_commandes']}</div>{lignes}
          <div style="border-top:1px solid #E2E8F5;padding-top:8px;display:flex;justify-content:space-between;align-items:baseline"><b>{L['total_visite']}</b>
          <span class="titre" style="font-size:20px;color:{MARINE}">{prix(total_visite)}</span></div></div>""", unsafe_allow_html=True)

    afficher_visite()

    if servie:
        deja = db.avis_de(derniere)
        with st.container(key="carte_avis"):
            if deja or etat.get(f"avis_ok_{derniere}"):
                st.markdown(f'<div style="text-align:center;font-weight:700;color:#166534">{L["merci"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="titre" style="font-size:17px">{L["avis_titre"]}</div><div style="color:#64748B;font-size:14px">{L["avis_q"]}</div>',
                            unsafe_allow_html=True)
                note = st.feedback("stars", key=f"etoiles_{derniere}")
                com = st.text_input(L["avis_com"], max_chars=300, key=f"com_{derniere}", label_visibility="collapsed", placeholder=L["avis_com"])
                if st.button(L["avis_env"], type="primary", width="stretch", disabled=note is None, key=f"env_{derniere}"):
                    db.donner_avis(derniere, note + 1, com)
                    etat[f"avis_ok_{derniere}"] = True
                    st.rerun()
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        bouton_appel("cloche_suivi", plein=True)
    if ouvert:
        b2.button(L["autre"], type="primary", width="stretch", on_click=commander_autre, icon=":material/add:")
    st.stop()


# ---------- Vue : panier ----------
if etat.vue == "panier":
    st.button(L["retour"], icon=":material/arrow_back:", on_click=aller, args=("menu",))
    st.markdown(f'<div class="titre" style="font-size:26px">{L["ma_commande"]}</div>', unsafe_allow_html=True)
    m = db.delai_moyen(etab)
    if m:
        st.info(L["delai"].format(m=round(m)))
    if not etat.panier:
        st.caption(L["vide"])
    rangs = {c: i for i, c in enumerate(dict.fromkeys(a["nom_categorie"] for a in articles))}
    for aid, q in list(etat.panier.items()):
        a = noms[aid]
        with st.container(key=f"carte_p_{aid}"):
            c1, c2 = st.columns([5, 3], vertical_alignment="center")
            c1.markdown(f"""<div style="display:flex;gap:12px;align-items:center">{icone_categorie(a['nom_categorie'], rangs[a['nom_categorie']])}
              <div><div style="font-weight:700">{e(a['nom_article'])}</div><div style="font-size:13px;color:#64748B">{prix(a['prix_ttc'])} {L['unite']}</div>
              <div style="font-size:13px;color:#92400E">{" · ".join(e(o) for o in traduire(etat.options.get(aid, [])))}</div>
              <div style="font-weight:700;color:{BLEU}">{prix(q * a['prix_ttc'])}</div></div></div>""", unsafe_allow_html=True)
            m1, m2, m3 = c2.columns(3, vertical_alignment="center")
            m1.button("−", key=f"pm_{aid}", on_click=modifier, args=(aid, -1), width="stretch")
            m2.markdown(f"<div style='text-align:center;font-weight:700'>{q}</div>", unsafe_allow_html=True)
            m3.button("+", key=f"pp_{aid}", on_click=modifier, args=(aid, 1), type="primary", width="stretch")
    st.button(L["ajouter_autres"], icon=":material/add:", on_click=aller, args=("menu",), type="tertiary")
    note = st.text_area(L["note"], placeholder=L["note_ex"], max_chars=200, key="note")
    if etat.panier:
        with st.container(key="carte_recap"):
            st.markdown(f"""<div style="display:flex;justify-content:space-between;color:{GRIS}"><span>{L['sous_total']} ({nb} {L['articles']})</span><span>{prix(total)}</span></div>
              <div style="color:{GRIS};font-size:14px;margin:6px 0 10px">{L['reglement']}</div>
              <div style="border-top:1px solid #E2E8F5;padding-top:10px;display:flex;justify-content:space-between;align-items:baseline"><b>{L['total']}</b>
              <span class="titre" style="font-size:28px;color:{MARINE}">{prix(total)}</span></div>""", unsafe_allow_html=True)
            if st.button(L["envoyer"], type="primary", icon=":material/send:", width="stretch", disabled=not ouvert):
                try:
                    etat.commande = db.passer_commande(etat.session_id, table_id, etab, dict(etat.panier), note,
                                                    {k: v for k, v in etat.options.items() if k in etat.panier})
                    etat.commandes.append(etat.commande)
                    etat.panier, etat.options, etat.vue = {}, {}, "suivi"
                    sauver()
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))
        if not ouvert:
            st.warning(L["ferme"])
    st.stop()


# ---------- Vue : menu ----------
if etat.commandes:
    st.button(L["suivre"], icon=":material/receipt_long:", on_click=aller, args=("suivi",), width="stretch", key="suivre")
if not peut_commander:
    st.info(L["essentiel"])
elif not ouvert:
    st.warning(L["ferme"])
recherche = st.text_input("Recherche", placeholder=L["recherche"], label_visibility="collapsed", icon=":material/search:").strip().lower()
categories = list(dict.fromkeys(a["nom_categorie"] for a in articles))
rangs = {c: i for i, c in enumerate(categories)}
if recherche:
    liste, titre = [a for a in articles if recherche in a["nom_article"].lower() or recherche in (a["description"] or "").lower()], f"« {recherche} »"
else:
    cat = st.pills("Catégories", categories, default=categories[0], key="categorie", label_visibility="collapsed") or categories[0]
    liste, titre = [a for a in articles if a["nom_categorie"] == cat], cat
st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 0"><span class="titre" style="font-size:20px">{e(titre)}</span>'
            f'<span style="font-size:13px;color:#64748B">{len(liste)} {L["articles"]}</span></div>', unsafe_allow_html=True)

for a in liste:
    aid = a["article_id"]
    badge = f'<span class="badge" style="background:#FEF3C7;color:#92400E">{L["populaire"]}</span>' if a["populaire"] else ""
    with st.container(key=f"carte_art_{aid}"):
        # bouton invisible sous la carte : toucher la carte (hors boutons + et −) ouvre la fiche de l'article
        st.button(a["nom_article"], key=f"voile_{aid}", on_click=ouvrir_fiche, args=(aid,))
        if ouvert:
            c1, c2 = st.columns([5, 2], vertical_alignment="center")
        else:
            c1 = st.container()
        c1.markdown(f"""<div style="display:flex;gap:12px;align-items:center">{icone_categorie(a['nom_categorie'], rangs[a['nom_categorie']])}
          <div style="min-width:0"><div style="font-weight:700;font-size:16px">{e(a['nom_article'])}{badge}</div>
          <div style="font-size:13px;color:#64748B;line-height:1.35">{e(a['description'] or '')}</div>
          <div style="font-weight:700;color:{BLEU}">{prix(a['prix_ttc'])}
          <span style="font-weight:500;font-size:12px;color:#64748B">{" · ".join(e(o) for o in traduire(etat.options.get(aid, []))) if etat.panier.get(aid) else ""}</span></div></div></div>""",
                    unsafe_allow_html=True)
        if ouvert:
            q = etat.panier.get(aid, 0)
            if q:
                m1, m2, m3 = c2.columns(3, vertical_alignment="center")
                m1.button("−", key=f"m_{aid}", on_click=modifier, args=(aid, -1), width="stretch")
                m2.markdown(f"<div style='text-align:center;font-weight:700'>{q}</div>", unsafe_allow_html=True)
                m3.button("+", key=f"p_{aid}", on_click=modifier, args=(aid, 1), type="primary", width="stretch")
            else:
                c2.button("+", key=f"a_{aid}", on_click=modifier, args=(aid, 1), type="primary", width="stretch")

st.markdown('<div class="espace-bas"></div>', unsafe_allow_html=True)
if peut_commander:
    with st.container(key="barre"):
        b1, b2 = st.columns([1, 4], vertical_alignment="center")
        with b1:
            bouton_appel("cloche")
        if nb:
            b2.button(f"\u2066{nb}\u2069  ·  {L['panier']}  ·  \u2066{prix(total)}\u2069", type="primary", on_click=aller, args=("panier",), width="stretch")
        else:
            b2.caption(L["vide"])


# ---------- Fiche article (lot 3) ----------
def fiche(a):
    @st.dialog(a["nom_article"], on_dismiss=fermer_fiche)
    def contenu():
        aid = a["article_id"]
        st.markdown(f"""<div style="display:flex;gap:14px;align-items:center">{icone_categorie(a['nom_categorie'], rangs.get(a['nom_categorie'], 0))}
          <div><div style="color:#64748B;font-size:13px">{e(a['nom_categorie'])}</div>
          <div class="titre" style="font-size:24px;color:{MARINE}">{prix(a['prix_ttc'])}</div></div></div>
          <div style="font-size:15px;color:#334155;margin:10px 0 4px">{e(a['description'] or '')}</div>""", unsafe_allow_html=True)
        if not ouvert:
            st.caption(L["essentiel"] if not peut_commander else L["ferme"])
            return
        choix = OPTIONS.get(a["nom_categorie"], [])
        opts = []
        if choix:
            opts = st.pills(L["options"], choix, selection_mode="multi", default=etat.options.get(aid, []),
                            format_func=lambda o: OPTIONS_AR.get(o, o) if etat.get("langue", "fr") == "ar" else o, key=f"opt_{aid}")
        deja = etat.panier.get(aid, 0)
        q = st.number_input(L["qte"], min_value=1, max_value=20, step=1, value=deja or 1, key=f"qf_{aid}")
        if st.button(f"{L['maj'] if deja else L['ajouter']} · \u2066{prix(q * a['prix_ttc'])}\u2069", type="primary", width="stretch",
                     icon=":material/add_shopping_cart:"):
            if q != deja:
                db.journaliser(etat.session_id, etab, "ajout_panier" if q > deja else "retrait_panier", aid, abs(q - deja))
            etat.panier[aid] = q
            etat.options[aid] = list(opts)
            fermer_fiche()
            sauver()
            st.rerun()
        if deja and st.button(L["retirer_panier"], type="tertiary", width="stretch"):
            db.journaliser(etat.session_id, etab, "retrait_panier", aid, deja)
            etat.panier.pop(aid, None)
            etat.options.pop(aid, None)
            fermer_fiche()
            sauver()
            st.rerun()
    contenu()


if etat.get("fiche") in noms and etat.vue == "menu":
    fiche(noms[etat.fiche])
