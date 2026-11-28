# Application MenuScan TN

Deux applications Streamlit (phase 1, tâche T1.3), qui suivent les maquettes validées le 24/11/2026 et partagent la base applicative `menuscan_app` (schéma `menuscan`) :

- **l'application client**, ouverte par le QR code de la table, sans compte : menu, panier, suivi de la commande ;
- **l'application équipe** (back-office), avec connexion : écran du serveur ou du gérant selon le rôle (décision D-25).

## Lancement

Conteneur PostgreSQL démarré, base chargée et migrée, environnement Python activé. Deux terminaux :

```bash
python 02_oltp/charger_base_app.py --migrer   # une fois, sur une base chargée avant les migrations 001 à 010
python 02_oltp/copier_resultats_ml.py         # après chaque publication du schéma ml (phase 7) : scores et plats recommandés

cd 01_application/client
streamlit run app.py                          # application client : http://localhost:8501/?table=TBL00079

cd 01_application/equipe
streamlit run app.py                          # application équipe : http://localhost:8502
```

Chaque application lit sa configuration (thème, port) dans son dossier `.streamlit/` : il faut la lancer depuis son dossier. L'adresse de l'application client, utilisée par les liens de démonstration et plus tard par les QR codes, se règle avec `CLIENT_URL` dans `.env` (par défaut `http://localhost:8501`).

## Fichiers

| Fichier | Rôle |
|---|---|
| `commun/db.py` | Toutes les lectures et écritures en base, connexion des comptes |
| `commun/theme.py` | Couleurs, polices (Inter, Plus Jakarta Sans), cartes, barre de panier fixe |
| `client/app.py` | Application client : menu, panier, suivi de la commande |
| `equipe/app.py` | Application équipe : navigation selon la connexion et le rôle, déconnexion |
| `equipe/vues/accueil.py` | Page publique : présentation, chiffres de la base, formules, tables de démonstration, comptes de démonstration |
| `equipe/vues/connexion.py` | Connexion : identifiant et mot de passe |
| `equipe/vues/tableau.py` | Écran du gérant (tableau de bord) ou du serveur (service) |
| `equipe/vues/qr_codes.py` | Tables et QR codes (gérant) : un QR par table, PNG et planche PDF à imprimer |
| `equipe/vues/recommandations.py` | Plats recommandés (gérant, formule Pro) : plats à mettre en avant, « souvent pris avec » chaque plat de la carte |
| `equipe/vues/risques.py` | Espace MenuScan (rôle `menuscan`) : établissements à risque de résiliation avec leurs facteurs, candidats à la formule Commande |
| `commun/qr.py` | Génération des QR codes, des cartes de table et de la planche PDF (A4, 6 cartes par page) |
| `qr/generer_qr.py` | Même génération en ligne de commande, écrite dans `qr/sortie/` (exclu de Git) |

Les dossiers ne s'appellent pas `pages/` : ce nom déclencherait l'ancienne navigation automatique de Streamlit.

## Comptes et rôles (migrations 002 et 010)

Deux comptes de démonstration par établissement : `gerant.etbXXXX` et `serveur.etbXXXX` (par exemple `gerant.etb0005` pour le Café Les Arcades). Mot de passe de démonstration commun : `Demo2026!`. Les mots de passe sont hachés avec bcrypt (extension `pgcrypto`) et comparés par PostgreSQL ; ils ne sont jamais stockés en clair.

