# -*- coding: utf-8 -*-
"""MenuScan TN - phase 3 : contrôle des volumes de la couche brute et rapport d'ingestion.

Deux contrôles, à relancer après chaque ingestion :

1. Volumes (bloquant). Pour chaque fichier de donnees_brutes/, le nombre d'enregistrements est recompté avec un autre
   lecteur que celui de l'ingestion (pandas pour les CSV, comptage des lignes pour les JSON), puis comparé au journal
   (lignes lues, écrites, rejetées), aux lignes présentes dans la table raw et aux lignes de raw.rejets. L'empreinte
   SHA-256 du fichier doit être celle du dernier chargement réussi. Tout écart fait échouer le script (code 1).

2. Rapprochement avec la couche de référence (informatif). Si donnees_reference/ est présent, chaque table raw est
   comparée à sa table de référence par identifiant : lignes, identifiants distincts, identifiants absents de part et
   d'autre, lignes en double. Les écarts attendus (doublons d'ingestion, données en retard) sont traités en phase 4.

Le rapport est écrit dans 04_ingestion/rapport_ingestion.md.

Usage, depuis la racine du dépôt, environnement Python activé, Docker lancé :
    python 04_ingestion/controler.py
"""
import argparse
import csv
import gzip
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingerer import RACINE, SOURCES, connexion, empreinte, nom_base  # noqa: E402

SEPARATEURS = {"csv": ",", "csv_fr": ";"}

# Table raw -> (fichier ou dossier de référence, identifiant dans la référence, expression SQL de l'identifiant dans raw)
REFERENCE = {
    "backoffice_abonnements": ("abonnements.csv", "abonnement_id", "abonnement_id"),
    "backoffice_etablissements": ("etablissements.csv", "etablissement_id", "etablissement_id"),
    "backoffice_formules": ("formules.csv", "formule_id", "formule_id"),
    "backoffice_tables_salle": ("tables_salle.csv", "table_id", "table_id"),
    "crm_prospects": ("prospects.csv", "prospect_id", "prospect_id"),
    "facturation_factures": ("factures.csv", "facture_id", "facture_id"),
    "marketing_campagnes": ("campagnes_marketing.csv", "campagne_id", "campagne_id"),
    "marketing_depenses_quotidiennes": ("marketing_depenses_quotidiennes.csv", "depense_id", "depense_id"),
    "menus_articles": ("articles.csv", "article_id", "article_id"),
    "menus_articles_prix_historique": ("articles_prix_historique.csv", "prix_id", "prix_id"),
    "menus_categories": ("categories_menu.csv", "categorie_id", "categorie_id"),
    "paiements_api_paiements": ("paiements.csv", "paiement_id", "donnees->>'payment_id'"),
    "referentiels_calendrier": ("dim_calendrier.csv", "date", "date"),
    "referentiels_canaux_acquisition": ("canaux_acquisition.csv", "canal_id", "canal_id"),
    "referentiels_villes": ("ref_villes.csv", "ville_id", "ville_id"),
    "support_tickets": ("tickets_support.csv", "ticket_id", "ticket_id"),
    "tracking_events": ("evenements", "evenement_id", "donnees->>'event_id'"),
    "ventes_commandes": ("commandes.csv", "commande_id", "commande_id"),
    "ventes_lignes_commande": ("lignes_commande.csv", "ligne_id", "ligne_id"),
}


def nb(n):
    return "–" if n is None else f"{n:,}".replace(",", " ")


def compter_fichier(chemin, fmt):
    """Recompte les enregistrements d'un fichier sans passer par les chargeurs de l'ingestion."""
    if fmt in SEPARATEURS:
        mauvaises = []
        df = pd.read_csv(chemin, sep=SEPARATEURS[fmt], dtype=str, keep_default_na=False, engine="python",
                         skip_blank_lines=True, on_bad_lines=lambda ligne: mauvaises.append(ligne))
        return len(df) + len(mauvaises)
    ouvrir = gzip.open if fmt == "json_gz" else open
    with ouvrir(chemin, "rb") as f:
        return sum(1 for ligne in f if ligne.strip())


