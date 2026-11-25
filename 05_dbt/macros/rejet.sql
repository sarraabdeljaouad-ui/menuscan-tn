{#- Règles de rejet d'une ligne vers la quarantaine. regles = liste de [regle_dq, condition SQL, motif].
    La première règle vraie l'emporte ; une ligne sans règle vraie passe en staging.
    DQ-01 (identifiant vide) et DQ-29 (doublon d'ingestion) sont toujours testées en premier. -#}
{% macro rejet(cle, regles=[]) -%}
    {%- set toutes = [['DQ-01', cle ~ ' is null', 'identifiant vide'],
                      ['DQ-29', '_rang > 1', "doublon d'ingestion (copie d'une ligne déjà reçue)"]] + regles -%}
    case {% for r in toutes %}when {{ r[1] }} then '{{ r[0] }}' {% endfor %}end as _regle_rejet,
    case {% for r in toutes %}when {{ r[1] }} then '{{ r[2] | replace("'", "''") }}' {% endfor %}end as _motif_rejet
{%- endmacro %}
