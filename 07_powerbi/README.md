# 07_powerbi : rapports Power BI (phases 6 et 7)

Auteure : Sarra Abdeljaouad

Ce dossier contient le projet Power BI complet de MenuScan TN, au format PBIP : un modèle sémantique partagé et deux rapports. Tous les fichiers sont en texte (TMDL pour le modèle, JSON pour les rapports) et sont **générés** par un script à partir des schémas `marts` (entrepôt dbt) et `ml` (résultats de la phase 7) de PostgreSQL.

| Élément | Rôle |
|---|---|
| `MenuScan.SemanticModel/` | Modèle partagé : 23 tables en Import (17 du schéma `marts`, 6 du schéma `ml`), 5 tables calculées (axes et recette), 35 relations, 184 mesures, 1 rôle de sécurité |
| `MenuScan_Startup.pbip` | Rapport Startup, pour la direction de MenuScan : TB-1 Croissance, TB-2 Rétention, TB-3 Acquisition, TB-4 Pilotage, page Recette T6.4 |
| `MenuScan_Etablissement.pbip` | Rapport Établissement, pour les gérants : TB-5 Activité, TB-6 Menu, TB-7 Temps, TB-8 Prix |
| `outils/generer_pbip.py` | Génère tout le projet |
| `outils/modele_def.py` | Relations, mesures DAX et rôle de sécurité |
| `outils/rapports_def.py` | Pages et visuels des deux rapports |

## 1. Le modèle

- **Mode Import** : les données sont copiées dans Power BI. On clique sur **Actualiser** pour charger les données de la nuit.
- **Modèle en étoile** : 9 tables de faits (dont `fait_vue_article`, ajoutée pour la page TB-6), 8 dimensions. Chaque relation va d'un fait vers une dimension (plusieurs vers un, filtre dans un seul sens). Aucune relation entre dimensions.
- **Tables `ml_…` (phase 7)** : scores de résiliation K19, candidats à la formule Commande, plats recommandés, élasticités, règles d'association et registre des modèles. Elles sont écrites par `08_analyse_ml/03_machine_learning/04_publication_resultats`. Les trois premières sont reliées à `dim_etablissement` : le rôle de sécurité les filtre aussi.
- **Mesures** : toutes dans la table `_Mesures`, rangées par dossier (0. Bases à 10. Recette). Ce sont les KPI K01 à K23 du référentiel, sauf K06 (cohortes).
- **Paramètres** : `Serveur` (localhost:5440) et `Base` (menuscan_dwh), modifiables dans Power Query.
- **Date/heure automatique désactivée** : la table `dim_date` est marquée comme table de dates.
- **Sécurité par ligne (RLS)** : le rôle `Gérant démo` ne voit que le Café Ennour (ETB0003). Il filtre les établissements, les articles et les tables, et masque le marketing et les prospects. Le rattachement à de vrais comptes de gérants (fonction `USERPRINCIPALNAME`) viendra en phase 9, avec les comptes de l'application.

## 2. Ouvrir le projet

1. Démarre PostgreSQL : `docker compose up -d postgres`. Le schéma `ml` doit exister : sinon, exécute d'abord `08_analyse_ml/03_machine_learning/04_publication_resultats` (voir `08_analyse_ml/00_ordre_execution.md`).
2. Dans Power BI Desktop, **Fichier > Ouvrir**, choisis `07_powerbi/MenuScan_Startup.pbip`.
3. Un bandeau signale que les tables n'ont pas de données : clique sur **Actualiser maintenant**.
4. Si Power BI demande les identifiants : onglet **Base de données**, utilisateur `POSTGRES_USER` et mot de passe `POSTGRES_PASSWORD` du fichier `.env`.
5. Si la connexion est refusée pour une raison de chiffrement : **Fichier > Options et paramètres > Paramètres de la source de données**, sélectionne `localhost:5440;menuscan_dwh`, **Modifier les autorisations**, décoche **Chiffrer les connexions**.
6. Enregistre (Ctrl+S).

**Le rapport Établissement** utilise le même modèle. Ferme d'abord le rapport Startup, puis ouvre `MenuScan_Etablissement.pbip`. Deux rapports ouverts en même temps modifieraient le même modèle.

**Tester la sécurité** : dans le rapport Établissement, **Modélisation > Afficher en tant que**, coche `Gérant démo`. Seul le Café Ennour doit rester dans le filtre Établissement.

