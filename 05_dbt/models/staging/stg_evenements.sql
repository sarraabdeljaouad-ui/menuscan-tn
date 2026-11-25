-- Lignes valides de prep_evenements : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_evenements') }}
