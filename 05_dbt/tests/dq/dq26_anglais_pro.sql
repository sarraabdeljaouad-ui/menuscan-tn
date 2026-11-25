-- DQ-26 : menu en anglais seulement sous formule Pro.
select s.session_id from {{ ref('fait_session') }} s join {{ ref('dim_formule') }} f using (formule_id)
where s.langue = 'en' and f.nom_formule <> 'Pro'
