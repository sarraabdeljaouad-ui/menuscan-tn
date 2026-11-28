# -*- coding: utf-8 -*-
"""Accès à la base applicative menuscan_app (schéma menuscan) pour l'application Streamlit.

Toutes les écritures respectent les règles de la couche de référence :
une commande par session (DQ-12), événements dans la fenêtre de la session (DQ-11),
prix en vigueur le jour de la commande (DQ-06), commande réservée aux formules Commande et Pro (DQ-09),
montants cohérents entre commande et lignes (DQ-03, DQ-04).

Parcours d'une commande (migration 001) : nouvelle -> en_prepa -> prete -> servie, ou annulee.
"""
import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
from sqlalchemy import URL, create_engine, text

RACINE = Path(__file__).resolve().parents[2]  # racine du dépôt (01_application/commun/db.py)
TUNIS = timezone(timedelta(hours=1))  # la Tunisie est en UTC+1 toute l'année, sans heure d'été
SEQUENCES = {  # nom de la séquence : (table, colonne, préfixe, nombre de chiffres)
    "seq_session": ("sessions", "session_id", "SES", 7),
    "seq_evenement": ("evenements", "evenement_id", "EVT", 9),
    "seq_commande": ("commandes", "commande_id", "CMD", 7),
    "seq_ligne": ("lignes_commande", "ligne_id", "LIG", 7),
}
DUREE_CONNEXION_JOURS = 30  # connexion de l'équipe : expire après 30 jours sans utilisation
DUREE_ETAT_CLIENT_HEURES = 4  # au-delà, un client qui rouvre la page repart d'une nouvelle session
FORMULES_COMMANDE = "('FRM02', 'FRM03')"
ACTIVES = "('nouvelle', 'en_prepa', 'prete')"
SUIVANT = {"nouvelle": ("en_prepa", "date_heure_acceptation"), "en_prepa": ("prete", "date_heure_prete"),
           "prete": ("servie", "date_heure_service")}


class MigrationManquante(RuntimeError):
    pass


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


@st.cache_resource(show_spinner="Connexion à la base de données…")
def moteur():
    env = _lire_env()
    # URL.create échappe les caractères spéciaux du mot de passe (@, :, /, #...)
    url = URL.create("postgresql+psycopg2", username=env.get("POSTGRES_USER"), password=env.get("POSTGRES_PASSWORD"),
                     host=env.get("POSTGRES_HOST", "127.0.0.1"), port=int(env.get("POSTGRES_PORT", "5440")), database="menuscan_app")
    # 127.0.0.1 plutôt que localhost : Windows essaie d'abord ::1 (IPv6). Délai de 10 s : un message clair plutôt qu'une attente sans fin.
    eng = create_engine(url, pool_pre_ping=True, connect_args={"options": "-c search_path=menuscan", "connect_timeout": 10})
    _preparer(eng)
    return eng


class BaseInjoignable(Exception):
    pass


def verifier_connexion(public=False):
    """À appeler en tête de chaque application : affiche un message clair si PostgreSQL ne répond pas, puis arrête la page.
    public=True (application client) : message pour le client, sans détail technique."""
    try:
        with moteur().connect() as c:  # aussi quand la base s'arrête pendant que l'application tourne
            c.execute(text("SELECT 1"))
    except MigrationManquante as err:
        st.error(str(err))
        st.stop()
    except Exception as err:  # psycopg2.OperationalError le plus souvent : Docker arrêté ou bloqué, mauvais mot de passe
        detail = str(err).strip().splitlines()[0] if str(err).strip() else type(err).__name__
        if public:
            st.error("Le menu est momentanément indisponible. Merci de prévenir le serveur. · القائمة غير متاحة حاليًا، يرجى إعلام النادل.")
            if st.button("Réessayer · إعادة المحاولة", type="primary"):
                st.rerun()
            st.stop()
        st.error("La base de données ne répond pas. Vérifier que Docker Desktop tourne (`docker ps`), puis relancer "
                 "`python outils/verifier_poste.py`. Si `docker ps` répond « 500 Internal Server Error » : quitter Docker Desktop, "
                 "lancer `wsl --shutdown`, rouvrir Docker Desktop, puis `docker compose up -d`.")
        st.caption(f"Détail technique : {detail}")
        if st.button("Réessayer", type="primary"):
            st.rerun()
        st.stop()


def _preparer(eng):
    """Vérifie la migration 001, crée les séquences d'identifiants et les cale sur le plus grand identifiant existant."""
    with eng.begin() as c:
        ok = c.execute(text("""SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'menuscan' AND table_name = 'migrations')""")).scalar()
        faites = {r[0] for r in c.execute(text("SELECT migration_id FROM migrations"))} if ok else set()
        manquantes = sorted({"001_parcours_commande", "002_comptes_equipe", "003_persistance", "004_service_salle", "005_gestion_menu", "006_gestion_tables", "007_fiche_article", "008_avis", "009_cout_revient", "010_resultats_ml"} - faites)
        if manquantes:
            raise MigrationManquante(f"Migration manquante ({', '.join(manquantes)}). Lancer : python 02_oltp/charger_base_app.py --migrer")
        for seq, (table, col, pref, _) in SEQUENCES.items():
            c.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq}"))
            # Les identifiants ont une longueur fixe (préfixe + chiffres complétés de zéros) : leur plus grande valeur se lit
            # dans l'index de la clé primaire, sans parcourir la table (1,6 million d'événements). Démarrage rapide, même à froid.
            c.execute(text(f"""SELECT setval('{seq}', GREATEST(
                COALESCE((SELECT CAST(SUBSTRING(MAX({col}) FROM {len(pref) + 1}) AS BIGINT) FROM {table}), 0),
                (SELECT last_value FROM {seq}), 1))"""))


def _nouvel_id(c, seq):
    _, _, pref, n = SEQUENCES[seq]
    return f"{pref}{c.execute(text('SELECT nextval(:s)'), {'s': seq}).scalar():0{n}d}"


def url_client():
    """Adresse de l'application client (variable CLIENT_URL du fichier .env, par défaut http://localhost:8501)."""
    return _lire_env().get("CLIENT_URL", "http://localhost:8501").rstrip("/")


def lire(sql, **params):
    with moteur().connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql), params)]


def un(sql, **params):
    r = lire(sql, **params)
    return r[0] if r else None


# ---------- Lecture : client ----------

def table_et_etablissement(table_id):
    """Table, établissement et formule en vigueur aujourd'hui (selon les abonnements, comme DQ-09)."""
    return un("""
        SELECT t.table_id, t.numero_table, t.zone, (t.date_retrait IS NOT NULL AND t.date_retrait <= CAST(:j AS DATE)) AS table_retiree,
               e.etablissement_id, e.nom_etablissement, e.type_etablissement,
               e.statut_etablissement, e.commandes_ouvertes, v.ville AS nom_ville, a.formule_id, f.nom_formule, f.inclut_commande
        FROM tables_salle t
        JOIN etablissements e USING (etablissement_id)
        LEFT JOIN ref_villes v USING (ville_id)
        LEFT JOIN abonnements a ON a.etablissement_id = e.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        LEFT JOIN formules f ON f.formule_id = a.formule_id
        WHERE t.table_id = :t""", t=table_id, j=maintenant().date())


