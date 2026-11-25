-- Les marts ne perdent ni ne créent de montant : chiffre d'affaires des lignes = staging, MRR = intermediate.
select 'lignes' as controle, (select sum(montant_ligne_ttc) from {{ ref('fait_ligne_commande') }}) as marts,
       (select sum(montant_ligne_ttc) from {{ ref('stg_lignes_commande') }}) as source
where (select sum(montant_ligne_ttc) from {{ ref('fait_ligne_commande') }}) <> (select sum(montant_ligne_ttc) from {{ ref('stg_lignes_commande') }})
union all
select 'mrr', (select sum(mrr_ht) from {{ ref('fait_abonnement_mensuel') }}), (select sum(mrr_ht) from {{ ref('int_mrr_mensuel') }})
where (select sum(mrr_ht) from {{ ref('fait_abonnement_mensuel') }}) <> (select sum(mrr_ht) from {{ ref('int_mrr_mensuel') }})
