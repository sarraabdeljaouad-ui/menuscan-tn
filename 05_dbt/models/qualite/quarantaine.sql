-- Quarantaine : toutes les lignes écartées du staging, avec la règle, le motif et la ligne complète.
-- Une ligne n'est jamais perdue : elle est soit en staging, soit ici.
{% for nom, cle in preparations() %}
select
    '{{ nom }}'::text as table_source,
    {{ cle if cle != 'date' else '"date"' }}::text as identifiant,
    _regle_rejet as regle_dq,
    _motif_rejet as motif,
    _fichier as fichier,
    _ligne as ligne,
    to_jsonb(p) - '_corrections' - '_regle_rejet' - '_motif_rejet' - '_fichier' - '_ligne' as contenu
from {{ ref('prep_' ~ nom) }} p
where _regle_rejet is not null
{% if not loop.last %}union all{% endif %}
{% endfor %}
