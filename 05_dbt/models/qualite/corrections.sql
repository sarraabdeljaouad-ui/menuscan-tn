-- Journal des corrections : une ligne par valeur corrigée dans une ligne gardée en staging,
-- avec la règle, la colonne, la valeur d'origine et la valeur corrigée.
-- Les corrections de l'étage intermediate (DQ-03, DQ-30, DQ-37) sont ajoutées à la fin.
{% for nom, cle in preparations() %}
select
    '{{ nom }}'::text as table_source,
    {{ cle if cle != 'date' else 'p."date"' }}::text as identifiant,
    c->>'regle' as regle_dq,
    c->>'colonne' as colonne,
    c->>'avant' as valeur_avant,
    c->>'apres' as valeur_apres,
    p._fichier as fichier,
    p._ligne as ligne
from {{ ref('prep_' ~ nom) }} p
cross join lateral jsonb_array_elements(p._corrections) c
where p._regle_rejet is null
{% if not loop.last %}union all{% endif %}
{% endfor %}
union all
select table_source, identifiant, regle_dq, colonne, valeur_avant, valeur_apres, null::text as fichier, null::integer as ligne
from {{ ref('int_corrections') }}
