-- MenuScan TN - migration 006 : gestion des tables par le gérant (lot 2, décision D-26)
-- Idempotente.
--   tables_salle.date_retrait : table retirée du service à cette date (son QR code ne s'ouvre plus).
--   La table n'est jamais supprimée : ses sessions et ses commandes restent dans l'historique.
SET search_path TO menuscan;

ALTER TABLE tables_salle ADD COLUMN IF NOT EXISTS date_retrait DATE;

INSERT INTO migrations (migration_id) VALUES ('006_gestion_tables') ON CONFLICT DO NOTHING;
