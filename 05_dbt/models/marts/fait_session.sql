-- Fait session : une ligne par session (entonnoir scan -> menu -> article -> panier -> commande, KPI K13 et K20).
-- formule_id = formule de l'établissement le jour de la session (la formule Essentiel ne permet pas de commander).
select
    s.session_id, s.etablissement_id, s.table_id, a.formule_id,
    {{ date_id('s.debut_session') }} as date_id, extract(hour from s.debut_session)::smallint as heure,
    s.debut_session, s.fin_session, extract(epoch from (s.fin_session - s.debut_session))::integer as duree_secondes,
    s.appareil, s.langue, s.nb_evenements, s.nb_articles_vus,
    s.a_vu_menu, s.nb_articles_vus > 0 as a_vu_article, s.a_ajoute_panier, s.a_commande,
    c.commande_id,
    -- commande envoyée juste avant l'arrêté et pas encore reçue dans les fichiers (décision D-32)
    s.a_commande and c.commande_id is null
        and s.debut_session::date > '{{ var("date_arrete") }}'::date - {{ var('fenetre_retard_jours') }} as commande_non_recue
from {{ ref('int_sessions') }} s
left join {{ ref('stg_abonnements') }} a
  on a.etablissement_id = s.etablissement_id and s.debut_session::date between a.date_debut and coalesce(a.date_fin, '9999-12-31')
left join {{ ref('int_commandes') }} c on c.session_id = s.session_id
