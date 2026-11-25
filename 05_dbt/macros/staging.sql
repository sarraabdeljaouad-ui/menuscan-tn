{#- Modèle staging : les lignes de la préparation qui n'ont été rejetées par aucune règle.
    Les colonnes de contrôle (_corrections, _regle_rejet, _motif_rejet) restent dans la préparation ;
    _fichier et _ligne sont gardées pour retrouver l'origine de chaque ligne. -#}
{% macro staging_depuis(preparation) -%}
    {%- set colonnes = adapter.get_columns_in_relation(ref(preparation)) -%}
    {%- set gardees = [] -%}
    {%- for c in colonnes if c.name not in ('_corrections', '_regle_rejet', '_motif_rejet') -%}
        {%- do gardees.append(adapter.quote(c.name) if c.name == 'date' else c.name) -%}
    {%- endfor %}
select {{ gardees | join(', ') if gardees else '*' }}
from {{ ref(preparation) }}
where _regle_rejet is null
{%- endmacro %}

{#- Liste des préparations et de leur identifiant : sert à la quarantaine et au journal des corrections -#}
{% macro preparations() -%}
    {{ return([
        ('dim_calendrier', 'date'), ('ref_villes', 'ville_id'), ('formules', 'formule_id'),
        ('canaux_acquisition', 'canal_id'), ('campagnes_marketing', 'campagne_id'),
        ('marketing_depenses_quotidiennes', 'depense_id'), ('prospects', 'prospect_id'),
        ('etablissements', 'etablissement_id'), ('abonnements', 'abonnement_id'), ('factures', 'facture_id'),
        ('paiements', 'paiement_id'), ('tickets_support', 'ticket_id'), ('categories_menu', 'categorie_id'),
        ('articles', 'article_id'), ('articles_prix_historique', 'prix_id'), ('tables_salle', 'table_id'),
        ('evenements', 'evenement_id'), ('commandes', 'commande_id'), ('lignes_commande', 'ligne_id'),
    ]) }}
{%- endmacro %}
