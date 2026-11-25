-- Événements de navigation (une ligne JSON par événement). Source : tracking/events_AAAA_MM.jsonl.gz
-- Renommage des clés anglaises, types traduits (DQ-32), heure UTC -> Tunis (DQ-34).
-- Données en retard (DQ-35) : chaque événement est rattaché à sa date, pas au mois du fichier ; le retard est tracé.
-- Les fichiers mensuels sont découpés en heure UTC : le retard se mesure donc sur l'horodatage UTC.
-- Quarantaine : article inconnu (DQ-02), quantité non positive (DQ-05), date après l'arrêté ou pendant la panne (DQ-27).
-- Les horloges décalées (DQ-37) sont traitées en T4.2, avec les sessions.
with source as (
    select
        donnees->>'event_id' as evenement_id, donnees->>'session_token' as session_id, donnees->>'venue_id' as etablissement_id,
        donnees->>'table_ref' as table_id, donnees->>'ts' as _horodatage_brut, donnees->>'event_type' as _type_brut,
        donnees->>'item_id' as article_id, (donnees->>'qty')::smallint as quantite,
        donnees->>'device' as appareil, donnees->>'lang' as langue,
        _fichier, _ligne,
        {{ rang_doublon("donnees->>'event_id'") }} as _rang
    from {{ source('raw', 'tracking_events') }}
),
nettoyee as (
    select
        s.*, {{ utc_vers_tunis('s._horodatage_brut') }} as horodatage, t.valeur_cible as _type_traduit,
        {{ mois_fichier('s._fichier') }} as _mois_fichier
    from source s
    left join {{ ref('correspondance_libelles') }} t on t.domaine = 'type_evenement' and t.valeur_source = lower(s._type_brut)
),
avec_articles as (
    select n.*, coalesce(n._type_traduit, lower(n._type_brut)) as type_evenement, a.article_id as _article_connu
    from nettoyee n
    left join {{ ref('prep_articles') }} a on a.article_id = n.article_id and a._regle_rejet is null
)
select
    evenement_id, session_id, etablissement_id, table_id, horodatage, type_evenement, article_id, quantite, appareil, langue,
    _fichier, _ligne,
    {{ corrections([
        corr('DQ-35', 'horodatage', "date_trunc('month', _horodatage_brut::timestamptz at time zone 'UTC')::date < _mois_fichier",
             "to_char(_mois_fichier, 'YYYY-MM')", "to_char(_horodatage_brut::timestamptz at time zone 'UTC', 'YYYY-MM')"),
    ]) }} as _corrections,
    {{ rejet('evenement_id', [
        ['DQ-02', 'article_id is not null and _article_connu is null', 'article inconnu'],
        ['DQ-05', 'quantite <= 0', 'quantité non positive'],
        ['DQ-27', apres_arrete('horodatage'), "événement après la date d'arrêté"],
        ['DQ-27', "horodatage between '" ~ var('panne_debut') ~ "' and '" ~ var('panne_fin') ~ "'", 'événement pendant la panne du 12/09/2025'],
    ]) }}
from avec_articles
