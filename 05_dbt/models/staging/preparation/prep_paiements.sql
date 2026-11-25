-- Paiements reçus par l'API (une ligne JSON par paiement). Source : paiements_api/paiements.jsonl
-- Renommage des clés anglaises, codes traduits (DQ-32), heure UTC -> Tunis (DQ-34), montants en millimes (DQ-33).
-- Quarantaine (DQ-18) : second paiement réussi pour une facture, montant différent du TTC, paiement réussi avant l'émission.
-- Une tentative échouée peut précéder l'émission : elle reste valide (46 cas dans la couche de référence).
with source as (
    select
        donnees->>'payment_id' as paiement_id, donnees->>'invoice_ref' as facture_id, donnees->>'customer_ref' as etablissement_id,
        donnees->>'created_at' as _date_brute, donnees->>'method' as _mode_brut, donnees->'amount'->>'value' as _montant_brut,
        donnees->>'status' as _statut_brut, donnees->>'error_code' as code_erreur, (donnees->>'attempt')::smallint as numero_tentative,
        _fichier, _ligne,
        {{ rang_doublon("donnees->>'payment_id'") }} as _rang
    from {{ source('raw', 'paiements_api_paiements') }}
),
nettoyee as (
    select
        s.*, {{ utc_vers_tunis('_date_brute') }} as date_paiement, {{ traduire('mode_paiement', '_mode_brut') }} as mode_paiement,
        {{ dinars('_montant_brut') }}::numeric(10, 3) as montant_ttc, {{ traduire('statut_paiement', '_statut_brut') }} as statut_paiement
    from source s
),
controlee as (
    select
        n.*, f.montant_ttc as _ttc_facture, f.date_emission as _emission_facture,
        -- rang du paiement réussi pour sa facture, doublons d'ingestion exclus
        case when n.statut_paiement = 'reussi' and n._rang = 1
             then row_number() over (partition by n.facture_id, (n.statut_paiement = 'reussi' and n._rang = 1) order by n.date_paiement, n.paiement_id)
        end as _rang_reussi
    from nettoyee n
    left join {{ ref('prep_factures') }} f on f.facture_id = n.facture_id and f._regle_rejet is null
)
select
    paiement_id, facture_id, etablissement_id, date_paiement, mode_paiement, montant_ttc, statut_paiement, code_erreur, numero_tentative,
    _fichier, _ligne,
    {{ corrections([corr('DQ-33', 'montant_ttc', est_millimes('_montant_brut'), '_montant_brut', 'montant_ttc')]) }} as _corrections,
    {{ rejet('paiement_id', [
        ['DQ-02', '_ttc_facture is null', 'facture inconnue'],
        ['DQ-18', '_rang_reussi > 1', 'second paiement réussi pour la même facture'],
        ['DQ-18', "statut_paiement = 'reussi' and abs(montant_ttc - _ttc_facture) > 0.001", 'montant différent du TTC de la facture'],
        ['DQ-18', "statut_paiement = 'reussi' and date_paiement::date < _emission_facture", "paiement réussi antérieur à l'émission de la facture"],
        ['DQ-27', apres_arrete('date_paiement'), "paiement après la date d'arrêté"],
    ]) }}
from controlee