def menu(etablissement_id):
    """Articles proposés aujourd'hui (entre leur date d'ajout et de retrait, hors rupture du jour), prix en vigueur (DQ-06),
    description et rang de popularité sur 30 jours. Le statut_article n'est pas utilisé : c'est une photo à la date d'arrêté du jeu."""
    n = maintenant()
    return lire("""
        WITH pop AS (
            SELECT l.article_id, SUM(l.quantite) AS q
            FROM lignes_commande l JOIN commandes c USING (commande_id)
            WHERE c.etablissement_id = :e AND c.statut_commande = 'servie' AND c.date_heure_commande BETWEEN :d AND :n
            GROUP BY l.article_id ORDER BY q DESC LIMIT 5)
        SELECT c.categorie_id, c.nom_categorie, c.ordre_affichage, a.article_id, a.nom_article, a.description, p.prix_ttc,
               (pop.article_id IS NOT NULL) AS populaire
        FROM articles a
        JOIN categories_menu c USING (categorie_id)
        JOIN articles_prix_historique p ON p.article_id = a.article_id
             AND CAST(:j AS DATE) BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')
        LEFT JOIN pop ON pop.article_id = a.article_id
        WHERE a.etablissement_id = :e
              AND CAST(:j AS DATE) >= a.date_ajout AND (a.date_retrait IS NULL OR a.date_retrait > CAST(:j AS DATE))
              AND NOT EXISTS (SELECT 1 FROM ruptures r WHERE r.article_id = a.article_id AND r.jour = CAST(:j AS DATE))
        ORDER BY c.ordre_affichage, (pop.article_id IS NULL), a.nom_article""",
                e=etablissement_id, j=n.date(), d=n - timedelta(days=30), n=n)


def delai_moyen(etablissement_id):
    """Délai moyen entre commande et service sur les 30 derniers jours, en minutes."""
    n = maintenant()
    r = un("""SELECT AVG(EXTRACT(EPOCH FROM date_heure_service - date_heure_commande) / 60) AS m FROM commandes
              WHERE etablissement_id = :e AND statut_commande = 'servie' AND date_heure_commande BETWEEN :d AND :n""",
           e=etablissement_id, d=n - timedelta(days=30), n=n)
    return float(r["m"]) if r and r["m"] is not None else None


def estimation(etablissement_id, commande):
    """Heure de service estimée : heure de la commande + délai moyen de l'établissement sur 30 jours. None sans historique."""
    m = delai_moyen(etablissement_id)
    return (commande["date_heure_commande"] + timedelta(minutes=m), m) if m else None


def avis_de(commande_id):
    return un("SELECT note, commentaire FROM avis WHERE commande_id = :c", c=commande_id)


def donner_avis(commande_id, note, commentaire=None):
    """Avis du client sur une commande servie ; un seul par commande (le premier est gardé)."""
    if not 1 <= int(note) <= 5:
        return
    with moteur().begin() as c:
        c.execute(text("""INSERT INTO avis (commande_id, etablissement_id, table_id, note, commentaire, date_heure)
                          SELECT commande_id, etablissement_id, table_id, :n, :t, :h FROM commandes
                          WHERE commande_id = :c AND statut_commande = 'servie'
                          ON CONFLICT (commande_id) DO NOTHING"""),
                  dict(c=commande_id, n=int(note), t=(commentaire or "").strip()[:300] or None, h=maintenant()))


def suivi(commande_id):
    c = un("""SELECT commande_id, statut_commande, date_heure_commande, date_heure_acceptation, date_heure_prete,
                     date_heure_service, montant_total_ttc, note FROM commandes WHERE commande_id = :c""", c=commande_id)
    if c:
        c["lignes"] = lire("""SELECT l.quantite, a.nom_article, l.montant_ligne_ttc, l.options FROM lignes_commande l
                              JOIN articles a USING (article_id) WHERE l.commande_id = :c ORDER BY l.ligne_id""", c=commande_id)
    return c


# ---------- Comptes de l'équipe ----------

_COMPTE = """
        SELECT u.utilisateur_id, u.identifiant, u.role, u.prenom, u.etablissement_id, e.nom_etablissement, e.gerant_prenom,
               v.ville AS nom_ville, a.formule_id, f.nom_formule, f.inclut_statistiques
        FROM utilisateurs u
        LEFT JOIN etablissements e ON e.etablissement_id = u.etablissement_id  -- vide pour le rôle menuscan (migration 010)
        LEFT JOIN ref_villes v ON v.ville_id = e.ville_id
        LEFT JOIN abonnements a ON a.etablissement_id = e.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        LEFT JOIN formules f ON f.formule_id = a.formule_id
        WHERE u.actif AND """


def authentifier(identifiant, mot_de_passe):
    """Renvoie le compte si l'identifiant et le mot de passe sont bons (comparaison bcrypt faite par PostgreSQL), sinon None."""
    u = un(_COMPTE + "u.identifiant = LOWER(TRIM(:i)) AND u.mot_de_passe_hash = crypt(:m, u.mot_de_passe_hash)",
           i=identifiant or "", m=mot_de_passe or "", j=maintenant().date())
    if u:
        with moteur().begin() as c:
            c.execute(text("UPDATE utilisateurs SET derniere_connexion = :h WHERE utilisateur_id = :u"), dict(h=maintenant(), u=u["utilisateur_id"]))
    return u


def _empreinte(jeton):
    return hashlib.sha256(jeton.encode()).hexdigest()


def creer_jeton(utilisateur_id):
    """Crée un jeton de connexion (à poser dans un cookie). Seule son empreinte SHA-256 est stockée."""
    jeton = secrets.token_urlsafe(32)
    with moteur().begin() as c:
        c.execute(text("DELETE FROM jetons_connexion WHERE dernier_usage < now() - make_interval(days => :d)"), dict(d=DUREE_CONNEXION_JOURS))
        c.execute(text("INSERT INTO jetons_connexion (jeton_hash, utilisateur_id) VALUES (:h, :u)"), dict(h=_empreinte(jeton), u=utilisateur_id))
    return jeton


def compte_par_jeton(jeton):
    """Renvoie le compte lié au jeton s'il a servi depuis moins de 30 jours et que le compte est actif ; prolonge sa validité."""
    if not isinstance(jeton, str) or not jeton or len(jeton) > 100:
        return None
    with moteur().begin() as c:
        uid = c.execute(text("""UPDATE jetons_connexion SET dernier_usage = now()
                                WHERE jeton_hash = :h AND dernier_usage >= now() - make_interval(days => :d)
                                RETURNING utilisateur_id"""), dict(h=_empreinte(jeton), d=DUREE_CONNEXION_JOURS)).scalar()
    return un(_COMPTE + "u.utilisateur_id = :u", u=uid, j=maintenant().date()) if uid else None


def supprimer_jeton(jeton):
    if jeton:
        with moteur().begin() as c:
            c.execute(text("DELETE FROM jetons_connexion WHERE jeton_hash = :h"), dict(h=_empreinte(jeton)))


def deconnecter_etablissement(etablissement_id):
    """Déconnecte tous les appareils de tous les comptes de l'établissement (téléphone perdu, départ d'un serveur)."""
    with moteur().begin() as c:
        return c.execute(text("""DELETE FROM jetons_connexion WHERE utilisateur_id IN
                                 (SELECT utilisateur_id FROM utilisateurs WHERE etablissement_id = :e)"""), dict(e=etablissement_id)).rowcount


def commandes_ouvertes(etablissement_id):
    return bool(un("SELECT commandes_ouvertes AS o FROM etablissements WHERE etablissement_id = :e", e=etablissement_id)["o"])


# ---------- Lecture : équipe ----------

def etablissements_commande():
    """Établissements actifs dont la formule du jour permet la commande."""
    return lire(f"""
        SELECT e.etablissement_id, e.nom_etablissement, e.gerant_prenom, e.commandes_ouvertes, v.ville AS nom_ville, a.formule_id, f.nom_formule
        FROM etablissements e
        JOIN ref_villes v USING (ville_id)
        JOIN abonnements a ON a.etablissement_id = e.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        JOIN formules f ON f.formule_id = a.formule_id
        WHERE e.statut_etablissement = 'actif' AND a.formule_id IN {FORMULES_COMMANDE}
        ORDER BY e.nom_etablissement""", j=maintenant().date())


