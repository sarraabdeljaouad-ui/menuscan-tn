-- Lignes valides de prep_tickets_support : nettoyées, typées, sans doublon. Les lignes rejetées sont dans qualite.quarantaine.
{{ staging_depuis('prep_tickets_support') }}
