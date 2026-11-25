-- Bilan par table : lignes brutes, lignes en staging, lignes en quarantaine et corrections, par règle.
with brutes as (
    {% for nom, cle in preparations() %}
    select '{{ nom }}'::text as table_source, count(*) as lignes_brutes,
           count(*) filter (where _regle_rejet is null) as lignes_staging,
           count(*) filter (where _regle_rejet is not null) as lignes_quarantaine
    from {{ ref('prep_' ~ nom) }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
),
regles as (
    select table_source, 'quarantaine' as nature, regle_dq, count(*) as n from {{ ref('quarantaine') }} group by 1, 2, 3
    union all
    select table_source, 'correction', regle_dq, count(*) from {{ ref('corrections') }} group by 1, 2, 3
)
select b.table_source, b.lignes_brutes, b.lignes_staging, b.lignes_quarantaine,
       r.nature, r.regle_dq, coalesce(r.n, 0) as nb_lignes
from brutes b
left join regles r on r.table_source = b.table_source
order by b.table_source, r.nature, r.regle_dq
