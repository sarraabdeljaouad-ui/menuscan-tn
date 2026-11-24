# Application MenuScan TN

Application Streamlit du menu numérique à QR code, avec commande depuis la table (phase 1, tâche T1.3). Elle suit les maquettes validées le 24/11/2026 et lit et écrit dans la base applicative `menuscan_app` (schéma `menuscan`).

## Lancement

Conteneur PostgreSQL démarré, base chargée et migrée, environnement Python activé :

```bash
python 02_oltp/charger_base_app.py --migrer   # une fois, sur une base chargée avant la migration 001
cd 01_application
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`. Le thème est défini dans `.streamlit/config.toml` et `theme.py` ; le fichier de configuration n'est lu que si l'application est lancée depuis ce dossier.

## Fichiers

| Fichier | Rôle |
|---|---|
| `app.py` | Point d'entrée : thème, vérification de la base, navigation |
| `theme.py` | Couleurs, polices (Inter, Plus Jakarta Sans), cartes, barre de panier fixe |
| `db.py` | Toutes les lectures et écritures en base |
| `vues/accueil.py` | Accueil : présentation, chiffres de la base, étapes, formules et tables de démonstration |
| `vues/menu_client.py` | Menu client en trois vues : menu, panier, suivi de la commande |
| `vues/espace_gerant.py` | Espace gérant : indicateurs, commandes en direct, meilleures ventes, plan des tables |

Le dossier s'appelle `vues/` et non `pages/` : un dossier `pages/` déclencherait l'ancienne navigation automatique de Streamlit.

## Pages

| Page | Adresse | Contenu |
|---|---|---|
| Accueil | `/` | Présentation, 4 chiffres lus en base, parcours en 4 étapes, une table de démonstration par formule |
| Menu client | `/menu?table=TBL00001` | Ouvert par le QR code : en-tête de l'établissement, bouton FR · ع, recherche, catégories, articles avec description et badge « Populaire », barre de panier avec appel du serveur ; panier avec note pour le serveur ; suivi de la commande en 4 étapes, mis à jour toutes les 10 secondes |
| Espace gérant | `/gerant` | Ouverture ou fermeture des commandes, 5 indicateurs, commandes en direct en 3 colonnes (nouvelles, en préparation, prêtes), meilleures ventes du mois, plan des tables ; mise à jour toutes les 10 secondes |

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

Après un parcours complet (commande, quatre étapes, annulation, fermeture des commandes), les 23 contrôles de `02_oltp/controles_qualite.sql` restent à 0.

## Évolutions du modèle de données (migration 001, décision D-24)

`02_oltp/migrations/001_parcours_commande.sql`, appliquée automatiquement après un chargement complet, ou seule avec `--migrer` :

- `commandes` : statuts `nouvelle`, `en_prepa`, `prete` (contrainte de valeurs), colonnes `date_heure_acceptation`, `date_heure_prete` et `note` ;
- `articles` : colonne `description`, remplie pour les 87 noms d'articles du jeu (textes rédigés pour l'application, pas issus du générateur) ;
- `etablissements` : colonne `commandes_ouvertes` ;
- table `migrations` : journal des migrations appliquées.

## Valeurs propres à l'application

| Colonne | Valeur | Signification |
|---|---|---|
| `commandes.statut_commande` | `nouvelle`, `en_prepa`, `prete` | Étapes avant le service |
| `sessions.appareil` | `web` | Ordinateur (les données générées ne contiennent que `android` et `ios`) |

Ces valeurs seront ajoutées au dictionnaire des données et traitées par dbt (phase 4).

## Limites connues

- **Pas d'authentification** dans l'espace gérant : le choix de l'établissement est libre (démonstration).
- **Arabe :** l'interface est traduite, pas les noms ni les descriptions des plats, qui n'existent qu'en français.
- **Articles vus :** l'application n'écrit pas d'événement `vue_article` ; `nb_articles_vus` reste à 0 pour ses sessions.
- **Données simulées jusqu'au 31/12/2026 :** le jeu contient déjà des commandes datées après le jour présent ; tous les calculs s'arrêtent à l'heure courante.
- **Contrôle DQ-27 :** il interdit les événements après le 31/12/2026, date d'arrêté du jeu généré. Des événements créés par l'application après cette date seront signalés ; la règle sera adaptée en phase 3.
