-- Dimension heure : 24 lignes. Les moments de la journée sont une convention du projet, pour lire l'activité des cafés.
select
    h as heure,
    lpad(h::text, 2, '0') || ':00' as libelle,
    case when h between 6 and 10 then 'matin'
         when h between 11 and 14 then 'midi'
         when h between 15 and 18 then 'après-midi'
         when h between 19 and 22 then 'soir'
         else 'nuit' end as moment_journee
from generate_series(0, 23) h
