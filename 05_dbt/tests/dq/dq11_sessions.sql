-- DQ-11 : début <= fin, événements dans la fenêtre de la session, premier événement = scan_qr.
with premier as (
    select distinct on (session_id) session_id, type_evenement from {{ ref('int_evenements') }} order by session_id, horodatage, evenement_id
)
select s.session_id from {{ ref('fait_session') }} s where s.debut_session > s.fin_session
union all
select e.session_id from {{ ref('int_evenements') }} e join {{ ref('fait_session') }} s using (session_id) where e.horodatage not between s.debut_session and s.fin_session
union all
select session_id from premier where type_evenement <> 'scan_qr'
