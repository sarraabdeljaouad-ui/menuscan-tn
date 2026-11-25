-- Lignes valides de prep_dim_calendrier : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_dim_calendrier') }}
