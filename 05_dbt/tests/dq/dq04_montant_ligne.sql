-- DQ-04 : montant de ligne = prix unitaire x quantité.
select ligne_id from {{ ref('fait_ligne_commande') }} where abs(montant_ligne_ttc - prix_unitaire_ttc * quantite) > 0.001
