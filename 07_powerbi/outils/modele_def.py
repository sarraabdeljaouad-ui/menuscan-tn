"""Définition du modèle sémantique MenuScan : tables, relations, mesures, rôle de sécurité."""

SERVEUR = "localhost:5440"   # vu depuis Windows (port publié du conteneur PostgreSQL)

TABLES = ["dim_date", "dim_heure", "dim_etablissement", "dim_table", "dim_article", "dim_formule", "dim_canal",
          "dim_ville", "fait_session", "fait_commande", "fait_ligne_commande", "fait_abonnement_mensuel",
          "fait_facturation", "fait_marketing", "fait_prospect", "fait_ticket_support", "fait_vue_article",
          # phase 7 : résultats publiés dans le schéma ml par 08_analyse_ml/03_machine_learning/04_publication_resultats
          "ml_score_resiliation", "ml_candidat_commande", "ml_recommandation_plat", "ml_elasticite_categorie",
          "ml_regle_association", "ml_registre_modele"]

# (table de faits, colonne) -> (dimension, colonne) ; plusieurs vers un, filtre dans un seul sens
RELATIONS = [
    ("ml_score_resiliation", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("ml_candidat_commande", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("ml_recommandation_plat", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_session", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_session", "table_id", "dim_table", "table_id"),
    ("fait_session", "formule_id", "dim_formule", "formule_id"),
    ("fait_session", "date_id", "dim_date", "date_id"),
    ("fait_session", "heure", "dim_heure", "heure"),
    ("fait_commande", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_commande", "table_id", "dim_table", "table_id"),
    ("fait_commande", "date_id", "dim_date", "date_id"),
    ("fait_commande", "heure", "dim_heure", "heure"),
    ("fait_ligne_commande", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_ligne_commande", "table_id", "dim_table", "table_id"),
    ("fait_ligne_commande", "prix_id", "dim_article", "prix_id"),
    ("fait_ligne_commande", "date_id", "dim_date", "date_id"),
    ("fait_ligne_commande", "heure", "dim_heure", "heure"),
    ("fait_abonnement_mensuel", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_abonnement_mensuel", "formule_id", "dim_formule", "formule_id"),
    ("fait_abonnement_mensuel", "date_id", "dim_date", "date_id"),
    ("fait_facturation", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_facturation", "formule_id", "dim_formule", "formule_id"),
    ("fait_facturation", "date_id", "dim_date", "date_id"),
    ("fait_marketing", "canal_id", "dim_canal", "canal_id"),
    ("fait_marketing", "ville_id", "dim_ville", "ville_id"),
    ("fait_marketing", "date_id", "dim_date", "date_id"),
    ("fait_prospect", "canal_id", "dim_canal", "canal_id"),
    ("fait_prospect", "ville_id", "dim_ville", "ville_id"),
    ("fait_prospect", "date_id", "dim_date", "date_id"),
    ("fait_ticket_support", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_ticket_support", "date_id", "dim_date", "date_id"),
    ("fait_vue_article", "etablissement_id", "dim_etablissement", "etablissement_id"),
    ("fait_vue_article", "prix_id", "dim_article", "prix_id"),
    ("fait_vue_article", "date_id", "dim_date", "date_id"),
    ("fait_vue_article", "heure", "dim_heure", "heure"),
]

TRI = {("dim_date", "nom_mois"): "mois", ("dim_date", "nom_jour"): "jour_semaine", ("dim_heure", "libelle"): "heure",
       ("dim_date", "jour_court"): "jour_semaine", ("dim_heure", "libelle_court"): "ordre_journee",
       ("dim_etablissement", "trimestre_cohorte"): "ordre_cohorte"}

# Colonnes calculées (DAX) ajoutées aux tables importées : (table, nom, type, format, expression)
COLONNES_CALCULEES = [
    # nom + ville : 403 établissements pour 214 noms ; le couple (nom, ville) est unique
    ("dim_etablissement", "etablissement", "string", None,
     'dim_etablissement[nom_etablissement] & " · " & dim_etablissement[ville]'),
    ("dim_date", "jour_court", "string", None,
     'UPPER ( LEFT ( dim_date[nom_jour], 1 ) ) & MID ( dim_date[nom_jour], 2, 2 )'),
    ("dim_date", "debut_semaine", "dateTime", "dd/MM/yyyy",
     "dim_date[date] - WEEKDAY ( dim_date[date], 2 ) + 1"),
    ("dim_heure", "ordre_journee", "int64", "0", "MOD ( dim_heure[heure] - 6 + 24, 24 )"),
    ("dim_heure", "libelle_court", "string", None, 'FORMAT ( dim_heure[heure], "0" ) & " h"'),
    ("dim_etablissement", "trimestre_cohorte", "string", None,
     '"T" & QUARTER ( dim_etablissement[mois_cohorte] ) & " " & YEAR ( dim_etablissement[mois_cohorte] )'),
    ("dim_etablissement", "ordre_cohorte", "int64", "0",
     "YEAR ( dim_etablissement[mois_cohorte] ) * 10 + QUARTER ( dim_etablissement[mois_cohorte] )"),
    ("dim_table", "libelle_table", "string", None,
     '"Table " & dim_table[numero_table] & " · " & dim_table[zone]'),
]

# Tables calculées sans relation (axes des graphiques) : (nom, colonnes [(nom, type)], tri, expression DAX)
TABLES_CALCULEES = [
    ("Pont MRR", [("etape", "string"), ("ordre", "int64")], ("etape", "ordre"), """
DATATABLE (
    "etape", STRING, "ordre", INTEGER,
    { { "MRR de départ", 1 }, { "Nouveaux", 2 }, { "Expansion", 3 }, { "Contraction", 4 }, { "Pertes", 5 } }
)"""),
    ("Mois écoulés", [("libelle", "string"), ("mois", "int64")], ("libelle", "mois"), """
DATATABLE (
    "libelle", STRING, "mois", INTEGER,
    { { "M0", 0 }, { "M3", 3 }, { "M6", 6 }, { "M9", 9 }, { "M12", 12 }, { "M18", 18 }, { "M24", 24 } }
)"""),
    ("Étapes commerciales", [("etape", "string"), ("ordre", "int64")], ("etape", "ordre"), """
DATATABLE (
    "etape", STRING, "ordre", INTEGER,
    { { "Prospects contactés", 1 }, { "En cours ou signés", 2 }, { "Signés", 3 } }
)"""),
    ("Étapes de session", [("etape", "string"), ("ordre", "int64")], ("etape", "ordre"), """
DATATABLE (
    "etape", STRING, "ordre", INTEGER,
    { { "Scans", 1 }, { "Panier", 2 }, { "Commande", 3 } }
)"""),
]

# Rôle de démonstration du rapport Établissement : le gérant ne voit que son établissement.
ROLE_NOM = "Gérant démo"
ROLE_ETAB = "ETB0003"   # Café Ennour (Ariana, formule Pro), l'établissement le plus actif
ROLE_FILTRES = [
    ("dim_etablissement", f'dim_etablissement[etablissement_id] = "{ROLE_ETAB}"'),
    ("dim_article", f'dim_article[etablissement_id] = "{ROLE_ETAB}"'),
    ("dim_table", f'dim_table[etablissement_id] = "{ROLE_ETAB}"'),
    ("fait_marketing", "FALSE ()"),
    ("fait_prospect", "FALSE ()"),
]

# Mesures : (dossier, nom, format, expression DAX)
MESURES = [
    ("0. Bases", "Sessions", "#,0", "COUNTROWS ( fait_session )"),
    ("0. Bases", "Commandes", "#,0", "COUNTROWS ( fait_commande )"),
    ("0. Bases", "Commandes servies", "#,0",
     "CALCULATE ( COUNTROWS ( fait_commande ), fait_commande[est_servie] = TRUE () )"),
    ("0. Bases", "CA commandes servies TTC", "#,0",
     "CALCULATE ( SUM ( fait_commande[montant_total_ttc] ), fait_commande[est_servie] = TRUE () )"),
    ("0. Bases", "Commandes servies par jour", "#,0.0",
     "DIVIDE ( [Commandes servies], COUNTROWS ( dim_date ) )"),
    ("0. Bases", "Prospects", "#,0", "COUNTROWS ( fait_prospect )"),
    ("0. Bases", "Dépenses marketing TTC", "#,0", "SUM ( fait_marketing[depense_ttc] )"),
    ("1. Croissance", "K01 Établissements actifs", "#,0", """
VAR m = MAX ( dim_date[premier_jour_mois] )
RETURN
    CALCULATE (
        COUNTROWS ( fait_abonnement_mensuel ),
        fait_abonnement_mensuel[est_abonne] = TRUE (),
        REMOVEFILTERS ( dim_date ),
        dim_date[premier_jour_mois] = m
    )"""),
    ("1. Croissance", "K02 MRR", "#,0", """
VAR m = MAX ( dim_date[premier_jour_mois] )
VAR r =
    CALCULATE (
        SUM ( fait_abonnement_mensuel[mrr_ht] ),
        REMOVEFILTERS ( dim_date ),
        dim_date[premier_jour_mois] = m
    )
RETURN
    IF ( r <> 0, r )"""),
    ("1. Croissance", "K03 ARR", "#,0", "12 * [K02 MRR]"),
    ("1. Croissance", "K04 MRR nouveau", "#,0", "SUM ( fait_abonnement_mensuel[mrr_nouveau_ht] )"),
    ("1. Croissance", "K04 MRR expansion", "#,0", "SUM ( fait_abonnement_mensuel[mrr_expansion_ht] )"),
    ("1. Croissance", "K04 MRR contraction", "#,0", "SUM ( fait_abonnement_mensuel[mrr_contraction_ht] )"),
    ("1. Croissance", "K04 MRR perdu", "#,0", "SUM ( fait_abonnement_mensuel[mrr_resiliation_ht] )"),
    ("1. Croissance", "K04 Variation nette du MRR", "#,0", "SUM ( fait_abonnement_mensuel[variation_ht] )"),
    ("2. Rétention", "Résiliations", "#,0", """
VAR d1 = MIN ( dim_date[date] )
VAR d2 = MAX ( dim_date[date] )
RETURN
    COUNTROWS (
        FILTER (
            dim_etablissement,
            dim_etablissement[date_resiliation] >= d1
                && dim_etablissement[date_resiliation] <= d2
        )
    )"""),
    ("2. Rétention", "K05 Taux de résiliation mensuel", "0.00 %", """
VAR mois = VALUES ( dim_date[premier_jour_mois] )
VAR resiliations =
    SUMX (
        mois,
        VAR d = dim_date[premier_jour_mois]
        RETURN
            COUNTROWS (
                FILTER (
                    dim_etablissement,
                    dim_etablissement[date_resiliation] >= d
                        && dim_etablissement[date_resiliation] < EDATE ( d, 1 )
                )
            )
    )
VAR actifs_debut =
    SUMX (
        mois,
        VAR d = dim_date[premier_jour_mois]
        RETURN
            COUNTROWS (
                FILTER (
                    dim_etablissement,
                    dim_etablissement[date_mise_en_service] < d
                        && ( ISBLANK ( dim_etablissement[date_resiliation] )
                            || dim_etablissement[date_resiliation] >= d )
                )
            )
    )
RETURN
    DIVIDE ( resiliations, actifs_debut )"""),
    ("3. Acquisition", "K07 Taux de conversion des prospects", "0.0 %", """
DIVIDE (
    CALCULATE ( COUNTROWS ( fait_prospect ), fait_prospect[est_converti] = TRUE () ),
    [Prospects]
)"""),
    ("3. Acquisition", "K08 Délai de signature médian", "#,0",
     "CALCULATE ( MEDIAN ( fait_prospect[delai_conversion_jours] ), fait_prospect[est_converti] = TRUE () )"),
    ("3. Acquisition", "Signatures", "#,0", """
CALCULATE (
    COUNTROWS ( fait_prospect ),
    fait_prospect[est_converti] = TRUE (),
    REMOVEFILTERS ( dim_date ),
    TREATAS ( VALUES ( dim_date[date] ), fait_prospect[date_conversion] )
)"""),
    ("3. Acquisition", "K09 CAC", "#,0.0", "DIVIDE ( [Dépenses marketing TTC], [Signatures] )"),
    ("3. Acquisition", "Revenu mensuel moyen par établissement", "#,0.00", """
DIVIDE (
    CALCULATE ( SUM ( fait_abonnement_mensuel[mrr_ht] ), fait_abonnement_mensuel[est_abonne] = TRUE () ),
    CALCULATE ( COUNTROWS ( fait_abonnement_mensuel ), fait_abonnement_mensuel[est_abonne] = TRUE () )
)"""),
    ("3. Acquisition", "K10 Valeur vie client", "#,0",
     "DIVIDE ( [Revenu mensuel moyen par établissement], [K05 Taux de résiliation mensuel] )"),
    ("3. Acquisition", "K11 Coût par clic", "#,0.000", """
CALCULATE (
    DIVIDE ( SUM ( fait_marketing[depense_ttc] ), SUM ( fait_marketing[clics] ) ),
    KEEPFILTERS ( dim_canal[type_canal] = "en_ligne" )
)"""),
    ("3. Acquisition", "K11 Taux de clic", "0.00 %", """
CALCULATE (
    DIVIDE ( SUM ( fait_marketing[clics] ), SUM ( fait_marketing[impressions] ) ),
    KEEPFILTERS ( dim_canal[type_canal] = "en_ligne" )
)"""),
    ("4. Usage", "K12 Sessions par table et par jour", "#,0.000", """
VAR d1 = MIN ( dim_date[date] )
VAR d2 = MAX ( dim_date[date] )
VAR tables_jours =
    SUMX (
        dim_etablissement,
        VAR debut = MAX ( d1, dim_etablissement[date_mise_en_service] )
        VAR fin =
            MIN (
                d2,
                IF (
                    ISBLANK ( dim_etablissement[date_resiliation] ),
                    d2,
                    dim_etablissement[date_resiliation]
                )
            )
        RETURN
            IF ( fin >= debut, ( DATEDIFF ( debut, fin, DAY ) + 1 ) * dim_etablissement[nb_tables] )
    )
RETURN
    DIVIDE ( [Sessions], tables_jours )"""),
    ("4. Usage", "K13 Taux de commande", "0.0 %", """
DIVIDE (
    CALCULATE (
        COUNTROWS ( fait_session ),
        fait_session[a_commande] = TRUE (),
        KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () )
    ),
    CALCULATE ( COUNTROWS ( fait_session ), KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ) )
)"""),
    ("4. Usage", "K20 Étape 1 Article consulté", "0.0 %",
     "DIVIDE ( CALCULATE ( COUNTROWS ( fait_session ), fait_session[a_vu_article] = TRUE () ), [Sessions] )"),
    ("4. Usage", "K20 Étape 2 Panier", "0.0 %", """
DIVIDE (
    CALCULATE (
        COUNTROWS ( fait_session ),
        fait_session[a_ajoute_panier] = TRUE (),
        KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () )
    ),
    CALCULATE ( COUNTROWS ( fait_session ), KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ) )
)"""),
    ("4. Usage", "K20 Étape 3 Commande", "0.0 %", "[K13 Taux de commande]"),
    ("5. Activité en salle", "K14 Panier moyen", "#,0.00",
     "DIVIDE ( [CA commandes servies TTC], [Commandes servies] )"),
    ("5. Activité en salle", "K15 Taux d'annulation", "0.00 %",
     'DIVIDE ( CALCULATE ( COUNTROWS ( fait_commande ), fait_commande[statut_commande] = "annulee" ), [Commandes] )'),
    ("6. Facturation", "K16 Facturé HT", "#,0", "SUM ( fait_facturation[montant_net_ht] )"),
    ("6. Facturation", "K16 Encaissé TTC", "#,0", "SUM ( fait_facturation[montant_encaisse_ttc] )"),
    ("6. Facturation", "K17 Taux de factures payées en retard", "0.0 %", """
DIVIDE (
    CALCULATE ( COUNTROWS ( fait_facturation ), fait_facturation[statut_facture] = "payee_en_retard" ),
    CALCULATE ( COUNTROWS ( fait_facturation ), fait_facturation[montant_ttc] > 0 )
)"""),
    ("6. Facturation", "K17 Factures impayées", "#,0",
     'CALCULATE ( COUNTROWS ( fait_facturation ), fait_facturation[statut_facture] = "impayee" )'),
    ("7. Support", "K18 Délai de résolution médian (h)", "#,0.0",
     'CALCULATE ( MEDIAN ( fait_ticket_support[delai_resolution_heures] ), fait_ticket_support[statut_ticket] = "resolu" )'),
    ("7. Support", "K18 Satisfaction moyenne", "0.00",
     'CALCULATE ( AVERAGE ( fait_ticket_support[note_satisfaction] ), fait_ticket_support[statut_ticket] = "resolu" )'),
    ("8. Menu et marge", "Quantités servies", "#,0",
     "CALCULATE ( SUM ( fait_ligne_commande[quantite] ), fait_ligne_commande[est_servie] = TRUE () )"),
    ("8. Menu et marge", "Ventes servies TTC (lignes)", "#,0",
     "CALCULATE ( SUM ( fait_ligne_commande[montant_ligne_ttc] ), fait_ligne_commande[est_servie] = TRUE () )"),
    ("8. Menu et marge", "K21 Marge brute estimée TTC", "#,0",
     "CALCULATE ( SUM ( fait_ligne_commande[marge_brute_estimee_ttc] ), fait_ligne_commande[est_servie] = TRUE () )"),
    ("8. Menu et marge", "K21 Taux de coût estimé", "0.0 %", """
DIVIDE (
    CALCULATE ( SUM ( fait_ligne_commande[cout_matiere_estime_ttc] ), fait_ligne_commande[est_servie] = TRUE () ),
    [Ventes servies TTC (lignes)]
)"""),
    ("8. Menu et marge", "K22 Marge unitaire estimée", "#,0.000",
     "DIVIDE ( [K21 Marge brute estimée TTC], [Quantités servies] )"),
    # dim_article n'est pas reliée à dim_etablissement : sans TREATAS, une ligne « Pancakes » regroupe les Pancakes
    # de tous les établissements et la classe reste vide (sauf sous le rôle Gérant démo, qui filtre dim_article).
    ("8. Menu et marge", "K22 Classe du plat", None, """
CALCULATE (
    [K22 Classe (calcul)],
    TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_article[etablissement_id] )
)"""),
    ("8. Menu et marge", "K22 Classe (calcul)", None, """
VAR q = [Quantités servies]
VAR etab = VALUES ( dim_article[etablissement_id] )
VAR q_etab =
    CALCULATE ( [Quantités servies], REMOVEFILTERS ( dim_article ), dim_article[etablissement_id] IN etab )
VAR marge_etab =
    CALCULATE ( [K21 Marge brute estimée TTC], REMOVEFILTERS ( dim_article ), dim_article[etablissement_id] IN etab )
VAR nb_plats =
    CALCULATE (
        COUNTROWS ( FILTER ( VALUES ( dim_article[article_id] ), [Quantités servies] > 0 ) ),
        REMOVEFILTERS ( dim_article ),
        dim_article[etablissement_id] IN etab
    )
VAR populaire = DIVIDE ( q, q_etab ) >= 0.7 / nb_plats
VAR rentable = DIVIDE ( [K21 Marge brute estimée TTC], q ) >= DIVIDE ( marge_etab, q_etab )
RETURN
    IF (
        HASONEVALUE ( dim_article[article_id] ) && q > 0,
        SWITCH (
            TRUE (),
            populaire && rentable, "Vedette",
            populaire, "Cheval de labour",
            rentable, "Énigme",
            "Poids mort"
        )
    )"""),
]
for _classe, _nom in [("Vedette", "K22 Nombre de vedettes"), ("Cheval de labour", "K22 Nombre de chevaux de labour"),
                      ("Énigme", "K22 Nombre d'énigmes"), ("Poids mort", "K22 Nombre de poids morts")]:
    MESURES.append(("8. Menu et marge", _nom, "#,0", f"""
COUNTROWS (
    FILTER (
        FILTER ( VALUES ( dim_article[article_id] ), [Quantités servies] > 0 ),
        [K22 Classe du plat] = "{_classe}"
    )
)"""))
MESURES += [
    ("9. Saisonnalité", "Part des commandes du soir", "0.0 %", """
DIVIDE (
    CALCULATE ( [Commandes servies], fait_commande[heure] >= 19 || fait_commande[heure] < 2 ),
    [Commandes servies]
)"""),
    ("9. Saisonnalité", "K23 Part du soir en Ramadan", "0.0 %",
     "CALCULATE ( [Part des commandes du soir], dim_date[est_ramadan] = TRUE () )"),
    ("9. Saisonnalité", "K23 Part du soir hors Ramadan", "0.0 %",
     "CALCULATE ( [Part des commandes du soir], dim_date[est_ramadan] = FALSE () )"),
    ("9. Saisonnalité", "K23 Commandes par jour en Ramadan", "#,0.0",
     "CALCULATE ( [Commandes servies par jour], dim_date[est_ramadan] = TRUE () )"),
    ("9. Saisonnalité", "K23 Commandes par jour hors Ramadan", "#,0.0",
     "CALCULATE ( [Commandes servies par jour], dim_date[est_ramadan] = FALSE () )"),
]

# ------------------------------------------------------------------ mesures des maquettes (affichage et couleurs)
BLEU, BLEU_FONCE, ORANGE, GRIS = "#1D4ED8", "#1E3A8A", "#C2410C", "#CBD5E1"
NB = '"#,0"'
DT = '"#,0.000"'


def _fmt(expr, fmt):
    return f"FORMAT ( {expr}, {fmt} )"


MESURES += [
    # ---- croissance
    ("1. Croissance", "K02 MRR A-1", "#,0", """
VAR m = EDATE ( MAX ( dim_date[premier_jour_mois] ), -12 )
RETURN
    CALCULATE ( SUM ( fait_abonnement_mensuel[mrr_ht] ), REMOVEFILTERS ( dim_date ), dim_date[premier_jour_mois] = m )"""),
    ("1. Croissance", "Pont MRR valeur", "#,0", """
VAR a = MAX ( dim_date[annee] )
VAR depart =
    CALCULATE ( [K02 MRR], REMOVEFILTERS ( dim_date ), dim_date[annee] = a - 1 )
RETURN
    SWITCH (
        SELECTEDVALUE ( 'Pont MRR'[ordre] ),
        1, IF ( ISFILTERED ( dim_date[annee] ), depart, 0 ),
        2, [K04 MRR nouveau],
        3, [K04 MRR expansion],
        4, [K04 MRR contraction],
        5, [K04 MRR perdu]
    )"""),
    ("1. Croissance", "Texte K01", None, f"{_fmt('[K01 Établissements actifs]', NB)}"),
    ("1. Croissance", "Texte K01 détail", None,
     '"au " & FORMAT ( EOMONTH ( MAX ( dim_date[premier_jour_mois] ), 0 ), "dd/MM/yyyy" )'),
    ("1. Croissance", "Texte K02", None, f'{_fmt("[K02 MRR]", NB)} & " DT HT"'),
    ("1. Croissance", "Texte K02 détail", None, """
VAR p = [K02 MRR A-1]
RETURN
    IF (
        ISBLANK ( p ),
        "A-1 : non disponible",
        "A-1 : " & FORMAT ( p, "#,0" ) & " DT · " & FORMAT ( DIVIDE ( [K02 MRR] - p, p ), "+0.0 %;-0.0 %" )
    )"""),
    ("1. Croissance", "Texte K03", None, f'{_fmt("[K03 ARR]", NB)} & " DT HT"'),
    ("1. Croissance", "Texte K03 détail", None, """
VAR p = 12 * [K02 MRR A-1]
RETURN
    IF (
        p = 0,
        "A-1 : non disponible",
        "A-1 : " & FORMAT ( p, "#,0" ) & " DT · " & FORMAT ( DIVIDE ( [K03 ARR] - p, p ), "+0.0 %;-0.0 %" )
    )"""),
    ("1. Croissance", "Texte K16", None, f'{_fmt("[K16 Facturé HT]", NB)} & " DT HT"'),
    ("1. Croissance", "Texte K16 détail", None, f'"encaissé : " & {_fmt("[K16 Encaissé TTC]", NB)} & " DT TTC"'),
    ("1. Croissance", "Texte K17", None, '{_fmt}'.replace("{_fmt}", _fmt("[K17 Taux de factures payées en retard]", '"0.0 %"'))),
    ("1. Croissance", "Texte K17 détail", None, """
VAR p = CALCULATE ( [K17 Taux de factures payées en retard], SAMEPERIODLASTYEAR ( dim_date[date] ) )
RETURN
    FORMAT ( [K17 Factures impayées], "#,0" ) & " impayées · A-1 : " & IF ( ISBLANK ( p ), "n. d.", FORMAT ( p, "0.0 %" ) )"""),
    ("1. Croissance", "Texte variation MRR", None,
     '"Variation nette : " & FORMAT ( [K04 Variation nette du MRR], "+#,0;-#,0" ) & " DT HT"'),
    # ---- rétention
    ("2. Rétention", "K06 Rétention de cohorte", "0 %", """
VAR n = SELECTEDVALUE ( 'Mois écoulés'[mois], 12 )
VAR arrete = CALCULATE ( MAX ( dim_date[date] ), REMOVEFILTERS ( dim_date ) )
VAR cohorte = FILTER ( dim_etablissement, NOT ISBLANK ( dim_etablissement[date_mise_en_service] ) )
VAR eligibles = FILTER ( cohorte, EDATE ( dim_etablissement[date_mise_en_service], n ) <= arrete )
VAR actifs =
    FILTER (
        eligibles,
        ISBLANK ( dim_etablissement[date_resiliation] )
            || dim_etablissement[date_resiliation] >= EDATE ( dim_etablissement[date_mise_en_service], n )
    )
RETURN
    IF (
        COUNTROWS ( cohorte ) > 0 && COUNTROWS ( eligibles ) = COUNTROWS ( cohorte ),
        DIVIDE ( COUNTROWS ( actifs ), COUNTROWS ( eligibles ) )
    )"""),
    ("2. Rétention", "K06 Rétention à 12 mois des cohortes A-1", "0.0 %", """
VAR a = MAX ( dim_date[annee] ) - 1
RETURN
    CALCULATE (
        [K06 Rétention de cohorte],
        'Mois écoulés'[mois] = 12,
        KEEPFILTERS ( FILTER ( ALL ( dim_etablissement[mois_cohorte] ), YEAR ( dim_etablissement[mois_cohorte] ) = a ) )
    )"""),
    ("2. Rétention", "Couleur cohorte", None, f"""
VAR r = [K06 Rétention de cohorte]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( r ), BLANK (),
        r >= 0.95, "{BLEU_FONCE}",
        r >= 0.8, "#3B5BDB",
        r >= 0.7, "#748FFC",
        r >= 0.6, "#BAC8FF",
        "#E0E7FF"
    )"""),
    ("2. Rétention", "Couleur texte cohorte", None, """
IF ( [K06 Rétention de cohorte] >= 0.8, "#FFFFFF", "#0F172A" )"""),
    ("2. Rétention", "Texte K05", None, _fmt("[K05 Taux de résiliation mensuel]", '"0.00 %"')),
    ("2. Rétention", "Texte K05 détail", None, """
VAR p = CALCULATE ( [K05 Taux de résiliation mensuel], SAMEPERIODLASTYEAR ( dim_date[date] ) )
RETURN
    "moyenne pondérée · A-1 : " & IF ( ISBLANK ( p ), "n. d.", FORMAT ( p, "0.00 %" ) )"""),
    ("2. Rétention", "Texte résiliations", None, _fmt("[Résiliations]", NB)),
    ("2. Rétention", "Texte résiliations détail", None,
     '"du " & FORMAT ( MIN ( dim_date[date] ), "dd/MM/yyyy" ) & " au " & FORMAT ( MAX ( dim_date[date] ), "dd/MM/yyyy" )'),
    ("2. Rétention", "Texte K06", None, """
VAR r = [K06 Rétention à 12 mois des cohortes A-1]
RETURN IF ( ISBLANK ( r ), "n. d.", FORMAT ( r, "0.0 %" ) )"""),
    ("2. Rétention", "Texte K06 détail", None, '"cohortes " & ( MAX ( dim_date[annee] ) - 1 )'),
    ("2. Rétention", "Texte MRR perdu", None, f'{_fmt("-[K04 MRR perdu]", NB)} & " DT HT"'),
    ("2. Rétention", "Texte MRR perdu détail", None, '"somme des pertes du K04"'),
    ("2. Rétention", "Texte moyenne K05", None,
     '"Moyenne de la période : " & FORMAT ( [K05 Taux de résiliation mensuel], "0.00 %" )'),
    # ---- acquisition
    ("3. Acquisition", "Clics", "#,0", "SUM ( fait_marketing[clics] )"),
    ("3. Acquisition", "Signatures (campagne)", "#,0", """
CALCULATE ( [Signatures], TREATAS ( VALUES ( fait_marketing[campagne_id] ), fait_prospect[campagne_id] ) )"""),
    ("3. Acquisition", "K10 Valeur vie client par canal", "#,0", """
CALCULATE ( [K10 Valeur vie client], TREATAS ( VALUES ( dim_canal[canal_id] ), dim_etablissement[canal_id] ) )"""),
    ("3. Acquisition", "Prospects par étape", "#,0", """
SWITCH (
    SELECTEDVALUE ( 'Étapes commerciales'[ordre] ),
    1, [Prospects],
    2, CALCULATE ( [Prospects], fait_prospect[statut_prospect] IN { "en_cours", "converti" } ),
    3, CALCULATE ( [Prospects], fait_prospect[statut_prospect] = "converti" )
)"""),
    ("3. Acquisition", "Couleur CAC", None, f"""
VAR c = [K09 CAC]
VAR canaux = FILTER ( ALLSELECTED ( dim_canal[nom_canal] ), NOT ISBLANK ( [K09 CAC] ) )
VAR mini = MINX ( canaux, [K09 CAC] )
VAR maxi = MAXX ( canaux, [K09 CAC] )
RETURN SWITCH ( TRUE (), c = mini, "{BLEU}", c = maxi, "{ORANGE}", "{GRIS}" )"""),
    ("3. Acquisition", "Texte K07", None, _fmt("[K07 Taux de conversion des prospects]", '"0.0 %"')),
    ("3. Acquisition", "Texte K07 détail", None,
     'FORMAT ( CALCULATE ( [Prospects], fait_prospect[est_converti] = TRUE () ), "#,0" ) & " convertis / " & FORMAT ( [Prospects], "#,0" ) & " contactés"'),
    ("3. Acquisition", "Texte K08", None, f'{_fmt("[K08 Délai de signature médian]", NB)} & " jours"'),
    ("3. Acquisition", "Texte K08 détail", None, '"médiane, prospects convertis"'),
    ("3. Acquisition", "Texte CAC bas", None, """
VAR canaux = FILTER ( VALUES ( dim_canal[nom_canal] ), NOT ISBLANK ( [K09 CAC] ) )
RETURN FORMAT ( MINX ( canaux, [K09 CAC] ), "#,0.0" ) & " DT\""""),
    ("3. Acquisition", "Texte CAC bas détail", None, """
VAR canaux = FILTER ( VALUES ( dim_canal[nom_canal] ), NOT ISBLANK ( [K09 CAC] ) )
RETURN CONCATENATEX ( TOPN ( 1, canaux, [K09 CAC], ASC ), dim_canal[nom_canal], ", " )"""),
    ("3. Acquisition", "Texte CAC haut", None, """
VAR canaux = FILTER ( VALUES ( dim_canal[nom_canal] ), NOT ISBLANK ( [K09 CAC] ) )
RETURN FORMAT ( MAXX ( canaux, [K09 CAC] ), "#,0.0" ) & " DT\""""),
    ("3. Acquisition", "Texte CAC haut détail", None, """
VAR canaux = FILTER ( VALUES ( dim_canal[nom_canal] ), NOT ISBLANK ( [K09 CAC] ) )
RETURN CONCATENATEX ( TOPN ( 1, canaux, [K09 CAC], DESC ), dim_canal[nom_canal], ", " )"""),
    ("3. Acquisition", "Texte K10", None, f'{_fmt("[K10 Valeur vie client]", NB)} & " DT HT"'),
    ("3. Acquisition", "Texte K10 détail", None,
     '"revenu mensuel moyen " & FORMAT ( [Revenu mensuel moyen par établissement], "#,0.00" ) & " / K05"'),
    ("3. Acquisition", "Texte prospects", None,
     'FORMAT ( [Prospects], "#,0" ) & " prospects · statuts du jeu : perdu, en cours, converti"'),
    # ---- pilotage
    ("4. Usage", "MRR actuel de l'établissement", "#,0", """
IF ( SELECTEDVALUE ( dim_etablissement[est_actif] ), [K02 MRR] )"""),
    # ---- phase 7 : scores et résultats du schéma ml
    ("4. Usage", "Score K19", "0.0 %", "MAX ( ml_score_resiliation[probabilite] )"),
    ("4. Usage", "Établissements scorés", "#,0", "COUNTROWS ( ml_score_resiliation )"),
    ("4. Usage", "Établissements en alerte K19", "#,0",
     "CALCULATE ( COUNTROWS ( ml_score_resiliation ), ml_score_resiliation[alerte] = TRUE () )"),
    ("4. Usage", "MRR menacé", "#,0", """
CALCULATE (
    [K02 MRR],
    TREATAS (
        CALCULATETABLE ( VALUES ( ml_score_resiliation[etablissement_id] ), ml_score_resiliation[alerte] = TRUE () ),
        dim_etablissement[etablissement_id]
    )
)"""),
    ("4. Usage", "Facteurs K19", None, """
VAR f1 = SELECTEDVALUE ( ml_score_resiliation[facteur_1] )
VAR f2 = SELECTEDVALUE ( ml_score_resiliation[facteur_2] )
VAR f3 = SELECTEDVALUE ( ml_score_resiliation[facteur_3] )
RETURN
    IF ( NOT ISBLANK ( f1 ), f1 & IF ( NOT ISBLANK ( f2 ), " · " & f2 ) & IF ( NOT ISBLANK ( f3 ), " · " & f3 ) )"""),
    ("4. Usage", "Candidats Commande", "#,0", "COUNTROWS ( ml_candidat_commande )"),
    ("4. Usage", "Usage 3 mois (candidat)", "#,0.000", "MAX ( ml_candidat_commande[sessions_table_jour_3m] )"),
    ("4. Usage", "Score K19 (candidat)", "0.0 %", "IF ( NOT ISBLANK ( [Usage 3 mois (candidat)] ), [Score K19] )"),
    ("4. Usage", "Tables (candidat)", "#,0",
     "IF ( NOT ISBLANK ( [Usage 3 mois (candidat)] ), SUM ( dim_etablissement[nb_tables] ) )"),
    ("7. Support", "Texte K19 alertes", None,
     'FORMAT ( [Établissements en alerte K19], "#,0" ) & " / " & FORMAT ( [Établissements scorés], "#,0" )'),
    ("7. Support", "Texte MRR menacé valeur", None, 'FORMAT ( [MRR menacé], "#,0" ) & " DT HT"'),
    ("7. Support", "Texte candidats valeur", None, 'FORMAT ( [Candidats Commande], "#,0" )'),
    ("7. Support", "Texte K18", None, f'{_fmt("[K18 Délai de résolution médian (h)]", '"#,0.0"')} & " h"'),
    ("7. Support", "Texte K18 détail", None,
     '"médiane · satisfaction : " & FORMAT ( [K18 Satisfaction moyenne], "0.0" ) & " / 5"'),
    ("7. Support", "Texte seuil K19", None, """
"10 % les plus à risque · AUC 2026 = "
    & FORMAT ( LOOKUPVALUE ( ml_registre_modele[valeur], ml_registre_modele[mesure], "AUC test 2026" ), "0.000" )"""),
    ("7. Support", "Texte MRR menacé", None,
     '"MRR mensuel des établissements en alerte · " & FORMAT ( DIVIDE ( [MRR menacé], [K02 MRR] ), "0.0 %" ) & " du MRR"'),
    ("7. Support", "Texte candidats", None, '"Essentiel · usage ≥ médiane Commande · hors alerte"'),
    # ---- établissement : activité
    ("5. Activité en salle", "Nom de l'établissement", None, """
IF (
    HASONEVALUE ( dim_etablissement[etablissement_id] ),
    SELECTEDVALUE ( dim_etablissement[nom_etablissement] ) & " · " & SELECTEDVALUE ( dim_etablissement[etablissement_id] ),
    "Tous les établissements"
)"""),
    ("5. Activité en salle", "Tables de l'établissement", "#,0", """
CALCULATE ( COUNTROWS ( dim_table ), TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_table[etablissement_id] ) )"""),
    ("5. Activité en salle", "Commandes servies par table", "#,0.0",
     "DIVIDE ( [Commandes servies], [Tables de l'établissement] )"),
    ("5. Activité en salle", "Texte commandes servies", None, _fmt("[Commandes servies]", NB)),
    ("5. Activité en salle", "Texte commandes servies détail", None, '"sur " & FORMAT ( [Commandes], "#,0" ) & " commandes"'),
    ("5. Activité en salle", "Texte CA servi", None, f'{_fmt("[CA commandes servies TTC]", NB)} & " DT"'),
    ("5. Activité en salle", "Texte CA servi détail", None, '"TTC, commandes servies"'),
    ("5. Activité en salle", "Texte K14", None, f'{_fmt("[K14 Panier moyen]", DT)} & " DT"'),
    ("5. Activité en salle", "Texte K14 détail", None, '"TTC par commande servie"'),
    ("5. Activité en salle", "Texte K15", None, _fmt("COALESCE ( [K15 Taux d'annulation], 0 )", '"0.00 %"')),
    ("5. Activité en salle", "Texte K15 détail", None,
     'FORMAT ( COALESCE ( CALCULATE ( [Commandes], fait_commande[statut_commande] = "annulee" ), 0 ), "#,0" ) & " commandes annulées"'),
    ("5. Activité en salle", "Texte commandes par table", None, _fmt("[Commandes servies par table]", '"#,0.0"')),
    ("5. Activité en salle", "Texte commandes par table détail", None,
     'FORMAT ( [Tables de l\'établissement], "#,0" ) & " tables"'),
    ("5. Activité en salle", "Couleur semaine", None, f"""
IF ( CALCULATE ( COUNTROWS ( dim_date ), dim_date[est_ramadan] = TRUE () ) > 0, "{ORANGE}", "{BLEU}" )"""),
    ("5. Activité en salle", "Couleur zone", None, f"""
SWITCH ( SELECTEDVALUE ( dim_table[zone] ), "salle", "{BLEU_FONCE}", "terrasse", "{BLEU}", "etage", "{ORANGE}", "{GRIS}" )"""),
    ("5. Activité en salle", "Texte CA par zone", None, """
CONCATENATEX (
    VALUES ( dim_table[zone] ),
    dim_table[zone] & " : " & FORMAT ( [CA commandes servies TTC], "#,0" ) & " DT",
    " · ",
    [CA commandes servies TTC], DESC
)"""),
    # ---- établissement : menu
    ("8. Menu et marge", "Vues de fiche", "#,0", "SUM ( fait_vue_article[nb_vues] )"),
    ("8. Menu et marge", "Commandes de l'article", "#,0", """
CALCULATE ( DISTINCTCOUNT ( fait_ligne_commande[commande_id] ), fait_ligne_commande[est_servie] = TRUE () )"""),
    ("8. Menu et marge", "Conversion de la fiche", "0.0 %", "DIVIDE ( [Commandes de l'article], [Vues de fiche] )"),
    ("8. Menu et marge", "Prix TTC actuel", "#,0.000", """
CALCULATE (
    MAX ( dim_article[prix_ttc] ),
    dim_article[est_prix_actuel] = TRUE (),
    TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_article[etablissement_id] )
)"""),
    ("8. Menu et marge", "Couleur article", None, f"""
VAR arts = ALLSELECTED ( dim_article[nom_article] )
VAR vues_moy = AVERAGEX ( arts, [Vues de fiche] )
VAR conv_moy = DIVIDE ( SUMX ( arts, [Commandes de l'article] ), SUMX ( arts, [Vues de fiche] ) )
RETURN IF ( [Vues de fiche] >= vues_moy && [Conversion de la fiche] < conv_moy, "{ORANGE}", "{BLEU}" )"""),
    ("8. Menu et marge", "Étapes de session valeur", "#,0", """
SWITCH (
    SELECTEDVALUE ( 'Étapes de session'[ordre] ),
    1, CALCULATE ( [Sessions], KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ) ),
    2, CALCULATE ( [Sessions], KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ), fait_session[a_ajoute_panier] = TRUE () ),
    3, CALCULATE ( [Sessions], KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ), fait_session[a_commande] = TRUE () )
)"""),
    ("8. Menu et marge", "Articles au menu", "#,0", """
CALCULATE (
    DISTINCTCOUNT ( dim_article[article_id] ),
    dim_article[est_prix_actuel] = TRUE (),
    TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_article[etablissement_id] )
)"""),
    ("8. Menu et marge", "Texte K13", None, _fmt("[K13 Taux de commande]", '"0.0 %"')),
    ("8. Menu et marge", "Texte K13 détail", None, """
VAR s = CALCULATE ( [Sessions], KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ) )
VAR c = CALCULATE ( [Sessions], KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ), fait_session[a_commande] = TRUE () )
RETURN
    FORMAT ( c, "#,0" ) & " sessions avec commande sur " & FORMAT ( s, "#,0" )"""),
    ("8. Menu et marge", "Texte panier", None, _fmt("[K20 Étape 2 Panier]", '"0.0 %"')),
    ("8. Menu et marge", "Texte panier détail", None, """
FORMAT (
    CALCULATE ( [Sessions], fait_session[a_ajoute_panier] = TRUE (), KEEPFILTERS ( dim_formule[inclut_commande] = TRUE () ) ),
    "#,0"
) & " sessions avec un ajout au panier\""""),
    ("8. Menu et marge", "Texte articles", None, _fmt("[Articles au menu]", NB)),
    ("8. Menu et marge", "Texte articles détail", None, """
FORMAT (
    CALCULATE (
        DISTINCTCOUNT ( dim_article[categorie_id] ),
        dim_article[est_prix_actuel] = TRUE (),
        TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_article[etablissement_id] )
    ),
    "#,0"
) & " catégories\""""),
    ("8. Menu et marge", "Article le moins converti", None, """
VAR plus_vus = TOPN ( 10, FILTER ( VALUES ( dim_article[nom_article] ), [Vues de fiche] > 0 ), [Vues de fiche], DESC )
RETURN CONCATENATEX ( TOPN ( 1, plus_vus, [Conversion de la fiche], ASC ), dim_article[nom_article], ", " )"""),
    ("8. Menu et marge", "Article le moins converti détail", None, """
VAR plus_vus = TOPN ( 10, FILTER ( VALUES ( dim_article[nom_article] ), [Vues de fiche] > 0 ), [Vues de fiche], DESC )
VAR a = TOPN ( 1, plus_vus, [Conversion de la fiche], ASC )
RETURN
    FORMAT ( CALCULATE ( [Vues de fiche], a ), "#,0" ) & " vues, "
        & FORMAT ( CALCULATE ( [Commandes de l'article], a ), "#,0" ) & " commandes ("
        & FORMAT ( CALCULATE ( [Conversion de la fiche], a ), "0.0 %" ) & ")\""""),
    # ---- établissement : temps
    ("9. Saisonnalité", "Couleur heure", None, f"""
VAR v = [Commandes servies]
VAR maxi =
    CALCULATE (
        MAXX ( CROSSJOIN ( VALUES ( dim_date[jour_court] ), VALUES ( dim_heure[libelle_court] ) ), [Commandes servies] ),
        REMOVEFILTERS ( dim_date[jour_court], dim_date[jour_semaine], dim_date[nom_jour] ),
        REMOVEFILTERS ( dim_heure )
    )
VAR r = DIVIDE ( v, maxi )
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( v ), "#F1F5F9",
        r >= 0.8, "#3B5BDB",
        r >= 0.6, "#748FFC",
        r >= 0.4, "#A5B4FC",
        r >= 0.2, "#C7D2FE",
        "#E0E7FF"
    )"""),
    ("9. Saisonnalité", "Part horaire hors Ramadan", "0.0 %", """
DIVIDE (
    CALCULATE ( [Commandes servies], dim_date[est_ramadan] = FALSE () ),
    CALCULATE ( [Commandes servies], dim_date[est_ramadan] = FALSE (), REMOVEFILTERS ( dim_heure ) )
)"""),
    ("9. Saisonnalité", "Part horaire Ramadan", "0.0 %", """
DIVIDE (
    CALCULATE ( [Commandes servies], dim_date[est_ramadan] = TRUE () ),
    CALCULATE ( [Commandes servies], dim_date[est_ramadan] = TRUE (), REMOVEFILTERS ( dim_heure ) )
)"""),
    ("9. Saisonnalité", "CA servi par jour", "#,0.0", "DIVIDE ( [CA commandes servies TTC], COUNTROWS ( dim_date ) )"),
]
for _nom, _filtre in [("hors Ramadan", "FALSE ()"), ("Ramadan", "TRUE ()")]:
    MESURES += [
        ("9. Saisonnalité", f"Heure de pointe {_nom}", None, f"""
VAR h = CALCULATETABLE ( VALUES ( dim_heure[heure] ), REMOVEFILTERS ( dim_heure ) )
VAR pic = TOPN ( 1, h, CALCULATE ( [Commandes servies], dim_date[est_ramadan] = {_filtre} ), DESC )
VAR total = CALCULATE ( [Commandes servies], dim_date[est_ramadan] = {_filtre}, REMOVEFILTERS ( dim_heure ) )
RETURN IF ( ISBLANK ( total ), "aucune commande", CONCATENATEX ( pic, FORMAT ( dim_heure[heure], "0" ) & " h", ", " ) )"""),
        ("9. Saisonnalité", f"Heure de pointe {_nom} détail", None, f"""
VAR h = CALCULATETABLE ( VALUES ( dim_heure[heure] ), REMOVEFILTERS ( dim_heure ) )
VAR pic = TOPN ( 1, h, CALCULATE ( [Commandes servies], dim_date[est_ramadan] = {_filtre} ), DESC )
VAR total = CALCULATE ( [Commandes servies], dim_date[est_ramadan] = {_filtre}, REMOVEFILTERS ( dim_heure ) )
RETURN
    IF (
        ISBLANK ( total ),
        "pas de commande servie sur cette période",
        FORMAT ( CALCULATE ( [Commandes servies], pic, dim_date[est_ramadan] = {_filtre} ), "#,0" ) & " commandes servies à cette heure"
    )"""),
    ]
MESURES += [
    ("9. Saisonnalité", "Texte commandes par jour", None, """
FORMAT ( [K23 Commandes par jour hors Ramadan], "#,0.00" ) & " → "
    & IF ( ISBLANK ( [K23 Commandes par jour en Ramadan] ), "aucune", FORMAT ( [K23 Commandes par jour en Ramadan], "#,0.00" ) )"""),
    ("9. Saisonnalité", "Texte commandes par jour détail", None, """
IF (
    ISBLANK ( [K23 Commandes par jour en Ramadan] ) || ISBLANK ( [K23 Commandes par jour hors Ramadan] ),
    "comparaison impossible : pas de commande sur l'une des deux périodes",
    "hors Ramadan → Ramadan ("
        & FORMAT ( DIVIDE ( [K23 Commandes par jour en Ramadan], [K23 Commandes par jour hors Ramadan] ) - 1, "+0 %;-0 %" ) & ")"
)"""),
    ("9. Saisonnalité", "Texte CA par jour", None, """
VAR h = CALCULATE ( [CA servi par jour], dim_date[est_ramadan] = FALSE () )
VAR r = CALCULATE ( [CA servi par jour], dim_date[est_ramadan] = TRUE () )
RETURN FORMAT ( h, "#,0.0" ) & " → " & IF ( ISBLANK ( r ), "aucun", FORMAT ( r, "#,0.0" ) & " DT" )"""),
    ("9. Saisonnalité", "Texte CA par jour détail", None, """
VAR h = CALCULATE ( [CA servi par jour], dim_date[est_ramadan] = FALSE () )
VAR r = CALCULATE ( [CA servi par jour], dim_date[est_ramadan] = TRUE () )
RETURN
    IF (
        ISBLANK ( r ) || ISBLANK ( h ),
        "comparaison impossible : pas de commande sur l'une des deux périodes",
        "hors Ramadan → Ramadan (" & FORMAT ( DIVIDE ( r, h ) - 1, "+0 %;-0 %" ) & ")"
    )"""),
    ("9. Saisonnalité", "Texte été", None, """
VAR e = CALCULATE ( [Commandes servies par jour], dim_date[periode_activite] = "ete" )
VAR n = CALCULATE ( [Commandes servies par jour], dim_date[periode_activite] = "normale" )
RETURN IF ( ISBLANK ( e ) || ISBLANK ( n ), "comparaison impossible", FORMAT ( DIVIDE ( e, n ) - 1, "+0 %;-0 %" ) & " par jour en été" )"""),
    ("9. Saisonnalité", "Texte été détail", None, """
VAR e = CALCULATE ( [Commandes servies par jour], dim_date[periode_activite] = "ete" )
VAR n = CALCULATE ( [Commandes servies par jour], dim_date[periode_activite] = "normale" )
RETURN "commandes par jour : " & FORMAT ( e, "#,0.0" ) & " en été, " & FORMAT ( n, "#,0.0" ) & " en période normale\""""),
    # ---- établissement : prix
    ("8. Menu et marge", "Prix moyen pratiqué", "#,0.000", """
DIVIDE ( SUM ( fait_ligne_commande[montant_ligne_ttc] ), SUM ( fait_ligne_commande[quantite] ) )"""),
    ("8. Menu et marge", "Hausse de prix", "+0.0 %;-0.0 %", """
VAR p = SELECTEDVALUE ( dim_article[prix_precedent] )
RETURN
    IF (
        NOT ISBLANK ( [Fenêtre (jours)] ),
        DIVIDE ( SELECTEDVALUE ( dim_article[prix_ttc] ) - p, p )
    )"""),
    ("8. Menu et marge", "Fenêtre brute (jours)", "0", """
VAR d = SELECTEDVALUE ( dim_article[valide_du] )
VAR prec = SELECTEDVALUE ( dim_article[debut_version_precedente] )
VAR arrete = CALCULATE ( MAX ( dim_date[date] ), REMOVEFILTERS ( dim_date ) )
VAR fin = COALESCE ( SELECTEDVALUE ( dim_article[valide_au] ), arrete )
RETURN
    IF (
        HASONEVALUE ( dim_article[prix_id] ) && NOT ISBLANK ( prec )
            && SELECTEDVALUE ( dim_article[etablissement_id] ) IN VALUES ( dim_etablissement[etablissement_id] ),
        VAR w = MIN ( 60, MIN ( DATEDIFF ( prec, d, DAY ), DATEDIFF ( d, fin, DAY ) + 1 ) )
        RETURN IF ( w >= 14, w )
    )"""),
]
for _nom, _sens in [("avant", "avant"), ("après", "apres")]:
    _borne = ("dim_date[date] >= d - w && dim_date[date] < d" if _sens == "avant"
              else "dim_date[date] >= d && dim_date[date] < d + w")
    MESURES.append(("8. Menu et marge", f"Quantités {_nom} le changement", "#,0", f"""
VAR d = SELECTEDVALUE ( dim_article[valide_du] )
VAR w = [Fenêtre brute (jours)]
VAR a = SELECTEDVALUE ( dim_article[article_id] )
RETURN
    IF (
        NOT ISBLANK ( w ),
        CALCULATE (
            [Quantités servies] + 0,
            REMOVEFILTERS ( dim_article ),
            dim_article[article_id] = a,
            REMOVEFILTERS ( dim_date ),
            FILTER ( ALL ( dim_date[date] ), {_borne} )
        )
    )"""))
MESURES += [
    ("8. Menu et marge", "Fenêtre (jours)", "0", """
VAR w = [Fenêtre brute (jours)]
RETURN
    IF ( NOT ISBLANK ( w ) && [Quantités avant le changement] + [Quantités après le changement] > 0, w )"""),
    ("8. Menu et marge", "Prix avant → après", None, """
IF (
    NOT ISBLANK ( [Hausse de prix] ),
    FORMAT ( SELECTEDVALUE ( dim_article[prix_precedent] ), "0.000" ) & " → " & FORMAT ( SELECTEDVALUE ( dim_article[prix_ttc] ), "0.000" )
)"""),
    ("8. Menu et marge", "Quantités avant → après", None, """
IF (
    NOT ISBLANK ( [Fenêtre (jours)] ),
    FORMAT ( [Quantités avant le changement], "0" ) & " → " & FORMAT ( [Quantités après le changement], "0" )
)"""),
    ("8. Menu et marge", "Écart des quantités", "+0 %;-0 %", """
VAR av = [Quantités avant le changement]
RETURN IF ( av > 0, DIVIDE ( [Quantités après le changement] - av, av ) )"""),
    ("8. Menu et marge", "Changements de prix", "#,0", """
CALCULATE (
    COUNTROWS ( dim_article ),
    dim_article[motif_changement] <> "creation",
    NOT ISBLANK ( dim_article[prix_precedent] ),
    TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_article[etablissement_id] ),
    TREATAS ( VALUES ( dim_date[date] ), dim_article[valide_du] )
)"""),
    ("8. Menu et marge", "Hausse moyenne", "+0.0 %;-0.0 %", """
VAR lignes =
    CALCULATETABLE (
        dim_article,
        dim_article[motif_changement] <> "creation",
        NOT ISBLANK ( dim_article[prix_precedent] ),
        TREATAS ( VALUES ( dim_etablissement[etablissement_id] ), dim_article[etablissement_id] ),
        TREATAS ( VALUES ( dim_date[date] ), dim_article[valide_du] )
    )
RETURN AVERAGEX ( lignes, DIVIDE ( dim_article[prix_ttc] - dim_article[prix_precedent], dim_article[prix_precedent] ) )"""),
    ("8. Menu et marge", "Texte changements", None, _fmt("[Changements de prix]", NB)),
    ("8. Menu et marge", "Texte changements détail", None, '"révisions et repositionnements sur la période"'),
    ("8. Menu et marge", "Texte hausse", None, _fmt("[Hausse moyenne]", '"+0.0 %;-0.0 %"')),
    ("8. Menu et marge", "Texte hausse détail", None,
     '"moyenne simple des " & FORMAT ( [Changements de prix], "0" ) & " changements"'),
    ("8. Menu et marge", "Catégorie de sensibilité", None,
     'SELECTEDVALUE ( dim_article[nom_categorie], "Toutes catégories" )'),
    ("8. Menu et marge", "Texte sensibilité", None, """
VAR c = [Catégorie de sensibilité]
VAR l = LOOKUPVALUE ( ml_elasticite_categorie[lecture], ml_elasticite_categorie[categorie], c )
VAR e = LOOKUPVALUE ( ml_elasticite_categorie[elasticite], ml_elasticite_categorie[categorie], c )
RETURN
    IF ( l = "non concluant", "non concluant", FORMAT ( e, "0.00" ) )"""),
    ("8. Menu et marge", "Texte sensibilité détail", None, """
VAR c = [Catégorie de sensibilité]
VAR b = LOOKUPVALUE ( ml_elasticite_categorie[bas_95], ml_elasticite_categorie[categorie], c )
VAR h = LOOKUPVALUE ( ml_elasticite_categorie[haut_95], ml_elasticite_categorie[categorie], c )
VAR l = LOOKUPVALUE ( ml_elasticite_categorie[lecture], ml_elasticite_categorie[categorie], c )
RETURN
    c & " · intervalle " & FORMAT ( b, "0.00" ) & " à " & FORMAT ( h, "0.00" ) & " · " & l"""),
    ("8. Menu et marge", "Titre prix et quantités", None, """
"Prix et quantités par article : " & IF ( HASONEVALUE ( dim_article[nom_article] ), SELECTEDVALUE ( dim_article[nom_article] ), "choisir un article" )"""),
]

# ------------------------------------------------------------------ recette T6.4 : valeurs attendues (SQL sur menuscan_dwh, 26/11/2026)
# (code, indicateur, filtre, attendu, tolérance, expression DAX)
_A26 = "dim_date[annee] = 2026"
RECETTE = [
    ("R01", "K01 Établissements actifs", "31/12/2026", 265, 0, "[K01 Établissements actifs]"),
    ("R02", "K02 MRR (DT HT)", "31/12/2026", 8510, 0, "[K02 MRR]"),
    ("R03", "K02 MRR (DT HT)", "31/12/2025", 5125, 0, "CALCULATE ( [K02 MRR], dim_date[annee] = 2025 )"),
    ("R04", "K03 ARR (DT HT)", "31/12/2026", 102120, 0, "[K03 ARR]"),
    ("R05", "K04 MRR nouveau", "2026", 4990, 0, f"CALCULATE ( [K04 MRR nouveau], {_A26} )"),
    ("R06", "K04 MRR expansion", "2026", 520, 0, f"CALCULATE ( [K04 MRR expansion], {_A26} )"),
    ("R07", "K04 MRR contraction", "2026", -20, 0, f"CALCULATE ( [K04 MRR contraction], {_A26} )"),
    ("R08", "K04 MRR perdu", "2026", -2105, 0, f"CALCULATE ( [K04 MRR perdu], {_A26} )"),
    ("R09", "Résiliations", "2026", 76, 0, f"CALCULATE ( [Résiliations], {_A26} )"),
    ("R10", "K05 Taux de résiliation mensuel", "2026", 0.0309194, 0.00005,
     f"CALCULATE ( [K05 Taux de résiliation mensuel], {_A26} )"),
    ("R11", "K06 Rétention à 12 mois", "cohorte T1 2025", 0.6296296, 0.00005,
     "CALCULATE ( [K06 Rétention de cohorte], 'Mois écoulés'[mois] = 12, dim_etablissement[trimestre_cohorte] = \"T1 2025\" )"),
    ("R12", "K07 Taux de conversion des prospects", "2024-2026", 0.1794301, 0.00005,
     "[K07 Taux de conversion des prospects]"),
    ("R13", "K08 Délai de signature médian (j)", "2024-2026", 18, 0, "[K08 Délai de signature médian]"),
    ("R14", "K09 CAC Parrainage", "2024-2026", 15.3571429, 0.0005,
     'CALCULATE ( [K09 CAC], dim_canal[nom_canal] = "Parrainage" )'),
    ("R15", "K09 CAC Salons professionnels", "2024-2026", 110.5263158, 0.0005,
     'CALCULATE ( [K09 CAC], dim_canal[nom_canal] = "Salons professionnels" )'),
    ("R16", "K10 Valeur vie client", "2026", 1025.74, 0.05, f"CALCULATE ( [K10 Valeur vie client], {_A26} )"),
    ("R17", "K11 Coût par clic", "2026", 0.1164094, 0.00005, f"CALCULATE ( [K11 Coût par clic], {_A26} )"),
    ("R18", "K11 Taux de clic", "2026", 0.0153677, 0.00005, f"CALCULATE ( [K11 Taux de clic], {_A26} )"),
    ("R19", "K12 Sessions par table et par jour", "2026", 0.1281513, 0.00005,
     f"CALCULATE ( [K12 Sessions par table et par jour], {_A26} )"),
    ("R20", "K13 Taux de commande", "formule Commande", 0.5999430, 0.00005,
     'CALCULATE ( [K13 Taux de commande], dim_formule[nom_formule] = "Commande" )'),
    ("R21", "K13 Taux de commande", "formule Pro", 0.6654206, 0.00005,
     'CALCULATE ( [K13 Taux de commande], dim_formule[nom_formule] = "Pro" )'),
    ("R22", "K14 Panier moyen (DT TTC)", "2024-2026", 23.4379617, 0.00005, "[K14 Panier moyen]"),
    ("R23", "K15 Taux d'annulation", "2024-2026", 0.0303738, 0.00005, "[K15 Taux d'annulation]"),
    ("R24", "Commandes", "2026", 64977, 0, f"CALCULATE ( [Commandes], {_A26} )"),
    ("R25", "CA des commandes servies (DT TTC)", "2026", 1467087.921, 0.001,
     f"CALCULATE ( [CA commandes servies TTC], {_A26} )"),
    ("R26", "K16 Facturé (DT HT)", "2026", 103760, 0.001, f"CALCULATE ( [K16 Facturé HT], {_A26} )"),
    ("R27", "K16 Encaissé (DT TTC)", "2026", 122439.1, 0.001, f"CALCULATE ( [K16 Encaissé TTC], {_A26} )"),
    ("R28", "K17 Factures payées en retard", "2026", 0.0987230, 0.00005,
     f"CALCULATE ( [K17 Taux de factures payées en retard], {_A26} )"),
    ("R29", "K17 Factures impayées", "2026", 25, 0, f"CALCULATE ( [K17 Factures impayées], {_A26} )"),
    ("R30", "K18 Délai de résolution médian (h)", "2024-2026", 5.6, 0.00005, "[K18 Délai de résolution médian (h)]"),
    ("R31", "K18 Satisfaction moyenne", "2024-2026", 3.9239130, 0.00005, "[K18 Satisfaction moyenne]"),
    ("R32", "K20 Étape 1 Article consulté", "formule Commande", 0.8664309, 0.00005,
     'CALCULATE ( [K20 Étape 1 Article consulté], dim_formule[nom_formule] = "Commande" )'),
    ("R33", "K20 Étape 2 Panier", "formule Commande", 0.6797388, 0.00005,
     'CALCULATE ( [K20 Étape 2 Panier], dim_formule[nom_formule] = "Commande" )'),
    ("R34", "K21 Marge brute estimée (DT TTC)", "2026", 1093756.116, 0.001,
     f"CALCULATE ( [K21 Marge brute estimée TTC], {_A26} )"),
    ("R35", "K21 Taux de coût estimé", "2026", 0.2533099, 0.00005, f"CALCULATE ( [K21 Taux de coût estimé], {_A26} )"),
    ("R36", "K22 Nombre de vedettes", "2026", 1078, 0, f"CALCULATE ( [K22 Nombre de vedettes], {_A26} )"),
    ("R37", "K22 Nombre de chevaux de labour", "2026", 1487, 0,
     f"CALCULATE ( [K22 Nombre de chevaux de labour], {_A26} )"),
    ("R38", "K22 Nombre d'énigmes", "2026", 1006, 0, f"CALCULATE ( [K22 Nombre d'énigmes], {_A26} )"),
    ("R39", "K22 Nombre de poids morts", "2026", 1123, 0, f"CALCULATE ( [K22 Nombre de poids morts], {_A26} )"),
    ("R40", "K23 Part du soir en Ramadan", "2024-2026", 0.9177434, 0.00005, "[K23 Part du soir en Ramadan]"),
    ("R41", "K23 Part du soir hors Ramadan", "2024-2026", 0.3331768, 0.00005, "[K23 Part du soir hors Ramadan]"),
    # phase 7 (T7.4) : valeurs attendues calculées en SQL sur le schéma ml le 27/11/2026
    ("R42", "K19 Établissements scorés", "31/12/2026", 265, 0, "[Établissements scorés]"),
    ("R43", "K19 Établissements en alerte", "31/12/2026", 27, 0, "[Établissements en alerte K19]"),
    ("R44", "K19 MRR menacé (DT HT)", "31/12/2026", 850, 0, "[MRR menacé]"),
    ("R45", "K19 Probabilité moyenne", "31/12/2026", 0.037358, 0.000001,
     "AVERAGE ( ml_score_resiliation[probabilite] )"),
    ("R46", "Candidats à la formule Commande", "31/12/2026", 47, 0, "[Candidats Commande]"),
    ("R47", "Recommandations de plats (Pro)", "carte actuelle", 749, 0, "COUNTROWS ( ml_recommandation_plat )"),
    ("R48", "Recommandations de plats", "Café Ennour", 21, 0,
     'CALCULATE ( COUNTROWS ( ml_recommandation_plat ), dim_etablissement[etablissement_id] = "ETB0003" )'),
    ("R49", "Élasticité-prix toutes catégories", "2024-2026", -0.6978, 0.001,
     'LOOKUPVALUE ( ml_elasticite_categorie[elasticite], ml_elasticite_categorie[categorie], "Toutes catégories" )'),
]


def _ch(s):
    return '"' + s.replace('"', '""') + '"'


TABLES_CALCULEES.append((
    "Recette", [("code", "string"), ("indicateur", "string"), ("filtre", "string"), ("attendu", "double"),
                ("tolerance", "double")], None,
    'DATATABLE ( "code", STRING, "indicateur", STRING, "filtre", STRING, "attendu", DOUBLE, "tolerance", DOUBLE, { '
    + ", ".join(f"{{ {_ch(c)}, {_ch(i)}, {_ch(f)}, {a}, {t} }}" for c, i, f, a, t, _ in RECETTE) + " } )"))

MESURES += [
    ("10. Recette", "Recette valeur", "#,0.0000", "SWITCH (\n    SELECTEDVALUE ( Recette[code] ),\n"
     + ",\n".join(f'    "{c}", {e}' for c, *_, e in RECETTE) + "\n)"),
    ("10. Recette", "Recette attendu", "#,0.0000", "SELECTEDVALUE ( Recette[attendu] )"),
    ("10. Recette", "Recette écart", "#,0.0000", """
IF ( HASONEVALUE ( Recette[code] ), [Recette valeur] - [Recette attendu] )"""),
    ("10. Recette", "Recette statut", None, """
VAR v = [Recette valeur]
RETURN
    IF (
        HASONEVALUE ( Recette[code] ),
        IF ( ISBLANK ( v ), "ABSENT", IF ( ABS ( v - [Recette attendu] ) <= SELECTEDVALUE ( Recette[tolerance] ) + 1E-9, "OK", "ÉCART" ) )
    )"""),
    ("10. Recette", "Couleur statut", None, f"""
SWITCH ( [Recette statut], "OK", "#DCFCE7", "ÉCART", "#FEE2E2", "ABSENT", "#FEF3C7" )"""),
    ("10. Recette", "Texte recette", None, """
VAR ok = COUNTROWS ( FILTER ( VALUES ( Recette[code] ), [Recette statut] = "OK" ) )
RETURN FORMAT ( ok, "0" ) & " / " & FORMAT ( COUNTROWS ( Recette ), "0" ) & " contrôles conformes\""""),
    ("10. Recette", "Texte recette détail", None,
     '"valeurs attendues calculées en SQL : R01 à R41 le 26/11/2026, R42 à R49 (schéma ml) le 27/11/2026"'),
]
