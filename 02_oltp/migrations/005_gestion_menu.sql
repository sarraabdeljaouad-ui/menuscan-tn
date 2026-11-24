-- MenuScan TN - migration 005 : gestion du menu par l'équipe (lot 2, décision D-26, règle des prix : décision D-27, 24/11/2026)
-- Idempotente.
--   ruptures      : article indisponible pour une journée (signalé par le gérant ou un serveur), il disparaît du menu client.
--   journal_prix  : chaque changement de prix fait dans l'application, avec les commandes simulées recalculées (D-27).
-- Nouvelle valeur : articles_prix_historique.motif_changement = 'modification_gerant'.
SET search_path TO menuscan;

CREATE TABLE IF NOT EXISTS ruptures (
    article_id VARCHAR(9) NOT NULL REFERENCES articles (article_id),
    jour DATE NOT NULL,
    signale_par INTEGER REFERENCES utilisateurs (utilisateur_id),
    date_heure TIMESTAMP NOT NULL,
    PRIMARY KEY (article_id, jour)
);

CREATE TABLE IF NOT EXISTS journal_prix (
    journal_id SERIAL PRIMARY KEY,
    article_id VARCHAR(9) NOT NULL REFERENCES articles (article_id),
    ancien_prix NUMERIC(10,3) NOT NULL,
    nouveau_prix NUMERIC(10,3) NOT NULL,
    date_effet DATE NOT NULL,
    date_heure TIMESTAMP NOT NULL,
    utilisateur_id INTEGER REFERENCES utilisateurs (utilisateur_id),
    lignes_recalculees INTEGER NOT NULL DEFAULT 0,
    commandes_recalculees INTEGER NOT NULL DEFAULT 0
);

INSERT INTO migrations (migration_id) VALUES ('005_gestion_menu') ON CONFLICT DO NOTHING;
