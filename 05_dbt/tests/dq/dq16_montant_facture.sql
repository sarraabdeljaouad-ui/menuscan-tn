-- DQ-16 : montant HT d'une facture d'abonnement = prix de la formule en vigueur (x 10 en annuel).
select f.facture_id from {{ ref('fait_facturation') }} f join {{ ref('stg_abonnements') }} a using (abonnement_id)
where f.type_facture in ('abonnement_mensuel', 'abonnement_annuel')
  and abs(f.montant_ht - a.prix_mensuel_ht * case when f.type_facture = 'abonnement_annuel' then 10 else 1 end) > 0.001
