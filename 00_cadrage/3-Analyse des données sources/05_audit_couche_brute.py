# -*- coding: utf-8 -*-
# Usage : python 05_audit_couche_brute.py <dossier donnees_brutes> <fichier de sortie audit.json>
"""Audit indépendant de la couche brute MenuScan TN (aucune lecture de solutions/)."""
import glob, gzip, json, os, sys
import pandas as pd, numpy as np

B = sys.argv[1]  # dossier donnees_brutes
R = []


def chk(fichier, table, colonne, anomalie, regle, dimension, gravite, serie_ou_nb, methode, impact, action, cle, exemple=None):
    nb = int(serie_ou_nb.sum()) if hasattr(serie_ou_nb, "sum") and not isinstance(serie_ou_nb, (int, np.integer)) else int(serie_ou_nb)
    R.append(dict(fichier=fichier, table=table, colonne=colonne, anomalie=anomalie, regle=regle, dimension=dimension, gravite=gravite,
                  detecte=nb, methode=methode, impact=impact, action=action, cle=cle, exemple=None if exemple is None else str(exemple)[:80]))


def ex(df, mask, col):
    s = df.loc[mask, col] if hasattr(mask, "__len__") else df[col]
    return s.iloc[0] if len(s) else None


norm = lambda s: s.fillna("").str.strip().str.replace(r"\s+", " ", regex=True)
pas_norm = lambda s: (s.fillna("") != norm(s)) | s.fillna("").str.isupper() | s.fillna("").str.islower()
TEL = r"\+216\d{8}"
EMAIL = r"[^@\s]+@[^@\s]+\.[a-z]{2,}"

# --- back-office
e = pd.read_csv(f"{B}/backoffice/etablissements.csv", dtype=str)
m = ~e.telephone.str.fullmatch(TEL)
chk("backoffice/etablissements.csv", "etablissements", "telephone", "Téléphone hors format +216XXXXXXXX", "DQ-31", "Format", "Mineure", m,
    "Expression régulière ^\\+216\\d{8}$", "Relances SMS et WhatsApp impossibles ; doublons non détectés", "Normaliser : garder les 8 derniers chiffres, préfixer +216",
    ("etablissements", "format_telephone_non_normalise"), ex(e, m, "telephone"))
m = e.email.notna() & ~e.email.fillna("").str.fullmatch(EMAIL)
chk("backoffice/etablissements.csv", "etablissements", "email", "Email invalide", "DQ-31", "Format", "Mineure", m,
    "Expression régulière d'adresse email", "Factures et relances non envoyées", "Supprimer les espaces, signaler les adresses sans @",
    ("etablissements", "email_invalide"), ex(e, m, "email"))
m = e.nb_tables.isna()
chk("backoffice/etablissements.csv", "etablissements", "nb_tables", "Nombre de tables vide", "DQ-38", "Complétude", "Majeure", m,
    "Valeur nulle sur un champ obligatoire", "Usage par table impossible à calculer", "Recalculer depuis tables_salle",
    ("etablissements", "champ_obligatoire_vide"), None)
m = pas_norm(e.nom_etablissement)
chk("backoffice/etablissements.csv", "etablissements", "nom_etablissement", "Nom non normalisé (casse, espaces)", "DQ-32", "Normalisation", "Mineure", m,
    "Espaces en trop, ou nom entièrement en majuscules ou en minuscules", "Doublons non reconnus, affichage incohérent", "Supprimer les espaces, rétablir la casse d'origine",
    ("etablissements", "libelle_non_normalise"), ex(e, m, "nom_etablissement"))
k = norm(e.nom_etablissement).str.lower() + "|" + e.telephone.str.replace(r"\D", "", regex=True).str[-8:]
m = k.duplicated()
chk("backoffice/etablissements.csv", "etablissements", "etablissement_id", "Doublon métier d'établissement (même nom, même téléphone)", "DQ-30", "Unicité", "Majeure", m,
    "Clé nom normalisé + 8 derniers chiffres du téléphone", "Parc surévalué, historique coupé en deux", "Fusionner et tracer ancien → nouvel identifiant",
    ("etablissements", "doublon_metier_etablissement"), ex(e, m, "etablissement_id"))
