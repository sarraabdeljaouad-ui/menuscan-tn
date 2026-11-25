-- DQ-22 : la campagne d'un prospect est du même canal et active à la date de contact (salons : jusqu'à 3 jours après).
select p.prospect_id from {{ ref('fait_prospect') }} p join {{ ref('stg_campagnes_marketing') }} c using (campagne_id)
join {{ ref('dim_canal') }} k on k.canal_id = c.canal_id
where c.canal_id <> p.canal_id
   or p.date_contact < c.date_debut
   or p.date_contact > c.date_fin + case when k.type_canal = 'evenementiel' or lower(k.nom_canal) like '%salon%' then 3 else 0 end