## 3. Régénérer le projet

Après un changement dans les marts, dans le schéma `ml` ou dans les fichiers `outils/*_def.py` (le script lit les colonnes des deux schémas : `ml` doit avoir été publié) :

```
python 07_powerbi/outils/generer_pbip.py
```

Ferme Power BI avant. Le script remplace les dossiers du modèle et des rapports : une modification faite à la main dans Power BI serait perdue. Les changements se font donc dans `outils/`, puis on régénère.

## 4. Lire les pages

Les pages suivent les maquettes (`Maquettes des tableaux de bord`) : bandeau bleu avec navigation entre les pages, filtres en haut, chiffres clés, puis graphiques. Les chiffres clés sont des mesures texte (dossiers « Texte … ») : elles affichent l'unité et la comparaison à l'année précédente.

**Écarts avec les maquettes :**

| Maquette | Rapport | Raison |
|---|---|---|
| Fond rose sur les semaines de Ramadan (TB-5) | Barres orange pour ces semaines | Power BI ne trace pas de zone de fond sur un axe |
| Top 10 des tables, top 8 des articles | Toutes les lignes, triées | Un filtre « N premiers » reste à poser à la main |
| Diagonale VVC = 3 × CAC (TB-3) | Nuage de points sans diagonale | Pas de ligne de référence oblique dans ce visuel |
| Étapes « En discussion », « Démo faite » (TB-3) | Contactés, en cours ou signés, signés | Le jeu de données n'a que trois statuts : perdu, en cours, converti |
| Plats recommandés (TB-8) en encadré de texte | Tableau « Plats recommandés » | Liste produite en phase 7 (EF-12) ; graphique et tableau de prix raccourcis pour lui faire de la place |
| Période de 6 mois, Café Les Arcades | Période et établissement au choix | Les maquettes montraient un échantillon |
| Colonne Catégorie du tableau des articles (TB-6) | Filtre Catégorie en haut de page | Place gagnée pour la marge et la classe du plat (K22) |
| Tous les changements de prix (TB-8) | Changements avec au moins 14 jours de recul, fenêtre de 60 jours au plus | Une fenêtre de quelques jours ne contient presque aucune vente |


| Page | Question à laquelle elle répond |
|---|---|
| TB-1 Croissance | Le parc et le revenu récurrent progressent-ils, et d'où vient la variation du MRR ? |
| TB-2 Rétention | Combien d'établissements partent, pourquoi, et selon leur canal d'arrivée ? |
| TB-3 Acquisition | Quel canal coûte le moins cher par établissement signé ? |
| TB-4 Pilotage | Quels établissements utilisent peu le menu, paient en retard ou sont insatisfaits ? |
| TB-5 Activité | Combien l'établissement vend, à quelles tables et dans quelles zones ? |
| TB-6 Menu | Quels plats sont populaires et rentables (vedettes) ou à revoir (poids morts) ? |
| TB-7 Temps | À quelles heures l'activité se concentre-t-elle, et comment le Ramadan la déplace-t-il ? |
| TB-8 Prix | Comment les prix ont changé et ce que sont devenues les ventes ensuite |

## 5. Valeurs attendues (recette)

La page **Recette T6.4** du rapport Startup compare automatiquement 49 valeurs attendues (table calculée `Recette`, définie dans `outils/modele_def.py`) aux valeurs calculées par le modèle, avec un statut OK, ÉCART ou ABSENT. Les valeurs attendues ont été calculées en SQL sur `menuscan_dwh` : R01 à R41 le 26/11/2026, R42 à R49 (schéma `ml`, phase 7) le 27/11/2026. Le tableau ci-dessous en reprend les principales.