a = pd.read_csv(f"{B}/backoffice/abonnements.csv", dtype=str)
m = ~a.periodicite.isin(["mensuelle", "annuelle"])
chk("backoffice/abonnements.csv", "abonnements", "periodicite", "Périodicité non normalisée", "DQ-32", "Normalisation", "Mineure", m,
    "Valeur hors liste {mensuelle, annuelle}", "MRR des abonnés annuels faux", "Table de correspondance (Mensuel, mois → mensuelle ; an → annuelle)",
    ("abonnements", "libelle_non_normalise"), ex(a, m, "periodicite"))

# --- menus
ar = pd.read_csv(f"{B}/menus/articles.csv", dtype=str)
m = ar.duplicated()
chk("menus/articles.csv", "articles", "*", "Ligne en double", "DQ-29", "Unicité", "Bloquante", m,
    "Ligne entièrement identique à une précédente", "Articles comptés deux fois", "Dédoublonner",
    ("articles", "doublon_ingestion"), ex(ar, m, "article_id"))
m = pas_norm(ar.nom_article)
chk("menus/articles.csv", "articles", "nom_article", "Libellé non normalisé (casse, espaces)", "DQ-32", "Normalisation", "Mineure", m,
    "Espaces en trop, ou libellé entièrement en majuscules ou en minuscules", "Un même plat éclaté en plusieurs libellés", "Normaliser les espaces et la casse",
    ("articles", "libelle_non_normalise"), ex(ar, m, "nom_article"))
px = pd.read_csv(f"{B}/menus/articles_prix_historique.csv")
m = px.prix_ttc > 200
chk("menus/articles_prix_historique.csv", "articles_prix_historique", "prix_ttc", "Prix en millimes (supérieur à 200 DT)", "DQ-33", "Exactitude", "Bloquante", m,
    "Prix supérieur à 200 DT, impossible pour un menu", "Prix moyens et chiffre d'affaires faussés", "Diviser par 1 000",
    ("articles_prix_historique", "montant_en_millimes"), ex(px, m, "prix_ttc"))

# --- ventes
files = sorted(glob.glob(f"{B}/ventes/commandes/*.csv"))
c = pd.concat([pd.read_csv(f, dtype=str).assign(_f=os.path.basename(f)) for f in files], ignore_index=True)
m = c.drop(columns="_f").duplicated()
chk("ventes/commandes/*.csv", "commandes", "*", "Commande en double (ré-extraction)", "DQ-29", "Unicité", "Bloquante", m,
    "Ligne identique déjà vue, dans le même fichier ou un autre", "Commandes et chiffre d'affaires comptés deux fois", "Dédoublonner sur commande_id",
    ("commandes", "doublon_ingestion"), ex(c, m, "commande_id"))
iso = c.date_heure_commande.str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
chk("ventes/commandes/*.csv", "commandes", "date_heure_commande", "Date au format JJ/MM/AAAA HH:MM", "DQ-28", "Format", "Mineure", ~iso,
    "Date non conforme au format ISO", "Dates rejetées ou mal lues (jour et mois inversés)", "Convertir avec le format JJ/MM/AAAA HH:MM",
    ("commandes", "format_date_non_iso"), ex(c, ~iso, "date_heure_commande"))
d = pd.Series(pd.NaT, index=c.index)
d[iso] = pd.to_datetime(c.date_heure_commande[iso]); d[~iso] = pd.to_datetime(c.date_heure_commande[~iso], format="%d/%m/%Y %H:%M")
fm = c._f.str.extract(r"(\d{4})_(\d{2})").agg("-".join, axis=1)
m = (d.dt.strftime("%Y-%m") != fm) & ~c.drop(columns="_f").duplicated()
chk("ventes/commandes/*.csv", "commandes", "date_heure_commande", "Commande livrée dans le fichier du mois suivant", "DQ-35", "Fraîcheur", "Majeure", m,
    "Mois de la commande différent du mois du fichier (premières occurrences seulement)", "Activité affectée au mauvais mois", "Rattacher à la date métier",
    ("commandes", "arrivee_tardive"), ex(c, m, "commande_id"))
