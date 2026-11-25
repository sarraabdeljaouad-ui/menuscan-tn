-- DQ-10 : sessions, commandes et tickets dans la période de service de l'établissement (mise en service -> fin du mois de résiliation).
with e as (select etablissement_id, date_mise_en_service, coalesce(date_resiliation, '9999-12-31') as fin from {{ ref('dim_etablissement') }})
select s.session_id as identifiant from {{ ref('fait_session') }} s join e using (etablissement_id) where s.debut_session::date not between e.date_mise_en_service and e.fin
union all
select c.commande_id from {{ ref('fait_commande') }} c join e using (etablissement_id) where c.date_heure_commande::date not between e.date_mise_en_service and e.fin
union all
select t.ticket_id from {{ ref('fait_ticket_support') }} t join e using (etablissement_id) where t.date_ouverture::date not between e.date_mise_en_service and e.fin
