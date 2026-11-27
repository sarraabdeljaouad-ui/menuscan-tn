"""features.py : tables de variables.

panel() : une ligne par établissement actif en fin de mois, avec la cible de résiliation (T7.2, EF-10).
Toutes les variables utilisent des données antérieures ou égales à la fin du mois (pas de fuite).
"""
from __future__ import annotations

import pandas as pd

from . import chargement, temporal_split

# Une ligne par établissement actif en fin de mois m. Cible : résiliation effective le mois suivant (m + 1).
# Toutes les variables sont calculées avec des données antérieures ou égales à la fin du mois m (pas de fuite).
SQL_ETAB_MOIS = """
with m as (
    select debut::date, (debut + interval '1 month - 1 day')::date as fin
    from generate_series('2024-01-01'::date, %(dernier_mois)s::date, interval '1 month') debut
)
select
    e.etablissement_id, m.debut as mois,
    (e.date_resiliation is not null
        and e.date_resiliation between (m.debut + interval '1 month')::date
                                   and (m.debut + interval '2 month - 1 day')::date)::int as resilie_mois_suivant,
    e.type_etablissement, e.region, e.nom_canal, e.type_canal, e.nb_tables, e.periodicite_facturation,
    e.formule_initiale,
    (extract(year from age(m.fin, e.date_mise_en_service)) * 12
        + extract(month from age(m.fin, e.date_mise_en_service)))::int as anciennete_mois,
    f.nom_formule as formule, a.mrr_ht
from marts.dim_etablissement e
join m on e.date_mise_en_service <= m.fin and (e.date_resiliation is null or e.date_resiliation > m.fin)
left join marts.fait_abonnement_mensuel a on a.etablissement_id = e.etablissement_id and a.mois = m.debut
left join marts.dim_formule f on f.formule_id = a.formule_id
"""

# Agrégats mensuels par établissement (les fenêtres glissantes sont calculées ensuite en pandas).
SQL_ACTIVITE = """
select s.etablissement_id, date_trunc('month', d.date)::date as mois,
       count(*) as sessions, sum(s.a_commande::int) as sessions_commande,
       sum(case when f.inclut_commande then 1 else 0 end) as sessions_formule_commande
from marts.fait_session s
join marts.dim_date d using (date_id)
join marts.dim_formule f using (formule_id)
group by 1, 2
"""
SQL_TICKETS = """
select etablissement_id, date_trunc('month', date_ouverture)::date as mois,
       count(*) as tickets, sum(note_satisfaction) as somme_notes, count(note_satisfaction) as nb_notes
from marts.fait_ticket_support group by 1, 2
"""
SQL_FACTURES = """
select etablissement_id, date_trunc('month', date_emission)::date as mois, count(*) as factures,
       sum((statut_facture in ('payee_en_retard', 'impayee'))::int) as factures_retard
from marts.fait_facturation where montant_ttc > 0 group by 1, 2
"""


def _glissant(base, agr, colonnes, n, suffixe, decalage=0):
    """Somme des n mois se terminant au mois m - decalage, pour chaque ligne de base."""
    mois = pd.date_range("2023-01-01", "2026-12-01", freq="MS")
    grille = pd.MultiIndex.from_product([base["etablissement_id"].unique(), mois],
                                        names=["etablissement_id", "mois"])
    a = agr.set_index(["etablissement_id", "mois"])[colonnes].reindex(grille, fill_value=0)
    roul = a.groupby(level=0).rolling(n, min_periods=1).sum().droplevel(0)
    if decalage:
        roul = roul.groupby(level=0).shift(decalage).fillna(0)
    roul.columns = [f"{c}_{suffixe}" for c in colonnes]
    return base.join(roul, on=["etablissement_id", "mois"])


