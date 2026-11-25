-- DQ-27 : aucune date après l'arrêté du 31/12/2026 ; aucun événement pendant la panne du 12/09/2025.
select evenement_id as identifiant from {{ ref('int_evenements') }}
where horodatage >= '{{ var("date_arrete") }}'::date + 1 or horodatage between '{{ var("panne_debut") }}' and '{{ var("panne_fin") }}'
union all select commande_id from {{ ref('fait_commande') }} where date_heure_commande >= '{{ var("date_arrete") }}'::date + 1
union all select session_id from {{ ref('fait_session') }} where fin_session >= '{{ var("date_arrete") }}'::date + 1
union all select facture_id from {{ ref('fait_facturation') }} where date_emission > '{{ var("date_arrete") }}'::date or date_paiement >= '{{ var("date_arrete") }}'::date + 1
union all select ticket_id from {{ ref('fait_ticket_support') }} where date_ouverture >= '{{ var("date_arrete") }}'::date + 1
