-- Fait facturation : une ligne par facture, avec son encaissement (chiffre d'affaires facturé et encaissé, retards, impayés).
with paiements as (
    select facture_id, count(*) as nb_tentatives,
           count(*) filter (where statut_paiement = 'echoue') as nb_echecs,
           max(date_paiement) filter (where statut_paiement = 'reussi') as date_paiement,
           max(mode_paiement) filter (where statut_paiement = 'reussi') as mode_paiement,
           coalesce(sum(montant_ttc) filter (where statut_paiement = 'reussi'), 0) as montant_encaisse_ttc
    from {{ ref('stg_paiements') }} group by facture_id
)
select
    f.facture_id, f.etablissement_id, f.abonnement_id, a.formule_id, f.type_facture,
    {{ date_id('f.date_emission') }} as date_id, f.date_emission, f.date_echeance, f.periode_debut, f.periode_fin,
    f.montant_ht, f.remise_ht, f.motif_remise, f.montant_net_ht, f.montant_tva, f.montant_ttc,
    coalesce(p.montant_encaisse_ttc, 0) as montant_encaisse_ttc, p.date_paiement, p.mode_paiement,
    coalesce(p.nb_tentatives, 0) as nb_tentatives, coalesce(p.nb_echecs, 0) as nb_echecs,
    greatest(p.date_paiement::date - f.date_echeance, 0) as jours_retard,
    f.statut_facture
from {{ ref('stg_factures') }} f
left join paiements p on p.facture_id = f.facture_id
left join {{ ref('stg_abonnements') }} a on a.abonnement_id = f.abonnement_id
