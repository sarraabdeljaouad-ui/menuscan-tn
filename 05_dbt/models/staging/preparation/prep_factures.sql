-- Factures. Source : facturation/factures.csv, au format français : dates JJ/MM/AAAA, virgule décimale (DQ-36).
-- Correction : TTC recalculé quand il ne vaut pas net HT + TVA (DQ-15).
with source as (
    select *, {{ rang_doublon('facture_id') }} as _rang from {{ source('raw', 'facturation_factures') }}
),
typee as (
    select
        facture_id, etablissement_id, abonnement_id, type_facture,
        {{ date_fr('periode_debut') }} as periode_debut, {{ date_fr('periode_fin') }} as periode_fin,
        {{ date_fr('date_emission') }} as date_emission,
        {{ decimal_fr('montant_ht') }}::numeric(10, 3) as montant_ht, {{ decimal_fr('remise_ht') }}::numeric(10, 3) as remise_ht,
        motif_remise, {{ decimal_fr('montant_net_ht') }}::numeric(10, 3) as montant_net_ht,
        {{ decimal_fr('montant_tva') }}::numeric(10, 3) as montant_tva, {{ decimal_fr('montant_ttc') }}::numeric(10, 3) as _ttc_brut,
        {{ date_fr('date_echeance') }} as date_echeance, statut_facture, _fichier, _ligne, _rang
    from source
)
select
    facture_id, etablissement_id, abonnement_id, type_facture, periode_debut, periode_fin, date_emission, montant_ht, remise_ht,
    motif_remise, montant_net_ht, montant_tva,
    case when abs(_ttc_brut - (montant_net_ht + montant_tva)) > 0.001 then montant_net_ht + montant_tva else _ttc_brut end as montant_ttc,
    date_echeance, statut_facture, _fichier, _ligne,
    {{ corrections([corr('DQ-15', 'montant_ttc', 'abs(_ttc_brut - (montant_net_ht + montant_tva)) > 0.001', '_ttc_brut', 'montant_net_ht + montant_tva')]) }} as _corrections,
    {{ rejet('facture_id') }}
from typee
