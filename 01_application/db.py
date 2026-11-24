# -*- coding: utf-8 -*-
"""Accès à la base applicative menuscan_app (schéma menuscan) pour l'application Streamlit.

Toutes les écritures respectent les règles de la couche de référence :
une commande par session (DQ-12), événements dans la fenêtre de la session (DQ-11),
prix en vigueur le jour de la commande (DQ-06), commande réservée aux formules Commande et Pro (DQ-09),
montants cohérents entre commande et lignes (DQ-03, DQ-04).
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
from sqlalchemy import URL, create_engine, text

RACINE = Path(__file__).resolve().parent.parent
TUNIS = timezone(timedelta(hours=1))  # la Tunisie est en UTC+1 toute l'année, sans heure d'été
SEQUENCES = {  # nom de la séquence : (table, colonne, préfixe, nombre de chiffres)
    "seq_session": ("sessions", "session_id", "SES", 7),
    "seq_evenement": ("evenements", "evenement_id", "EVT", 9),
    "seq_commande": ("commandes", "commande_id", "CMD", 7),
    "seq_ligne": ("lignes_commande", "ligne_id", "LIG", 7),
}
FORMULES_COMMANDE = ("FRM02", "FRM03")


def maintenant():
    """Heure de Tunis, à la seconde, sans fuseau (comme les données existantes)."""
    return datetime.now(TUNIS).replace(tzinfo=None, microsecond=0)


def _lire_env():
    env = {}
    f = RACINE / ".env"
    if f.exists():
        for ligne in f.read_text(encoding="utf-8").splitlines():
            if "=" in ligne and not ligne.strip().startswith("#"):
                k, v = ligne.split("=", 1)
                env[k.strip()] = v.strip()
    return env


@st.cache_resource
def moteur():
    env = _lire_env()
    # URL.create échappe les caractères spéciaux du mot de passe (@, :, /, #...)
    url = URL.create("postgresql+psycopg2", username=env.get("POSTGRES_USER"), password=env.get("POSTGRES_PASSWORD"),
                     host=env.get("POSTGRES_HOST", "localhost"), port=int(env.get("POSTGRES_PORT", "5440")), database="menuscan_app")
    eng = create_engine(url, pool_pre_ping=True, connect_args={"options": "-c search_path=menuscan"})
    _preparer(eng)
    return eng


def _preparer(eng):
    """Crée les séquences d'identifiants si besoin et les cale sur le plus grand identifiant existant."""
    with eng.begin() as c:
        for seq, (table, col, pref, _) in SEQUENCES.items():
            c.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq}"))
            c.execute(text(f"""SELECT setval('{seq}', GREATEST(
                (SELECT COALESCE(MAX(CAST(SUBSTRING({col} FROM {len(pref) + 1}) AS BIGINT)), 0) FROM {table}),
                (SELECT last_value FROM {seq}), 1))"""))


def _nouvel_id(c, seq):
    _, _, pref, n = SEQUENCES[seq]
    return f"{pref}{c.execute(text(f'SELECT nextval(:s)'), {'s': seq}).scalar():0{n}d}"


def lire(sql, **params):
    with moteur().connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql), params)]


# ---------- Lecture ----------

def table_et_etablissement(table_id):
    """Table, établissement et formule en vigueur aujourd'hui (selon les abonnements, comme DQ-09)."""
    r = lire("""
        SELECT t.table_id, t.numero_table, t.zone, e.etablissement_id, e.nom_etablissement, e.type_etablissement,
               e.statut_etablissement, v.ville AS nom_ville, a.formule_id, f.nom_formule, f.inclut_commande
        FROM tables_salle t
        JOIN etablissements e USING (etablissement_id)
        LEFT JOIN ref_villes v USING (ville_id)
        LEFT JOIN abonnements a ON a.etablissement_id = e.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        LEFT JOIN formules f ON f.formule_id = a.formule_id
        WHERE t.table_id = :t""", t=table_id, j=maintenant().date())
    return r[0] if r else None


