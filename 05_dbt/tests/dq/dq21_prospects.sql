-- DQ-21 : prospect converti <=> établissement ; contact <= conversion = signature.
select p.prospect_id from {{ ref('fait_prospect') }} p left join {{ ref('dim_etablissement') }} e using (etablissement_id)
where (p.est_converti <> (p.etablissement_id is not null))
   or (p.est_converti and (p.date_contact > p.date_conversion or p.date_conversion <> e.date_signature))
