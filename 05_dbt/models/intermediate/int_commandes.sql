-- Commandes avec le total recalculé depuis les lignes (DQ-03) : montant = somme des lignes,
-- nb_lignes = nombre de lignes, nb_articles = somme des quantités.
-- Si une ligne de la commande est en quarantaine, les lignes restantes sont incomplètes :
-- les valeurs de la source sont gardées et lignes_completes vaut faux.
with lignes as (
    select commande_id, count(*) as nb_lignes, sum(quantite) as nb_articles, sum(montant_ligne_ttc) as montant
    from {{ ref('stg_lignes_commande') }} group by commande_id
),
lignes_ecartees as (
    select contenu->>'commande_id' as commande_id, count(*) as nb
    from {{ ref('quarantaine') }}
    where table_source = 'lignes_commande' and regle_dq <> 'DQ-29'
    group by 1
),
calcul as (
    select c.*, l.nb_lignes as _nb_lignes_calc, l.nb_articles as _nb_articles_calc, l.montant as _montant_calc,
           (l.commande_id is not null and q.commande_id is null) as lignes_completes
    from {{ ref('stg_commandes') }} c
    left join lignes l on l.commande_id = c.commande_id
    left join lignes_ecartees q on q.commande_id = c.commande_id
)
select
    commande_id, session_id, etablissement_id, table_id, date_heure_commande, statut_commande, date_heure_service,
    case when lignes_completes then _nb_lignes_calc::smallint else nb_lignes end as nb_lignes,
    case when lignes_completes then _nb_articles_calc::smallint else nb_articles end as nb_articles,
    case when lignes_completes then _montant_calc else montant_total_ttc end as montant_total_ttc,
    mode_reglement, motif_annulation, lignes_completes,
    lignes_completes and (abs(montant_total_ttc - _montant_calc) > 0.001 or nb_lignes <> _nb_lignes_calc
                          or nb_articles <> _nb_articles_calc) as total_recalcule,
    montant_total_ttc as montant_total_source, nb_lignes as nb_lignes_source, nb_articles as nb_articles_source,
    _fichier, _ligne
from calcul
