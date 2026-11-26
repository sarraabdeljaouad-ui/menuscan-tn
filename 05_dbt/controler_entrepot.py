# -*- coding: utf-8 -*-
"""MenuScan TN - phase 4 (T4.4) : contrôle de l'entrepôt après « dbt build ».

1. Anomalies retrouvées (jalon J5). Si le corrigé solutions/anomalies_injectees.csv est présent (il n'est pas publié,
   décision D-16), chaque anomalie injectée est cherchée dans qualite.corrections (valeur corrigée) et
   qualite.quarantaine (ligne écartée). Critère J5 : au moins 95 %.
2. Comparaison avec la couche de référence (donnees_reference/, publiée). Chaque table de référence est comparée,
   valeur par valeur, au modèle final de l'entrepôt qui lui correspond.

Le rapport est écrit dans 05_dbt/rapport_validation.md.

Usage, depuis la racine du dépôt, après python 05_dbt/lancer_dbt.py build :
    python 05_dbt/controler_entrepot.py
"""
import glob
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent
JEU = RACINE / "menuscan_dataset"
CORRIGE = JEU / "solutions" / "anomalies_injectees.csv"
REFERENCE = JEU / "donnees_reference"

# Table de référence -> (modèle de l'entrepôt, identifiant)
CORRESPONDANCE = {
    "dim_calendrier": ("staging.stg_dim_calendrier", "date"),
    "ref_villes": ("marts.dim_ville", "ville_id"),
    "formules": ("marts.dim_formule", "formule_id"),
    "canaux_acquisition": ("marts.dim_canal", "canal_id"),
    "campagnes_marketing": ("staging.stg_campagnes_marketing", "campagne_id"),
    "marketing_depenses_quotidiennes": ("marts.fait_marketing", "depense_id"),
    "prospects": ("marts.fait_prospect", "prospect_id"),
    "etablissements": ("marts.dim_etablissement", "etablissement_id"),
    "abonnements": ("staging.stg_abonnements", "abonnement_id"),
    "factures": ("marts.fait_facturation", "facture_id"),
    "paiements": ("staging.stg_paiements", "paiement_id"),
    "tickets_support": ("marts.fait_ticket_support", "ticket_id"),
    "categories_menu": ("marts.dim_categorie", "categorie_id"),
    "articles": ("staging.stg_articles", "article_id"),
    "articles_prix_historique": ("staging.stg_articles_prix_historique", "prix_id"),
    "tables_salle": ("marts.dim_table", "table_id"),
    "commandes": ("marts.fait_commande", "commande_id"),
    "lignes_commande": ("marts.fait_ligne_commande", "ligne_id"),
    "sessions": ("marts.fait_session", "session_id"),
    "evenements": ("intermediate.int_evenements", "evenement_id"),
}
HORODATAGES = {"horodatage", "date_paiement", "date_heure_commande", "date_heure_service", "date_ouverture",
               "date_resolution", "debut_session", "fin_session"}


def nb(n):
    return f"{n:,}".replace(",", " ")


def moteur():
    for ligne in (RACINE / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.strip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip())
    e = os.environ
    # URL.create encode le mot de passe : il peut contenir @, !, : ou / sans casser l'adresse
    url = URL.create("postgresql+psycopg2", username=e["POSTGRES_USER"], password=e["POSTGRES_PASSWORD"],
                     host=e.get("POSTGRES_HOST", "127.0.0.1"), port=int(e.get("POSTGRES_PORT", "5440")),
                     database=e.get("MENUSCAN_DWH", "menuscan_dwh"))
    return create_engine(url, connect_args={"connect_timeout": 10})


def mesurer_anomalies(db):
    """Renvoie (tableau par type, nombre retrouvé, total, détail des non retrouvées) ou None sans corrigé."""
    if not CORRIGE.exists():
        return None
    a = pd.read_csv(CORRIGE, dtype=str)
    trace = pd.read_sql("select table_source, identifiant, regle_dq from qualite.corrections "
                        "union select table_source, identifiant, regle_dq from qualite.quarantaine", db)
    isolees = pd.read_sql("select distinct table_source, identifiant from qualite.quarantaine", db)
    par_regle = set(trace.table_source + "|" + trace.identifiant + "|" + trace.regle_dq)
    par_ligne = set(isolees.table_source + "|" + isolees.identifiant)
    # retrouvée si la valeur a été corrigée pour sa règle, ou si la ligne entière a été écartée en quarantaine
    a["retrouvee"] = (a["table"] + "|" + a.identifiant + "|" + a.regle_dq).isin(par_regle) | \
                     (a["table"] + "|" + a.identifiant).isin(par_ligne)
    t = a.groupby(["regle_dq", "type_anomalie", "table"]).agg(injectees=("retrouvee", "size"), retrouvees=("retrouvee", "sum"))
    return t.reset_index(), int(a.retrouvee.sum()), len(a)


