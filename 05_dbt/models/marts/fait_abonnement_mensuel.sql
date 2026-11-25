-- Fait abonnement mensuel : un établissement x un mois. MRR et mouvements (décision D-33).
select
    m.etablissement_id, m.mois, {{ date_id('m.mois') }} as date_id, m.abonnement_id, m.formule_id, m.periodicite,
    m.mrr_ht, m.mrr_precedent_ht, m.variation_ht, m.mouvement,
    case when m.mouvement in ('nouveau', 'reactivation') then m.variation_ht else 0 end as mrr_nouveau_ht,
    case when m.mouvement = 'expansion' then m.variation_ht else 0 end as mrr_expansion_ht,
    case when m.mouvement = 'contraction' then m.variation_ht else 0 end as mrr_contraction_ht,
    case when m.mouvement = 'resiliation' then m.variation_ht else 0 end as mrr_resiliation_ht,
    m.mrr_ht > 0 as est_abonne
from {{ ref('int_mrr_mensuel') }} m
