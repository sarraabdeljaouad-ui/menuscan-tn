-- MenuScan TN - migration 004 : service en salle (lot 1, décision D-26, validée le 24/11/2026)
-- Idempotente.
--   appels                       : appels des clients (motif, heure, prise en charge par un compte de l'équipe).
--                                  L'événement appel_serveur reste écrit dans evenements, comme dans les données générées.
--   commandes.date_heure_reglement : heure de l'encaissement. Une commande servie sans règlement est « à encaisser ».
--                                  Les commandes servies existantes ont toutes un mode de règlement : leur heure
--                                  d'encaissement est fixée à leur heure de service.
--   etats_client.commandes       : toutes les commandes passées par un client pendant sa visite (une par session, DQ-12).
SET search_path TO menuscan;

CREATE TABLE IF NOT EXISTS appels (
    appel_id SERIAL PRIMARY KEY,
    etablissement_id VARCHAR(7) NOT NULL REFERENCES etablissements (etablissement_id),
    table_id VARCHAR(8) NOT NULL REFERENCES tables_salle (table_id),
    session_id VARCHAR(10) NOT NULL REFERENCES sessions (session_id),
    motif VARCHAR(8) NOT NULL CHECK (motif IN ('serveur', 'addition', 'eau')),
    date_heure_appel TIMESTAMP NOT NULL,
    date_heure_prise TIMESTAMP,
    pris_par INTEGER REFERENCES utilisateurs (utilisateur_id)
);
CREATE INDEX IF NOT EXISTS ix_appels_attente ON appels (etablissement_id) WHERE date_heure_prise IS NULL;

ALTER TABLE commandes ADD COLUMN IF NOT EXISTS date_heure_reglement TIMESTAMP;
UPDATE commandes SET date_heure_reglement = date_heure_service
WHERE statut_commande = 'servie' AND mode_reglement IS NOT NULL AND date_heure_reglement IS NULL;

ALTER TABLE etats_client ADD COLUMN IF NOT EXISTS commandes VARCHAR(10)[] NOT NULL DEFAULT '{}';
UPDATE etats_client SET commandes = ARRAY[commande_id] WHERE commande_id IS NOT NULL AND commandes = '{}';

INSERT INTO migrations (migration_id) VALUES ('004_service_salle') ON CONFLICT DO NOTHING;