ok = ["servie", "annulee"]
m = ~c.statut_commande.isin(ok)
chk("ventes/commandes/*.csv", "commandes", "statut_commande", "Statut non normalisé", "DQ-32", "Normalisation", "Mineure", m,
    "Valeur hors liste {servie, annulee}", "Commandes servies sous-comptées", "Correspondance (SERVIE, Servie, served → servie ; Annulée, ANNULEE, cancelled → annulee)",
    ("commandes", "libelle_non_normalise"), ex(c, m, "statut_commande"))
st = c.statut_commande.str.lower().str.replace("é", "e")
m = c.mode_reglement.isna() & st.isin(["servie", "served"])
chk("ventes/commandes/*.csv", "commandes", "mode_reglement", "Mode de règlement vide sur une commande servie", "DQ-38", "Complétude", "Majeure", m,
    "Champ vide alors que la commande est servie", "Répartition des règlements faussée", "Mettre « inconnu » et isoler",
    ("commandes", "champ_obligatoire_vide"), ex(c, m, "commande_id"))
fl = sorted(glob.glob(f"{B}/ventes/lignes_commande/*.csv"))
l = pd.concat([pd.read_csv(f, dtype=str) for f in fl], ignore_index=True)
l["q"] = pd.to_numeric(l.quantite); l["pu"] = pd.to_numeric(l.prix_unitaire_ttc); l["mt"] = pd.to_numeric(l.montant_ligne_ttc)
lu = l.drop_duplicates("ligne_id")
s = lu.groupby("commande_id").mt.sum()
cu = c.drop_duplicates("commande_id").set_index("commande_id")
m = (pd.to_numeric(cu.montant_total_ttc) - s.reindex(cu.index)).abs() > 0.002
chk("ventes/commandes/*.csv", "commandes", "montant_total_ttc", "Montant différent de la somme des lignes", "DQ-03", "Exactitude", "Majeure", m,
    "Écart supérieur à 0,002 DT entre le total et la somme des lignes brutes", "Chiffre d'affaires incohérent selon la table utilisée", "Recalculer le total depuis les lignes corrigées",
    ("commandes", "montant_incoherent"), m[m].index[0] if m.any() else None)
m = l.drop(columns=["q", "pu", "mt"]).duplicated()
chk("ventes/lignes_commande/*.csv", "lignes_commande", "*", "Ligne de commande en double", "DQ-29", "Unicité", "Bloquante", m,
    "Ligne identique déjà vue", "Quantités et montants comptés deux fois", "Dédoublonner sur ligne_id",
    ("lignes_commande", "doublon_ingestion"), ex(l, m, "ligne_id"))
first = ~l.ligne_id.duplicated()
m = (l.q <= 0) & first
chk("ventes/lignes_commande/*.csv", "lignes_commande", "quantite", "Quantité nulle ou négative", "DQ-05", "Validité", "Bloquante", m,
    "Quantité inférieure ou égale à 0 (premières occurrences)", "Ventes sous-estimées, montants négatifs", "Quarantaine",
    ("lignes_commande", "quantite_non_positive"), ex(l, m, "quantite"))
m = (l.pu > 200) & first
chk("ventes/lignes_commande/*.csv", "lignes_commande", "prix_unitaire_ttc", "Prix unitaire en millimes", "DQ-33", "Exactitude", "Bloquante", m,
    "Prix unitaire supérieur à 200 DT (premières occurrences)", "Chiffre d'affaires gonflé", "Diviser par 1 000 et recalculer le montant",
    ("lignes_commande", "montant_en_millimes"), ex(l, m, "prix_unitaire_ttc"))
arts = set(ar.article_id)
m = ~l.article_id.isin(arts) & first
chk("ventes/lignes_commande/*.csv", "lignes_commande", "article_id", "Article inconnu du menu", "DQ-02", "Intégrité", "Bloquante", m,
    "article_id absent de menus/articles.csv", "Lignes perdues dans les jointures", "Quarantaine",
    ("lignes_commande", "cle_etrangere_orpheline"), ex(l, m, "article_id"))

