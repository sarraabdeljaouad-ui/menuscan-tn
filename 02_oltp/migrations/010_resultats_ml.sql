-- MenuScan TN - migration 010 : résultats de la phase 7 dans l'application (T8.1, exigence EF-14)
-- Idempotente. Les résultats viennent du schéma ml de l'entrepôt, copiés par 02_oltp/copier_resultats_ml.py :
-- l'application ne lit jamais l'entrepôt directement.
SET search_path TO menuscan;

-- Rôle « menuscan » (équipe Succès client de MenuScan) : compte rattaché à aucun établissement
ALTER TABLE utilisateurs ALTER COLUMN etablissement_id DROP NOT NULL;
ALTER TABLE utilisateurs DROP CONSTRAINT IF EXISTS utilisateurs_role_check;
ALTER TABLE utilisateurs ADD CONSTRAINT utilisateurs_role_check CHECK (role IN ('gerant', 'serveur', 'menuscan'));
ALTER TABLE utilisateurs DROP CONSTRAINT IF EXISTS utilisateurs_role_etablissement;
ALTER TABLE utilisateurs ADD CONSTRAINT utilisateurs_role_etablissement
    CHECK ((role = 'menuscan' AND etablissement_id IS NULL) OR (role <> 'menuscan' AND etablissement_id IS NOT NULL));

INSERT INTO utilisateurs (identifiant, etablissement_id, role, prenom, mot_de_passe_hash)
VALUES ('succes.client', NULL, 'menuscan', 'Succès client', crypt('Demo2026!', gen_salt('bf', 6)))
ON CONFLICT (identifiant) DO NOTHING;

-- Scores de résiliation (K19) au dernier mois de données, avec le MRR du mois pour chiffrer le MRR menacé
CREATE TABLE IF NOT EXISTS ml_score_resiliation (
    etablissement_id VARCHAR(7) PRIMARY KEY REFERENCES etablissements (etablissement_id),
    mois_observe DATE NOT NULL,
    probabilite NUMERIC(7, 5) NOT NULL CHECK (probabilite BETWEEN 0 AND 1),
    rang INTEGER NOT NULL,
    alerte BOOLEAN NOT NULL,
    facteur_1 TEXT,
    facteur_2 TEXT,
    facteur_3 TEXT,
    mrr_ht NUMERIC(10, 3),
    version_modele TEXT NOT NULL,
    publie_le TIMESTAMP NOT NULL
);

-- Candidats au passage de la formule Essentiel à la formule Commande (EF-13)
CREATE TABLE IF NOT EXISTS ml_candidat_commande (
    etablissement_id VARCHAR(7) PRIMARY KEY REFERENCES etablissements (etablissement_id),
    sessions_table_jour_3m NUMERIC(8, 4) NOT NULL,
    seuil_usage NUMERIC(8, 4) NOT NULL,
    probabilite_resiliation NUMERIC(7, 5),
    publie_le TIMESTAMP NOT NULL
);

-- Plats recommandés (EF-12) : jusqu'à 3 plats « souvent pris avec » chaque plat de la carte, formule Pro
CREATE TABLE IF NOT EXISTS ml_recommandation_plat (
    etablissement_id VARCHAR(7) NOT NULL REFERENCES etablissements (etablissement_id),
    plat TEXT NOT NULL,
    rang INTEGER NOT NULL CHECK (rang BETWEEN 1 AND 3),
    plat_recommande TEXT NOT NULL,
    motif TEXT NOT NULL,
    publie_le TIMESTAMP NOT NULL,
    PRIMARY KEY (etablissement_id, plat, rang)
);

-- Journal des copies : une ligne par table et par copie
CREATE TABLE IF NOT EXISTS ml_copie (
    copie_id SERIAL PRIMARY KEY,
    copie_le TIMESTAMP NOT NULL,
    publie_le TIMESTAMP NOT NULL,
    nom_table TEXT NOT NULL,
    lignes INTEGER NOT NULL
);

INSERT INTO migrations (migration_id) VALUES ('010_resultats_ml') ON CONFLICT DO NOTHING;
