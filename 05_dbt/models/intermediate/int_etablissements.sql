-- Établissements dédoublonnés (DQ-30) : les identifiants fusionnés sont retirés,
-- leur rattachement est dans int_correspondance_etablissements.
select e.*
from {{ ref('stg_etablissements') }} e
where not exists (select 1 from {{ ref('int_correspondance_etablissements') }} f where f.ancien_id = e.etablissement_id)
