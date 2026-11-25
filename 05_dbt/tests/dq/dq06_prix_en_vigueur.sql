-- DQ-06 : prix unitaire = prix en vigueur le jour de la commande.
select ligne_id from {{ ref('fait_ligne_commande') }} where prix_id is null or not prix_conforme
