-- MenuScan TN - migration 007 : fiche article et options (lot 3, décision D-26)
-- Idempotente.
--   lignes_commande.options : options choisies par le client (ex. « Sans sucre · Lait à part »), sans effet sur le prix.
--   etats_client.options    : options en cours dans le panier du client, conservées après actualisation.
-- L'ouverture d'une fiche écrit l'événement vue_article et incrémente sessions.nb_articles_vus, comme dans les données générées.
SET search_path TO menuscan;

ALTER TABLE lignes_commande ADD COLUMN IF NOT EXISTS options VARCHAR(120);
ALTER TABLE etats_client ADD COLUMN IF NOT EXISTS options JSONB NOT NULL DEFAULT '{}'::jsonb;

INSERT INTO migrations (migration_id) VALUES ('007_fiche_article') ON CONFLICT DO NOTHING;