def panel(avec_mois_a_scorer: bool = False):
    """Jeu mensuel : une ligne par établissement actif et par mois, avec la cible et les variables explicatives.

    Par défaut, de janvier 2024 au dernier mois dont la cible est connue (temporal_split.DERNIER_MOIS_PANEL).
    avec_mois_a_scorer=True ajoute le mois d'arrêté (décembre 2026), dont la cible est inconnue (NaN) :
    ce sont les lignes à scorer.
    """
    dernier = temporal_split.MOIS_A_SCORER if avec_mois_a_scorer else temporal_split.DERNIER_MOIS_PANEL
    df = chargement.lire(SQL_ETAB_MOIS, dernier_mois=dernier.date())
    df["mois"] = pd.to_datetime(df["mois"])
    df["resilie_mois_suivant"] = df["resilie_mois_suivant"].astype("float")
    df.loc[df["mois"] > temporal_split.DERNIER_MOIS_PANEL, "resilie_mois_suivant"] = float("nan")
    act, tic, fac = chargement.lire(SQL_ACTIVITE), chargement.lire(SQL_TICKETS), chargement.lire(SQL_FACTURES)
    for t in (act, tic, fac):
        t["mois"] = pd.to_datetime(t["mois"])
    df = _glissant(df, act, ["sessions"], 1, "1m")
    df = _glissant(df, act, ["sessions", "sessions_commande", "sessions_formule_commande"], 3, "3m")
    df = _glissant(df, act, ["sessions"], 3, "3m_avant", decalage=3)
    df = _glissant(df, tic, ["tickets"], 3, "3m")
    df = _glissant(df, tic, ["somme_notes", "nb_notes"], 6, "6m")
    df = _glissant(df, fac, ["factures", "factures_retard"], 6, "6m")
    jours = df["mois"].dt.days_in_month
    df["sessions_table_jour_1m"] = df["sessions_1m"] / (df["nb_tables"] * jours)
    df["sessions_table_jour_3m"] = df["sessions_3m"] / (df["nb_tables"] * 91)
    df["tendance_usage"] = (df["sessions_3m"] + 1) / (df["sessions_3m_avant"] + 1)
    df["taux_commande_3m"] = df["sessions_commande_3m"] / df["sessions_formule_commande_3m"]
    df["satisfaction_6m"] = df["somme_notes_6m"] / df["nb_notes_6m"]
    df["part_factures_retard_6m"] = (df["factures_retard_6m"] / df["factures_6m"]).fillna(0)
    return df.drop(columns=["somme_notes_6m", "nb_notes_6m", "sessions_formule_commande_3m"])


# ---------------------------------------------------------------------------------------------------------------
# Data mining (T7.3)
# ---------------------------------------------------------------------------------------------------------------
SQL_LIGNES_SERVIES = """
select l.commande_id, l.etablissement_id, d.date, l.article_id, a.nom_article, a.nom_categorie, l.quantite
from marts.fait_ligne_commande l
join marts.dim_date d using (date_id)
join marts.dim_article a on a.prix_id = l.prix_id
where l.est_servie
"""


def lignes_servies() -> pd.DataFrame:
    """Une ligne par article de commande servie, avec le nom du plat et sa catégorie (paniers des règles d'association)."""
    df = chargement.lire(SQL_LIGNES_SERVIES)
    df["date"] = pd.to_datetime(df["date"])
    df["annee"] = df["date"].dt.year
    return df


SQL_VERSIONS_PRIX = """
select article_id, etablissement_id, nom_categorie, nom_article, date_ajout, date_retrait,
       valide_du, valide_au, prix_ttc, prix_precedent, motif_changement
from marts.dim_article
"""
SQL_VENTES_ARTICLE_MOIS = """
select l.article_id, date_trunc('month', d.date)::date as mois, sum(l.quantite) as q
from marts.fait_ligne_commande l join marts.dim_date d using (date_id)
where l.est_servie group by 1, 2
"""


def versions_prix() -> pd.DataFrame:
    """Versions de prix des articles (SCD2 de dim_article)."""
    v = chargement.lire(SQL_VERSIONS_PRIX)
    for c in ["date_ajout", "date_retrait", "valide_du", "valide_au"]:
        v[c] = pd.to_datetime(v[c])
    return v


def panel_prix(versions: pd.DataFrame | None = None) -> pd.DataFrame:
    """Une ligne par article proposé et par mois : prix en vigueur le 15 du mois et quantité vendue (zéros compris).

    Un article compte pour un mois s'il était à la carte du premier au dernier jour du mois. On ne garde que les
    cellules (établissement x catégorie x mois) qui ont au moins une vente : une cellule sans vente ne dit rien
    sur la répartition entre articles.
    """
    v = versions_prix() if versions is None else versions
    ventes = chargement.lire(SQL_VENTES_ARTICLE_MOIS)
    ventes["mois"] = pd.to_datetime(ventes["mois"])
    q = ventes.set_index(["article_id", "mois"])["q"]
    morceaux = []
    for m in pd.date_range(temporal_split.DEBUT_DONNEES, temporal_split.MOIS_A_SCORER, freq="MS"):
        j = m + pd.Timedelta(days=14)
        fin = m + pd.offsets.MonthEnd(0)
        actif = ((v["valide_du"] <= j) & (v["valide_au"].isna() | (v["valide_au"] >= j))
                 & (v["date_ajout"] <= m) & (v["date_retrait"].isna() | (v["date_retrait"] > fin)))
        morceaux.append(v.loc[actif, ["article_id", "etablissement_id", "nom_categorie", "nom_article", "prix_ttc"]]
                        .assign(mois=m))
    p = pd.concat(morceaux, ignore_index=True)
    p["q"] = q.reindex(pd.MultiIndex.from_frame(p[["article_id", "mois"]])).fillna(0).to_numpy()
    p["cellule"] = p["etablissement_id"] + "|" + p["nom_categorie"] + "|" + p["mois"].dt.strftime("%Y-%m")
    return p[p.groupby("cellule")["q"].transform("sum") > 0].reset_index(drop=True)
