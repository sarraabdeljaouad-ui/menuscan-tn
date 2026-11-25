-- Aucune ligne perdue : pour chaque table, lignes brutes = lignes en staging + lignes en quarantaine.
-- Le test échoue s'il renvoie au moins une ligne.
select table_source, lignes_brutes, lignes_staging, lignes_quarantaine
from {{ ref('bilan_qualite') }}
group by table_source, lignes_brutes, lignes_staging, lignes_quarantaine
having lignes_brutes <> lignes_staging + lignes_quarantaine
