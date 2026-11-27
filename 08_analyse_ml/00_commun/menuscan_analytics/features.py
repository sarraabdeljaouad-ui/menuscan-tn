"""features.py : tables de variables.

panel() : une ligne par établissement actif en fin de mois, avec la cible de résiliation (T7.2, EF-10).
Toutes les variables utilisent des données antérieures ou égales à la fin du mois (pas de fuite).
"""
from __future__ import annotations

import pandas as pd

from . import chargement

# Une ligne par établissement actif en fin de mois m. Cible : résiliation effective le mois suivant (m + 1).
# Toutes les variables sont calculées avec des données antérieures ou égales à la fin du mois m (pas de fuite).
SQL_ETAB_MOIS = """
with m as (
    select debut::date, (debut + interval '1 month - 1 day')::date as fin
    from generate_series('2024-01-01'::date, '2026-11-01'::date, interval '1 month') debut
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


def panel():
    """Jeu mensuel : une ligne par établissement actif et par mois, avec la cible et les variables explicatives."""
    df = chargement.lire(SQL_ETAB_MOIS)
    df["mois"] = pd.to_datetime(df["mois"])
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
