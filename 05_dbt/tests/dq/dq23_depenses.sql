-- DQ-23 : jour dans la campagne, clics <= impressions, dépense >= 0, prospects réconciliés avec le CRM.
with crm as (select campagne_id, date_contact, count(*) n from {{ ref('fait_prospect') }} group by 1, 2)
select m.depense_id from {{ ref('fait_marketing') }} m
join {{ ref('stg_campagnes_marketing') }} c using (campagne_id)
join {{ ref('dim_date') }} d using (date_id)
left join crm on crm.campagne_id = m.campagne_id and crm.date_contact = d."date"
where d."date" not between c.date_debut and c.date_fin or m.clics > m.impressions or m.depense_ttc < 0
   or m.nb_prospects <> coalesce(crm.n, 0)
