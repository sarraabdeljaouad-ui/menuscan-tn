-- Forme de référence de chaque nom d'établissement, déduite des fichiers établissements et prospects (DQ-32)
{{ noms_canoniques([[source('raw', 'backoffice_etablissements'), 'nom_etablissement'],
                    [source('raw', 'crm_prospects'), 'nom_etablissement']], casse_titre) }}
