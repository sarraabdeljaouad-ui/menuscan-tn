-- Tables de salle : typage seul. Source : backoffice/tables_salle.csv
with source as (
    select *, {{ rang_doublon('table_id') }} as _rang from {{ source('raw', 'backoffice_tables_salle') }}
)
select
    table_id, etablissement_id, numero_table::smallint as numero_table, zone, capacite::smallint as capacite, qr_code_id,
    date_installation::date as date_installation,
    _fichier, _ligne, '[]'::jsonb as _corrections,
    {{ rejet('table_id') }}
from source
