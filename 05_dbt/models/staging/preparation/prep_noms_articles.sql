-- Forme de référence de chaque nom de plat, déduite des écritures présentes dans le fichier (DQ-32)
{{ noms_canoniques([[source('raw', 'menus_articles'), 'nom_article']], casse_phrase) }}
