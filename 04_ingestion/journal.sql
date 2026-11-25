-- MenuScan TN - phase 3 : schéma raw de menuscan_dwh, journal des chargements et rejets. Idempotent.
CREATE SCHEMA IF NOT EXISTS raw;

CREATE SEQUENCE IF NOT EXISTS raw.seq_lot;

-- Un enregistrement par fichier et par lancement de ingerer.py
CREATE TABLE IF NOT EXISTS raw.chargements (
    chargement_id BIGSERIAL PRIMARY KEY,
    lot_id BIGINT NOT NULL,
    fichier TEXT NOT NULL,                 -- chemin relatif à donnees_brutes/
    table_cible TEXT NOT NULL,
    format TEXT NOT NULL,
    empreinte_sha256 CHAR(64) NOT NULL,
    octets BIGINT NOT NULL,
    lignes_lues INTEGER,                   -- enregistrements lus dans le fichier (hors en-tête)
    lignes_ecrites INTEGER,                -- lignes insérées dans la table cible
    lignes_rejetees INTEGER,               -- lignes envoyées dans raw.rejets
    debut TIMESTAMPTZ NOT NULL,
    fin TIMESTAMPTZ,
    duree_s NUMERIC(10, 3),
    statut TEXT NOT NULL CHECK (statut IN ('charge', 'recharge', 'deja_charge', 'echec')),
    message TEXT
);
CREATE INDEX IF NOT EXISTS ix_chargements_fichier ON raw.chargements (fichier, empreinte_sha256);

-- Lignes illisibles (nombre de colonnes inattendu, JSON invalide) : gardées telles quelles, jamais perdues
CREATE TABLE IF NOT EXISTS raw.rejets (
    rejet_id BIGSERIAL PRIMARY KEY,
    lot_id BIGINT NOT NULL,
    fichier TEXT NOT NULL,
    ligne INTEGER NOT NULL,
    motif TEXT NOT NULL,
    contenu TEXT,
    date_rejet TIMESTAMPTZ NOT NULL DEFAULT now()
);