def menu(etablissement_id):
    """Articles proposés aujourd'hui, avec le prix en vigueur (DQ-06)."""
    return lire("""
        SELECT c.categorie_id, c.nom_categorie, c.ordre_affichage, a.article_id, a.nom_article, p.prix_ttc
        FROM articles a
        JOIN categories_menu c USING (categorie_id)
        JOIN articles_prix_historique p ON p.article_id = a.article_id
             AND CAST(:j AS DATE) BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')
        WHERE a.etablissement_id = :e AND a.statut_article = 'propose'
              AND CAST(:j AS DATE) >= a.date_ajout AND (a.date_retrait IS NULL OR a.date_retrait > CAST(:j AS DATE))
        ORDER BY c.ordre_affichage, a.nom_article""", e=etablissement_id, j=maintenant().date())


def etablissements_commande():
    """Établissements actifs dont la formule du jour permet la commande."""
    return lire("""
        SELECT e.etablissement_id, e.nom_etablissement, v.ville AS nom_ville, a.formule_id
        FROM etablissements e
        JOIN ref_villes v USING (ville_id)
        JOIN abonnements a ON a.etablissement_id = e.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        WHERE e.statut_etablissement = 'actif' AND a.formule_id IN :f
        ORDER BY e.nom_etablissement""".replace(":f", str(FORMULES_COMMANDE)), j=maintenant().date())


def commandes_en_cours(etablissement_id):
    return lire("""
        SELECT c.commande_id, c.date_heure_commande, c.montant_total_ttc, c.nb_articles, t.numero_table, t.zone,
               STRING_AGG(l.quantite || ' × ' || a.nom_article, ', ' ORDER BY l.ligne_id) AS detail
        FROM commandes c
        JOIN tables_salle t USING (table_id)
        JOIN lignes_commande l USING (commande_id)
        JOIN articles a ON a.article_id = l.article_id
        WHERE c.etablissement_id = :e AND c.statut_commande = 'en_cours'
        GROUP BY c.commande_id, t.numero_table, t.zone
        ORDER BY c.date_heure_commande""", e=etablissement_id)


def appels_recents(etablissement_id, minutes=30):
    return lire("""
        SELECT ev.horodatage, t.numero_table, t.zone
        FROM evenements ev JOIN sessions s USING (session_id) JOIN tables_salle t ON t.table_id = s.table_id
        WHERE ev.etablissement_id = :e AND ev.type_evenement = 'appel_serveur' AND ev.horodatage BETWEEN :d AND :n
        ORDER BY ev.horodatage DESC""", e=etablissement_id, d=maintenant() - timedelta(minutes=minutes), n=maintenant())


def activite_du_jour(etablissement_id):
    r = lire("""
        SELECT COUNT(*) FILTER (WHERE statut_commande = 'servie') AS servies,
               COUNT(*) FILTER (WHERE statut_commande = 'annulee') AS annulees,
               COALESCE(SUM(montant_total_ttc) FILTER (WHERE statut_commande = 'servie'), 0) AS chiffre
        FROM commandes WHERE etablissement_id = :e AND CAST(date_heure_commande AS DATE) = :j AND date_heure_commande <= :n""",
             e=etablissement_id, j=maintenant().date(), n=maintenant())
    return r[0]


# ---------- Écriture ----------

def _evenement(c, session_id, etab, type_ev, h, article_id=None, quantite=None):
    c.execute(text("""INSERT INTO evenements (evenement_id, session_id, etablissement_id, horodatage, type_evenement, article_id, quantite)
                      VALUES (:i, :s, :e, :h, :t, :a, :q)"""),
              dict(i=_nouvel_id(c, "seq_evenement"), s=session_id, e=etab, h=h, t=type_ev, a=article_id, q=quantite))
    c.execute(text("""UPDATE sessions SET fin_session = GREATEST(fin_session, :h), nb_evenements = nb_evenements + 1,
                      a_ajoute_panier = a_ajoute_panier OR :p WHERE session_id = :s"""),
              dict(h=h, s=session_id, p=(type_ev == "ajout_panier")))


