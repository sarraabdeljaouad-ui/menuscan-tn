/* MenuScan TN - contrôles de qualité sur la couche de référence (schéma menuscan, PostgreSQL).
   Chaque requête renvoie le nombre de violations : 0 attendu partout.
   Les identifiants de règle renvoient à docs/regles_qualite.md. */
SET search_path TO menuscan;

-- DQ-01 Unicité des clés primaires (échantillon des tables principales)
SELECT 'DQ-01' AS regle, 'commandes' AS objet, COUNT(*) - COUNT(DISTINCT commande_id) AS violations FROM commandes
UNION ALL SELECT 'DQ-01', 'lignes_commande', COUNT(*) - COUNT(DISTINCT ligne_id) FROM lignes_commande
UNION ALL SELECT 'DQ-01', 'sessions', COUNT(*) - COUNT(DISTINCT session_id) FROM sessions
UNION ALL SELECT 'DQ-01', 'evenements', COUNT(*) - COUNT(DISTINCT evenement_id) FROM evenements
UNION ALL SELECT 'DQ-01', 'factures', COUNT(*) - COUNT(DISTINCT facture_id) FROM factures

-- DQ-02 Intégrité référentielle (clés sans parent)
UNION ALL SELECT 'DQ-02', 'lignes_commande.article_id', COUNT(*) FROM lignes_commande l
          WHERE NOT EXISTS (SELECT 1 FROM articles a WHERE a.article_id = l.article_id)
UNION ALL SELECT 'DQ-02', 'evenements.session_id', COUNT(*) FROM evenements e
          WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = e.session_id)
UNION ALL SELECT 'DQ-02', 'prospects.etablissement_id', COUNT(*) FROM prospects p
          WHERE p.etablissement_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM etablissements e WHERE e.etablissement_id = p.etablissement_id)

-- DQ-03 Montant commande = somme des lignes , nb_lignes et nb_articles
UNION ALL SELECT 'DQ-03', 'commandes', COUNT(*) FROM commandes c
          JOIN (SELECT commande_id, SUM(montant_ligne_ttc) AS s, COUNT(*) AS n, SUM(quantite) AS q
                FROM lignes_commande GROUP BY commande_id) l USING (commande_id)
          WHERE ABS(c.montant_total_ttc - l.s) > 0.0015 OR c.nb_lignes <> l.n OR c.nb_articles <> l.q

-- DQ-04 Montant de ligne = prix unitaire x quantité , DQ-05 quantités > 0
UNION ALL SELECT 'DQ-04', 'lignes_commande', COUNT(*) FROM lignes_commande
          WHERE ABS(montant_ligne_ttc - prix_unitaire_ttc * quantite) > 0.0015
UNION ALL SELECT 'DQ-05', 'lignes_commande', COUNT(*) FROM lignes_commande WHERE quantite <= 0

-- DQ-06 Prix unitaire = prix en vigueur le jour de la commande
UNION ALL SELECT 'DQ-06', 'lignes_commande', COUNT(*) FROM lignes_commande l
          JOIN commandes c USING (commande_id)
          JOIN articles_prix_historique p ON p.article_id = l.article_id
           AND CAST(c.date_heure_commande AS DATE) BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')
          WHERE ABS(p.prix_ttc - l.prix_unitaire_ttc) > 0.0005

-- DQ-09 Commande uniquement sous formule Commande ou Pro
UNION ALL SELECT 'DQ-09', 'commandes', COUNT(*) FROM commandes c
          JOIN abonnements a ON a.etablissement_id = c.etablissement_id
           AND CAST(c.date_heure_commande AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
          WHERE a.formule_id NOT IN ('FRM02', 'FRM03')

-- DQ-11 Événements dans la fenêtre de leur session
UNION ALL SELECT 'DQ-11', 'evenements', COUNT(*) FROM evenements e JOIN sessions s USING (session_id)
          WHERE e.horodatage < s.debut_session OR e.horodatage > s.fin_session

-- DQ-12 Au plus une commande par session , a_commande cohérent
UNION ALL SELECT 'DQ-12', 'sessions', COUNT(*) FROM sessions s
          LEFT JOIN (SELECT session_id, COUNT(*) AS n FROM commandes GROUP BY session_id) c USING (session_id)
          WHERE COALESCE(c.n, 0) > 1 OR (s.a_commande <> (COALESCE(c.n, 0) = 1))

-- DQ-14 Abonnements contigus (début = veille + 1 de la période précédente)
UNION ALL SELECT 'DQ-14', 'abonnements', COUNT(*) FROM (
            SELECT date_debut, LAG(date_fin) OVER (PARTITION BY etablissement_id ORDER BY date_debut) AS fin_prec
            FROM abonnements) x
          WHERE fin_prec IS NOT NULL AND date_debut <> fin_prec + 1

-- DQ-15 Montants de facture
UNION ALL SELECT 'DQ-15', 'factures', COUNT(*) FROM factures
          WHERE ABS(montant_net_ht - (montant_ht - remise_ht)) > 0.0015
             OR ABS(montant_tva - ROUND(montant_net_ht * 0.19, 3)) > 0.0015
             OR ABS(montant_ttc - (montant_net_ht + montant_tva)) > 0.0015

-- DQ-18 Au plus un paiement réussi par facture, montant = TTC
UNION ALL SELECT 'DQ-18', 'paiements', COUNT(*) FROM (
            SELECT p.facture_id, COUNT(*) AS n, MAX(ABS(p.montant_ttc - f.montant_ttc)) AS ecart
            FROM paiements p JOIN factures f USING (facture_id)
            WHERE p.statut_paiement = 'reussi' GROUP BY p.facture_id) x
          WHERE n > 1 OR ecart > 0.0015

-- DQ-21 Prospect converti <=> établissement , conversion = signature
UNION ALL SELECT 'DQ-21', 'prospects', COUNT(*) FROM prospects p
          LEFT JOIN etablissements e ON e.etablissement_id = p.etablissement_id
          WHERE (p.statut_prospect = 'converti') <> (p.etablissement_id IS NOT NULL)
             OR (p.statut_prospect = 'converti' AND (p.date_conversion <> e.date_signature OR p.date_contact > p.date_conversion))

-- DQ-23 Clics <= impressions, dépense >= 0
UNION ALL SELECT 'DQ-23', 'marketing_depenses_quotidiennes', COUNT(*) FROM marketing_depenses_quotidiennes
          WHERE COALESCE(clics, 0) > COALESCE(impressions, 0) OR depense_ttc < 0

-- DQ-24 Un seul prix en vigueur par article
UNION ALL SELECT 'DQ-24', 'articles_prix_historique', COUNT(*) FROM (
            SELECT article_id FROM articles_prix_historique WHERE date_fin IS NULL GROUP BY article_id HAVING COUNT(*) <> 1) x

-- DQ-26 Anglais uniquement en formule Pro
UNION ALL SELECT 'DQ-26', 'sessions', COUNT(*) FROM sessions s
          JOIN abonnements a ON a.etablissement_id = s.etablissement_id
           AND CAST(s.debut_session AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
          WHERE s.langue = 'en' AND a.formule_id <> 'FRM03'

-- DQ-27 Aucun événement après l'arrêté ni pendant la panne du 12/09/2025
UNION ALL SELECT 'DQ-27', 'evenements', COUNT(*) FROM evenements
          WHERE horodatage > TIMESTAMP '2026-12-31 23:59:59'
             OR (horodatage >= TIMESTAMP '2025-09-12 10:00:00' AND horodatage < TIMESTAMP '2025-09-12 16:00:00');