def normaliser(serie, horodatage=False):
    s = serie.astype(object).where(serie.notna(), "").astype(str).str.strip()
    s = s.replace({"nan": "", "None": "", "NaT": "", "<NA>": "", "NaN": ""})
    if horodatage:
        return pd.to_datetime(s, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    def f(v):
        if v in ("True", "False", "true", "false"):
            return v.lower()
        try:
            return "%.3f" % float(v) if v and not v[0].isalpha() and ":" not in v and "-" not in v[1:] else v
        except ValueError:
            return v
    return s.map(f)


def comparer_reference(db):
    resultats = []
    for nom, (modele, cle) in CORRESPONDANCE.items():
        chemin = REFERENCE / nom
        fichiers = sorted(glob.glob(str(chemin / "*.csv"))) if chemin.is_dir() else [str(chemin) + ".csv"]
        if not fichiers or not Path(fichiers[0]).exists():
            continue
        ref = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in fichiers])
        entrepot = pd.read_sql(f"select * from {modele}", db)
        entrepot[cle] = entrepot[cle].astype(str)  # les dates du calendrier sont comparées comme texte AAAA-MM-JJ
        communes = [c for c in ref.columns if c in entrepot.columns and c != cle]
        m = ref[[cle] + communes].merge(entrepot[[cle] + communes], on=cle, how="outer", suffixes=("_r", "_e"), indicator=True)
        deux = m[m._merge == "both"]
        ecarts = {}
        for c in communes:
            d = int((normaliser(deux[c + "_r"], c in HORODATAGES) != normaliser(deux[c + "_e"], c in HORODATAGES)).sum())
            if d:
                ecarts[c] = d
        resultats.append(dict(reference=nom, modele=modele, lignes_ref=len(ref), lignes_entrepot=len(entrepot),
                              absentes=int((m._merge == "left_only").sum()), en_plus=int((m._merge == "right_only").sum()),
                              colonnes=len(communes), ecarts=ecarts))
        print(f"  {nom} : {nb(len(ref))} lignes de référence, {nb(len(entrepot))} dans {modele}")
    return resultats


def ecrire(mesure, comparaison, chemin):
    r = ["# Rapport de validation de l'entrepôt", "",
         f"**Généré le :** {datetime.now():%d/%m/%Y à %H:%M} par `05_dbt/controler_entrepot.py`, après `dbt build`.", "",
         "## 1. Anomalies retrouvées (jalon J5)", ""]
    if mesure is None:
        # sans corrigé, la dernière mesure faite (si le rapport existe déjà) est gardée telle quelle
        ancien = chemin.read_text(encoding="utf-8") if chemin.exists() else ""
        debut, fin = ancien.find("## 1."), ancien.find("## 2.")
        if debut >= 0 and fin > debut and "Corrigé `solutions" not in ancien[debut:fin]:
            r = r[:-2] + [ancien[debut:fin].rstrip(), "",
                          "*Corrigé absent de ce poste (non publié, décision D-16) : la mesure ci-dessus est celle du dernier poste qui l'avait.*"]
        else:
            r.append("Corrigé `solutions/anomalies_injectees.csv` absent de ce poste (non publié, décision D-16) : mesure non faite.")
    else:
        t, trouvees, total = mesure
        taux = 100 * trouvees / total
        taux_txt = f"{taux:.2f}".replace(".", ",")
        r += [f"**{nb(trouvees)} anomalies retrouvées sur {nb(total)}, soit {taux_txt} %.** "
              f"Critère du jalon J5 : au moins 95 % ({'atteint' if taux >= 95 else 'NON atteint'}).", "",
              "Une anomalie est retrouvée si sa valeur a été corrigée pour sa règle (`qualite.corrections`) "
              "ou si sa ligne a été écartée (`qualite.quarantaine`).", "",
              "| Règle | Type d'anomalie | Table | Injectées | Retrouvées | Taux |", "|---|---|---|---:|---:|---:|"]
        for x in t.itertuples():
            r.append(f"| {x.regle_dq} | {x.type_anomalie} | {x.table} | {nb(x.injectees)} | {nb(x.retrouvees)} | "
                     f"{100 * x.retrouvees / x.injectees:.1f} % |".replace(".", ","))
    r += ["", "## 2. Comparaison avec la couche de référence", "",
          "Chaque table de `donnees_reference/` est comparée au modèle final qui lui correspond, sur l'identifiant et sur chaque "
          "colonne commune. Un écart est une valeur différente après normalisation des formats (nombres à 3 décimales, dates).", "",
          "| Référence | Modèle de l'entrepôt | Lignes référence | Lignes entrepôt | Absentes de l'entrepôt | En plus | Colonnes comparées | Valeurs différentes |",
          "|---|---|---:|---:|---:|---:|---:|---|"]
    for x in comparaison:
        e = ", ".join(f"{c} : {nb(n)}" for c, n in x["ecarts"].items()) or "aucune"
        r.append(f"| {x['reference']} | `{x['modele']}` | {nb(x['lignes_ref'])} | {nb(x['lignes_entrepot'])} | {nb(x['absentes'])} | "
                 f"{nb(x['en_plus'])} | {x['colonnes']} | {e} |")
    r += ["", "Écarts attendus, expliqués dans `05_dbt/README.md` (§ 7) :",
          "- lignes absentes : lignes en quarantaine (dépenses DQ-23, lignes et événements à identifiant inconnu DQ-02, quantités DQ-05) "
          "et 11 commandes en retard non reçues avec leurs 19 lignes (décision D-32) ;",
          "- valeurs différentes : secondes perdues des dates au format français (DQ-28), modes de règlement et catégories vides "
          "remplacés par « non renseigné » (DQ-38), horloges décalées non détectables ou non exactement corrigeables (DQ-37), "
          "total d'une commande dont une ligne est en quarantaine (DQ-03).", ""]
    chemin.write_text("\n".join(r), encoding="utf-8")


def main():
    db = moteur()
    print("Mesure des anomalies retrouvées...")
    mesure = mesurer_anomalies(db)
    print("  corrigé absent : mesure non faite" if mesure is None else f"  {nb(mesure[1])} / {nb(mesure[2])} retrouvées")
    print("Comparaison avec la couche de référence...")
    comparaison = comparer_reference(db) if REFERENCE.is_dir() else []
    chemin = DOSSIER / "rapport_validation.md"
    ecrire(mesure, comparaison, chemin)
    print(f"Rapport : {chemin.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