def ouvrir_session(table_id, etablissement_id, appareil):
    """Un scan de QR code : crée la session et ses deux premiers événements (scan_qr, vue_menu)."""
    h = maintenant()
    with moteur().begin() as c:
        sid = _nouvel_id(c, "seq_session")
        c.execute(text("""INSERT INTO sessions (session_id, etablissement_id, table_id, debut_session, fin_session, appareil, langue,
                          nb_articles_vus, a_ajoute_panier, a_commande, nb_evenements)
                          VALUES (:s, :e, :t, :h, :h, :a, 'fr', 0, FALSE, FALSE, 0)"""),
                  dict(s=sid, e=etablissement_id, t=table_id, h=h, a=appareil))
        _evenement(c, sid, etablissement_id, "scan_qr", h)
        _evenement(c, sid, etablissement_id, "vue_menu", h)
    return sid


def journaliser(session_id, etablissement_id, type_ev, article_id=None, quantite=None):
    with moteur().begin() as c:
        _evenement(c, session_id, etablissement_id, type_ev, maintenant(), article_id, quantite)


def passer_commande(session_id, table_id, etablissement_id, panier):
    """panier : {article_id: quantite}. Les prix sont relus en base au moment de la commande (DQ-06)."""
    h = maintenant()
    with moteur().begin() as c:
        deja = c.execute(text("SELECT a_commande FROM sessions WHERE session_id = :s FOR UPDATE"), dict(s=session_id)).scalar()
        if deja:
            raise ValueError("Cette session a déjà une commande.")
        prix = {r.article_id: r.prix_ttc for r in c.execute(text("""
            SELECT p.article_id, p.prix_ttc FROM articles_prix_historique p
            WHERE p.article_id = ANY(:ids) AND CAST(:j AS DATE) BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')"""),
            dict(ids=list(panier), j=h.date()))}
        if set(prix) != set(panier):
            raise ValueError("Un article n'est plus disponible.")
        cid = _nouvel_id(c, "seq_commande")
        lignes = [(_nouvel_id(c, "seq_ligne"), a, q, prix[a], prix[a] * q) for a, q in panier.items()]
        total = sum(l[4] for l in lignes)
        c.execute(text("""INSERT INTO commandes (commande_id, session_id, etablissement_id, table_id, date_heure_commande, statut_commande,
                          date_heure_service, nb_lignes, nb_articles, montant_total_ttc, mode_reglement, motif_annulation)
                          VALUES (:c, :s, :e, :t, :h, 'en_cours', NULL, :nl, :na, :m, NULL, NULL)"""),
                  dict(c=cid, s=session_id, e=etablissement_id, t=table_id, h=h, nl=len(lignes), na=sum(l[2] for l in lignes), m=total))
        for lid, a, q, pu, mt in lignes:
            c.execute(text("""INSERT INTO lignes_commande (ligne_id, commande_id, article_id, quantite, prix_unitaire_ttc, montant_ligne_ttc)
                              VALUES (:l, :c, :a, :q, :p, :m)"""), dict(l=lid, c=cid, a=a, q=q, p=pu, m=mt))
        _evenement(c, session_id, etablissement_id, "commande_envoyee", h)
        c.execute(text("UPDATE sessions SET a_commande = TRUE WHERE session_id = :s"), dict(s=session_id))
    return cid, total


def servir(commande_id, mode_reglement):
    with moteur().begin() as c:
        c.execute(text("""UPDATE commandes SET statut_commande = 'servie', date_heure_service = :h, mode_reglement = :m
                          WHERE commande_id = :c AND statut_commande = 'en_cours'"""),
                  dict(h=maintenant(), m=mode_reglement, c=commande_id))


def annuler(commande_id, motif="article_indisponible"):
    with moteur().begin() as c:
        c.execute(text("""UPDATE commandes SET statut_commande = 'annulee', motif_annulation = :m
                          WHERE commande_id = :c AND statut_commande = 'en_cours'"""), dict(m=motif, c=commande_id))
