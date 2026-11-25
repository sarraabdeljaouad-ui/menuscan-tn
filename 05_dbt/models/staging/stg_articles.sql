-- Lignes valides de prep_articles : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_articles') }}
