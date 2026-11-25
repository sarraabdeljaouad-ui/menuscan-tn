-- DQ-15 : net = HT - remise, TVA = 19 % du net (arrondi au millime), TTC = net + TVA.
select facture_id from {{ ref('fait_facturation') }}
where abs(montant_net_ht - (montant_ht - remise_ht)) > 0.001 or abs(montant_tva - round(montant_net_ht * 0.19, 3)) > 0.001
   or abs(montant_ttc - (montant_net_ht + montant_tva)) > 0.001
