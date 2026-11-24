# Application MenuScan TN

Application Streamlit du menu numérique à QR code, avec commande depuis la table (phase 1, tâche T1.3). Elle lit et écrit dans la base applicative `menuscan_app` (schéma `menuscan`).

## Lancement

Conteneur PostgreSQL démarré, base chargée (`02_oltp/charger_base_app.py`), environnement Python activé :

```bash
cd 01_application
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`. Le thème bleu est défini dans `.streamlit/config.toml`, lu uniquement si l'application est lancée depuis ce dossier.

## Pages

| Page | Adresse | Rôle |
|---|---|---|
| Accueil | `/accueil` | Présentation, une table de démonstration par formule, chiffres de la base |
| Menu client | `/menu?table=TBL00001` | Ouvert par le QR code de la table : menu du jour par catégorie, prix en vigueur, panier, commande, appel du serveur |
| Espace gérant | `/gerant` | Commandes en cours (servie ou annulée), appels du serveur des 30 dernières minutes, activité du jour ; mise à jour toutes les 10 secondes |

L'espace MenuScan (établissements à risque) sera ajouté en phase 8.

## Règles appliquées

| Règle | Application |
|---|---|
| Formule | Essentiel : menu consultable seulement. Commande et Pro : panier et commande. La formule est celle de l'abonnement en vigueur le jour même (comme le contrôle DQ-09). |
| Session | Un scan de QR code ouvre une session et écrit les événements `scan_qr` et `vue_menu`. Chaque action ajoute un événement et prolonge la fin de session (DQ-11). |
| Une commande par session | Après une commande, « Nouvelle commande » ouvre une nouvelle session (DQ-12). |
| Prix | Relus en base au moment de la commande, selon l'historique des prix (DQ-06). |
| Montants | Montant de ligne = prix × quantité ; total, nombre de lignes et d'articles cohérents avec les lignes (DQ-03, DQ-04). |
| Identifiants | Séquences PostgreSQL créées au premier lancement et calées sur le plus grand identifiant existant (`SES`, `EVT`, `CMD`, `LIG`). |
| Heure | Heure de Tunis (UTC+1, pas d'heure d'été), comme les données existantes. |

Après des commandes passées dans l'application, les 23 contrôles de `02_oltp/controles_qualite.sql` restent à 0.

## Valeurs propres à l'application

| Colonne | Valeur | Signification |
|---|---|---|
| `commandes.statut_commande` | `en_cours` | Commande envoyée, pas encore servie ni annulée. Les données générées ne contiennent que `servie` et `annulee`. |
| `sessions.appareil` | `web` | Ordinateur. Les données générées ne contiennent que `android` et `ios`. |

Ces deux valeurs seront ajoutées au dictionnaire des données et traitées par dbt (phase 4).

## Limites connues

- **Pas d'authentification** dans l'espace gérant : le choix de l'établissement est libre. C'est une démonstration.
- **Langue :** les sessions sont créées en français ; les noms des plats n'existent qu'en français.
- **Articles vus :** l'application n'écrit pas d'événement `vue_article` ; `nb_articles_vus` reste à 0 pour ses sessions.
- **Données simulées jusqu'au 31/12/2026 :** le jeu généré contient déjà des commandes datées après le jour présent. Les compteurs du jour et les appels du serveur ne retiennent que ce qui est antérieur à l'heure courante.
- **Contrôle DQ-27 :** il interdit les événements après le 31/12/2026, date d'arrêté du jeu généré. Des événements créés par l'application après cette date seront signalés ; la règle sera adaptée en phase 3.
