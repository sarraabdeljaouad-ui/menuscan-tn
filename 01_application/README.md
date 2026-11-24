# Application MenuScan TN

Deux applications Streamlit (phase 1, tâche T1.3), qui suivent les maquettes validées le 24/11/2026 et partagent la base applicative `menuscan_app` (schéma `menuscan`) :

- **l'application client**, ouverte par le QR code de la table, sans compte : menu, panier, suivi de la commande ;
- **l'application équipe** (back-office), avec connexion : écran du serveur ou du gérant selon le rôle (décision D-25).

## Lancement

Conteneur PostgreSQL démarré, base chargée et migrée, environnement Python activé. Deux terminaux :

```bash
python 02_oltp/charger_base_app.py --migrer   # une fois, sur une base chargée avant les migrations 001 à 003

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
| `commun/qr.py` | Génération des QR codes, des cartes de table et de la planche PDF (A4, 6 cartes par page) |
| `qr/generer_qr.py` | Même génération en ligne de commande, écrite dans `qr/sortie/` (exclu de Git) |

Les dossiers ne s'appellent pas `pages/` : ce nom déclencherait l'ancienne navigation automatique de Streamlit.

## Comptes et rôles (migration 002)

Deux comptes de démonstration par établissement : `gerant.etbXXXX` et `serveur.etbXXXX` (par exemple `gerant.etb0005` pour le Café Les Arcades). Mot de passe de démonstration commun : `Demo2026!`. Les mots de passe sont hachés avec bcrypt (extension `pgcrypto`) et comparés par PostgreSQL ; ils ne sont jamais stockés en clair.

| Fonction | Serveur | Gérant |
|---|---|---|
| Commandes en direct : accepter, marquer prête, servir avec le règlement, annuler | Oui | Oui |
| Plan des tables et appels du serveur | Oui | Oui |
| Chiffre du jour, panier moyen, délai, taux de commande | Non | Oui |
| Meilleures ventes du mois | Non | Oui |
| Ouvrir ou fermer les commandes | Non | Oui |
| Tables et QR codes | Non | Oui |

**Rester connecté :** après la connexion, l'appareil reste connecté, même après une actualisation ou la fermeture du navigateur, jusqu'au bouton « Se déconnecter ». La connexion expire seulement après 30 jours sans utilisation ; chaque ouverture de l'application relance ce délai. Le navigateur garde un jeton aléatoire dans un cookie ; la base n'en garde que l'empreinte SHA-256. Le gérant dispose d'un bouton « Déconnecter partout », qui déconnecte tous les appareils des comptes de son établissement (appareil perdu, départ d'un serveur).

Les droits sont vérifiés à chaque exécution de l'écran, pas seulement par la navigation. Chaque écriture de l'équipe est limitée à l'établissement du compte connecté : un compte ne peut pas avancer ni annuler la commande d'un autre établissement.

## Pages

| Application | Adresse | Contenu |
|---|---|---|
| Client | `/?table=TBL00001` | En-tête de l'établissement, bouton FR · ع, recherche, catégories, articles avec description et badge « Populaire », barre de panier avec appel du serveur ; panier avec note pour le serveur ; suivi de la commande en 4 étapes, mis à jour toutes les 10 secondes |
| Équipe | `/` | Accueil public |
| Équipe | `/connexion` | Connexion |
| Équipe | `/qr` | Gérant seulement : un QR code par table, lien encodé, PNG par table et planche PDF à imprimer |
| Équipe | `/tableau` | Gérant : ouverture des commandes, 5 indicateurs, commandes en direct, meilleures ventes, plan des tables. Serveur : compteurs des commandes, commandes en direct, plan des tables. Mise à jour toutes les 10 secondes |

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
| Servie | `servie` | Le gérant choisit le règlement et clique sur « Servie » | `date_heure_service` |
| Annulée | `annulee` | Le gérant clique sur « Annuler » (nouvelle commande seulement) | – |

Les commandes du jeu de données n'ont que `servie` ou `annulee`, sans heure d'acceptation ni de préparation.

## Règles appliquées

| Règle | Application |
|---|---|
| Formule | Essentiel : menu consultable seulement. Commande et Pro : panier et commande. La formule est celle de l'abonnement en vigueur le jour même (comme le contrôle DQ-09). |
| Commandes fermées | Si le gérant ferme les commandes, le menu reste consultable mais le bouton d'envoi est désactivé ; la base refuse aussi la commande. |
| Session | Un scan ouvre une session et écrit `scan_qr` et `vue_menu`. Chaque action ajoute un événement et prolonge la fin de session (DQ-11). |
| Une commande par session | « Nouvelle commande » ouvre une nouvelle session (DQ-12). |
| Prix | Relus en base au moment de la commande, selon l'historique des prix (DQ-06). |
| Montants | Ligne = prix × quantité ; total, nombre de lignes et d'articles cohérents (DQ-03, DQ-04). |
| Populaire | Les 5 articles les plus servis de l'établissement sur les 30 derniers jours. |
| État des tables | Appel du serveur depuis moins de 15 min, sinon commande active, sinon menu ouvert depuis moins de 30 min, sinon libre. |
| Indicateurs | Chiffre et commandes du jour jusqu'à l'heure courante, comparés au même jour de la semaine précédente à la même heure ; panier moyen, délai de service et taux de commande depuis le 1er du mois. |
| Identifiants | Séquences PostgreSQL calées sur le plus grand identifiant existant (`SES`, `EVT`, `CMD`, `LIG`). |
| Heure | Heure de Tunis (UTC+1, pas d'heure d'été), comme les données existantes. |

Après un parcours complet (commande, quatre étapes par le gérant et le serveur, annulation, fermeture des commandes), les 23 contrôles de `02_oltp/controles_qualite.sql` restent à 0.

## Évolutions du modèle de données (migrations 001 à 003, décisions D-24 à D-26)

`02_oltp/migrations/001_parcours_commande.sql`, appliquée automatiquement après un chargement complet, ou seule avec `--migrer` :

- `commandes` : statuts `nouvelle`, `en_prepa`, `prete` (contrainte de valeurs), colonnes `date_heure_acceptation`, `date_heure_prete` et `note` ;
- `articles` : colonne `description`, remplie pour les 87 noms d'articles du jeu (textes rédigés pour l'application, pas issus du générateur) ;
- `etablissements` : colonne `commandes_ouvertes` ;
- table `migrations` : journal des migrations appliquées ;
- table `utilisateurs` (migration 002) : identifiant, établissement, rôle (`gerant`, `serveur`), prénom, mot de passe haché, dernière connexion ;
- table `etats_client` (migration 003) : panier, langue, écran et commande de chaque client, retrouvés grâce au jeton placé dans l'adresse (`?table=TBL00079&s=...`). Une actualisation de la page ne fait rien perdre et ne compte pas comme un nouveau scan. Le jeton est valable 4 heures après la dernière action et seulement pour sa table ;
- table `jetons_connexion` (migration 003) : connexions gardées de l'équipe (empreinte du jeton, compte, dernière utilisation).

## Valeurs propres à l'application

| Colonne | Valeur | Signification |
|---|---|---|
| `commandes.statut_commande` | `nouvelle`, `en_prepa`, `prete` | Étapes avant le service |
| `sessions.appareil` | `web` | Ordinateur (les données générées ne contiennent que `android` et `ios`) |

Ces valeurs seront ajoutées au dictionnaire des données et traitées par dbt (phase 4).

## Limites connues

- **Comptes de démonstration :** un mot de passe commun, publié dans ce README, et pas de changement de mot de passe ni de gestion des comptes dans l'application.
- **Adresse du client :** quiconque obtient l'adresse complète d'un client (avec `s=`), par exemple par une capture partagée, voit son panier et le suivi de sa commande pendant 4 heures. Il ne peut rien voir d'autre.
- **Arabe :** l'interface est traduite, pas les noms ni les descriptions des plats, qui n'existent qu'en français.
- **Articles vus :** l'application n'écrit pas d'événement `vue_article` ; `nb_articles_vus` reste à 0 pour ses sessions.
- **Données simulées jusqu'au 31/12/2026 :** le jeu contient déjà des commandes datées après le jour présent ; tous les calculs s'arrêtent à l'heure courante.
- **Contrôle DQ-27 :** il interdit les événements après le 31/12/2026, date d'arrêté du jeu généré. Des événements créés par l'application après cette date seront signalés ; la règle sera adaptée en phase 3.
