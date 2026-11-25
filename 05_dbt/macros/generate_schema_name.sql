{#- Les modèles vont dans le schéma indiqué par +schema (staging, preparation, qualite...), sans préfixe.
    Par défaut, dbt écrirait "staging_preparation" : ce nom serait moins lisible dans DBeaver et Power BI. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}
