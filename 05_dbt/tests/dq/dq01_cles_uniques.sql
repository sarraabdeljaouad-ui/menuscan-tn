-- DQ-01 : clé primaire non nulle et unique (tables de l'entrepôt). Les tests unique et not_null des modèles le vérifient aussi colonne par colonne.
{% set tables = [('fait_commande','commande_id'),('fait_ligne_commande','ligne_id'),('fait_session','session_id'),('fait_facturation','facture_id'),('fait_marketing','depense_id'),('fait_prospect','prospect_id'),('fait_ticket_support','ticket_id'),('dim_etablissement','etablissement_id'),('dim_article','prix_id'),('dim_table','table_id'),('int_evenements','evenement_id')] %}
{% for t, k in tables %}
select '{{ t }}' as objet, count(*) - count(distinct {{ k }}) as violations from {{ ref(t) }} having count(*) - count(distinct {{ k }}) > 0 or count(*) <> count({{ k }})
{% if not loop.last %}union all{% endif %}{% endfor %}
