-- DQ-20 : résolution >= ouverture ; statut résolu <=> date de résolution renseignée.
select ticket_id from {{ ref('fait_ticket_support') }}
where date_resolution < date_ouverture or ((statut_ticket = 'resolu') <> (date_resolution is not null))
