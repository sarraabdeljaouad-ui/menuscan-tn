-- Doublons métier d'établissement (DQ-30) : même nom normalisé et même téléphone normalisé.
-- Décision tracée : l'identifiant gardé est celui qui porte le plus d'abonnements, puis le plus petit ;
-- les autres lui sont rattachés. Une ligne par identifiant fusionné.
with abonnements as (
    select etablissement_id, count(*) as nb from {{ ref('stg_abonnements') }} group by 1
),
groupes as (
    select e.etablissement_id, lower(e.nom_etablissement) as cle_nom, e.telephone, coalesce(a.nb, 0) as nb_abonnements
    from {{ ref('stg_etablissements') }} e
    left join abonnements a on a.etablissement_id = e.etablissement_id
    where e.telephone is not null
),
classement as (
    select *,
        first_value(etablissement_id) over (partition by cle_nom, telephone order by nb_abonnements desc, etablissement_id) as identifiant_garde,
        count(*) over (partition by cle_nom, telephone) as taille
    from groupes
)
select
    etablissement_id as ancien_id,
    identifiant_garde as nouvel_id,
    'DQ-30' as regle_dq,
    'même nom normalisé et même téléphone que ' || identifiant_garde
        || ' ; ' || nb_abonnements || ' abonnement(s) sur l''identifiant fusionné' as motif
from classement
where taille > 1 and etablissement_id <> identifiant_garde