def commandes_actives(etablissement_id):
    return lire(f"""
        SELECT c.commande_id, c.statut_commande, c.date_heure_commande, c.montant_total_ttc, c.note, t.numero_table, t.zone,
               STRING_AGG(l.quantite || ' ' || LOWER(a.nom_article) || COALESCE(' (' || LOWER(l.options) || ')', ''), ' · ' ORDER BY l.ligne_id) AS detail
        FROM commandes c
        JOIN tables_salle t USING (table_id)
        JOIN lignes_commande l USING (commande_id)
        JOIN articles a ON a.article_id = l.article_id
        WHERE c.etablissement_id = :e AND c.statut_commande IN {ACTIVES}
        GROUP BY c.commande_id, t.numero_table, t.zone
        ORDER BY c.date_heure_commande""", e=etablissement_id)


def indicateurs(etablissement_id):
    """Chiffres du jour jusqu'à maintenant, comparaison avec le même jour de la semaine précédente, et mois en cours."""
    n = maintenant()
    j0 = datetime.combine(n.date(), datetime.min.time())
    s7 = j0 - timedelta(days=7)
    m0 = j0.replace(day=1)
    jour = un("""SELECT COUNT(*) AS n, COALESCE(SUM(montant_total_ttc), 0) AS ca FROM commandes
                 WHERE etablissement_id = :e AND statut_commande = 'servie' AND date_heure_commande BETWEEN :d AND :f""",
              e=etablissement_id, d=j0, f=n)
    avant = un("""SELECT COALESCE(SUM(montant_total_ttc), 0) AS ca FROM commandes
                  WHERE etablissement_id = :e AND statut_commande = 'servie' AND date_heure_commande BETWEEN :d AND :f""",
               e=etablissement_id, d=s7, f=s7 + (n - j0))
    mois = un("""SELECT COUNT(*) AS n, AVG(montant_total_ttc) AS panier,
                        AVG(EXTRACT(EPOCH FROM date_heure_service - date_heure_commande) / 60) AS delai
                 FROM commandes WHERE etablissement_id = :e AND statut_commande = 'servie' AND date_heure_commande BETWEEN :d AND :f""",
              e=etablissement_id, d=m0, f=n)
    conv = un("""SELECT COUNT(*) AS s, AVG(CASE WHEN a_commande THEN 1.0 ELSE 0 END) AS t FROM sessions
                 WHERE etablissement_id = :e AND debut_session BETWEEN :d AND :f""", e=etablissement_id, d=m0, f=n)
    return dict(n_jour=jour["n"], ca_jour=float(jour["ca"]), ca_semaine=float(avant["ca"]), jour_semaine=s7,
                n_mois=mois["n"], panier=mois["panier"], delai=mois["delai"], sessions=conv["s"], taux=conv["t"], debut_mois=m0)


def meilleures_ventes(etablissement_id):
    n = maintenant()
    return lire("""
        SELECT a.nom_article, SUM(l.quantite) AS q FROM lignes_commande l JOIN commandes c USING (commande_id)
        JOIN articles a ON a.article_id = l.article_id
        WHERE c.etablissement_id = :e AND c.statut_commande = 'servie' AND c.date_heure_commande BETWEEN :d AND :n
        GROUP BY a.nom_article ORDER BY q DESC, a.nom_article LIMIT 5""",
                e=etablissement_id, d=datetime.combine(n.date().replace(day=1), datetime.min.time()), n=n)


def etat_tables(etablissement_id):
    """État de chaque table : appel en attente, commande en cours, servi à encaisser, menu ouvert (30 min) ou libre.
    Une table encaissée redevient libre, sauf si un client y a de nouveau ouvert le menu après l'encaissement."""
    n = maintenant()
    return lire(f"""
        SELECT t.table_id, t.numero_table, t.zone,
               EXISTS (SELECT 1 FROM appels a WHERE a.table_id = t.table_id AND a.date_heure_prise IS NULL) AS appel,
               EXISTS (SELECT 1 FROM commandes c WHERE c.table_id = t.table_id AND c.statut_commande IN {ACTIVES}) AS commande,
               EXISTS (SELECT 1 FROM commandes c WHERE c.table_id = t.table_id AND c.statut_commande = 'servie'
                       AND c.date_heure_reglement IS NULL) AS a_encaisser,
               EXISTS (SELECT 1 FROM sessions s WHERE s.table_id = t.table_id AND s.fin_session BETWEEN :o AND :n
                       AND s.fin_session > COALESCE((SELECT MAX(c.date_heure_reglement) FROM commandes c WHERE c.table_id = t.table_id),
                                                    TIMESTAMP '1900-01-01')) AS ouvert
        FROM tables_salle t WHERE t.etablissement_id = :e AND (t.date_retrait IS NULL OR t.date_retrait > CAST(:n AS DATE))
        ORDER BY t.numero_table""",
                e=etablissement_id, n=n, o=n - timedelta(minutes=30))


def appels_en_attente(etablissement_id):
    return lire("""SELECT a.appel_id, a.motif, a.date_heure_appel, t.table_id, t.numero_table, t.zone FROM appels a
                   JOIN tables_salle t USING (table_id)
                   WHERE a.etablissement_id = :e AND a.date_heure_prise IS NULL ORDER BY a.date_heure_appel""", e=etablissement_id)


def detail_table(etablissement_id, table_id):
    """Tout ce qui concerne une table : commandes en cours, commandes servies à encaisser, appels en attente."""
    cmd = lire(f"""
        SELECT c.commande_id, c.statut_commande, c.date_heure_commande, c.montant_total_ttc, c.note,
               (c.statut_commande = 'servie') AS a_encaisser,
               STRING_AGG(l.quantite || ' ' || LOWER(a.nom_article) || COALESCE(' (' || LOWER(l.options) || ')', ''), ' · ' ORDER BY l.ligne_id) AS detail
        FROM commandes c JOIN lignes_commande l USING (commande_id) JOIN articles a ON a.article_id = l.article_id
        WHERE c.etablissement_id = :e AND c.table_id = :t
          AND (c.statut_commande IN {ACTIVES} OR (c.statut_commande = 'servie' AND c.date_heure_reglement IS NULL))
        GROUP BY c.commande_id ORDER BY c.date_heure_commande""", e=etablissement_id, t=table_id)
    appels = [a for a in appels_en_attente(etablissement_id) if a["table_id"] == table_id]
    return dict(commandes=cmd, appels=appels)


# ---------- Écriture ----------

def _evenement(c, session_id, etab, type_ev, h, article_id=None, quantite=None):
    c.execute(text("""INSERT INTO evenements (evenement_id, session_id, etablissement_id, horodatage, type_evenement, article_id, quantite)
                      VALUES (:i, :s, :e, :h, :t, :a, :q)"""),
              dict(i=_nouvel_id(c, "seq_evenement"), s=session_id, e=etab, h=h, t=type_ev, a=article_id, q=quantite))
    c.execute(text("""UPDATE sessions SET fin_session = GREATEST(fin_session, :h), nb_evenements = nb_evenements + 1,
                      nb_articles_vus = nb_articles_vus + :v, a_ajoute_panier = a_ajoute_panier OR :p WHERE session_id = :s"""),
              dict(h=h, s=session_id, p=(type_ev == "ajout_panier"), v=int(type_ev == "vue_article")))


