-- Lignes valides de prep_ref_villes : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_ref_villes') }}
