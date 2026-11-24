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
from datetime import datetime, timedelta, timezone
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
    """Vérifie la migration 001, crée les séquences d'identifiants et les cale sur le plus grand identifiant existant."""
    with eng.begin() as c:
        ok = c.execute(text("""SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'menuscan' AND table_name = 'migrations')""")).scalar()
        faites = {r[0] for r in c.execute(text("SELECT migration_id FROM migrations"))} if ok else set()
        manquantes = sorted({"001_parcours_commande", "002_comptes_equipe", "003_persistance"} - faites)
        if manquantes:
            raise MigrationManquante(f"Migration manquante ({', '.join(manquantes)}). Lancer : python 02_oltp/charger_base_app.py --migrer")
        for seq, (table, col, pref, _) in SEQUENCES.items():
            c.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq}"))
            c.execute(text(f"""SELECT setval('{seq}', GREATEST(
                (SELECT COALESCE(MAX(CAST(SUBSTRING({col} FROM {len(pref) + 1}) AS BIGINT)), 0) FROM {table}),
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
        SELECT t.table_id, t.numero_table, t.zone, e.etablissement_id, e.nom_etablissement, e.type_etablissement,
               e.statut_etablissement, e.commandes_ouvertes, v.ville AS nom_ville, a.formule_id, f.nom_formule, f.inclut_commande
        FROM tables_salle t
        JOIN etablissements e USING (etablissement_id)
        LEFT JOIN ref_villes v USING (ville_id)
        LEFT JOIN abonnements a ON a.etablissement_id = e.etablissement_id
             AND CAST(:j AS DATE) BETWEEN a.date_debut AND COALESCE(a.date_fin, DATE '2099-12-31')
        LEFT JOIN formules f ON f.formule_id = a.formule_id
        WHERE t.table_id = :t""", t=table_id, j=maintenant().date())


def menu(etablissement_id):
    """Articles proposés aujourd'hui, prix en vigueur (DQ-06), description et rang de popularité sur 30 jours."""
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
        WHERE a.etablissement_id = :e AND a.statut_article = 'propose'
              AND CAST(:j AS DATE) >= a.date_ajout AND (a.date_retrait IS NULL OR a.date_retrait > CAST(:j AS DATE))
        ORDER BY c.ordre_affichage, (pop.article_id IS NULL), a.nom_article""",
                e=etablissement_id, j=n.date(), d=n - timedelta(days=30), n=n)


def delai_moyen(etablissement_id):
    """Délai moyen entre commande et service sur les 30 derniers jours, en minutes."""
    n = maintenant()
    r = un("""SELECT AVG(EXTRACT(EPOCH FROM date_heure_service - date_heure_commande) / 60) AS m FROM commandes
              WHERE etablissement_id = :e AND statut_commande = 'servie' AND date_heure_commande BETWEEN :d AND :n""",
           e=etablissement_id, d=n - timedelta(days=30), n=n)
    return float(r["m"]) if r and r["m"] is not None else None


def suivi(commande_id):
    c = un("""SELECT commande_id, statut_commande, date_heure_commande, date_heure_acceptation, date_heure_prete,
                     date_heure_service, montant_total_ttc, note FROM commandes WHERE commande_id = :c""", c=commande_id)
    if c:
        c["lignes"] = lire("""SELECT l.quantite, a.nom_article, l.montant_ligne_ttc FROM lignes_commande l
                              JOIN articles a USING (article_id) WHERE l.commande_id = :c ORDER BY l.ligne_id""", c=commande_id)
    return c


# ---------- Comptes de l'équipe ----------

_COMPTE = """
        SELECT u.utilisateur_id, u.identifiant, u.role, u.prenom, u.etablissement_id, e.nom_etablissement, e.gerant_prenom,
               v.ville AS nom_ville, a.formule_id, f.nom_formule, f.inclut_statistiques
        FROM utilisateurs u
        JOIN etablissements e USING (etablissement_id)
        JOIN ref_villes v USING (ville_id)
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
               STRING_AGG(l.quantite || ' ' || LOWER(a.nom_article), ' · ' ORDER BY l.ligne_id) AS detail
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
    """État de chaque table : appel du serveur (15 min), commande active, menu ouvert (30 min) ou libre."""
    n = maintenant()
    return lire(f"""
        SELECT t.table_id, t.numero_table, t.zone,
               EXISTS (SELECT 1 FROM evenements ev JOIN sessions s USING (session_id)
                       WHERE s.table_id = t.table_id AND ev.type_evenement = 'appel_serveur' AND ev.horodatage BETWEEN :a AND :n) AS appel,
               EXISTS (SELECT 1 FROM commandes c WHERE c.table_id = t.table_id AND c.statut_commande IN {ACTIVES}) AS commande,
               EXISTS (SELECT 1 FROM sessions s WHERE s.table_id = t.table_id AND s.fin_session BETWEEN :o AND :n) AS ouvert
        FROM tables_salle t WHERE t.etablissement_id = :e ORDER BY t.numero_table""",
                e=etablissement_id, n=n, a=n - timedelta(minutes=15), o=n - timedelta(minutes=30))


# ---------- Écriture ----------

def _evenement(c, session_id, etab, type_ev, h, article_id=None, quantite=None):
    c.execute(text("""INSERT INTO evenements (evenement_id, session_id, etablissement_id, horodatage, type_evenement, article_id, quantite)
                      VALUES (:i, :s, :e, :h, :t, :a, :q)"""),
              dict(i=_nouvel_id(c, "seq_evenement"), s=session_id, e=etab, h=h, t=type_ev, a=article_id, q=quantite))
    c.execute(text("""UPDATE sessions SET fin_session = GREATEST(fin_session, :h), nb_evenements = nb_evenements + 1,
                      a_ajoute_panier = a_ajoute_panier OR :p WHERE session_id = :s"""),
              dict(h=h, s=session_id, p=(type_ev == "ajout_panier")))


def ouvrir_session(table_id, etablissement_id, appareil, langue="fr"):
    """Un scan de QR code : crée la session et ses deux premiers événements (scan_qr, vue_menu)."""
    h = maintenant()
    with moteur().begin() as c:
        sid = _nouvel_id(c, "seq_session")
        c.execute(text("""INSERT INTO sessions (session_id, etablissement_id, table_id, debut_session, fin_session, appareil, langue,
                          nb_articles_vus, a_ajoute_panier, a_commande, nb_evenements)
                          VALUES (:s, :e, :t, :h, :h, :a, :l, 0, FALSE, FALSE, 0)"""),
                  dict(s=sid, e=etablissement_id, t=table_id, h=h, a=appareil, l=langue))
        _evenement(c, sid, etablissement_id, "scan_qr", h)
        _evenement(c, sid, etablissement_id, "vue_menu", h)
    return sid


def changer_langue(session_id, langue):
    with moteur().begin() as c:
        c.execute(text("UPDATE sessions SET langue = :l WHERE session_id = :s"), dict(l=langue, s=session_id))


def journaliser(session_id, etablissement_id, type_ev, article_id=None, quantite=None):
    with moteur().begin() as c:
        _evenement(c, session_id, etablissement_id, type_ev, maintenant(), article_id, quantite)


def passer_commande(session_id, table_id, etablissement_id, panier, note=None):
    """panier : {article_id: quantite}. Les prix sont relus en base au moment de la commande (DQ-06)."""
    h = maintenant()
    with moteur().begin() as c:
        ouvert = c.execute(text("SELECT commandes_ouvertes FROM etablissements WHERE etablissement_id = :e"), dict(e=etablissement_id)).scalar()
        if not ouvert:
            raise ValueError("L'établissement ne prend plus de commandes pour le moment.")
        if c.execute(text("SELECT a_commande FROM sessions WHERE session_id = :s FOR UPDATE"), dict(s=session_id)).scalar():
            raise ValueError("Cette session a déjà une commande.")
        prix = {r.article_id: r.prix_ttc for r in c.execute(text("""
            SELECT p.article_id, p.prix_ttc FROM articles_prix_historique p
            WHERE p.article_id = ANY(:ids) AND CAST(:j AS DATE) BETWEEN p.date_debut AND COALESCE(p.date_fin, DATE '2099-12-31')"""),
            dict(ids=list(panier), j=h.date()))}
        if set(prix) != set(panier):
            raise ValueError("Un article n'est plus disponible.")
        cid = _nouvel_id(c, "seq_commande")
        lignes = [(_nouvel_id(c, "seq_ligne"), a, q, prix[a], prix[a] * q) for a, q in panier.items()]
        c.execute(text("""INSERT INTO commandes (commande_id, session_id, etablissement_id, table_id, date_heure_commande, statut_commande,
                          date_heure_service, nb_lignes, nb_articles, montant_total_ttc, mode_reglement, motif_annulation, note)
                          VALUES (:c, :s, :e, :t, :h, 'nouvelle', NULL, :nl, :na, :m, NULL, NULL, :no)"""),
                  dict(c=cid, s=session_id, e=etablissement_id, t=table_id, h=h, nl=len(lignes),
                       na=sum(l[2] for l in lignes), m=sum(l[4] for l in lignes), no=(note or "").strip()[:200] or None))
        for lid, a, q, pu, mt in lignes:
            c.execute(text("""INSERT INTO lignes_commande (ligne_id, commande_id, article_id, quantite, prix_unitaire_ttc, montant_ligne_ttc)
                              VALUES (:l, :c, :a, :q, :p, :m)"""), dict(l=lid, c=cid, a=a, q=q, p=pu, m=mt))
        _evenement(c, session_id, etablissement_id, "commande_envoyee", h)
        c.execute(text("UPDATE sessions SET a_commande = TRUE WHERE session_id = :s"), dict(s=session_id))
    return cid


def avancer(etablissement_id, commande_id, mode_reglement=None):
    """Fait passer une commande à l'étape suivante et horodate l'étape (seulement une commande de l'établissement du compte)."""
    with moteur().begin() as c:
        statut = c.execute(text("SELECT statut_commande FROM commandes WHERE commande_id = :c AND etablissement_id = :e FOR UPDATE"),
                           dict(c=commande_id, e=etablissement_id)).scalar()
        if statut not in SUIVANT:
            return
        suivant, colonne = SUIVANT[statut]
        c.execute(text(f"""UPDATE commandes SET statut_commande = :s, {colonne} = :h,
                           mode_reglement = COALESCE(:m, mode_reglement) WHERE commande_id = :c"""),
                  dict(s=suivant, h=maintenant(), m=mode_reglement if suivant == "servie" else None, c=commande_id))


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
    return dict(jeton=jeton, session_id=sid, panier={}, langue=langue, vue="menu", commande_id=None)


def etat_client(jeton, table_id):
    """Relit l'état d'un client. None si le jeton est inconnu, d'une autre table ou inutilisé depuis plus de 4 heures."""
    if not isinstance(jeton, str) or not jeton or len(jeton) > 40:
        return None
    r = un("""SELECT jeton, session_id, panier, langue, vue, commande_id FROM etats_client
              WHERE jeton = :j AND table_id = :t AND date_maj >= now() - make_interval(hours => :h)""",
           j=jeton, t=table_id, h=DUREE_ETAT_CLIENT_HEURES)
    if r and isinstance(r["panier"], str):
        r["panier"] = json.loads(r["panier"])
    return r


def sauver_etat_client(jeton, panier, langue, vue, commande_id):
    with moteur().begin() as c:
        c.execute(text("""UPDATE etats_client SET panier = CAST(:p AS JSONB), langue = :l, vue = :v, commande_id = :c, date_maj = now()
                          WHERE jeton = :j"""), dict(p=json.dumps(panier), l=langue, v=vue, c=commande_id, j=jeton))