| Fonction | Serveur | Gérant |
|---|---|---|
| Commandes en direct : accepter, marquer prête, servir, annuler | Oui | Oui |
| Appels des clients : prise en charge (« Je m'en occupe ») | Oui | Oui |
| Plan de salle cliquable : fenêtre de la table, actions, encaissement | Oui | Oui |
| Prendre une commande pour un client sans téléphone (fenêtre de la table) | Oui | Oui |
| Chiffre du jour, panier moyen, délai, taux de commande | Non | Oui |
| Meilleures ventes du mois | Non | Oui |
| Ouvrir ou fermer les commandes | Non | Oui |
| Activité des tables : recherche, comparaison, historique, avis des clients, export CSV | Non | Oui |
| Menu : mettre un article en rupture pour la journée | Oui | Oui |
| Menu : changer un prix, une description, un coût de revient, retirer, remettre ou ajouter un article | Non | Oui |
| Clôture de la journée : encaissements par mode, servies, annulées, reste à encaisser, ventes et marges, export CSV | Non | Oui |
| Tables et QR codes : ajouter, renuméroter, changer de zone ou de places, retirer ou remettre une table | Non | Oui |
| Plats recommandés (formule Pro seulement) | Non | Oui |

**Rester connecté :** après la connexion, l'appareil reste connecté, même après une actualisation ou la fermeture du navigateur, jusqu'au bouton « Se déconnecter ». La connexion expire seulement après 30 jours sans utilisation ; chaque ouverture de l'application relance ce délai. Le navigateur garde un jeton aléatoire dans un cookie ; la base n'en garde que l'empreinte SHA-256. Le gérant dispose d'un bouton « Déconnecter partout », qui déconnecte tous les appareils des comptes de son établissement (appareil perdu, départ d'un serveur).

Les droits sont vérifiés à chaque exécution de l'écran, pas seulement par la navigation. Chaque écriture de l'équipe est limitée à l'établissement du compte connecté : un compte ne peut pas avancer ni annuler la commande d'un autre établissement.

## Pages

| Application | Adresse | Contenu |
|---|---|---|
| Client | `/?table=TBL00001` | En-tête de l'établissement, bouton FR · ع, recherche, catégories, articles avec description et badge « Populaire » ; toucher un article ouvre sa fiche (description, préférences sans effet sur le prix comme « Sans sucre » ou « Sans glaçons », quantité) ; cloche d'appel avec motif (serveur, eau, addition) ; panier avec note pour le serveur ; suivi de la commande en 4 étapes, mis à jour toutes les 10 secondes ; heure de service estimée tant que la commande n'est pas prête (heure de commande + délai moyen de l'établissement sur 30 jours) ; bandeau vert « Votre commande est prête ! », titre de l'onglet « ✅ Commande prête ! » et vibration sur Android ; carte « Votre avis » (1 à 5 étoiles, commentaire facultatif) une fois servie ; « Commander autre chose » et liste « Mes commandes » avec le total de la visite et les commandes réglées |
| Équipe | `/` | Accueil public |
| Équipe | `/connexion` | Connexion |
| Équipe | `/menu` | Serveur et gérant : articles de la carte par catégorie, recherche, interrupteur « Rupture » (l'article disparaît du menu client pour la journée). Gérant : bouton « Modifier » (prix, description, retrait), ajout d'un article, articles retirés à remettre, prix programmé affiché (« → 2,300 DT à partir du 25/11 ») |
| Équipe | `/cloture` | Gérant seulement : choix de la journée (aujourd'hui par défaut, bornée à maintenant), encaissé et chiffre servi, panier moyen, annulations et motifs, délai de service, alerte « Reste à encaisser » par table, encaissements par mode de règlement, appels, avis, ruptures, ventes par article avec coût et marge quand le coût de revient est saisi, export CSV |
| Équipe | `/activite` | Gérant seulement : période (aujourd'hui, 7 jours, 30 jours, mois en cours ou dates choisies), recherche par numéro ou par zone, tableau comparatif des tables (visites, commandes servies et annulées, chiffre, panier moyen, délai, appels), puis historique de la table choisie : indicateurs, commandes avec articles, statut, délai et règlement (export CSV), appels avec délai de prise en charge |
| Équipe | `/qr` | Gérant seulement : un QR code par table, lien encodé, PNG par table et planche PDF à imprimer ; « ＋ Ajouter une table » (QR code affiché et téléchargeable tout de suite) ; crayon sur chaque carte pour changer le numéro, la zone ou les places, ou retirer la table du service ; tables retirées à remettre en service |
| Équipe | `/tableau` | Gérant : ouverture des commandes, 5 indicateurs, appels, commandes en direct, meilleures ventes, plan de salle. Serveur : 4 compteurs (dont les tables à encaisser), appels, commandes en direct, plan de salle. Mise à jour toutes les 10 secondes |

**Plan de salle (lot 1) :** chaque table est un bouton coloré selon son état, du plus urgent au moins urgent : appel en attente, commande en cours, servi à encaisser, menu ouvert depuis moins de 30 minutes, libre. Toucher une table ouvre sa fenêtre : appels à prendre en charge, commandes avec leur bouton d'étape, puis le total à encaisser avec le mode de règlement. Le bouton « Prendre une commande » ouvre une saisie (catégorie, recherche, quantités, note) : la commande part directement en préparation. Chaque commande en cours porte un chronomètre : vert sous 5 minutes, orange de 5 à 9, rouge à partir de 10. La fenêtre reste ouverte après chaque action et se ferme après l'encaissement ; un message confirme le montant encaissé. Une table encaissée redevient libre, sauf si un client y rouvre le menu.

## QR codes et test depuis un téléphone

Chaque QR code encode `CLIENT_URL/?table=<identifiant de la table>`. Pour qu'un téléphone l'ouvre :

1. Le téléphone et le PC sont sur le même Wi-Fi.
2. Dans `.env`, `CLIENT_URL` contient l'adresse réseau du PC, celle que Streamlit affiche comme « Network URL » au lancement de l'application client (par exemple `CLIENT_URL=http://192.168.1.222:8501`). Relancer ensuite l'application équipe.
3. Au premier lancement, Windows peut demander d'autoriser Python dans le pare-feu : accepter pour les réseaux **privés** seulement.

En ligne de commande : `python 01_application/qr/generer_qr.py ETB0005` (option `--url` pour forcer une adresse). Les QR codes ont été vérifiés avec un décodeur : chacun renvoie l'adresse de sa table.

## Parcours d'une commande

| Étape | Statut | Action | Heure enregistrée |
|---|---|---|---|
| Reçue | `nouvelle` | Le client envoie la commande | `date_heure_commande` |
| En préparation | `en_prepa` | Le gérant clique sur « Accepter » | `date_heure_acceptation` |
| Prête | `prete` | Le gérant clique sur « Marquer prête » | `date_heure_prete` |
| Servie | `servie` | L'équipe clique sur « Servie » | `date_heure_service` |
| Réglée | `servie` | L'équipe encaisse la table dans sa fenêtre, avec le mode de règlement ; toutes les commandes servies non réglées de la table sont encaissées ensemble | `date_heure_reglement`, `mode_reglement` |
| Annulée | `annulee` | Le gérant clique sur « Annuler » (nouvelle commande seulement) | – |

Les commandes du jeu de données n'ont que `servie` ou `annulee`, sans heure d'acceptation ni de préparation.

## Règles appliquées

| Règle | Application |
|---|---|
| Formule | Essentiel : menu consultable seulement. Commande et Pro : panier et commande. La formule est celle de l'abonnement en vigueur le jour même (comme le contrôle DQ-09). |
| Commandes fermées | Si le gérant ferme les commandes, le menu reste consultable mais le bouton d'envoi est désactivé ; la base refuse aussi la commande. L'équipe peut toujours prendre une commande en salle (formules Commande et Pro seulement, DQ-09). |
| Session | Un scan ouvre une session et écrit `scan_qr` et `vue_menu`. Ouvrir la fiche d'un article écrit `vue_article` et incrémente `nb_articles_vus`, comme dans les données générées. Chaque action ajoute un événement et prolonge la fin de session (DQ-11). |
| Une commande par session | « Commander autre chose » ouvre une nouvelle session (DQ-12), rattachée à la même visite par le jeton du client. |
| Appels | Un même motif ne peut pas être demandé deux fois tant que le premier appel n'est pas pris en charge. Chaque appel écrit aussi l'événement `appel_serveur`, comme dans les données générées. Encaisser une table clôt ses demandes d'addition. |
| Prix | Relus en base au moment de la commande, selon l'historique des prix (DQ-06). |
| Montants | Ligne = prix × quantité ; total, nombre de lignes et d'articles cohérents (DQ-03, DQ-04). |
| Populaire | Les 5 articles les plus servis de l'établissement sur les 30 derniers jours. |
| État des tables | Appel du serveur depuis moins de 15 min, sinon commande active, sinon menu ouvert depuis moins de 30 min, sinon libre. |
| Indicateurs | Chiffre et commandes du jour jusqu'à l'heure courante, comparés au même jour de la semaine précédente à la même heure ; panier moyen, délai de service et taux de commande depuis le 1er du mois. |
| Identifiants | Séquences PostgreSQL calées sur le plus grand identifiant existant (`SES`, `EVT`, `CMD`, `LIG`). |
| Heure | Heure de Tunis (UTC+1, pas d'heure d'été), comme les données existantes. |

Après un parcours complet (commande, quatre étapes par le gérant et le serveur, annulation, fermeture des commandes), les 23 contrôles de `02_oltp/controles_qualite.sql` restent à 0.

## Évolutions du modèle de données (migrations 001 à 010, décisions D-24 à D-28)

`02_oltp/migrations/001_parcours_commande.sql`, appliquée automatiquement après un chargement complet, ou seule avec `--migrer` :

- `commandes` : statuts `nouvelle`, `en_prepa`, `prete` (contrainte de valeurs), colonnes `date_heure_acceptation`, `date_heure_prete` et `note` ;
- `articles` : colonne `description`, remplie pour les 87 noms d'articles du jeu (textes rédigés pour l'application, pas issus du générateur) ;
- `etablissements` : colonne `commandes_ouvertes` ;
- table `migrations` : journal des migrations appliquées ;
- table `utilisateurs` (migration 002) : identifiant, établissement, rôle (`gerant`, `serveur`), prénom, mot de passe haché, dernière connexion ;
- table `etats_client` (migration 003) : panier, langue, écran et commande de chaque client, retrouvés grâce au jeton placé dans l'adresse (`?table=TBL00079&s=...`). Une actualisation de la page ne fait rien perdre et ne compte pas comme un nouveau scan. Le jeton est valable 4 heures après la dernière action et seulement pour sa table ;
- table `jetons_connexion` (migration 003) : connexions gardées de l'équipe (empreinte du jeton, compte, dernière utilisation) ;
- table `appels` (migration 004) : motif (`serveur`, `addition`, `eau`), heure de l'appel, heure de prise en charge et compte qui l'a prise ;
- `commandes.date_heure_reglement` (migration 004) : heure de l'encaissement. Les commandes servies du jeu, qui ont toutes un mode de règlement, reçoivent leur heure de service ;
- `etats_client.commandes` (migration 004) : les commandes d'un client pendant sa visite ;
- table `ruptures` (migration 005) : article indisponible pour une journée, avec le compte qui l'a signalé ;
- table `journal_prix` (migration 005) : changements de prix faits dans l'application ;
- `tables_salle.date_retrait` (migration 006) : table retirée du service ;
- `lignes_commande.options` et `etats_client.options` (migration 007) : préférences choisies par le client, par exemple « Sans sucre · Lait à part », affichées à l'équipe entre parenthèses ;
- table `avis` (migration 008) : un avis au plus par commande servie (note de 1 à 5, commentaire), visible dans « Activité des tables » (colonne « Note clients » par table, étoiles dans l'historique, onglet « Avis » avec la note moyenne et les commentaires) ;
- `articles.cout_revient` et `articles.date_maj_cout` (migration 009) : coût saisi par le gérant dans « Menu », bouton « Modifier ». Aucun coût n'est inventé : la colonne reste vide tant qu'il n'est pas saisi, et la marge ne s'affiche que pour les articles renseignés.

- tables `ml_score_resiliation`, `ml_candidat_commande`, `ml_recommandation_plat` et `ml_copie` (migration 010) : copies des résultats de la phase 7, remplies par `02_oltp/copier_resultats_ml.py` ; rôle `menuscan` et compte `succes.client`, rattaché à aucun établissement.

Le menu client choisit les articles par leurs dates d'ajout et de retrait, et non par `statut_article`, qui est une photo à la date d'arrêté du jeu.

## Résultats de la phase 7 dans l'application (migration 010, exigence EF-14)

- **Origine :** le schéma `ml` de l'entrepôt, publié par `08_analyse_ml/03_machine_learning/04_publication_resultats`. L'application ne lit jamais l'entrepôt : `02_oltp/copier_resultats_ml.py` copie les résultats dans `menuscan_app`, en une transaction (en cas d'erreur, l'ancienne copie reste) et contrôle les nombres de lignes.
- **Espace MenuScan** (`succes.client`) : un compte de l'équipe Succès client de MenuScan, sans établissement. Il voit les établissements à risque (probabilité de résiliation le mois suivant, alerte pour les 10 % les plus à risque, MRR menacé, 3 facteurs) et les candidats à la formule Commande. Export CSV.
- **Espace gérant**, formule Pro : page « Plats recommandés ». Les recommandations sont limitées à la carte du jour : un plat retiré depuis la publication disparaît des deux côtés. Un gérant d'une autre formule voit un message.
- **Le client ne voit pas les recommandations** : elles n'ont pas été testées auprès de vrais clients (test A/B à prévoir).
- **Fraîcheur :** les scores portent sur les données jusqu'à fin décembre 2026 ; la page affiche la date de publication et la date de copie.

## Gestion des tables (migration 006)

- Le QR code encode l'identifiant de la table (`TBL...`), pas son numéro : renuméroter une table ne demande pas de réimprimer son QR code.
- Un numéro ne peut être utilisé que par une seule table en service ; une zone vaut `terrasse`, `salle` ou `etage` ; de 1 à 20 places.
- Une table n'est jamais supprimée : la retirer remplit `tables_salle.date_retrait`. Son QR code affiche alors « Cette table n'est plus en service », elle disparaît du plan de salle, et son historique reste dans « Activité des tables » avec la mention « (retirée) ». Le retrait est refusé si une commande y est en cours ou à encaisser.

## Changement de prix (décision D-27)

- **Date d'effet :** aujourd'hui si l'article n'a pas encore été commandé aujourd'hui, sinon demain. Le contrôle DQ-06 juge le prix à la journée : une commande du matin ne doit pas changer de prix l'après-midi.
- **Historique :** la ligne de prix en cours est fermée la veille de la date d'effet et une ligne `modification_gerant` est ajoutée ; un seul prix reste ouvert par article (DQ-24). Un deuxième changement le même jour remplace le premier.
- **Commandes simulées :** le jeu simulé va jusqu'au 31/12/2026. Les commandes simulées de l'article sur la période du nouveau prix sont recalculées (prix et montant des lignes, total de la commande), pour que DQ-03, DQ-04 et DQ-06 restent à 0. Chaque changement est écrit dans `journal_prix`, avec le nombre de lignes et de commandes recalculées.

## Valeurs propres à l'application

| Colonne | Valeur | Signification |
|---|---|---|
| `commandes.statut_commande` | `nouvelle`, `en_prepa`, `prete` | Étapes avant le service |
| `sessions.appareil` | `web` | Ordinateur (les données générées ne contiennent que `android` et `ios`) |
| `sessions.appareil` | `serveur` | Commande prise par le serveur : session sans `scan_qr` ni `vue_menu`, à exclure de l'entonnoir de conversion |
| `articles_prix_historique.motif_changement` | `modification_gerant` | Prix changé dans l'application |
| `commandes.mode_reglement` | vide sur une commande `servie` | Servie mais pas encore encaissée (dans le jeu, toute commande servie a un mode de règlement) |

Ces valeurs seront ajoutées au dictionnaire des données et traitées par dbt (phase 4).

## Limites connues

- **Comptes de démonstration :** un mot de passe commun, publié dans ce README, et pas de changement de mot de passe ni de gestion des comptes dans l'application. Le compte `succes.client` voit les scores de tous les établissements : en production, il faudrait des comptes nominatifs.
- **Adresse du client :** quiconque obtient l'adresse complète d'un client (avec `s=`), par exemple par une capture partagée, voit son panier et le suivi de sa commande pendant 4 heures. Il ne peut rien voir d'autre.
- **Deuxième commande d'un même client :** elle ouvre une nouvelle session, qui commence par un événement `scan_qr` comme dans les données générées. Le nombre de scans est donc un peu surestimé quand un client commande plusieurs fois ; le lien entre ces sessions est gardé dans `etats_client`.
- **Base injoignable :** si PostgreSQL ne répond pas dans les 10 secondes (Docker arrêté ou bloqué), l'équipe voit un message avec la marche à suivre et un bouton « Réessayer » ; le client voit « Le menu est momentanément indisponible ». Les connexions passent par `127.0.0.1` (Windows essaie sinon `::1` en premier).
- **Mise à jour du thème :** après le remplacement d'un fichier de `commun/`, relancer les deux applications ; Streamlit ne recharge pas tout seul ce dossier.
- **Activité des tables :** le détail des appels (motif, délai de prise en charge) n'existe que pour les appels passés depuis l'application ; les appels des données générées sont seulement comptés. L'historique affiche au plus les 300 commandes les plus récentes de la période.
- **Retrait d'un article :** les commandes simulées après la date de retrait restent dans le jeu ; aucun contrôle ne porte sur ce point.
- **Arabe :** l'interface est traduite, pas les noms ni les descriptions des plats, qui n'existent qu'en français.
- **Heure estimée :** moyenne simple des 30 derniers jours, sans tenir compte de l'affluence du moment.
- **Vibration :** l'iPhone ne la permet pas aux pages web ; le bandeau et le titre de l'onglet restent.
- **Arabe (fiche article) :** les options sont traduites, pas les noms, catégories et descriptions des plats.
- **Options :** une seule combinaison d'options par article et par commande (deux capucins, l'un sucré et l'autre non, se notent dans la note pour le serveur).
- **Données simulées jusqu'au 31/12/2026 :** le jeu contient déjà des commandes datées après le jour présent ; tous les calculs s'arrêtent à l'heure courante.
- **Contrôle DQ-27 :** il interdit les événements après le 31/12/2026, date d'arrêté du jeu généré. Des événements créés par l'application après cette date seront signalés ; la règle sera adaptée en phase 3.
