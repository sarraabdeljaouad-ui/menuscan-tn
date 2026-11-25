{#- Forme de référence d'un nom (plat, établissement) : parmi les écritures d'un même nom (même clé sans casse,
    sans accent, espaces normalisés), on garde la plus fréquente, en écartant celles tout en majuscules ou tout
    en minuscules. Si seule une écriture douteuse existe, sa casse est rétablie par la règle « casse ». -#}
{% macro noms_canoniques(selections, casse) -%}
with ecritures as (
    {% for s in selections %}
    select {{ cle_libelle(s[1]) }} as cle, {{ espaces(s[1]) }} as nom from {{ s[0] }}
    where {{ espaces(s[1]) }} is not null
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),
comptes as (
    select cle, nom, count(*) as n, (nom = upper(nom) or nom = lower(nom)) as casse_douteuse
    from ecritures group by cle, nom
),
choix as (
    select distinct on (cle) cle, nom, casse_douteuse, n
    from comptes order by cle, casse_douteuse, n desc, nom
)
select cle, case when casse_douteuse then {{ casse('nom') }} else nom end as nom_canonique,
       (select count(distinct c2.nom) from comptes c2 where c2.cle = choix.cle) as nb_ecritures
from choix
{%- endmacro %}

{# Casse d'un plat : première lettre en majuscule (« Salade verte ») #}
{% macro casse_phrase(col) -%}
    upper(left(lower({{ col }}), 1)) || substr(lower({{ col }}), 2)
{%- endmacro %}

{# Casse d'un établissement : chaque mot en majuscule, sauf « Salon de thé » (« Snack Le Sahel ») #}
{% macro casse_titre(col) -%}
    regexp_replace(initcap(lower({{ col }})), '^Salon De Thé', 'Salon de thé')
{%- endmacro %}
