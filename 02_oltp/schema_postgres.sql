-- MenuScan TN - schéma PostgreSQL de la couche de référence (généré par generateur/gen_part5_export.py)
CREATE SCHEMA IF NOT EXISTS menuscan;
SET search_path TO menuscan;

-- Dimension date du 01/01/2024 au 31/12/2026, reprise du référentiel TuniShop (jours fériés tunisiens, Ramadan), avec périodes d'activité propres à la restauration. (1 ligne = 1 jour)
CREATE TABLE dim_calendrier (
    date DATE NOT NULL,
    annee SMALLINT,
    trimestre SMALLINT,
    mois SMALLINT,
    nom_mois VARCHAR(12),
    semaine_iso SMALLINT,
    jour_semaine SMALLINT,
    nom_jour VARCHAR(10),
    est_weekend BOOLEAN,
    est_jour_ferie BOOLEAN,
    nom_jour_ferie VARCHAR(60),
    est_ramadan BOOLEAN,
    periode_activite VARCHAR(15),
    CONSTRAINT pk_dim_calendrier PRIMARY KEY (date)
);

-- Villes couvertes par MenuScan, avec date d'ouverture commerciale. (1 ligne = 1 ville)
CREATE TABLE ref_villes (
    ville_id CHAR(3) NOT NULL,
    ville VARCHAR(40),
    gouvernorat VARCHAR(30),
    region VARCHAR(20),
    est_cotiere BOOLEAN,
    poids_marche NUMERIC(4,2),
    date_ouverture_commerciale DATE,
    CONSTRAINT pk_ref_villes PRIMARY KEY (ville_id)
);

-- Formules d'abonnement (prix simulés, voir README). (1 ligne = 1 formule)
CREATE TABLE formules (
    formule_id CHAR(5) NOT NULL,
    nom_formule VARCHAR(20),
    prix_mensuel_ht NUMERIC(10,3),
    inclut_commande BOOLEAN,
    inclut_statistiques BOOLEAN,
    description VARCHAR(200),
    prix_annuel_ht NUMERIC(10,3),
    frais_mise_en_place_ht NUMERIC(10,3),
    CONSTRAINT pk_formules PRIMARY KEY (formule_id)
);

-- Canaux d'acquisition des établissements clients. (1 ligne = 1 canal)
CREATE TABLE canaux_acquisition (
    canal_id CHAR(5) NOT NULL,
    nom_canal VARCHAR(40),
    type_canal VARCHAR(20),
    taux_conversion_cible NUMERIC(4,2),
    CONSTRAINT pk_canaux_acquisition PRIMARY KEY (canal_id)
);

-- Campagnes marketing (publicité en ligne, tournées terrain, parrainage, salons , noms fictifs). (1 ligne = 1 campagne)
CREATE TABLE campagnes_marketing (
    campagne_id VARCHAR(6) NOT NULL,
    canal_id CHAR(5),
    nom_campagne VARCHAR(80),
    date_debut DATE,
    date_fin DATE,
    budget_prevu NUMERIC(10,3),
    ville_id_cible CHAR(3),
    CONSTRAINT pk_campagnes_marketing PRIMARY KEY (campagne_id),
    CONSTRAINT fk_campagnes_marketing_canal_id FOREIGN KEY (canal_id) REFERENCES canaux_acquisition(canal_id),
    CONSTRAINT fk_campagnes_marketing_ville_id_cible FOREIGN KEY (ville_id_cible) REFERENCES ref_villes(ville_id)
);

-- Dépenses et résultats marketing par campagne et par jour. (1 ligne = 1 campagne x 1 jour)
CREATE TABLE marketing_depenses_quotidiennes (
    depense_id VARCHAR(8) NOT NULL,
    campagne_id VARCHAR(6),
    date DATE,
    depense_ttc NUMERIC(10,3),
    impressions INTEGER,
    clics INTEGER,
    nb_prospects INTEGER,
    CONSTRAINT pk_marketing_depenses_quotidiennes PRIMARY KEY (depense_id),
    CONSTRAINT fk_marketing_depenses_quotidiennes_campagne_id FOREIGN KEY (campagne_id) REFERENCES campagnes_marketing(campagne_id)
);

