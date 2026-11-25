-- DQ-11 : une session commence avant de finir et ne concerne qu'un établissement et qu'une table.
select session_id, debut_session, fin_session, _nb_etablissements, _nb_tables
from {{ ref('int_sessions') }}
where debut_session > fin_session or _nb_etablissements > 1 or _nb_tables > 1
