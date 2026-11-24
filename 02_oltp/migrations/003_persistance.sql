-- MenuScan TN - migration 003 : état conservé après actualisation de la page (lot 0, décision D-26, validée le 24/11/2026)
-- Idempotente.
--   etats_client      : panier, langue, vue et commande d'un client, retrouvés grâce au jeton placé dans l'adresse (?s=...).
--   jetons_connexion  : connexions de l'équipe gardées 30 jours sans utilisation (cookie du navigateur).
--                       Seule l'empreinte SHA-256 du jeton est stockée : une copie de la base ne permet pas de se connecter.
SET search_path TO menuscan;

CREATE TABLE IF NOT EXISTS etats_client (
    jeton VARCHAR(40) PRIMARY KEY,
    table_id VARCHAR(8) NOT NULL REFERENCES tables_salle (table_id),
    session_id VARCHAR(10) NOT NULL REFERENCES sessions (session_id),
    panier JSONB NOT NULL DEFAULT '{}'::jsonb,
    langue VARCHAR(2) NOT NULL DEFAULT 'fr' CHECK (langue IN ('fr', 'ar')),
    vue VARCHAR(6) NOT NULL DEFAULT 'menu' CHECK (vue IN ('menu', 'panier', 'suivi')),
    commande_id VARCHAR(10) REFERENCES commandes (commande_id),
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now(),
    date_maj TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jetons_connexion (
    jeton_hash CHAR(64) PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs (utilisateur_id) ON DELETE CASCADE,
    date_creation TIMESTAMPTZ NOT NULL DEFAULT now(),
    dernier_usage TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_jetons_connexion_utilisateur ON jetons_connexion (utilisateur_id);

INSERT INTO migrations (migration_id) VALUES ('003_persistance') ON CONFLICT DO NOTHING;
