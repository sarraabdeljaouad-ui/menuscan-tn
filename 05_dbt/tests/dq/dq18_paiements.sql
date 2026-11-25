-- DQ-18 : au plus un paiement réussi par facture, montant = TTC, date >= émission (paiements réussis).
select p.facture_id from {{ ref('stg_paiements') }} p join {{ ref('fait_facturation') }} f using (facture_id)
where p.statut_paiement = 'reussi'
group by p.facture_id, f.montant_ttc, f.date_emission
having count(*) > 1 or max(abs(p.montant_ttc - f.montant_ttc)) > 0.001 or min(p.date_paiement::date) < f.date_emission
