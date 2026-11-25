-- DQ-08 : la table de la session et celle de la commande appartiennent au même établissement.
select s.session_id as identifiant from {{ ref('fait_session') }} s join {{ ref('dim_table') }} t using (table_id) where t.etablissement_id <> s.etablissement_id
union all
select c.commande_id from {{ ref('fait_commande') }} c join {{ ref('dim_table') }} t using (table_id) where t.etablissement_id <> c.etablissement_id
union all
select c.commande_id from {{ ref('fait_commande') }} c join {{ ref('fait_session') }} s using (session_id) where s.table_id <> c.table_id or s.etablissement_id <> c.etablissement_id
