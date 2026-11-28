-- MenuScan TN · schéma ml : résultats de la phase 7 publiés pour Power BI
-- Autrice : Sarra Abdeljaouad · T7.4
-- Script idempotent : il peut être relancé sans perte (create ... if not exists).
-- Les tables sont vidées et remplies à chaque publication par 04_publication_resultats (une seule transaction).

create schema if not exists ml;

create table if not exists ml.score_resiliation (
    etablissement_id    text primary key,
    mois_observe        date not null,          -- dernier mois de données utilisées (décembre 2026)
    probabilite         numeric(7, 5) not null check (probabilite between 0 and 1),
    rang                integer not null,
    alerte              boolean not null,       -- 10 % des établissements les plus à risque
    facteur_1           text,
    facteur_2           text,
    facteur_3           text,
    version_modele      text not null,
    publie_le           timestamp not null
);

create table if not exists ml.candidat_commande (
    etablissement_id        text primary key,
    sessions_table_jour_3m  numeric(8, 4) not null,
    seuil_usage             numeric(8, 4) not null,   -- médiane des établissements en formule Commande
    probabilite_resiliation numeric(7, 5),
    publie_le               timestamp not null
);

create table if not exists ml.regle_association (
    niveau              text not null check (niveau in ('categorie', 'plat')),
    antecedent          text not null,
    consequent          text not null,
    commandes_ensemble  integer not null,
    confiance           numeric(7, 5) not null,
    lift_ajuste         numeric(7, 4) not null,
    lift_2026           numeric(7, 4),
    publie_le           timestamp not null,
    primary key (niveau, antecedent, consequent)
);

create table if not exists ml.recommandation_plat (
    etablissement_id    text not null,
    plat                text not null,
    rang                integer not null check (rang between 1 and 3),
    plat_recommande     text not null,
    motif               text not null,
    publie_le           timestamp not null,
    primary key (etablissement_id, plat, rang)
);

create table if not exists ml.elasticite_categorie (
    categorie               text primary key,     -- « Toutes catégories » pour la mesure globale
    elasticite              numeric(8, 4) not null,
    bas_95                  numeric(8, 4) not null,
    haut_95                 numeric(8, 4) not null,
    plats_informatifs       integer not null,
    lecture                 text not null,
    effet_hausse_5pc_sur_ca numeric(8, 5),
    publie_le               timestamp not null
);

create table if not exists ml.registre_modele (
    modele          text not null,
    version         text not null,
    algorithme      text not null,
    mesure          text not null,
    valeur          numeric(10, 5),
    bas_95          numeric(10, 5),
    haut_95         numeric(10, 5),
    decision        text,
    publie_le       timestamp not null,
    primary key (modele, version, mesure)
);

create table if not exists ml.journal_publication (
    id              serial primary key,
    publie_le       timestamp not null,
    nom_table       text not null,
    lignes          integer not null,
    statut          text not null,
    message         text
);
