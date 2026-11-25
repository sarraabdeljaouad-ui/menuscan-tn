-- Tickets du support. Source : support/tickets_support.csv
-- Corrections : statut (DQ-32), catégorie manquante remplacée par « non_renseignee » (DQ-38).
with source as (
    select *, {{ rang_doublon('ticket_id') }} as _rang from {{ source('raw', 'support_tickets') }}
),
nettoyee as (
    select
        ticket_id, etablissement_id, date_ouverture::timestamp as date_ouverture,
        coalesce({{ espaces('categorie') }}, 'non_renseignee') as categorie, canal_contact,
        delai_resolution_heures::numeric(8, 1) as delai_resolution_heures, date_resolution::timestamp as date_resolution,
        {{ traduire('statut_ticket', 'statut_ticket') }} as statut_ticket, note_satisfaction::smallint as note_satisfaction,
        categorie as _categorie_brute, statut_ticket as _statut_brut, _fichier, _ligne, _rang
    from source
)
select
    ticket_id, etablissement_id, date_ouverture, categorie, canal_contact, delai_resolution_heures, date_resolution,
    statut_ticket, note_satisfaction, _fichier, _ligne,
    {{ corrections([
        corr('DQ-38', 'categorie', '_categorie_brute is null', '_categorie_brute', 'categorie'),
        corr_si_change('DQ-32', 'statut_ticket', '_statut_brut', 'statut_ticket'),
    ]) }} as _corrections,
    {{ rejet('ticket_id', [['DQ-27', apres_arrete('date_ouverture'), "ticket ouvert après la date d'arrêté"]]) }}
from nettoyee
