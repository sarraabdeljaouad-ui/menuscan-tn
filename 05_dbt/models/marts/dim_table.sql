-- Dimension table de salle.
select table_id, etablissement_id, numero_table, zone, capacite, qr_code_id, date_installation
from {{ ref('stg_tables_salle') }}