def lister_fichiers(source):
    fichiers = []
    for motif, table, fmt in SOURCES:
        fichiers += [(str(p.relative_to(source)).replace("\\", "/"), table, fmt) for p in sorted(source.glob(motif))]
    return fichiers


def controler_volumes(cur, source):
    cur.execute("""SELECT DISTINCT ON (fichier) fichier, empreinte_sha256, lignes_lues, lignes_ecrites, lignes_rejetees
                   FROM raw.chargements WHERE statut IN ('charge', 'recharge') ORDER BY fichier, chargement_id DESC""")
    journal = {r[0]: r[1:] for r in cur.fetchall()}
    cur.execute("SELECT fichier, count(*) FROM raw.rejets GROUP BY fichier")
    rejets = dict(cur.fetchall())
    en_base = {}
    for table in sorted({t for _, t, _ in SOURCES}):
        cur.execute("SELECT to_regclass(%s)", (f"raw.{table}",))
        if cur.fetchone()[0]:
            cur.execute(f'SELECT _fichier, count(*) FROM raw."{table}" GROUP BY _fichier')
            en_base.update({(table, f): n for f, n in cur.fetchall()})

    lignes, vus = [], set()
    for rel, table, fmt in lister_fichiers(source):
        vus.add((table, rel))
        n_fichier = compter_fichier(source / rel, fmt)
        j = journal.get(rel)
        n_base, n_rej = en_base.get((table, rel), 0), rejets.get(rel, 0)
        ecarts = []
        if j is None:
            ecarts.append("jamais chargé")
            lues = ecrites = rejetees = None
        else:
            sha, lues, ecrites, rejetees = j
            if sha != empreinte(source / rel):
                ecarts.append("fichier modifié depuis le chargement")
            if n_fichier != lues:
                ecarts.append(f"fichier {n_fichier} ≠ lues {lues}")
            if lues != ecrites + rejetees:
                ecarts.append(f"lues {lues} ≠ écrites {ecrites} + rejetées {rejetees}")
            if ecrites != n_base:
                ecarts.append(f"écrites {ecrites} ≠ en base {n_base}")
            if rejetees != n_rej:
                ecarts.append(f"rejetées {rejetees} ≠ rejets en base {n_rej}")
        lignes.append(dict(fichier=rel, table=table, n_fichier=n_fichier, lues=lues, ecrites=ecrites, rejetees=rejetees,
                           n_base=n_base, n_rejets=n_rej, ecarts=ecarts))
    # Lignes en base dont le fichier n'existe plus dans donnees_brutes/
    for (table, rel), n in sorted(en_base.items()):
        if (table, rel) not in vus:
            lignes.append(dict(fichier=rel, table=table, n_fichier=0, lues=None, ecrites=None, rejetees=None, n_base=n,
                               n_rejets=rejets.get(rel, 0), ecarts=["fichier absent de donnees_brutes/"]))
    return lignes


def rapprocher(cur, reference):
    resultats = []
    for table, (ref, cle, expr) in REFERENCE.items():
        chemin = reference / ref
        fichiers = sorted(chemin.glob("*.csv")) if chemin.is_dir() else [chemin]
        if not all(f.exists() for f in fichiers) or not fichiers:
            continue
        cles_ref = set()
        for f in fichiers:
            cles_ref.update(pd.read_csv(f, usecols=[cle], dtype=str, keep_default_na=False)[cle])
        cur.execute(f'SELECT {expr} FROM raw."{table}"')
        cles_brut = [r[0] for r in cur.fetchall()]
        distinctes = set(cles_brut)
        resultats.append(dict(table=table, reference=ref, lignes_brut=len(cles_brut), lignes_ref=len(cles_ref),
                              distinctes=len(distinctes), doubles=len(cles_brut) - len(distinctes),
                              absentes=len(cles_ref - distinctes), en_plus=len(distinctes - cles_ref),
                              exemples_absentes=sorted(cles_ref - distinctes)[:5]))
    return resultats


