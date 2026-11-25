-- Lignes de commande. Source : ventes/lignes_commande/lignes_commande_AAAA_MM.csv (36 fichiers)
-- Corrections : prix unitaire en millimes (DQ-33), montant de ligne recalculé = prix x quantité (DQ-04).
-- Quarantaine : article ou commande inconnus (DQ-02), quantité nulle ou négative (DQ-05).
with source as (
    select *, {{ rang_doublon('ligne_id') }} as _rang from {{ source('raw', 'ventes_lignes_commande') }}
),
typee as (
    select
        s.ligne_id, s.commande_id, s.article_id, s.quantite::smallint as quantite,
        {{ dinars('s.prix_unitaire_ttc') }}::numeric(10, 3) as prix_unitaire_ttc, s.montant_ligne_ttc::numeric(10, 3) as _montant_brut,
        s.prix_unitaire_ttc as _prix_brut, s._fichier, s._ligne, s._rang
    from source s
),
controlee as (
    select t.*, (t.prix_unitaire_ttc * t.quantite)::numeric(10, 3) as montant_ligne_ttc,
           a.article_id as _article_connu, c.commande_id as _commande_connue
    from typee t
    left join {{ ref('prep_articles') }} a on a.article_id = t.article_id and a._regle_rejet is null
    left join {{ ref('prep_commandes') }} c on c.commande_id = t.commande_id and c._regle_rejet is null
)
select
    ligne_id, commande_id, article_id, quantite, prix_unitaire_ttc, montant_ligne_ttc,
    _fichier, _ligne,
    {{ corrections([
        corr('DQ-33', 'prix_unitaire_ttc', est_millimes('_prix_brut'), '_prix_brut', 'prix_unitaire_ttc'),
        corr('DQ-04', 'montant_ligne_ttc', 'abs(_montant_brut - montant_ligne_ttc) > 0.001', '_montant_brut', 'montant_ligne_ttc'),
    ]) }} as _corrections,
    {{ rejet('ligne_id', [
        ['DQ-02', '_commande_connue is null', 'commande inconnue'],
        ['DQ-02', '_article_connu is null', 'article inconnu'],
        ['DQ-05', 'quantite <= 0', 'quantité nulle ou négative'],
    ]) }}
from controlee
