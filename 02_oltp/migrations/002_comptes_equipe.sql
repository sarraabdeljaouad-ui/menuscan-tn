-- MenuScan TN - migration 002 : comptes de l'équipe et rôles (décision D-25, validée le 24/11/2026)
-- Idempotente. Deux comptes de démonstration par établissement : gerant.etbXXXX et serveur.etbXXXX.
-- Mot de passe de démonstration commun : Demo2026! (à ne jamais utiliser hors démonstration).
SET search_path TO menuscan;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS utilisateurs (
    utilisateur_id SERIAL PRIMARY KEY,
    identifiant VARCHAR(40) NOT NULL UNIQUE,
    etablissement_id VARCHAR(7) NOT NULL REFERENCES etablissements (etablissement_id),
    role VARCHAR(8) NOT NULL CHECK (role IN ('gerant', 'serveur')),
    prenom VARCHAR(30),
    mot_de_passe_hash TEXT NOT NULL,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    derniere_connexion TIMESTAMP
);

-- Mots de passe hachés avec bcrypt (pgcrypto), jamais stockés en clair
INSERT INTO utilisateurs (identifiant, etablissement_id, role, prenom, mot_de_passe_hash)
SELECT 'gerant.' || LOWER(etablissement_id), etablissement_id, 'gerant', gerant_prenom, crypt('Demo2026!', gen_salt('bf', 6))
FROM etablissements
ON CONFLICT (identifiant) DO NOTHING;

INSERT INTO utilisateurs (identifiant, etablissement_id, role, prenom, mot_de_passe_hash)
SELECT 'serveur.' || LOWER(etablissement_id), etablissement_id, 'serveur', 'Équipe', crypt('Demo2026!', gen_salt('bf', 6))
FROM etablissements
ON CONFLICT (identifiant) DO NOTHING;

INSERT INTO migrations (migration_id) VALUES ('002_comptes_equipe') ON CONFLICT DO NOTHING;
