-- DQ-17 : pas de facture d'abonnement le mois de mise en service ni après la résiliation.
select f.facture_id from {{ ref('fait_facturation') }} f join {{ ref('dim_etablissement') }} e using (etablissement_id)
where f.type_facture in ('abonnement_mensuel', 'abonnement_annuel')
  and (date_trunc('month', f.periode_debut) = date_trunc('month', e.date_mise_en_service)
       or (e.date_resiliation is not null and f.periode_debut > e.date_resiliation))
