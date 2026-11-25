-- DQ-03 : montant de la commande = somme des lignes ; nb_lignes et nb_articles cohérents.
-- Hors commandes dont une ligne est en quarantaine (lignes_completes = faux) : leurs lignes valides sont incomplètes.
with l as (select commande_id, count(*) nl, sum(quantite) na, sum(montant_ligne_ttc) m from {{ ref('fait_ligne_commande') }} group by 1)
select c.commande_id from {{ ref('fait_commande') }} c join l using (commande_id)
where c.lignes_completes and (abs(c.montant_total_ttc - l.m) > 0.001 or c.nb_lignes <> l.nl or c.nb_articles <> l.na)
