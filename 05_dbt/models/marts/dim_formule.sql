-- Dimension formule d'abonnement.
select formule_id, nom_formule, prix_mensuel_ht, prix_annuel_ht, frais_mise_en_place_ht, inclut_commande, inclut_statistiques, description
from {{ ref('stg_formules') }}