def ouvrir_session(table_id, etablissement_id, appareil, langue="fr", scan=True):
    """Un scan de QR code : crée la session et ses deux premiers événements (scan_qr, vue_menu).
    scan=False : session d'une commande prise par le serveur (appareil 'serveur'), sans scan ni vue du menu."""
    h = maintenant()
    with moteur().begin() as c:
        sid = _nouvel_id(c, "seq_session")
        c.execute(text("""INSERT INTO sessions (session_id, etablissement_id, table_id, debut_session, fin_session, appareil, langue,
                          nb_articles_vus, a_ajoute_panier, a_commande, nb_evenements)
                          VALUES (:s, :e, :t, :h, :h, :a, :l, 0, FALSE, FALSE, 0)"""),
                  dict(s=sid, e=etablissement_id, t=table_id, h=h, a=appareil, l=langue))
        if scan:
            _evenement(c, sid, etablissement_id, "scan_qr", h)
            _evenement(c, sid, etablissement_id, "vue_menu", h)
    return sid


def changer_langue(session_id, langue):
    with moteur().begin() as c:
        c.execute(text("UPDATE sessions SET langue = :l WHERE session_id = :s"), dict(l=langue, s=session_id))


def journaliser(session_id, etablissement_id, type_ev, article_id=None, quantite=None):
    with moteur().begin() as c:
        _evenement(c, session_id, etablissement_id, type_ev, maintenant(), article_id, quantite)


def appeler(session_id, table_id, etablissement_id, motif="serveur"):
    """Appel du client. Renvoie False si le même appel attend déjà pour cette table (pas de doublon)."""
    h = maintenant()
    with moteur().begin() as c:
        deja = c.execute(text("""SELECT 1 FROM appels WHERE table_id = :t AND motif = :m AND date_heure_prise IS NULL"""),
                         dict(t=table_id, m=motif)).scalar()
        if deja:
            return False
        _evenement(c, session_id, etablissement_id, "appel_serveur", h)
        c.execute(text("""INSERT INTO appels (etablissement_id, table_id, session_id, motif, date_heure_appel)
                          VALUES (:e, :t, :s, :m, :h)"""), dict(e=etablissement_id, t=table_id, s=session_id, m=motif, h=h))
    return True


def passer_commande(session_id, table_id, etablissement_id, panier, note=None, options=None, par_equipe=False):
    """panier : {article_id: quantite} ; options : {article_id: [options]}, sans effet sur le prix.
    Les prix sont relus en base au moment de la commande (DQ-06)."""
    options = options or {}
    h = maintenant()
    with moteur().begin() as c:
        ouvert = c.execute(text("SELECT commandes_ouvertes FROM etablissements WHERE etablissement_id = :e"), dict(e=etablissement_id)).scalar()
        if not ouvert and not par_equipe:  # l'interrupteur ferme la commande par QR code, pas la prise de commande en salle
            raise ValueError("L'établissement ne prend plus de commandes pour le moment.")
        if c.execute(text("SELECT a_commande FROM sessions WHERE session_id = :s FOR UPDATE"), dict(s=session_id)).scalar():
            raise ValueError("Cette session a déjà une commande.")
        prix = {r.article_id: r.prix_ttc for r in c.execute(text("""
            SELECT p.article_id, p.prix_ttc FROM articles_prix_historique p
            WHERE p.article_id = ANY(:ids) AND CAST(:j AS DATE) BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')"""),
            dict(ids=list(panier), j=h.date()))}
        indispo = c.execute(text("""SELECT article_id FROM articles WHERE article_id = ANY(:ids)
                                    AND (date_retrait <= CAST(:j AS DATE) OR EXISTS (SELECT 1 FROM ruptures r
                                         WHERE r.article_id = articles.article_id AND r.jour = CAST(:j AS DATE)))"""),
                            dict(ids=list(panier), j=h.date())).first()
        if set(prix) != set(panier) or indispo:
            raise ValueError("Un article n'est plus disponible.")
        cid = _nouvel_id(c, "seq_commande")
        lignes = [(_nouvel_id(c, "seq_ligne"), a, q, prix[a], prix[a] * q) for a, q in panier.items()]
        c.execute(text("""INSERT INTO commandes (commande_id, session_id, etablissement_id, table_id, date_heure_commande, statut_commande,
                          date_heure_service, nb_lignes, nb_articles, montant_total_ttc, mode_reglement, motif_annulation, note)
                          VALUES (:c, :s, :e, :t, :h, 'nouvelle', NULL, :nl, :na, :m, NULL, NULL, :no)"""),
                  dict(c=cid, s=session_id, e=etablissement_id, t=table_id, h=h, nl=len(lignes),
                       na=sum(l[2] for l in lignes), m=sum(l[4] for l in lignes), no=(note or "").strip()[:120] or None))
        for lid, a, q, pu, mt in lignes:
            c.execute(text("""INSERT INTO lignes_commande (ligne_id, commande_id, article_id, quantite, prix_unitaire_ttc, montant_ligne_ttc, options)
                              VALUES (:l, :c, :a, :q, :p, :m, :o)"""),
                      dict(l=lid, c=cid, a=a, q=q, p=pu, m=mt, o=" · ".join(options.get(a) or [])[:120] or None))
        _evenement(c, session_id, etablissement_id, "commande_envoyee", h)
        c.execute(text("UPDATE sessions SET a_commande = TRUE WHERE session_id = :s"), dict(s=session_id))
    return cid


def avancer(etablissement_id, commande_id):
    """Fait passer une commande à l'étape suivante et horodate l'étape (seulement une commande de l'établissement du compte).
    Le règlement est séparé du service (migration 004) : une commande servie reste « à encaisser » jusqu'à encaisser()."""
    with moteur().begin() as c:
        statut = c.execute(text("SELECT statut_commande FROM commandes WHERE commande_id = :c AND etablissement_id = :e FOR UPDATE"),
                           dict(c=commande_id, e=etablissement_id)).scalar()
        if statut not in SUIVANT:
            return
        suivant, colonne = SUIVANT[statut]
        c.execute(text(f"UPDATE commandes SET statut_commande = :s, {colonne} = :h WHERE commande_id = :c"),
                  dict(s=suivant, h=maintenant(), c=commande_id))


def encaisser(etablissement_id, table_id, mode_reglement):
    """Encaisse toutes les commandes servies et non réglées de la table ; clôt les demandes d'addition. Renvoie le montant encaissé."""
    h = maintenant()
    with moteur().begin() as c:
        total = c.execute(text("""UPDATE commandes SET mode_reglement = :m, date_heure_reglement = :h
                                  WHERE etablissement_id = :e AND table_id = :t AND statut_commande = 'servie' AND date_heure_reglement IS NULL
                                  RETURNING montant_total_ttc"""), dict(m=mode_reglement, h=h, e=etablissement_id, t=table_id)).scalars().all()
        c.execute(text("""UPDATE appels SET date_heure_prise = :h WHERE etablissement_id = :e AND table_id = :t
                          AND motif = 'addition' AND date_heure_prise IS NULL"""), dict(h=h, e=etablissement_id, t=table_id))
    return sum(total)


def prendre_appel(etablissement_id, appel_id, utilisateur_id):
    with moteur().begin() as c:
        c.execute(text("""UPDATE appels SET date_heure_prise = :h, pris_par = :u
                          WHERE appel_id = :a AND etablissement_id = :e AND date_heure_prise IS NULL"""),
                  dict(h=maintenant(), u=utilisateur_id, a=appel_id, e=etablissement_id))


def annuler(etablissement_id, commande_id, motif="article_indisponible"):
    with moteur().begin() as c:
        c.execute(text(f"""UPDATE commandes SET statut_commande = 'annulee', motif_annulation = :m
                           WHERE commande_id = :c AND etablissement_id = :e AND statut_commande IN {ACTIVES}"""),
                  dict(m=motif, c=commande_id, e=etablissement_id))


