-- MenuScan TN - migration 008 : avis des clients après le service (lot 3, décision D-26)
-- Idempotente. Un avis au plus par commande servie : note de 1 à 5, commentaire facultatif.
SET search_path TO menuscan;

CREATE TABLE IF NOT EXISTS avis (
    commande_id VARCHAR(10) PRIMARY KEY REFERENCES commandes (commande_id),
    etablissement_id VARCHAR(7) NOT NULL REFERENCES etablissements (etablissement_id),
    table_id VARCHAR(8) NOT NULL REFERENCES tables_salle (table_id),
    note SMALLINT NOT NULL CHECK (note BETWEEN 1 AND 5),
    commentaire VARCHAR(300),
    date_heure TIMESTAMP NOT NULL
);

INSERT INTO migrations (migration_id) VALUES ('008_avis') ON CONFLICT DO NOTHING;
