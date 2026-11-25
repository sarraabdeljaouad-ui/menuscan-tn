-- DQ-02 : toute clé étrangère existe dans la table référencée (compléments aux tests relationships des modèles).
select 'evenements.session_id' as objet, e.evenement_id as identifiant from {{ ref('int_evenements') }} e left join {{ ref('fait_session') }} s using (session_id) where s.session_id is null
union all
select 'prospects.etablissement_id', p.prospect_id from {{ ref('fait_prospect') }} p left join {{ ref('dim_etablissement') }} e using (etablissement_id) where p.etablissement_id is not null and e.etablissement_id is null
union all
select 'factures.abonnement_id', f.facture_id from {{ ref('fait_facturation') }} f left join {{ ref('stg_abonnements') }} a using (abonnement_id) where f.abonnement_id is not null and a.abonnement_id is null