def ouvrir_commandes(etablissement_id, ouvert):
    with moteur().begin() as c:
        c.execute(text("UPDATE etablissements SET commandes_ouvertes = :o WHERE etablissement_id = :e"), dict(o=ouvert, e=etablissement_id))


# ---------- État du client conservé après actualisation (migration 003) ----------

def nouvel_etat_client(table_id, etablissement_id, appareil, langue="fr"):
    """Nouveau scan : ouvre la session et crée le jeton à placer dans l'adresse de la page."""
    sid = ouvrir_session(table_id, etablissement_id, appareil, langue)
    jeton = secrets.token_urlsafe(16)
    with moteur().begin() as c:
        c.execute(text("INSERT INTO etats_client (jeton, table_id, session_id, langue) VALUES (:j, :t, :s, :l)"),
                  dict(j=jeton, t=table_id, s=sid, l=langue))
    return dict(jeton=jeton, session_id=sid, panier={}, langue=langue, vue="menu", commande_id=None, commandes=[], options={})


def etat_client(jeton, table_id):
    """Relit l'état d'un client. None si le jeton est inconnu, d'une autre table ou inutilisé depuis plus de 4 heures."""
    if not isinstance(jeton, str) or not jeton or len(jeton) > 40:
        return None
    r = un("""SELECT jeton, session_id, panier, langue, vue, commande_id, commandes, options FROM etats_client
              WHERE jeton = :j AND table_id = :t AND date_maj >= now() - make_interval(hours => :h)""",
           j=jeton, t=table_id, h=DUREE_ETAT_CLIENT_HEURES)
    for k in ("panier", "options"):
        if r and isinstance(r[k], str):
            r[k] = json.loads(r[k])
    return r


def sauver_etat_client(jeton, session_id, panier, langue, vue, commande_id, commandes, options=None):
    with moteur().begin() as c:
        c.execute(text("""UPDATE etats_client SET session_id = :s, panier = CAST(:p AS JSONB), langue = :l, vue = :v, commande_id = :c,
                          commandes = :cs, options = CAST(:o AS JSONB), date_maj = now() WHERE jeton = :j"""),
                  dict(s=session_id, p=json.dumps(panier), l=langue, v=vue, c=commande_id, cs=list(commandes),
                       o=json.dumps(options or {}), j=jeton))


def commandes_visite(commande_ids):
    """Statut et montant des commandes d'un client pendant sa visite, dans l'ordre."""
    return lire("""SELECT commande_id, statut_commande, montant_total_ttc, date_heure_commande, date_heure_reglement FROM commandes
                   WHERE commande_id = ANY(:ids) ORDER BY date_heure_commande""", ids=list(commande_ids))


# ---------- Activité des tables (gérant, lot 2) ----------

def activite_tables(etablissement_id, debut, fin):
    """Une ligne par table sur la période [debut, fin] (bornée à maintenant) : visites, commandes, chiffre encaissé, appels.
    Les appels comptent les événements appel_serveur, présents aussi dans les données générées."""
    fin = min(fin, maintenant())
    return lire("""
        SELECT t.table_id, t.numero_table, t.zone, t.capacite, t.date_retrait,
               (SELECT COUNT(*) FROM sessions s WHERE s.table_id = t.table_id AND s.debut_session BETWEEN :d AND :f) AS visites,
               COUNT(c.commande_id) FILTER (WHERE c.statut_commande = 'servie') AS servies,
               COUNT(c.commande_id) FILTER (WHERE c.statut_commande = 'annulee') AS annulees,
               COALESCE(SUM(c.montant_total_ttc) FILTER (WHERE c.statut_commande = 'servie'), 0) AS chiffre,
               AVG(c.montant_total_ttc) FILTER (WHERE c.statut_commande = 'servie') AS panier,
               AVG(EXTRACT(EPOCH FROM c.date_heure_service - c.date_heure_commande) / 60) FILTER (WHERE c.statut_commande = 'servie') AS delai,
               (SELECT COUNT(*) FROM evenements ev JOIN sessions s USING (session_id)
                 WHERE s.table_id = t.table_id AND ev.type_evenement = 'appel_serveur' AND ev.horodatage BETWEEN :d AND :f) AS appels,
               MAX(c.date_heure_commande) AS derniere,
               (SELECT AVG(av.note) FROM avis av WHERE av.table_id = t.table_id AND av.date_heure BETWEEN :d AND :f) AS note_moyenne
        FROM tables_salle t
        LEFT JOIN commandes c ON c.table_id = t.table_id AND c.date_heure_commande BETWEEN :d AND :f
        WHERE t.etablissement_id = :e
        GROUP BY t.table_id ORDER BY t.numero_table""", e=etablissement_id, d=debut, f=fin)


def historique_table(etablissement_id, table_id, debut, fin, limite=300):
    """Commandes d'une table sur la période, les plus récentes d'abord, avec leurs articles et leurs heures d'étape."""
    fin = min(fin, maintenant())
    return lire("""
        SELECT c.commande_id, c.date_heure_commande, c.statut_commande, c.montant_total_ttc, c.mode_reglement,
               c.date_heure_reglement, c.note, c.motif_annulation,
               (SELECT av.note FROM avis av WHERE av.commande_id = c.commande_id) AS avis_note,
               (SELECT av.commentaire FROM avis av WHERE av.commande_id = c.commande_id) AS avis_commentaire,
               ROUND(EXTRACT(EPOCH FROM c.date_heure_service - c.date_heure_commande) / 60) AS delai,
               STRING_AGG(l.quantite || ' ' || LOWER(a.nom_article) || COALESCE(' (' || LOWER(l.options) || ')', ''), ' · ' ORDER BY l.ligne_id) AS detail
        FROM commandes c JOIN lignes_commande l USING (commande_id) JOIN articles a ON a.article_id = l.article_id
        WHERE c.etablissement_id = :e AND c.table_id = :t AND c.date_heure_commande BETWEEN :d AND :f
        GROUP BY c.commande_id ORDER BY c.date_heure_commande DESC LIMIT :n""",
                e=etablissement_id, t=table_id, d=debut, f=fin, n=limite)


def appels_table(etablissement_id, table_id, debut, fin):
    """Appels passés par l'application (table appels, migration 004), avec le délai de prise en charge."""
    fin = min(fin, maintenant())
    return lire("""SELECT motif, date_heure_appel, date_heure_prise,
                          ROUND(EXTRACT(EPOCH FROM date_heure_prise - date_heure_appel) / 60) AS attente
                   FROM appels WHERE etablissement_id = :e AND table_id = :t AND date_heure_appel BETWEEN :d AND :f
                   ORDER BY date_heure_appel DESC""", e=etablissement_id, t=table_id, d=debut, f=fin)


# ---------- Gestion du menu (lot 2, migration 005) ----------

def carte(etablissement_id):
    """Tous les articles de l'établissement pour l'écran de gestion : prix du jour, état (proposé, en rupture, retiré, à venir)."""
    j = maintenant().date()
    return lire("""
        SELECT a.article_id, a.nom_article, a.description, a.date_ajout, a.date_retrait, c.categorie_id, c.nom_categorie, c.ordre_affichage,
               a.cout_revient,
               p.prix_ttc,
               EXISTS (SELECT 1 FROM ruptures r WHERE r.article_id = a.article_id AND r.jour = :j) AS rupture,
               (a.date_retrait IS NOT NULL AND a.date_retrait <= :j) AS retire,
               (a.date_ajout > :j) AS a_venir,
               pr.prix_ttc AS prochain_prix, pr.date_debut AS prochain_date
        FROM articles a JOIN categories_menu c USING (categorie_id)
        LEFT JOIN LATERAL (SELECT q.prix_ttc, q.date_debut FROM articles_prix_historique q
                           WHERE q.article_id = a.article_id AND q.date_debut > :j AND q.motif_changement = 'modification_gerant'
                           ORDER BY q.date_debut LIMIT 1) pr ON TRUE
        LEFT JOIN articles_prix_historique p ON p.article_id = a.article_id AND :j BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')
        WHERE a.etablissement_id = :e ORDER BY c.ordre_affichage, a.nom_article""", e=etablissement_id, j=j)


