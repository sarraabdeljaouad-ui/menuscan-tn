-- Commandes. Source : ventes/commandes/commandes_AAAA_MM.csv (36 fichiers)
-- Corrections : date au format français (DQ-28), statut (DQ-32), mode de règlement manquant d'une commande servie (DQ-38).
-- Données en retard (DQ-35) : la commande est rattachée à sa date, pas au mois du fichier ; le retard est tracé.
-- Le total de la commande est recalculé depuis les lignes en T4.2 (DQ-03, étape intermediate du catalogue).
with source as (
    select *, {{ rang_doublon('commande_id') }} as _rang from {{ source('raw', 'ventes_commandes') }}
),
nettoyee as (
    select
        commande_id, session_id, etablissement_id, table_id,
        {{ horodatage_mixte('date_heure_commande') }} as date_heure_commande,
        {{ traduire('statut_commande', 'statut_commande') }} as statut_commande,
        date_heure_service::timestamp as date_heure_service, nb_lignes::smallint as nb_lignes, nb_articles::smallint as nb_articles,
        montant_total_ttc::numeric(10, 3) as montant_total_ttc, mode_reglement, motif_annulation,
        date_heure_commande as _date_brute, statut_commande as _statut_brut, {{ mois_fichier('_fichier') }} as _mois_fichier,
        _fichier, _ligne, _rang
    from source
),
completee as (
    select n.*,
        case when mode_reglement is null and statut_commande = 'servie' then 'non_renseigne' else mode_reglement end as _mode_complete
    from nettoyee n
)
select
    commande_id, session_id, etablissement_id, table_id, date_heure_commande, statut_commande, date_heure_service, nb_lignes,
    nb_articles, montant_total_ttc, _mode_complete as mode_reglement, motif_annulation,
    _fichier, _ligne,
    {{ corrections([
        corr('DQ-28', 'date_heure_commande', est_date_fr('_date_brute'), '_date_brute', 'date_heure_commande'),
        corr_si_change('DQ-32', 'statut_commande', '_statut_brut', 'statut_commande'),
        corr('DQ-38', 'mode_reglement', 'mode_reglement is null and _mode_complete is not null', 'mode_reglement', '_mode_complete'),
        corr('DQ-35', 'date_heure_commande', "date_trunc('month', date_heure_commande)::date < _mois_fichier",
             "to_char(_mois_fichier, 'YYYY-MM')", "to_char(date_heure_commande, 'YYYY-MM')"),
    ]) }} as _corrections,
    {{ rejet('commande_id', [['DQ-27', apres_arrete('date_heure_commande'), "commande après la date d'arrêté"]]) }}
from completee