-- Prospects (cafés et restaurants démarchés), convertis ou non. Données fictives. (1 ligne = 1 prospect)
CREATE TABLE prospects (
    prospect_id VARCHAR(8) NOT NULL,
    date_contact DATE,
    canal_id CHAR(5),
    campagne_id VARCHAR(6),
    ville_id CHAR(3),
    type_etablissement VARCHAR(15),
    nom_etablissement VARCHAR(60),
    telephone VARCHAR(12),
    statut_prospect VARCHAR(10),
    date_conversion DATE,
    etablissement_id VARCHAR(7),
    parrain_etablissement_id VARCHAR(7),
    motif_perte VARCHAR(30),
    CONSTRAINT pk_prospects PRIMARY KEY (prospect_id),
    CONSTRAINT fk_prospects_canal_id FOREIGN KEY (canal_id) REFERENCES canaux_acquisition(canal_id),
    CONSTRAINT fk_prospects_campagne_id FOREIGN KEY (campagne_id) REFERENCES campagnes_marketing(campagne_id),
    CONSTRAINT fk_prospects_ville_id FOREIGN KEY (ville_id) REFERENCES ref_villes(ville_id)
);

-- Établissements clients de MenuScan (cafés, salons de thé, restaurants, snacks). Noms et personnes fictifs. (1 ligne = 1 établissement)
CREATE TABLE etablissements (
    etablissement_id VARCHAR(7) NOT NULL,
    nom_etablissement VARCHAR(60),
    type_etablissement VARCHAR(15),
    ville_id CHAR(3),
    gerant_prenom VARCHAR(30),
    gerant_nom VARCHAR(30),
    telephone VARCHAR(12),
    email VARCHAR(80),
    canal_id CHAR(5),
    campagne_id VARCHAR(6),
    prospect_id VARCHAR(8),
    date_signature DATE,
    date_mise_en_service DATE,
    nb_tables SMALLINT,
    formule_initiale_id CHAR(5),
    formule_actuelle_id CHAR(5),
    periodicite_facturation VARCHAR(10),
    statut_etablissement VARCHAR(8),
    date_resiliation DATE,
    motif_resiliation VARCHAR(40),
    CONSTRAINT pk_etablissements PRIMARY KEY (etablissement_id),
    CONSTRAINT fk_etablissements_ville_id FOREIGN KEY (ville_id) REFERENCES ref_villes(ville_id),
    CONSTRAINT fk_etablissements_canal_id FOREIGN KEY (canal_id) REFERENCES canaux_acquisition(canal_id),
    CONSTRAINT fk_etablissements_campagne_id FOREIGN KEY (campagne_id) REFERENCES campagnes_marketing(campagne_id),
    CONSTRAINT fk_etablissements_prospect_id FOREIGN KEY (prospect_id) REFERENCES prospects(prospect_id),
    CONSTRAINT fk_etablissements_formule_initiale_id FOREIGN KEY (formule_initiale_id) REFERENCES formules(formule_id),
    CONSTRAINT fk_etablissements_formule_actuelle_id FOREIGN KEY (formule_actuelle_id) REFERENCES formules(formule_id)
);

-- Périodes d'abonnement : une ligne par formule successive (SCD2 de l'abonnement). (1 ligne = 1 établissement x 1 formule x 1 période)
CREATE TABLE abonnements (
    abonnement_id VARCHAR(8) NOT NULL,
    etablissement_id VARCHAR(7),
    formule_id CHAR(5),
    date_debut DATE,
    date_fin DATE,
    periodicite VARCHAR(10),
    prix_mensuel_ht NUMERIC(10,3),
    type_mouvement VARCHAR(15),
    motif_fin VARCHAR(20),
    CONSTRAINT pk_abonnements PRIMARY KEY (abonnement_id),
    CONSTRAINT fk_abonnements_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id),
    CONSTRAINT fk_abonnements_formule_id FOREIGN KEY (formule_id) REFERENCES formules(formule_id)
);