def categories(etablissement_id):
    return lire("SELECT categorie_id, nom_categorie FROM categories_menu WHERE etablissement_id = :e ORDER BY ordre_affichage", e=etablissement_id)


def _article(c, etablissement_id, article_id):
    """Verrouille l'article s'il appartient bien à l'établissement du compte."""
    return c.execute(text("SELECT article_id FROM articles WHERE article_id = :a AND etablissement_id = :e FOR UPDATE"),
                     dict(a=article_id, e=etablissement_id)).scalar()


def signaler_rupture(etablissement_id, article_id, rupture, utilisateur_id):
    """Met l'article en rupture pour aujourd'hui, ou le rend de nouveau disponible."""
    h = maintenant()
    with moteur().begin() as c:
        if not _article(c, etablissement_id, article_id):
            return
        if rupture:
            c.execute(text("""INSERT INTO ruptures (article_id, jour, signale_par, date_heure) VALUES (:a, :j, :u, :h)
                              ON CONFLICT DO NOTHING"""), dict(a=article_id, j=h.date(), u=utilisateur_id, h=h))
        else:
            c.execute(text("DELETE FROM ruptures WHERE article_id = :a AND jour = :j"), dict(a=article_id, j=h.date()))


def retirer_article(etablissement_id, article_id, retirer):
    """Retire l'article de la carte à partir d'aujourd'hui, ou le remet. Son historique de prix est conservé."""
    j = maintenant().date()
    with moteur().begin() as c:
        if not _article(c, etablissement_id, article_id):
            return
        c.execute(text("""UPDATE articles SET date_retrait = :d, statut_article = :s WHERE article_id = :a"""),
                  dict(d=j if retirer else None, s="retire" if retirer else "propose", a=article_id))


def _nouveau_prix_id(c):
    n = c.execute(text("SELECT COALESCE(MAX(CAST(SUBSTRING(prix_id FROM 4) AS INTEGER)), 0) + 1 FROM articles_prix_historique")).scalar()
    return f"PRX{n:06d}"


def changer_prix(etablissement_id, article_id, nouveau, utilisateur_id):
    """Change le prix d'un article (décision D-27).

    - Date d'effet : aujourd'hui si l'article n'a pas encore été commandé aujourd'hui, sinon demain (DQ-06 se juge à la journée).
    - L'historique (SCD2) est coupé à la veille de la date d'effet ; un seul prix reste ouvert par article (DQ-24).
    - Le jeu simulé va jusqu'au 31/12/2026 : les commandes simulées de l'article, sur la période du nouveau prix, sont recalculées
      (prix de ligne, montant de ligne, total de commande ; DQ-03, DQ-04, DQ-06). Le changement est écrit dans journal_prix.
    Renvoie (date d'effet, lignes recalculées, commandes recalculées), ou None si rien ne change."""
    n = maintenant()
    nouveau = round(float(nouveau), 3)
    with moteur().begin() as c:
        if not _article(c, etablissement_id, article_id) or nouveau <= 0:
            return None
        vendu = c.execute(text("""SELECT 1 FROM lignes_commande l JOIN commandes k USING (commande_id)
                                  WHERE l.article_id = :a AND k.date_heure_commande BETWEEN :d AND :n LIMIT 1"""),
                          dict(a=article_id, d=datetime.combine(n.date(), datetime.min.time()), n=n)).first()
        effet = n.date() + timedelta(days=1 if vendu else 0)
        r = c.execute(text("""SELECT prix_id, date_debut, date_fin, prix_ttc FROM articles_prix_historique
                              WHERE article_id = :a AND :j BETWEEN date_debut AND COALESCE(date_fin, DATE '2099-12-31')"""),
                      dict(a=article_id, j=effet)).first()
        if r is None or abs(float(r.prix_ttc) - nouveau) < 0.0005:
            return None
        if r.date_debut == effet:
            c.execute(text("UPDATE articles_prix_historique SET prix_ttc = :p, motif_changement = 'modification_gerant' WHERE prix_id = :i"),
                      dict(p=nouveau, i=r.prix_id))
        else:
            c.execute(text("UPDATE articles_prix_historique SET date_fin = :f, est_prix_actuel = FALSE WHERE prix_id = :i"),
                      dict(f=effet - timedelta(days=1), i=r.prix_id))
            c.execute(text("""INSERT INTO articles_prix_historique (prix_id, article_id, date_debut, date_fin, prix_ttc, motif_changement, est_prix_actuel)
                              VALUES (:i, :a, :d, :f, :p, 'modification_gerant', :act)"""),
                      dict(i=_nouveau_prix_id(c), a=article_id, d=effet, f=r.date_fin, p=nouveau, act=r.date_fin is None))
        if r.date_fin is None:
            c.execute(text("UPDATE articles SET prix_actuel_ttc = :p WHERE article_id = :a"), dict(p=nouveau, a=article_id))
        fin = r.date_fin or date(2099, 12, 31)
        lignes = c.execute(text("""UPDATE lignes_commande l SET prix_unitaire_ttc = :p, montant_ligne_ttc = :p * l.quantite
                                   FROM commandes k WHERE k.commande_id = l.commande_id AND l.article_id = :a
                                   AND CAST(k.date_heure_commande AS DATE) BETWEEN :d AND :f
                                   RETURNING l.commande_id"""), dict(p=nouveau, a=article_id, d=effet, f=fin)).scalars().all()
        cmds = sorted(set(lignes))
        if cmds:
            c.execute(text("""UPDATE commandes k SET montant_total_ttc = s.total
                              FROM (SELECT commande_id, SUM(montant_ligne_ttc) AS total FROM lignes_commande
                                    WHERE commande_id = ANY(:ids) GROUP BY commande_id) s
                              WHERE k.commande_id = s.commande_id"""), dict(ids=cmds))
        c.execute(text("""INSERT INTO journal_prix (article_id, ancien_prix, nouveau_prix, date_effet, date_heure, utilisateur_id,
                          lignes_recalculees, commandes_recalculees) VALUES (:a, :o, :p, :d, :h, :u, :l, :k)"""),
                  dict(a=article_id, o=r.prix_ttc, p=nouveau, d=effet, h=n, u=utilisateur_id, l=len(lignes), k=len(cmds)))
    return effet, len(lignes), len(cmds)


