-- Sessions reconstituées à partir des événements (la table n'existe pas dans la couche brute).
-- Une session commence au scan du QR code et se termine au dernier événement (règles métier, § 8).
-- Les événements écartés pour article inconnu (DQ-02) comptent : la consultation a bien eu lieu.
with evenements as (
    select p.session_id, p.etablissement_id, p.table_id, p.type_evenement, p.appareil, p.langue,
           coalesce(c.horodatage_corrige, p.horodatage) as horodatage
    from {{ ref('prep_evenements') }} p
    left join {{ ref('int_horodatages_corriges') }} c on c.evenement_id = p.evenement_id
    where p._regle_rejet is null or p._regle_rejet = 'DQ-02'
)
select
    session_id,
    min(etablissement_id) as etablissement_id,
    min(table_id) as table_id,
    min(horodatage) as debut_session,
    max(horodatage) as fin_session,
    min(appareil) as appareil,
    min(langue) as langue,
    bool_or(type_evenement = 'vue_menu') as a_vu_menu,
    count(*) filter (where type_evenement = 'vue_article') as nb_articles_vus,
    bool_or(type_evenement = 'ajout_panier') as a_ajoute_panier,
    bool_or(type_evenement = 'commande_envoyee') as a_commande,
    count(*) as nb_evenements,
    count(distinct etablissement_id) as _nb_etablissements,
    count(distinct table_id) as _nb_tables
from evenements
group by session_id
