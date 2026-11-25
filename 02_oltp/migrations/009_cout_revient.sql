-- MenuScan TN - migration 009 : coût de revient saisi par le gérant (lot 3, décisions D-26 et D-28)
-- Idempotente. Le coût n'existe pas dans les données générées : il reste vide tant que le gérant ne le saisit pas.
-- Aucun coût n'est inventé ici. Les taux par type de plat (hypothèses documentées) viendront en phase 4, dans un fichier à part.
SET search_path TO menuscan;

ALTER TABLE articles ADD COLUMN IF NOT EXISTS cout_revient NUMERIC(10,3) CHECK (cout_revient IS NULL OR cout_revient >= 0);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS date_maj_cout DATE;

INSERT INTO migrations (migration_id) VALUES ('009_cout_revient') ON CONFLICT DO NOTHING;