def ajouter_article(etablissement_id, categorie_id, nom, description, prix):
    """Nouvel article proposé dès aujourd'hui, avec sa première ligne de prix (motif « creation »)."""
    j = maintenant().date()
    nom = (nom or "").strip()[:40]
    with moteur().begin() as c:
        ok = c.execute(text("SELECT 1 FROM categories_menu WHERE categorie_id = :c AND etablissement_id = :e"),
                       dict(c=categorie_id, e=etablissement_id)).first()
        if not ok or not nom or float(prix) <= 0:
            raise ValueError("Catégorie, nom et prix sont obligatoires.")
        if c.execute(text("""SELECT 1 FROM articles WHERE etablissement_id = :e AND LOWER(nom_article) = LOWER(:n)
                             AND (date_retrait IS NULL OR date_retrait > :j)"""), dict(e=etablissement_id, n=nom, j=j)).first():
            raise ValueError("Un article de ce nom est déjà sur la carte.")
        n = c.execute(text("SELECT COALESCE(MAX(CAST(SUBSTRING(article_id FROM 4) AS INTEGER)), 0) + 1 FROM articles")).scalar()
        aid = f"ART{n:06d}"
        c.execute(text("""INSERT INTO articles (article_id, etablissement_id, categorie_id, nom_article, date_ajout, date_retrait,
                          prix_actuel_ttc, statut_article, description) VALUES (:a, :e, :c, :n, :j, NULL, :p, 'propose', :d)"""),
                  dict(a=aid, e=etablissement_id, c=categorie_id, n=nom, j=j, p=round(float(prix), 3), d=(description or "").strip()[:120] or None))
        c.execute(text("""INSERT INTO articles_prix_historique (prix_id, article_id, date_debut, date_fin, prix_ttc, motif_changement, est_prix_actuel)
                          VALUES (:i, :a, :j, NULL, :p, 'creation', TRUE)"""), dict(i=_nouveau_prix_id(c), a=aid, j=j, p=round(float(prix), 3)))
    return aid


def modifier_description(etablissement_id, article_id, description):
    with moteur().begin() as c:
        if _article(c, etablissement_id, article_id):
            c.execute(text("UPDATE articles SET description = :d WHERE article_id = :a"),
                      dict(d=(description or "").strip()[:120] or None, a=article_id))


# ---------- Gestion des tables (lot 2, migration 006) ----------

ZONES_VALIDES = ("terrasse", "salle", "etage")


def tables_gestion(etablissement_id):
    """Tables de l'établissement : en service ou retirées, et si une commande y est en cours ou à encaisser."""
    j = maintenant().date()
    return lire(f"""
        SELECT t.table_id, t.numero_table, t.zone, t.capacite, t.qr_code_id, t.date_installation, t.date_retrait,
               (t.date_retrait IS NOT NULL AND t.date_retrait <= :j) AS retiree,
               EXISTS (SELECT 1 FROM commandes c WHERE c.table_id = t.table_id AND (c.statut_commande IN {ACTIVES}
                       OR (c.statut_commande = 'servie' AND c.date_heure_reglement IS NULL))) AS en_cours
        FROM tables_salle t WHERE t.etablissement_id = :e ORDER BY retiree, t.numero_table""", e=etablissement_id, j=j)


def _verifier_table(c, etablissement_id, numero, zone, capacite, sauf=None):
    if zone not in ZONES_VALIDES:
        raise ValueError("Zone inconnue.")
    if not 1 <= int(numero) <= 999 or not 1 <= int(capacite) <= 20:
        raise ValueError("Numéro entre 1 et 999, places entre 1 et 20.")
    if c.execute(text("""SELECT 1 FROM tables_salle WHERE etablissement_id = :e AND numero_table = :n AND table_id <> COALESCE(:s, '')
                         AND (date_retrait IS NULL OR date_retrait > :j)"""),
                 dict(e=etablissement_id, n=int(numero), s=sauf, j=maintenant().date())).first():
        raise ValueError(f"La table {int(numero)} existe déjà.")


def ajouter_table(etablissement_id, numero, zone, capacite):
    """Nouvelle table en service dès aujourd'hui ; son QR code est utilisable tout de suite."""
    with moteur().begin() as c:
        c.execute(text("LOCK TABLE tables_salle IN SHARE ROW EXCLUSIVE MODE"))
        _verifier_table(c, etablissement_id, numero, zone, capacite)
        n = c.execute(text("SELECT COALESCE(MAX(CAST(SUBSTRING(table_id FROM 4) AS INTEGER)), 0) + 1 FROM tables_salle")).scalar()
        tid = f"TBL{n:05d}"
        c.execute(text("""INSERT INTO tables_salle (table_id, etablissement_id, numero_table, zone, capacite, qr_code_id, date_installation)
                          VALUES (:t, :e, :n, :z, :c, :q, :j)"""),
                  dict(t=tid, e=etablissement_id, n=int(numero), z=zone, c=int(capacite), q=f"QR{n:05d}", j=maintenant().date()))
    return tid


def modifier_table(etablissement_id, table_id, numero, zone, capacite):
    """Renumérote une table, change sa zone ou ses places. Son QR code ne change pas : il encode l'identifiant, pas le numéro."""
    with moteur().begin() as c:
        if not c.execute(text("SELECT 1 FROM tables_salle WHERE table_id = :t AND etablissement_id = :e FOR UPDATE"),
                         dict(t=table_id, e=etablissement_id)).first():
            return
        _verifier_table(c, etablissement_id, numero, zone, capacite, sauf=table_id)
        c.execute(text("UPDATE tables_salle SET numero_table = :n, zone = :z, capacite = :c WHERE table_id = :t"),
                  dict(n=int(numero), z=zone, c=int(capacite), t=table_id))


def retirer_table(etablissement_id, table_id, retirer):
    """Retire une table du service (refusé si une commande y est en cours ou à encaisser), ou la remet en service."""
    j = maintenant().date()
    with moteur().begin() as c:
        t = c.execute(text("SELECT numero_table, zone, capacite FROM tables_salle WHERE table_id = :t AND etablissement_id = :e FOR UPDATE"),
                      dict(t=table_id, e=etablissement_id)).first()
        if not t:
            return
        if retirer:
            if c.execute(text(f"""SELECT 1 FROM commandes WHERE table_id = :t AND (statut_commande IN {ACTIVES}
                                  OR (statut_commande = 'servie' AND date_heure_reglement IS NULL))"""), dict(t=table_id)).first():
                raise ValueError("Une commande est en cours ou à encaisser à cette table.")
        else:
            _verifier_table(c, etablissement_id, t.numero_table, t.zone, t.capacite, sauf=table_id)
        c.execute(text("UPDATE tables_salle SET date_retrait = :d WHERE table_id = :t"), dict(d=j if retirer else None, t=table_id))


def avis_table(etablissement_id, table_id, debut, fin):
    """Avis laissés à une table sur la période, les plus récents d'abord."""
    fin = min(fin, maintenant())
    return lire("""SELECT av.date_heure, av.commande_id, av.note, av.commentaire FROM avis av
                   WHERE av.etablissement_id = :e AND av.table_id = :t AND av.date_heure BETWEEN :d AND :f
                   ORDER BY av.date_heure DESC""", e=etablissement_id, t=table_id, d=debut, f=fin)


# ---------- Commande prise par le serveur (lot 3) ----------

def peut_commander(etablissement_id):
    """La formule du jour permet-elle la commande (DQ-09) ?"""
    return bool(un(f"""SELECT 1 AS ok FROM abonnements WHERE etablissement_id = :e AND formule_id IN {FORMULES_COMMANDE}
                        AND CAST(:j AS DATE) BETWEEN date_debut AND COALESCE(date_fin, DATE '2099-12-31')""",
                   e=etablissement_id, j=maintenant().date()))


def commande_equipe(etablissement_id, table_id, panier, note=None):
    """Commande prise par le serveur pour un client sans téléphone : session « serveur » sans scan,
    commande acceptée d'emblée (elle part en préparation). Renvoie l'identifiant de la commande."""
    t = un("""SELECT table_id FROM tables_salle WHERE table_id = :t AND etablissement_id = :e
              AND (date_retrait IS NULL OR date_retrait > CAST(:j AS DATE))""", t=table_id, e=etablissement_id, j=maintenant().date())
    panier = {a: int(q) for a, q in panier.items() if int(q) > 0}
    if not t or not panier:
        raise ValueError("Choisissez au moins un article.")
    if not peut_commander(etablissement_id):
        raise ValueError("La formule de l'établissement ne comprend pas la commande.")
    sid = ouvrir_session(table_id, etablissement_id, "serveur", "fr", scan=False)
    cid = passer_commande(sid, table_id, etablissement_id, panier, note, par_equipe=True)
    avancer(etablissement_id, cid)
    return cid


