-- Articles des menus. Source : menus/articles.csv. Correction : nom du plat (DQ-32).
with source as (
    select *, {{ rang_doublon('article_id') }} as _rang from {{ source('raw', 'menus_articles') }}
),
nettoyee as (
    select
        s.article_id, s.etablissement_id, s.categorie_id,
        coalesce(n.nom_canonique, {{ espaces('s.nom_article') }}) as nom_article,
        s.date_ajout::date as date_ajout, s.date_retrait::date as date_retrait,
        {{ dinars('s.prix_actuel_ttc') }}::numeric(10, 3) as prix_actuel_ttc, s.statut_article,
        s.nom_article as _nom_brut, s.prix_actuel_ttc as _prix_brut, s._fichier, s._ligne, s._rang
    from source s
    left join {{ ref('prep_noms_articles') }} n on n.cle = {{ cle_libelle('s.nom_article') }}
)
select
    article_id, etablissement_id, categorie_id, nom_article, date_ajout, date_retrait, prix_actuel_ttc, statut_article,
    _fichier, _ligne,
    {{ corrections([
        corr_si_change('DQ-32', 'nom_article', '_nom_brut', 'nom_article'),
        corr('DQ-33', 'prix_actuel_ttc', est_millimes('_prix_brut'), '_prix_brut', 'prix_actuel_ttc'),
    ]) }} as _corrections,
    {{ rejet('article_id') }}
from nettoyee
