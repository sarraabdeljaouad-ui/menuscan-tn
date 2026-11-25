-- Établissements clients. Source : backoffice/etablissements.csv
-- Corrections : nom (DQ-32), téléphone (DQ-31), e-mail (DQ-31), nombre de tables manquant (DQ-38).
-- Les doublons métier (même établissement sous deux identifiants, DQ-30) sont fusionnés en T4.2 (intermediate).
with source as (
    select *, {{ rang_doublon('etablissement_id') }} as _rang from {{ source('raw', 'backoffice_etablissements') }}
),
domaines as (  -- domaines des e-mails bien formés, pour replacer un @ oublié
    select distinct split_part(replace(email, ' ', ''), '@', 2) as domaine
    from source where replace(email, ' ', '') ~ '^[^@]+@[^@]+\.[a-z]{2,}$'
),
tables_par_etablissement as (
    select etablissement_id, count(*) as nb from {{ source('raw', 'backoffice_tables_salle') }} group by etablissement_id
),
nettoyee as (
    select
        s.etablissement_id,
        coalesce(n.nom_canonique, {{ espaces('s.nom_etablissement') }}) as nom_etablissement,
        s.type_etablissement, s.ville_id, s.gerant_prenom, s.gerant_nom,
        {{ telephone('s.telephone') }} as telephone,
        case when replace(s.email, ' ', '') !~ '@' and d.domaine is not null
             then left(replace(s.email, ' ', ''), length(replace(s.email, ' ', '')) - length(d.domaine)) || '@' || d.domaine
             else replace(s.email, ' ', '') end as email,
        s.canal_id, s.campagne_id, s.prospect_id, s.date_signature::date as date_signature,
        s.date_mise_en_service::date as date_mise_en_service,
        coalesce(s.nb_tables::smallint, t.nb::smallint) as nb_tables,
        s.formule_initiale_id, s.formule_actuelle_id, s.periodicite_facturation, s.statut_etablissement,
        s.date_resiliation::date as date_resiliation, s.motif_resiliation,
        s.nom_etablissement as _nom_brut, s.telephone as _telephone_brut, s.email as _email_brut, s.nb_tables as _nb_tables_brut,
        s._fichier, s._ligne, s._rang
    from source s
    left join {{ ref('prep_noms_etablissements') }} n on n.cle = {{ cle_libelle('s.nom_etablissement') }}
    left join lateral (
        select domaine from domaines where replace(s.email, ' ', '') like '%' || domaine order by length(domaine) desc limit 1
    ) d on true
    left join tables_par_etablissement t on t.etablissement_id = s.etablissement_id
)
select
    etablissement_id, nom_etablissement, type_etablissement, ville_id, gerant_prenom, gerant_nom, telephone, email,
    canal_id, campagne_id, prospect_id, date_signature, date_mise_en_service, nb_tables, formule_initiale_id,
    formule_actuelle_id, periodicite_facturation, statut_etablissement, date_resiliation, motif_resiliation,
    _fichier, _ligne,
    {{ corrections([
        corr_si_change('DQ-32', 'nom_etablissement', '_nom_brut', 'nom_etablissement'),
        corr_si_change('DQ-31', 'telephone', '_telephone_brut', 'telephone'),
        corr_si_change('DQ-31', 'email', '_email_brut', 'email'),
        corr('DQ-38', 'nb_tables', '_nb_tables_brut is null and nb_tables is not null', '_nb_tables_brut', 'nb_tables'),
    ]) }} as _corrections,
    {{ rejet('etablissement_id') }}
from nettoyee
