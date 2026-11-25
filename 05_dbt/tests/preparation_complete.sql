-- Chaque préparation contient exactement les lignes de sa table raw (rien n'est perdu entre raw et preparation).
{% set paires = [
    ('dim_calendrier', 'referentiels_calendrier'), ('ref_villes', 'referentiels_villes'), ('formules', 'backoffice_formules'),
    ('canaux_acquisition', 'referentiels_canaux_acquisition'), ('campagnes_marketing', 'marketing_campagnes'),
    ('marketing_depenses_quotidiennes', 'marketing_depenses_quotidiennes'), ('prospects', 'crm_prospects'),
    ('etablissements', 'backoffice_etablissements'), ('abonnements', 'backoffice_abonnements'), ('factures', 'facturation_factures'),
    ('paiements', 'paiements_api_paiements'), ('tickets_support', 'support_tickets'), ('categories_menu', 'menus_categories'),
    ('articles', 'menus_articles'), ('articles_prix_historique', 'menus_articles_prix_historique'), ('tables_salle', 'backoffice_tables_salle'),
    ('evenements', 'tracking_events'), ('commandes', 'ventes_commandes'), ('lignes_commande', 'ventes_lignes_commande'),
] %}
{% for prep, brut in paires %}
select '{{ prep }}' as table_source, (select count(*) from {{ source('raw', brut) }}) as lignes_raw,
       (select count(*) from {{ ref('prep_' ~ prep) }}) as lignes_preparation
where (select count(*) from {{ source('raw', brut) }}) <> (select count(*) from {{ ref('prep_' ~ prep) }})
{% if not loop.last %}union all{% endif %}
{% endfor %}
