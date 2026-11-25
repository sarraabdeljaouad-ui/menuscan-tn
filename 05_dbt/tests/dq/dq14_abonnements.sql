-- DQ-14 : abonnements contigus, sans chevauchement, le premier commence à la mise en service, le dernier finit à la résiliation.
with a as (
    select *, lag(date_fin) over (partition by etablissement_id order by date_debut) as fin_precedente,
           row_number() over (partition by etablissement_id order by date_debut) as rang,
           row_number() over (partition by etablissement_id order by date_debut desc) as rang_inverse
    from {{ ref('stg_abonnements') }}
)
select a.abonnement_id from a join {{ ref('dim_etablissement') }} e using (etablissement_id)
where (a.rang > 1 and a.date_debut <> a.fin_precedente + 1)
   or (a.rang = 1 and a.date_debut <> e.date_mise_en_service)
   or (a.rang_inverse = 1 and a.date_fin is distinct from e.date_resiliation and a.date_debut <= '{{ var("date_arrete") }}')