| Mesure | Filtre | Valeur attendue |
|---|---|---|
| K01 Établissements actifs | aucun (dernier mois : décembre 2026) | 265 |
| K02 MRR | aucun | 8 510 |
| K02 MRR | annee = 2025 | 5 125 |
| K03 ARR | aucun | 102 120 |
| K04 MRR nouveau / expansion / contraction / perdu | annee = 2026 | 4 990 / 520 / -20 / -2 105 |
| Résiliations | annee = 2026 | 76 |
| K05 Taux de résiliation mensuel | annee = 2026 | 3,09 % |
| K07 Taux de conversion des prospects | aucun | 17,9 % |
| K08 Délai de signature médian | aucun | 18 |
| K09 CAC | aucun, par nom_canal | Parrainage 15,4 ; terrain 70,8 ; Facebook / Instagram 71,0 ; TikTok 43,9 ; salons 110,5 |
| K10 Valeur vie client | annee = 2026 | environ 1 026 |
| K11 Coût par clic / Taux de clic | annee = 2026 | 0,116 / 1,54 % |
| K12 Sessions par table et par jour | annee = 2026 | 0,128 |
| K13 Taux de commande | par nom_formule | Commande 60,0 % ; Pro 66,5 % |
| K20 Étapes 1 / 2 / 3 | nom_formule = Commande | 86,6 % / 68,0 % / 60,0 % |
| K14 Panier moyen | aucun | 23,44 |
| K15 Taux d'annulation | aucun | 3,04 % |
| Commandes / CA commandes servies TTC | annee = 2026 | 64 977 / 1 467 088 |
| K16 Facturé HT / Encaissé TTC | annee = 2026 | 103 760 / 122 439 |
| K17 Taux de factures payées en retard / impayées | annee = 2026 | 9,9 % / 25 |
| K18 Délai médian / satisfaction | aucun | 5,6 h / 3,92 |
| K21 Marge brute estimée / Taux de coût | annee = 2026 | 1 093 756 / 25,3 % |
| K22 Nombre de vedettes / chevaux de labour / énigmes / poids morts | annee = 2026 | 1 078 / 1 487 / 1 006 / 1 123 |
| K23 Part du soir en Ramadan / hors Ramadan | aucun | 91,8 % / 33,3 % |
| K19 Établissements scorés / en alerte | aucun | 265 / 27 |
| K19 MRR menacé (DT HT) | aucun | 850 |
| Candidats Essentiel → Commande | aucun | 47 |
| Plats recommandés (Pro) / dont Café Ennour | aucun | 749 / 21 |
| Élasticité-prix toutes catégories | aucun | -0,70 |

### Écarts connus avec le cahier des charges (D5)

Le cahier des charges a été chiffré en phase 0 sur les données de référence. L'entrepôt part des données brutes nettoyées. Trois écarts sont attendus :

| Valeur | D5 | Entrepôt | Cause |
|---|---|---|---|
| CAC du parrainage | 17,3 | 15,4 | Une dépense de parrainage de -110 DT est en quarantaine (règle DQ-23, dépense négative). |
| Commandes 2026 | 64 988 | 64 977 | 11 commandes en transit, non reçues à la date d'arrêté (décision D-32). |
| Montant des commandes servies 2026 | 1 467 230 | 1 467 088 | Mêmes 11 commandes. |

## 6. Limites connues des mesures

- **K01 et K02** donnent la valeur du **dernier mois** de la période filtrée, pas une somme.
- **K12** suppose une période continue (pas de dates isolées). Le dénominateur ne suit pas le filtre de formule.
- **K22 Classe du plat** se lit plat par plat, à l'intérieur d'un établissement. Corrigé le 28/11/2026 : la colonne restait vide hors rôle Gérant démo, car `dim_article` n'est pas reliée à `dim_etablissement` (la mesure passe désormais par `TREATAS`).
- **Textes du Ramadan et de l'été (TB-7)** : si l'établissement n'a aucune commande sur l'une des périodes (ouvert après le Ramadan, par exemple), ils affichent « aucune commande » ou « comparaison impossible » au lieu d'une heure de pointe fausse ou de -100 % (corrigé le 28/11/2026). Les nombres de plats par classe peuvent prendre quelques secondes à calculer.
- **K21 et K22** reposent sur des taux de coût estimés (seed `taux_cout_categorie`), pas sur des coûts réels.
- **Établissement = nom · ville** : 403 établissements portent seulement 214 noms (cinq « Café Ennour »). La colonne calculée `dim_etablissement[etablissement]` sert dans les filtres et les tableaux ; avant la phase 7, un filtre sur le nom regroupait les homonymes.
- **K19 et les résultats `ml`** sont une photo au 31/12/2026 : ils ne suivent pas le filtre de dates. Ils changent quand on republie le schéma `ml`, pas quand on actualise seulement les marts.
- **Élasticité (TB-8)** : la tuile affiche la catégorie choisie dans le filtre Catégorie, sinon la valeur toutes catégories. « non concluant » signifie trop peu de changements de prix pour conclure.
- **Pas encore dans les rapports** : K06 (matrice de cohortes, page TB-2).