-- Factures émises par MenuScan : mise en place, abonnements mensuels et annuels. (1 ligne = 1 facture)
CREATE TABLE factures (
    facture_id VARCHAR(9) NOT NULL,
    etablissement_id VARCHAR(7),
    abonnement_id VARCHAR(8),
    type_facture VARCHAR(20),
    periode_debut DATE,
    periode_fin DATE,
    date_emission DATE,
    montant_ht NUMERIC(10,3),
    remise_ht NUMERIC(10,3),
    motif_remise VARCHAR(30),
    montant_net_ht NUMERIC(10,3),
    montant_tva NUMERIC(10,3),
    montant_ttc NUMERIC(10,3),
    date_echeance DATE,
    statut_facture VARCHAR(20),
    CONSTRAINT pk_factures PRIMARY KEY (facture_id),
    CONSTRAINT fk_factures_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id),
    CONSTRAINT fk_factures_abonnement_id FOREIGN KEY (abonnement_id) REFERENCES abonnements(abonnement_id)
);

-- Encaissements et tentatives de paiement des factures. (1 ligne = 1 tentative ou 1 encaissement)
CREATE TABLE paiements (
    paiement_id VARCHAR(9) NOT NULL,
    facture_id VARCHAR(9),
    etablissement_id VARCHAR(7),
    date_paiement TIMESTAMP,
    mode_paiement VARCHAR(16),
    montant_ttc NUMERIC(10,3),
    statut_paiement VARCHAR(7),
    code_erreur VARCHAR(20),
    numero_tentative SMALLINT,
    CONSTRAINT pk_paiements PRIMARY KEY (paiement_id),
    CONSTRAINT fk_paiements_facture_id FOREIGN KEY (facture_id) REFERENCES factures(facture_id),
    CONSTRAINT fk_paiements_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id)
);

-- Demandes au support de MenuScan. (1 ligne = 1 ticket)
CREATE TABLE tickets_support (
    ticket_id VARCHAR(8) NOT NULL,
    etablissement_id VARCHAR(7),
    date_ouverture TIMESTAMP,
    categorie VARCHAR(25),
    canal_contact VARCHAR(10),
    delai_resolution_heures NUMERIC(8,1),
    date_resolution TIMESTAMP,
    statut_ticket VARCHAR(7),
    note_satisfaction SMALLINT,
    CONSTRAINT pk_tickets_support PRIMARY KEY (ticket_id),
    CONSTRAINT fk_tickets_support_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id)
);

-- Catégories du menu de chaque établissement. (1 ligne = 1 catégorie d'un menu)
CREATE TABLE categories_menu (
    categorie_id VARCHAR(8) NOT NULL,
    etablissement_id VARCHAR(7),
    nom_categorie VARCHAR(30),
    ordre_affichage SMALLINT,
    CONSTRAINT pk_categories_menu PRIMARY KEY (categorie_id),
    CONSTRAINT fk_categories_menu_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id)
);

-- Articles des menus (plats, boissons), vue à la date d'arrêté. (1 ligne = 1 article d'un menu)
CREATE TABLE articles (
    article_id VARCHAR(9) NOT NULL,
    etablissement_id VARCHAR(7),
    categorie_id VARCHAR(8),
    nom_article VARCHAR(40),
    date_ajout DATE,
    date_retrait DATE,
    prix_actuel_ttc NUMERIC(10,3),
    statut_article VARCHAR(8),
    CONSTRAINT pk_articles PRIMARY KEY (article_id),
    CONSTRAINT fk_articles_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id),
    CONSTRAINT fk_articles_categorie_id FOREIGN KEY (categorie_id) REFERENCES categories_menu(categorie_id)
);

-- Historique des prix des articles (SCD2). (1 ligne = 1 article x 1 période de prix)
CREATE TABLE articles_prix_historique (
    prix_id VARCHAR(9) NOT NULL,
    article_id VARCHAR(9),
    date_debut DATE,
    date_fin DATE,
    prix_ttc NUMERIC(10,3),
    motif_changement VARCHAR(20),
    est_prix_actuel BOOLEAN,
    CONSTRAINT pk_articles_prix_historique PRIMARY KEY (prix_id),
    CONSTRAINT fk_articles_prix_historique_article_id FOREIGN KEY (article_id) REFERENCES articles(article_id)
);

-- Tables équipées d'un QR code. (1 ligne = 1 table)
CREATE TABLE tables_salle (
    table_id VARCHAR(8) NOT NULL,
    etablissement_id VARCHAR(7),
    numero_table SMALLINT,
    zone VARCHAR(8),
    capacite SMALLINT,
    qr_code_id VARCHAR(7),
    date_installation DATE,
    CONSTRAINT pk_tables_salle PRIMARY KEY (table_id),
    CONSTRAINT fk_tables_salle_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id)
);

