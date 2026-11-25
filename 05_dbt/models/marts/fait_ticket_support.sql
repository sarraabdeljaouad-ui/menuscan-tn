-- Fait ticket de support : une ligne par ticket (délai de résolution, satisfaction).
-- Ajouté au modèle prévu en phase 0 pour couvrir le KPI K18.
select
    t.ticket_id, t.etablissement_id, {{ date_id('t.date_ouverture') }} as date_id, t.date_ouverture, t.date_resolution,
    t.categorie, t.canal_contact, t.statut_ticket, t.delai_resolution_heures, t.note_satisfaction
from {{ ref('stg_tickets_support') }} t
