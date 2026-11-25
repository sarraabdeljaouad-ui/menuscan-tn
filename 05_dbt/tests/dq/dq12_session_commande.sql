-- DQ-12 : a_commande <=> commande ; au plus une commande par session ; un événement commande_envoyee par commande.
-- Exception tracée : commande envoyée dans les derniers jours avant l'arrêté, pas encore reçue (commande_non_recue, décision D-32).
-- Une commande envoyée en dehors de cette fenêtre et jamais reçue reste une violation.
with cmd as (select session_id, count(*) n from {{ ref('fait_commande') }} group by 1),
     env as (select session_id, count(*) n from {{ ref('int_evenements') }} where type_evenement = 'commande_envoyee' group by 1)
select s.session_id from {{ ref('fait_session') }} s left join cmd using (session_id) left join env using (session_id)
where (s.a_commande and cmd.n is null and not s.commande_non_recue) or (not s.a_commande and cmd.n is not null) or cmd.n > 1 or (coalesce(env.n, 0) <> coalesce(cmd.n, 0) and not s.commande_non_recue)
