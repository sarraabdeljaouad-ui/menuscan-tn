# 07_powerbi : rapports Power BI (phase 6)

Auteure : Sarra Abdeljaouad

Ce dossier contient le projet Power BI complet de MenuScan TN, au format PBIP : un modèle sémantique partagé et deux rapports. Tous les fichiers sont en texte (TMDL pour le modèle, JSON pour les rapports) et sont **générés** par un script à partir du schéma `marts` de PostgreSQL.

| Élément | Rôle |
|---|---|
| `MenuScan.SemanticModel/` | Modèle partagé : 17 tables en Import, 4 tables calculées (axes), 32 relations, 165 mesures, 1 rôle de sécurité |
| `MenuScan_Startup.pbip` | Rapport Startup, pour la direction de MenuScan : TB-1 Croissance, TB-2 Rétention, TB-3 Acquisition, TB-4 Pilotage |
| `MenuScan_Etablissement.pbip` | Rapport Établissement, pour les gérants : TB-5 Activité, TB-6 Menu, TB-7 Temps, TB-8 Prix |
| `outils/generer_pbip.py` | Génère tout le projet |
| `outils/modele_def.py` | Relations, mesures DAX et rôle de sécurité |
| `outils/rapports_def.py` | Pages et visuels des deux rapports |

## 1. Le modèle

- **Mode Import** : les données sont copiées dans Power BI. On clique sur **Actualiser** pour charger les données de la nuit.
- **Modèle en étoile** : 9 tables de faits (dont `fait_vue_article`, ajoutée pour la page TB-6), 8 dimensions. Chaque relation va d'un fait vers une dimension (plusieurs vers un, filtre dans un seul sens). Aucune relation entre dimensions.
- **Mesures** : toutes dans la table `_Mesures`, rangées par dossier (0. Bases à 9. Saisonnalité). Ce sont les KPI K01 à K23 du référentiel, sauf K06 (cohortes) et K19 (score de risque, phase 7).
- **Paramètres** : `Serveur` (localhost:5440) et `Base` (menuscan_dwh), modifiables dans Power Query.
- **Date/heure automatique désactivée** : la table `dim_date` est marquée comme table de dates.
- **Sécurité par ligne (RLS)** : le rôle `Gérant démo` ne voit que le Café Ennour (ETB0003). Il filtre les établissements, les articles et les tables, et masque le marketing et les prospects. Le rattachement à de vrais comptes de gérants (fonction `USERPRINCIPALNAME`) viendra en phase 9, avec les comptes de l'application.

## 2. Ouvrir le projet

1. Démarre PostgreSQL : `docker compose up -d postgres`.
2. Dans Power BI Desktop, **Fichier > Ouvrir**, choisis `07_powerbi/MenuScan_Startup.pbip`.
3. Un bandeau signale que les tables n'ont pas de données : clique sur **Actualiser maintenant**.
4. Si Power BI demande les identifiants : onglet **Base de données**, utilisateur `POSTGRES_USER` et mot de passe `POSTGRES_PASSWORD` du fichier `.env`.
5. Si la connexion est refusée pour une raison de chiffrement : **Fichier > Options et paramètres > Paramètres de la source de données**, sélectionne `localhost:5440;menuscan_dwh`, **Modifier les autorisations**, décoche **Chiffrer les connexions**.
6. Enregistre (Ctrl+S).

**Le rapport Établissement** utilise le même modèle. Ferme d'abord le rapport Startup, puis ouvre `MenuScan_Etablissement.pbip`. Deux rapports ouverts en même temps modifieraient le même modèle.

**Tester la sécurité** : dans le rapport Établissement, **Modélisation > Afficher en tant que**, coche `Gérant démo`. Seul le Café Ennour doit rester dans le filtre Établissement.

## 3. Régénérer le projet

Après un changement dans les marts ou dans les fichiers `outils/*_def.py` :

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
| Scores K19, MRR menacé, sensibilité au prix | Mention « [phase 7] » | Produits par les modèles de la phase 7 |
| Période de 6 mois, Café Les Arcades | Période et établissement au choix | Les maquettes montraient un échantillon |


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

Calculées en SQL sur `menuscan_dwh` le 26/11/2026. Mets la mesure dans une carte, avec le filtre indiqué.

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
- **K22 Classe du plat** se lit plat par plat, à l'intérieur d'un établissement. Les nombres de plats par classe peuvent prendre quelques secondes à calculer.
- **K21 et K22** reposent sur des taux de coût estimés (seed `taux_cout_categorie`), pas sur des coûts réels.
- **Pas encore dans les rapports** : K06 (matrice de cohortes, page TB-2), K19 (score de risque, phase 7) et les plats recommandés (EF-12, phases 7 et 8).