def historique(cur):
    cur.execute("""SELECT lot_id, min(debut), count(*) FILTER (WHERE statut = 'charge'), count(*) FILTER (WHERE statut = 'recharge'),
                          count(*) FILTER (WHERE statut = 'deja_charge'), count(*) FILTER (WHERE statut = 'echec'),
                          coalesce(sum(lignes_ecrites), 0), sum(duree_s)
                   FROM raw.chargements GROUP BY lot_id ORDER BY lot_id""")
    return cur.fetchall()


def ecrire_rapport(chemin, source, volumes, rapprochement, lots, duree):
    ok = [l for l in volumes if not l["ecarts"]]
    ko = [l for l in volumes if l["ecarts"]]
    tables = {}
    for l in volumes:
        t = tables.setdefault(l["table"], dict(fichiers=0, n_fichier=0, lues=0, ecrites=0, n_base=0, rejets=0, ecarts=0))
        t["fichiers"] += 1
        t["n_fichier"] += l["n_fichier"]
        t["lues"] += l["lues"] or 0
        t["ecrites"] += l["ecrites"] or 0
        t["n_base"] += l["n_base"]
        t["rejets"] += l["n_rejets"]
        t["ecarts"] += bool(l["ecarts"])
    tot = {k: sum(t[k] for t in tables.values()) for k in ("fichiers", "n_fichier", "lues", "ecrites", "n_base", "rejets", "ecarts")}
    verdict = "CONFORME" if not ko else f"ÉCART ({len(ko)} fichier(s))"

    r = [f"# Rapport d'ingestion de la couche brute",
         "",
         f"**Généré le :** {datetime.now():%d/%m/%Y à %H:%M} par `04_ingestion/controler.py` · **Durée :** {duree:.0f} s",
         "",
         f"**Source :** `{source.relative_to(RACINE) if source.is_relative_to(RACINE) else source}` · **Base :** `{nom_base()}`, schéma `raw`",
         "",
         "## 1. Synthèse",
         "",
         "| Indicateur | Valeur |",
         "|---|---|",
         f"| Fichiers contrôlés | {nb(len(volumes))} |",
         f"| Fichiers conformes | {nb(len(ok))} |",
         f"| Fichiers en écart | {nb(len(ko))} |",
         f"| Enregistrements comptés dans les fichiers | {nb(tot['n_fichier'])} |",
         f"| Lignes écrites selon le journal | {nb(tot['ecrites'])} |",
         f"| Lignes présentes dans raw | {nb(tot['n_base'])} |",
         f"| Lignes rejetées (raw.rejets) | {nb(tot['rejets'])} |",
         f"| **Contrôle des volumes** | **{verdict}** |",
         "",
         "Un fichier est conforme si son empreinte est celle du dernier chargement réussi et si ces nombres sont égaux : "
         "enregistrements recomptés dans le fichier = lignes lues = lignes écrites + lignes rejetées ; lignes écrites = lignes en base ; "
         "lignes rejetées = lignes de raw.rejets.",
         "",
         "## 2. Volumes par table",
         "",
         "| Table raw | Fichiers | Dans les fichiers | Lues | Écrites | En base | Rejets | Fichiers en écart |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for table, t in sorted(tables.items()):
        r.append(f"| `raw.{table}` | {t['fichiers']} | {nb(t['n_fichier'])} | {nb(t['lues'])} | {nb(t['ecrites'])} | {nb(t['n_base'])} | "
                 f"{nb(t['rejets'])} | {t['ecarts']} |")
    r.append(f"| **Total** | **{tot['fichiers']}** | **{nb(tot['n_fichier'])}** | **{nb(tot['lues'])}** | **{nb(tot['ecrites'])}** | "
             f"**{nb(tot['n_base'])}** | **{nb(tot['rejets'])}** | **{tot['ecarts']}** |")
    r += ["", "## 3. Fichiers en écart", ""]
    if ko:
        r += ["| Fichier | Écart |", "|---|---|"] + [f"| `{l['fichier']}` | {' ; '.join(l['ecarts'])} |" for l in ko]
    else:
        r.append("Aucun.")

    r += ["", "## 4. Rapprochement avec la couche de référence", ""]
    if rapprochement:
        r += ["Contrôle informatif : la couche brute contient volontairement des anomalies. Ces écarts ne sont pas des erreurs "
              "d'ingestion ; ils seront traités en phase 4 (staging et quarantaine).",
              "",
              "| Table raw | Lignes brut | Lignes référence | Identifiants distincts (brut) | Lignes en double | Absents du brut | Absents de la référence |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for x in rapprochement:
            r.append(f"| `raw.{x['table']}` | {nb(x['lignes_brut'])} | {nb(x['lignes_ref'])} | {nb(x['distinctes'])} | {nb(x['doubles'])} | "
                     f"{nb(x['absentes'])} | {nb(x['en_plus'])} |")
        r += ["", "- **Lignes en double :** lignes dont l'identifiant figure déjà dans la table (doublons d'ingestion).",
              "- **Absents du brut :** identifiants de la référence qu'aucun fichier ne contient."
              + "".join(f" Exemples pour `{x['table']}` : {', '.join(x['exemples_absentes'])}." for x in rapprochement if x["absentes"]),
              "- **Absents de la référence :** identifiants présents dans le brut seulement (par exemple un établissement saisi deux fois sous deux identifiants).",
              "- La table `sessions` de la référence n'a pas de source brute : elle sera reconstruite en phase 4 à partir des événements."]
    else:
        r.append("Dossier `donnees_reference/` absent : rapprochement non fait.")

    r += ["", "## 5. Historique des lancements de l'ingestion", "",
          "| Lot | Début | Chargés | Rechargés | Inchangés | En échec | Lignes écrites | Durée cumulée (s) |",
          "|---:|---|---:|---:|---:|---:|---:|---:|"]
    for lot, debut, c, rc, dc, e, lw, d in lots:
        r.append(f"| {lot} | {debut.astimezone():%d/%m/%Y %H:%M} | {c} | {rc} | {dc} | {e} | {nb(lw)} | {float(d or 0):.1f} |")
    r.append("")
    chemin.write_text("\n".join(r), encoding="utf-8")
    return verdict, ko, tot


def main():
    ap = argparse.ArgumentParser(description="Contrôle des volumes de la couche brute MenuScan TN")
    ap.add_argument("--source", default="menuscan_dataset/donnees_brutes", help="dossier donnees_brutes du jeu complet")
    ap.add_argument("--reference", default="menuscan_dataset/donnees_reference", help="dossier donnees_reference (facultatif)")
    ap.add_argument("--rapport", default="04_ingestion/rapport_ingestion.md", help="fichier du rapport")
    a = ap.parse_args()
    source = Path(a.source) if Path(a.source).is_absolute() else RACINE / a.source
    reference = Path(a.reference) if Path(a.reference).is_absolute() else RACINE / a.reference
    if not source.is_dir():
        sys.exit(f"Dossier introuvable : {source}")
    t0 = time.perf_counter()
    conn = connexion()
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('raw.chargements')")
        if not cur.fetchone()[0]:
            sys.exit("Le schéma raw n'existe pas : lancer d'abord python 04_ingestion/ingerer.py")
        print("Contrôle des volumes fichier par fichier...")
        volumes = controler_volumes(cur, source)
        rapprochement = []
        if reference.is_dir():
            print("Rapprochement avec la couche de référence...")
            rapprochement = rapprocher(cur, reference)
        lots = historique(cur)
    conn.close()
    rapport = RACINE / a.rapport
    verdict, ko, tot = ecrire_rapport(rapport, source, volumes, rapprochement, lots, time.perf_counter() - t0)
    print(f"\n{len(volumes)} fichiers contrôlés, {nb(tot['n_fichier'])} enregistrements, {nb(tot['n_base'])} lignes dans raw, "
          f"{nb(tot['rejets'])} rejets.")
    for l in ko:
        print(f"  ÉCART {l['fichier']} : {' ; '.join(l['ecarts'])}")
    print(f"Contrôle des volumes : {verdict}. Rapport : {rapport.relative_to(RACINE) if rapport.is_relative_to(RACINE) else rapport}")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
