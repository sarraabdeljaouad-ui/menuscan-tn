-- Fait commande : une ligne par commande (taux de commande, taux d'annulation, panier moyen).
-- Ajouté au modèle prévu en phase 0 : 46 commandes n'ont plus de ligne valide (toutes en quarantaine)
-- et doivent quand même compter dans les taux.
select
    c.commande_id, c.session_id, c.etablissement_id, c.table_id,
    {{ date_id('c.date_heure_commande') }} as date_id, extract(hour from c.date_heure_commande)::smallint as heure,
    c.date_heure_commande, c.date_heure_service,
    extract(epoch from (c.date_heure_service - c.date_heure_commande))::integer / 60 as delai_service_minutes,
    c.statut_commande, c.statut_commande = 'servie' as est_servie, c.mode_reglement, c.motif_annulation,
    c.nb_lignes, c.nb_articles, c.montant_total_ttc, c.lignes_completes
from {{ ref('int_commandes') }} c
