-- DQ-25 : ouverture de la ville <= signature <= mise en service <= résiliation.
select e.etablissement_id from {{ ref('dim_etablissement') }} e join {{ ref('dim_ville') }} v using (ville_id)
where e.date_signature < v.date_ouverture_commerciale or e.date_mise_en_service < e.date_signature
   or e.date_resiliation < e.date_mise_en_service