-- Visites du menu numérique : une session commence au scan du QR code. Reconstituée à partir des événements. (1 ligne = 1 session (1 scan))
CREATE TABLE sessions (
    session_id VARCHAR(10) NOT NULL,
    etablissement_id VARCHAR(7),
    table_id VARCHAR(8),
    debut_session TIMESTAMP,
    fin_session TIMESTAMP,
    appareil VARCHAR(8),
    langue CHAR(2),
    nb_articles_vus SMALLINT,
    a_ajoute_panier BOOLEAN,
    a_commande BOOLEAN,
    nb_evenements SMALLINT,
    CONSTRAINT pk_sessions PRIMARY KEY (session_id),
    CONSTRAINT fk_sessions_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id),
    CONSTRAINT fk_sessions_table_id FOREIGN KEY (table_id) REFERENCES tables_salle(table_id)
);

-- Journal de navigation du menu (tracking). Fichiers mensuels dans donnees_reference/evenements/. (1 ligne = 1 événement)
CREATE TABLE evenements (
    evenement_id VARCHAR(12) NOT NULL,
    session_id VARCHAR(10),
    etablissement_id VARCHAR(7),
    horodatage TIMESTAMP,
    type_evenement VARCHAR(20),
    article_id VARCHAR(9),
    quantite SMALLINT,
    CONSTRAINT pk_evenements PRIMARY KEY (evenement_id),
    CONSTRAINT fk_evenements_session_id FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    CONSTRAINT fk_evenements_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id),
    CONSTRAINT fk_evenements_article_id FOREIGN KEY (article_id) REFERENCES articles(article_id)
);

-- Commandes passées depuis la table (formules Commande et Pro). (1 ligne = 1 commande)
CREATE TABLE commandes (
    commande_id VARCHAR(10) NOT NULL,
    session_id VARCHAR(10),
    etablissement_id VARCHAR(7),
    table_id VARCHAR(8),
    date_heure_commande TIMESTAMP,
    statut_commande VARCHAR(8),
    date_heure_service TIMESTAMP,
    nb_lignes SMALLINT,
    nb_articles SMALLINT,
    montant_total_ttc NUMERIC(10,3),
    mode_reglement VARCHAR(20),
    motif_annulation VARCHAR(25),
    CONSTRAINT pk_commandes PRIMARY KEY (commande_id),
    CONSTRAINT fk_commandes_session_id FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    CONSTRAINT fk_commandes_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id),
    CONSTRAINT fk_commandes_table_id FOREIGN KEY (table_id) REFERENCES tables_salle(table_id)
);

-- Lignes des commandes. (1 ligne = 1 article dans 1 commande)
CREATE TABLE lignes_commande (
    ligne_id VARCHAR(10) NOT NULL,
    commande_id VARCHAR(10),
    article_id VARCHAR(9),
    quantite SMALLINT,
    prix_unitaire_ttc NUMERIC(10,3),
    montant_ligne_ttc NUMERIC(10,3),
    CONSTRAINT pk_lignes_commande PRIMARY KEY (ligne_id),
    CONSTRAINT fk_lignes_commande_commande_id FOREIGN KEY (commande_id) REFERENCES commandes(commande_id),
    CONSTRAINT fk_lignes_commande_article_id FOREIGN KEY (article_id) REFERENCES articles(article_id)
);

-- Clés circulaires ajoutées après création
ALTER TABLE prospects ADD CONSTRAINT fk_prospects_etablissement_id FOREIGN KEY (etablissement_id) REFERENCES etablissements(etablissement_id);
ALTER TABLE prospects ADD CONSTRAINT fk_prospects_parrain FOREIGN KEY (parrain_etablissement_id) REFERENCES etablissements(etablissement_id);
-- Ordre de chargement : dim_calendrier, ref_villes, formules, canaux_acquisition, campagnes_marketing, marketing_depenses_quotidiennes, prospects, etablissements, abonnements, factures, paiements, tickets_support, categories_menu, articles, articles_prix_historique, tables_salle, sessions, evenements, commandes, lignes_commande (charger prospects avant etablissements : les clés circulaires sont ajoutées à la fin).
