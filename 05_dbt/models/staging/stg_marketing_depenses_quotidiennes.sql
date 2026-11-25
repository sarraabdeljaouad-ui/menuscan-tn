-- Lignes valides de prep_marketing_depenses_quotidiennes : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_marketing_depenses_quotidiennes') }}