# ---------- Clôture de la journée (gérant, lot 3) ----------

def cloture(etablissement_id, jour):
    """Bilan d'une journée, borné à maintenant (le jeu simulé contient des données futures)."""
    debut = datetime.combine(jour, datetime.min.time())
    fin = min(datetime.combine(jour, datetime.max.time()), maintenant())
    p = dict(e=etablissement_id, d=debut, f=fin)
    r = {}
    r["reglements"] = lire("""SELECT mode_reglement, COUNT(*) AS n, SUM(montant_total_ttc) AS montant FROM commandes
                              WHERE etablissement_id = :e AND date_heure_reglement BETWEEN :d AND :f
                              GROUP BY mode_reglement ORDER BY montant DESC""", **p)
    r["commandes"] = un("""SELECT COUNT(*) FILTER (WHERE statut_commande = 'servie') AS servies,
                                  COALESCE(SUM(montant_total_ttc) FILTER (WHERE statut_commande = 'servie'), 0) AS chiffre,
                                  COUNT(*) FILTER (WHERE statut_commande = 'annulee') AS annulees,
                                  COALESCE(SUM(montant_total_ttc) FILTER (WHERE statut_commande = 'annulee'), 0) AS montant_annule,
                                  COUNT(*) FILTER (WHERE statut_commande IN ('nouvelle', 'en_prepa', 'prete')) AS en_cours,
                                  AVG(EXTRACT(EPOCH FROM date_heure_service - date_heure_commande) / 60)
                                      FILTER (WHERE statut_commande = 'servie') AS delai
                           FROM commandes WHERE etablissement_id = :e AND date_heure_commande BETWEEN :d AND :f""", **p)
    r["a_encaisser"] = lire("""SELECT t.numero_table, COUNT(*) AS n, SUM(c.montant_total_ttc) AS montant FROM commandes c
                               JOIN tables_salle t USING (table_id)
                               WHERE c.etablissement_id = :e AND c.statut_commande = 'servie' AND c.date_heure_reglement IS NULL
                                 AND c.date_heure_commande <= :f
                               GROUP BY t.numero_table ORDER BY t.numero_table""", **p)
    r["annulations"] = lire("""SELECT COALESCE(motif_annulation, 'non précisé') AS motif, COUNT(*) AS n FROM commandes
                               WHERE etablissement_id = :e AND statut_commande = 'annulee' AND date_heure_commande BETWEEN :d AND :f
                               GROUP BY 1 ORDER BY 2 DESC""", **p)
    r["appels"] = un("""SELECT COUNT(*) AS n, AVG(EXTRACT(EPOCH FROM date_heure_prise - date_heure_appel) / 60) AS attente
                        FROM appels WHERE etablissement_id = :e AND date_heure_appel BETWEEN :d AND :f""", **p)
    r["avis"] = un("""SELECT COUNT(*) AS n, AVG(note) AS moyenne FROM avis WHERE etablissement_id = :e AND date_heure BETWEEN :d AND :f""", **p)
    r["ruptures"] = lire("""SELECT a.nom_article FROM ruptures r JOIN articles a USING (article_id)
                            WHERE a.etablissement_id = :e AND r.jour = :j ORDER BY 1""", e=etablissement_id, j=jour)
    r["ventes"] = lire("""SELECT a.nom_article, c2.nom_categorie, SUM(l.quantite) AS quantite, SUM(l.montant_ligne_ttc) AS montant,
                                 a.cout_revient, SUM(l.quantite * a.cout_revient) AS cout
                          FROM lignes_commande l JOIN commandes c USING (commande_id) JOIN articles a ON a.article_id = l.article_id
                          JOIN categories_menu c2 ON c2.categorie_id = a.categorie_id
                          WHERE c.etablissement_id = :e AND c.statut_commande = 'servie' AND c.date_heure_commande BETWEEN :d AND :f
                          GROUP BY a.article_id, a.nom_article, c2.nom_categorie, a.cout_revient ORDER BY montant DESC""", **p)
    return r


# ---------- Coût de revient (lot 3, migration 009) ----------

def changer_cout(etablissement_id, article_id, cout):
    """Coût de revient d'un article saisi par le gérant (None pour l'effacer)."""
    with moteur().begin() as c:
        if _article(c, etablissement_id, article_id):
            c.execute(text("UPDATE articles SET cout_revient = :c, date_maj_cout = :j WHERE article_id = :a"),
                      dict(c=None if cout is None else round(float(cout), 3), j=maintenant().date(), a=article_id))


# ---------- Résultats de la phase 7 (migration 010, copiés par 02_oltp/copier_resultats_ml.py) ----------

def copie_ml():
    """Dernière copie des résultats : date de publication dans l'entrepôt et date de copie (None si jamais copiés)."""
    return un("SELECT max(publie_le) AS publie_le, max(copie_le) AS copie_le FROM ml_copie")


def scores_resiliation():
    """Établissements scorés (K19) avec leur ville, leur formule actuelle et leurs 3 facteurs, du plus au moins risqué."""
    return lire("""
        SELECT s.etablissement_id, e.nom_etablissement, v.ville AS nom_ville, f.nom_formule, s.probabilite, s.rang, s.alerte,
               s.facteur_1, s.facteur_2, s.facteur_3, s.mrr_ht, s.mois_observe, s.version_modele, e.gerant_prenom
        FROM ml_score_resiliation s
        JOIN etablissements e USING (etablissement_id)
        JOIN ref_villes v USING (ville_id)
        LEFT JOIN abonnements a ON a.etablissement_id = s.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        LEFT JOIN formules f ON f.formule_id = a.formule_id
        ORDER BY s.rang""", j=maintenant().date())


def candidats_commande():
    """Établissements Essentiel candidats à la formule Commande (EF-13), du plus au moins utilisateur du menu."""
    return lire("""
        SELECT c.etablissement_id, e.nom_etablissement, v.ville AS nom_ville, c.sessions_table_jour_3m, c.seuil_usage,
               c.probabilite_resiliation, (SELECT count(*) FROM tables_salle t WHERE t.etablissement_id = c.etablissement_id) AS nb_tables
        FROM ml_candidat_commande c JOIN etablissements e USING (etablissement_id) JOIN ref_villes v USING (ville_id)
        ORDER BY c.sessions_table_jour_3m DESC""")


def recommandations(etablissement_id):
    """Plats recommandés (EF-12) limités à la carte d'aujourd'hui : un plat retiré depuis la publication disparaît,
    des deux côtés de la recommandation."""
    j = maintenant().date()
    return lire("""
        WITH carte AS (SELECT a.nom_article, c.nom_categorie FROM articles a JOIN categories_menu c USING (categorie_id)
                       WHERE a.etablissement_id = :e AND a.date_ajout <= :j AND (a.date_retrait IS NULL OR a.date_retrait > :j))
        SELECT r.plat, p.nom_categorie AS categorie, r.rang, r.plat_recommande, q.nom_categorie AS categorie_recommandee, r.motif
        FROM ml_recommandation_plat r
        JOIN carte p ON p.nom_article = r.plat
        JOIN carte q ON q.nom_article = r.plat_recommande
        WHERE r.etablissement_id = :e
        ORDER BY r.plat, r.rang""", e=etablissement_id, j=j)
