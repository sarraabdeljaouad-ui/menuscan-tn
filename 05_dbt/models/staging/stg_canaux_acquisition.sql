-- Lignes valides de prep_canaux_acquisition : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_canaux_acquisition') }}
