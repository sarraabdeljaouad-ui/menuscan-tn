-- Abonnements. Source : backoffice/abonnements.csv. Correction : périodicité (DQ-32).
with source as (
    select *, {{ rang_doublon('abonnement_id') }} as _rang from {{ source('raw', 'backoffice_abonnements') }}
),
nettoyee as (
    select
        abonnement_id, etablissement_id, formule_id, date_debut::date as date_debut, date_fin::date as date_fin,
        {{ traduire('periodicite', 'periodicite') }} as periodicite, prix_mensuel_ht::numeric(10, 3) as prix_mensuel_ht,
        type_mouvement, motif_fin, periodicite as _periodicite_brute, _fichier, _ligne, _rang
    from source
)
select
    abonnement_id, etablissement_id, formule_id, date_debut, date_fin, periodicite, prix_mensuel_ht, type_mouvement, motif_fin,
    _fichier, _ligne,
    {{ corrections([corr_si_change('DQ-32', 'periodicite', '_periodicite_brute', 'periodicite')]) }} as _corrections,
    {{ rejet('abonnement_id') }}
from nettoyee
