-- Lignes valides de prep_lignes_commande : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_lignes_commande') }}