# --- tracking
rows = []
for f in sorted(glob.glob(f"{B}/tracking/*.jsonl.gz")):
    fmn = os.path.basename(f)[7:14].replace("_", "-")
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            rows.append((r["event_id"], r["event_type"], r["ts"], r["session_token"], r["item_id"], fmn))
ev = pd.DataFrame(rows, columns=["event_id", "event_type", "ts", "session", "item_id", "fichier_mois"])
dupe = ev.duplicated(["event_id", "event_type", "ts", "session", "item_id"])
chk("tracking/events_*.jsonl.gz", "evenements", "*", "Événement en double (renvoi du SDK)", "DQ-29", "Unicité", "Bloquante", dupe,
    "event_id déjà vu avec le même contenu", "Sessions, vues et paniers surévalués", "Dédoublonner sur event_id",
    ("evenements", "doublon_ingestion"), ex(ev, dupe, "event_id"))
chk("tracking/events_*.jsonl.gz", "evenements", "ts", "Horodatage en UTC", "DQ-34", "Format", "Information", ev.ts.str.endswith("Z"),
    "Suffixe Z sur tous les horodatages", "Heures de pointe décalées d'une heure", "Ajouter 1 heure (heure de Tunis, sans heure d'été)",
    None, ex(ev, ev.ts.str.endswith("Z"), "ts"))
evu = ev[~dupe]
m = evu.ts.str[:7] != evu.fichier_mois
chk("tracking/events_*.jsonl.gz", "evenements", "ts", "Événement livré dans le fichier du mois suivant", "DQ-35", "Fraîcheur", "Majeure", m,
    "Mois UTC de l'événement différent du mois du fichier (hors doublons)", "Événements affectés au mauvais mois", "Rattacher à la date de l'événement",
    ("evenements", "arrivee_tardive"), ex(evu, m, "event_id"))
m = evu.item_id.notna() & ~evu.item_id.isin(arts)
chk("tracking/events_*.jsonl.gz", "evenements", "item_id", "Article inconnu du menu", "DQ-02", "Intégrité", "Bloquante", m,
    "item_id absent de menus/articles.csv (hors doublons)", "Vues d'articles perdues", "Quarantaine",
    ("evenements", "cle_etrangere_orpheline"), ex(evu, m, "item_id"))
scan = evu[evu.event_type == "qr_scan"].groupby("session").ts.min()
m = (evu.event_type != "qr_scan") & (evu.ts < evu.session.map(scan))
chk("tracking/events_*.jsonl.gz", "evenements", "ts", "Événement daté avant le scan de sa session", "DQ-37", "Exactitude", "Mineure", m,
    "Horodatage antérieur au qr_scan de la session (hors doublons)", "Sessions mal reconstituées, durées fausses", "Ramener l'horodatage au scan et signaler",
    ("evenements", "horloge_appareil_decalee"), ex(evu, m, "event_id"))

# --- paiements, facturation
pay = pd.json_normalize([json.loads(x) for x in open(f"{B}/paiements_api/paiements.jsonl", encoding="utf-8")])
fa = pd.read_csv(f"{B}/facturation/factures.csv", sep=";", decimal=",", dtype={"facture_id": str})
m = pay.duplicated()
chk("paiements_api/paiements.jsonl", "paiements", "*", "Paiement en double (webhook renvoyé)", "DQ-29", "Unicité", "Bloquante", m,
    "Enregistrement identique déjà reçu", "Encaissements comptés deux fois", "Dédoublonner sur payment_id",
    ("paiements", "doublon_ingestion"), ex(pay, m, "payment_id"))
ttc = fa.drop_duplicates("facture_id").set_index("facture_id").montant_ttc
m = (pay["amount.value"] > pay.invoice_ref.map(ttc) * 100) & ~pay.duplicated()
chk("paiements_api/paiements.jsonl", "paiements", "amount.value", "Montant en millimes", "DQ-33", "Exactitude", "Bloquante", m,
    "Montant plus de 100 fois supérieur au TTC de la facture (hors doublons)", "Encaissements gonflés", "Diviser par 1 000",
    ("paiements", "montant_en_millimes"), ex(pay, m, "amount.value"))
m = fa.duplicated()
chk("facturation/factures.csv", "factures", "*", "Facture en double", "DQ-29", "Unicité", "Bloquante", m,
    "Ligne identique déjà vue", "Chiffre d'affaires facturé doublé", "Dédoublonner sur facture_id",
    ("factures", "doublon_ingestion"), ex(fa, m, "facture_id"))
