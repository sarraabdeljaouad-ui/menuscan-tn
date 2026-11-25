-- DQ-19 : statut de facture cohérent avec les paiements.
select facture_id, statut_facture, montant_encaisse_ttc, jours_retard from {{ ref('fait_facturation') }}
where (statut_facture = 'payee' and (montant_encaisse_ttc = 0 or jours_retard > 0))
   or (statut_facture = 'payee_en_retard' and (montant_encaisse_ttc = 0 or jours_retard = 0))
   or (statut_facture in ('impayee', 'en_attente') and montant_encaisse_ttc > 0)
   or (statut_facture = 'soldee_par_remise' and montant_ttc > 0)
