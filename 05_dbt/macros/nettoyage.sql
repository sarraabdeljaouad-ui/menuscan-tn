{#- Macros de nettoyage de la couche brute (phase 4, T4.1).
    Chaque macro prend une expression SQL (souvent une colonne texte de raw) et renvoie l'expression nettoyée. -#}

{# Espaces en trop : début, fin et espaces multiples (DQ-32) #}
{% macro espaces(col) -%}
    nullif(regexp_replace(btrim({{ col }}), '\s+', ' ', 'g'), '')
{%- endmacro %}

{# Clé de comparaison d'un libellé : minuscules, sans accent, espaces normalisés #}
{% macro cle_libelle(col) -%}
    translate(lower({{ espaces(col) }}), 'àâäéèêëîïôöùûüç', 'aaaeeeeiioouuuc')
{%- endmacro %}

{# Libellé codé (statut, périodicité, type d'événement...) ramené à sa valeur de référence (DQ-32).
   La table de correspondance est le seed correspondance_libelles ; une valeur inconnue garde sa clé,
   et le test accepted_values du modèle la signale. #}
{% macro traduire(domaine, col) -%}
    coalesce(
        (select c.valeur_cible from {{ ref('correspondance_libelles') }} c
         where c.domaine = '{{ domaine }}' and c.valeur_source = {{ cle_libelle(col) }}),
        {{ cle_libelle(col) }})
{%- endmacro %}

{# Nombre au format français : virgule décimale (DQ-36) #}
{% macro decimal_fr(col) -%}
    replace({{ col }}, ',', '.')::numeric
{%- endmacro %}

{# Date au format français JJ/MM/AAAA (DQ-36) #}
{% macro date_fr(col) -%}
    to_date({{ col }}, 'DD/MM/YYYY')
{%- endmacro %}

{# Horodatage ISO ou français « JJ/MM/AAAA HH:MI » (DQ-28). Le format français n'a pas les secondes. #}
{% macro horodatage_mixte(col) -%}
    case when {{ col }} ~ '^\d{2}/\d{2}/\d{4}'
         then to_timestamp({{ col }}, 'DD/MM/YYYY HH24:MI')::timestamp
         else {{ col }}::timestamp end
{%- endmacro %}

{% macro est_date_fr(col) -%}
    ({{ col }} ~ '^\d{2}/\d{2}/\d{4}')
{%- endmacro %}

{# Horodatage UTC (« 2024-01-09T13:37:33Z ») converti en heure de Tunis (DQ-34) #}
{% macro utc_vers_tunis(col) -%}
    ({{ col }}::timestamptz at time zone '{{ var("fuseau") }}')
{%- endmacro %}

{# Montant saisi en millimes : au-dessus du seuil, il est divisé par 1 000 (DQ-33) #}
{% macro est_millimes(col) -%}
    ({{ col }}::numeric >= {{ var("seuil_millimes") }})
{%- endmacro %}

{% macro dinars(col) -%}
    case when {{ est_millimes(col) }} then {{ col }}::numeric / 1000 else {{ col }}::numeric end
{%- endmacro %}

{# Téléphone tunisien au format +216 suivi de 8 chiffres (DQ-31). Un numéro impossible à ramener reste tel quel. #}
{% macro telephone(col) -%}
    case
        when regexp_replace({{ col }}, '\D', '', 'g') ~ '^\d{8}$' then '+216' || regexp_replace({{ col }}, '\D', '', 'g')
        when regexp_replace({{ col }}, '\D', '', 'g') ~ '^00216\d{8}$' then '+' || substr(regexp_replace({{ col }}, '\D', '', 'g'), 3)
        when regexp_replace({{ col }}, '\D', '', 'g') ~ '^216\d{8}$' then '+' || regexp_replace({{ col }}, '\D', '', 'g')
        else {{ col }}
    end
{%- endmacro %}

{# Une correction tracée : objet JSON {regle, colonne, avant, apres} si la condition est vraie, sinon NULL #}
{% macro corr(regle, colonne, condition, avant, apres) -%}
    case when {{ condition }} then jsonb_build_object('regle', '{{ regle }}', 'colonne', '{{ colonne }}',
        'avant', ({{ avant }})::text, 'apres', ({{ apres }})::text) end
{%- endmacro %}

{# Liste des corrections d'une ligne : tableau JSON sans les NULL #}
{% macro corrections(liste) -%}
    coalesce((select jsonb_agg(x) from unnest(array[{{ liste | join(', ') }}]::jsonb[]) x where x is not null), '[]'::jsonb)
{%- endmacro %}

{# Correction d'un libellé : tracée seulement si la valeur change #}
{% macro corr_si_change(regle, colonne, avant, apres) -%}
    {{ corr(regle, colonne, '(' ~ avant ~ ') is distinct from (' ~ apres ~ ')', avant, apres) }}
{%- endmacro %}

{# Rang d'une ligne parmi les copies d'un même identifiant : 1 = la première reçue, les autres sont des doublons (DQ-29) #}
{% macro rang_doublon(cle) -%}
    row_number() over (partition by {{ cle }} order by _fichier, _ligne)
{%- endmacro %}

{# Date ou horodatage après la date d'arrêté des données (DQ-27) #}
{% macro apres_arrete(col) -%}
    ({{ col }} >= '{{ var("date_arrete") }}'::date + 1)
{%- endmacro %}

{# Mois du fichier mensuel d'où vient une ligne (« ventes/commandes/commandes_2026_06.csv » -> 2026-06-01) #}
{% macro mois_fichier(col) -%}
    to_date(substring({{ col }} from '(\d{4}_\d{2})'), 'YYYY_MM')
{%- endmacro %}

{# Clé de date au format entier AAAAMMJJ, utilisée par dim_date et les faits #}
{% macro date_id(col) -%}
    (to_char(({{ col }})::date, 'YYYYMMDD')::integer)
{%- endmacro %}