m = ((fa.montant_ttc - (fa.montant_net_ht + fa.montant_tva).round(3)).abs() > 0.002) & ~fa.duplicated()
chk("facturation/factures.csv", "factures", "montant_ttc", "TTC différent de net HT + TVA", "DQ-15", "Exactitude", "Majeure", m,
    "Recalcul du TTC à 0,002 DT près (hors doublons)", "Montants facturés faux", "Recalculer le TTC",
    ("factures", "montant_incoherent"), ex(fa, m, "facture_id"))
chk("facturation/factures.csv", "factures", "*", "Format français (; et virgule décimale, dates JJ/MM/AAAA)", "DQ-36", "Format", "Information", len(fa),
    "Lecture du fichier", "Montants lus comme du texte si le format est ignoré", "Lire avec sep=';' et decimal=','", None, None)

# --- marketing, CRM, support
mk = pd.read_csv(f"{B}/marketing/depenses_quotidiennes.csv", sep=";", decimal=",")
m = mk.clics > mk.impressions
chk("marketing/depenses_quotidiennes.csv", "marketing_depenses_quotidiennes", "impressions", "Clics supérieurs aux impressions", "DQ-23", "Validité", "Majeure", m,
    "clics > impressions", "Taux de clic supérieur à 100 %", "Quarantaine, contrôle de l'export",
    ("marketing_depenses_quotidiennes", "clics_superieurs_aux_impressions"), ex(mk, m, "depense_id"))
m = mk.depense_ttc < 0
chk("marketing/depenses_quotidiennes.csv", "marketing_depenses_quotidiennes", "depense_ttc", "Dépense négative", "DQ-23", "Validité", "Majeure", m,
    "Dépense inférieure à 0", "Coût d'acquisition sous-estimé", "Prendre la valeur absolue après vérification",
    ("marketing_depenses_quotidiennes", "montant_negatif"), ex(mk, m, "depense_id"))
pr = pd.read_csv(f"{B}/crm/prospects.csv", dtype=str)
m = pr.duplicated()
chk("crm/prospects.csv", "prospects", "*", "Prospect en double", "DQ-29", "Unicité", "Bloquante", m,
    "Ligne identique déjà vue", "Taux de conversion faussé", "Dédoublonner sur prospect_id",
    ("prospects", "doublon_ingestion"), ex(pr, m, "prospect_id"))
m = ~pr.telephone.str.fullmatch(TEL) & ~pr.duplicated()
chk("crm/prospects.csv", "prospects", "telephone", "Téléphone hors format", "DQ-31", "Format", "Mineure", m,
    "Expression régulière ^\\+216\\d{8}$ (hors doublons)", "Rapprochement prospect / établissement difficile", "Normaliser",
    ("prospects", "format_telephone_non_normalise"), ex(pr, m, "telephone"))
m = pas_norm(pr.nom_etablissement) & ~pr.duplicated()
chk("crm/prospects.csv", "prospects", "nom_etablissement", "Nom non normalisé", "DQ-32", "Normalisation", "Mineure", m,
    "Espaces en trop, ou nom entièrement en majuscules ou en minuscules (hors doublons)", "Rapprochement difficile", "Normaliser",
    ("prospects", "libelle_non_normalise"), ex(pr, m, "nom_etablissement"))
tk = pd.read_csv(f"{B}/support/tickets_support.csv", dtype=str)
m = ~tk.statut_ticket.isin(["resolu", "ouvert"])
chk("support/tickets_support.csv", "tickets_support", "statut_ticket", "Statut non normalisé", "DQ-32", "Normalisation", "Mineure", m,
    "Valeur hors liste {resolu, ouvert}", "Tickets résolus sous-comptés", "Correspondance (Résolu, RESOLU, closed, fermé → resolu ; Open → ouvert)",
    ("tickets_support", "libelle_non_normalise"), ex(tk, m, "statut_ticket"))
m = tk.categorie.isna()
chk("support/tickets_support.csv", "tickets_support", "categorie", "Catégorie vide", "DQ-38", "Complétude", "Majeure", m,
    "Champ vide", "Tickets non classés", "Classer « non renseignée »",
    ("tickets_support", "champ_obligatoire_vide"), None)

json.dump(R, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
for r in R:
    print(f"{r['regle']:6} {r['table']:32} {r['anomalie'][:55]:55} {r['detecte']}")
