"""Pages des deux rapports, d'après les maquettes (page 1280 x 720).

Éléments : dictionnaires avec une clé « k » :
- segment : filtre déroulant (champ « C:table.colonne ») ;
- tuile   : chiffre clé ; « valeur » et « detail » sont des mesures texte (« M:Nom ») ;
- visuel  : graphique ou tableau ; « roles » = {rôle: [champs]} ;
- texte   : zone de texte fixe.
Un champ s'écrit « M:mesure » ou « C:table.colonne » ; « |Libellé » à la fin renomme la colonne d'un tableau.
"""
from modele_def import BLEU, ORANGE

GRILLE = {"y_seg": 58, "y_tuile": 116, "h_tuile": 84, "y1": 210, "h1": 290, "y2": 510, "h2": 196}


def segments(*champs):
    return [{"k": "segment", "x": 16 + i * 160, "y": 58, "w": 150, "h": 50, "titre": t, "champ": c}
            for i, (t, c) in enumerate(champs)]


def tuiles(*defs):
    n = len(defs)
    w = (1248 - (n - 1) * 12) / n
    res = []
    for i, d in enumerate(defs):
        titre, valeur, detail = d[:3]
        res.append({"k": "tuile", "x": round(16 + i * (w + 12)), "y": 116, "w": round(w), "h": 84, "titre": titre,
                    "valeur": valeur, "detail": detail, "alerte": len(d) > 3 and d[3]})
    return res


def note(texte, x=700, w=564):
    return {"k": "texte", "x": x, "y": 66, "w": w, "h": 32, "texte": texte, "taille": 9, "couleur": "#64748B",
            "align": "right"}


def v(type_, x, y, w, h, titre, roles, **opt):
    return {"k": "visuel", "type": type_, "x": x, "y": y, "w": w, "h": h, "titre": titre, "roles": roles, **opt}


ANNEE = ("Période", "C:dim_date.annee")

STARTUP = [
    ("TB-1 · Croissance", segments(ANNEE, ("Ville", "C:dim_etablissement.ville"),
                                   ("Type", "C:dim_etablissement.type_etablissement"),
                                   ("Formule", "C:dim_formule.nom_formule")) + [
        note("Valeur du dernier mois de la période pour K01, K02 et K03"),
        *tuiles(("Établissements actifs (K01)", "M:Texte K01", "M:Texte K01 détail"),
                ("MRR (K02)", "M:Texte K02", "M:Texte K02 détail"),
                ("ARR (K03)", "M:Texte K03", "M:Texte K03 détail"),
                ("Facturé (K16)", "M:Texte K16", "M:Texte K16 détail"),
                ("Factures payées en retard (K17)", "M:Texte K17", "M:Texte K17 détail")),
        v("lineChart", 16, 210, 800, 290, "MRR mensuel sur 36 mois (DT HT)",
          {"Category": ["C:dim_date.premier_jour_mois"], "Y": ["M:K02 MRR"]},
          sous_titre="Valeur en fin de mois, lue dans fait_abonnement_mensuel"),
        v("waterfallChart", 828, 210, 436, 290, "Mouvements de MRR (K04)",
          {"Category": ["C:Pont MRR.etape"], "Y": ["M:Pont MRR valeur"]}, sous_titre="M:Texte variation MRR",
          tri=("C:Pont MRR.etape", "Ascending")),
        v("clusteredBarChart", 16, 510, 616, 196, "MRR par formule (DT HT)",
          {"Category": ["C:dim_formule.nom_formule"], "Y": ["M:K02 MRR"]}, etiquettes=True),
        v("clusteredBarChart", 648, 510, 616, 196, "Établissements actifs par ville",
          {"Category": ["C:dim_etablissement.ville"], "Y": ["M:K01 Établissements actifs"]}, etiquettes=True,
          tri=("M:K01 Établissements actifs", "Descending")),
    ]),
    ("TB-2 · Rétention", segments(ANNEE, ("Cohorte", "C:dim_etablissement.trimestre_cohorte"),
                                  ("Formule", "C:dim_etablissement.formule_actuelle"),
                                  ("Canal", "C:dim_etablissement.nom_canal")) + [
        note("Formule et canal : ceux de l'établissement"),
        *tuiles(("Taux de résiliation mensuel (K05)", "M:Texte K05", "M:Texte K05 détail"),
                ("Résiliations", "M:Texte résiliations", "M:Texte résiliations détail"),
                ("Rétention à 12 mois (K06)", "M:Texte K06", "M:Texte K06 détail"),
                ("MRR perdu (K04)", "M:Texte MRR perdu", "M:Texte MRR perdu détail")),
        v("lineChart", 16, 210, 640, 290, "Taux de résiliation mensuel (K05)",
          {"Category": ["C:dim_date.annee_mois"], "Y": ["M:K05 Taux de résiliation mensuel"]},
          sous_titre="M:Texte moyenne K05", tri=("C:dim_date.annee_mois", "Ascending")),
        v("pivotTable", 668, 210, 596, 290, "Rétention par cohorte de mise en service (K06)",
          {"Rows": ["C:dim_etablissement.trimestre_cohorte|Cohorte"], "Columns": ["C:Mois écoulés.libelle"],
           "Values": ["M:K06 Rétention de cohorte|Rétention"]},
          sous_titre="Part des établissements encore actifs n mois après leur mise en service",
          fond_cellules=("M:K06 Rétention de cohorte", "M:Couleur cohorte"),
          texte_cellules=("M:K06 Rétention de cohorte", "M:Couleur texte cohorte")),
        v("clusteredBarChart", 16, 510, 408, 196, "Résiliations par formule",
          {"Category": ["C:dim_etablissement.formule_actuelle"], "Y": ["M:Résiliations"]}, etiquettes=True),
        v("clusteredBarChart", 436, 510, 408, 196, "Résiliations par canal",
          {"Category": ["C:dim_etablissement.nom_canal"], "Y": ["M:Résiliations"]}, etiquettes=True,
          tri=("M:Résiliations", "Descending")),
        v("clusteredBarChart", 856, 510, 408, 196, "Motifs déclarés",
          {"Category": ["C:dim_etablissement.motif_resiliation"], "Y": ["M:Résiliations"]}, etiquettes=True,
          tri=("M:Résiliations", "Descending")),
    ]),
    ("TB-3 · Acquisition", segments(ANNEE, ("Canal", "C:dim_canal.nom_canal"),
                                    ("Campagne", "C:fait_marketing.campagne_id"), ("Ville", "C:dim_ville.ville")) + [
        note("CAC : dépenses / établissements signés sur la période"),
        *tuiles(("Conversion des prospects (K07)", "M:Texte K07", "M:Texte K07 détail"),
                ("Délai de signature (K08)", "M:Texte K08", "M:Texte K08 détail"),
                ("CAC le plus bas (K09)", "M:Texte CAC bas", "M:Texte CAC bas détail"),
                ("CAC le plus haut (K09)", "M:Texte CAC haut", "M:Texte CAC haut détail", True),
                ("Valeur vie client (K10)", "M:Texte K10", "M:Texte K10 détail")),
        v("funnel", 16, 210, 400, 290, "Entonnoir commercial (K07)",
          {"Category": ["C:Étapes commerciales.etape"], "Y": ["M:Prospects par étape"]},
          sous_titre="M:Texte prospects", tri=("C:Étapes commerciales.etape", "Ascending")),
        v("clusteredBarChart", 428, 210, 412, 290, "CAC par canal (K09)",
          {"Category": ["C:dim_canal.nom_canal"], "Y": ["M:K09 CAC"]}, etiquettes=True,
          sous_titre="DT TTC par établissement signé · bleu : le plus bas, orange : le plus haut",
          couleur_categorie="M:Couleur CAC"),
        v("scatterChart", 852, 210, 412, 290, "CAC et valeur vie client par canal",
          {"Category": ["C:dim_canal.nom_canal"], "X": ["M:K09 CAC"], "Y": ["M:K10 Valeur vie client par canal"]},
          sous_titre="Un point par canal : en haut à gauche, le canal le plus rentable", etiquettes=True),
        v("tableEx", 16, 510, 1248, 196, "Campagnes marketing (K11)",
          {"Values": ["C:fait_marketing.campagne_id|Campagne", "C:dim_canal.nom_canal|Canal",
                      "M:Dépenses marketing TTC|Dépense (DT)", "M:Clics|Clics", "M:K11 Coût par clic|Coût par clic",
                      "M:K11 Taux de clic|Taux de clic", "M:Signatures (campagne)|Signatures"]},
          sous_titre="Tri par dépense décroissante · coût par clic et taux de clic : canaux en ligne",
          tri=("M:Dépenses marketing TTC", "Descending")),
    ]),
    ("TB-4 · Pilotage ML", segments(("Ville", "C:dim_etablissement.ville"),
                                    ("Formule", "C:dim_etablissement.formule_actuelle")) + [
        note("Scores K19 produits en phase 7 · [phase 7] = à compléter"),
        *tuiles(("Établissements à risque élevé", "M:Texte phase 7", "M:Texte seuil K19"),
                ("MRR menacé", "M:Texte phase 7", "M:Texte MRR menacé"),
                ("Candidats Essentiel → Commande", "M:Texte phase 7", "M:Texte candidats"),
                ("Délai de résolution (K18)", "M:Texte K18", "M:Texte K18 détail")),
        v("tableEx", 16, 210, 740, 496, "Établissements à risque de résiliation (K19)",
          {"Values": ["C:dim_etablissement.nom_etablissement|Établissement",
                      "C:dim_etablissement.formule_actuelle|Formule", "M:Score K19|Score",
                      "M:MRR actuel de l'établissement|MRR (DT HT)"]},
          sous_titre="Mise en page seulement : les scores viendront du modèle de la phase 7 (jalon J8)",
          tri=("M:MRR actuel de l'établissement", "Descending")),
        v("tableEx", 768, 210, 496, 496, "Candidats à la formule Commande",
          {"Values": ["C:dim_etablissement.nom_etablissement|Établissement (Essentiel)",
                      "M:K12 (Essentiel)|Sessions / table / jour (K12)", "M:Sessions (Essentiel)|Sessions",
                      "M:Tables (Essentiel)|Tables"]},
          sous_titre="Tri par usage du QR code : plus le menu est consulté, plus la commande a de chances d'être utilisée",
          tri=("M:K12 (Essentiel)", "Descending")),
    ]),
]

ETAB = ("Établissement", "C:dim_etablissement.nom_etablissement")
ETABLISSEMENT = [
    ("TB-5 · Activité", segments(ETAB, ANNEE) + [
        note("Rôle « Gérant démo » : un seul établissement visible"),
        *tuiles(("Commandes servies", "M:Texte commandes servies", "M:Texte commandes servies détail"),
                ("Chiffre d'affaires servi", "M:Texte CA servi", "M:Texte CA servi détail"),
                ("Panier moyen (K14)", "M:Texte K14", "M:Texte K14 détail"),
                ("Taux d'annulation (K15)", "M:Texte K15", "M:Texte K15 détail"),
                ("Commandes par table", "M:Texte commandes par table", "M:Texte commandes par table détail")),
        v("clusteredColumnChart", 16, 210, 820, 496, "Chiffre d'affaires servi par semaine (DT TTC)",
          {"Category": ["C:dim_date.debut_semaine"], "Y": ["M:CA commandes servies TTC"]},
          sous_titre="Barres orange : semaines avec des jours de Ramadan", couleur_categorie="M:Couleur semaine"),
        v("clusteredBarChart", 848, 210, 416, 496, "Chiffre d'affaires par table (DT TTC)",
          {"Category": ["C:dim_table.libelle_table"], "Y": ["M:CA commandes servies TTC"]}, etiquettes=True,
          sous_titre="M:Texte CA par zone", couleur_categorie="M:Couleur zone",
          tri=("M:CA commandes servies TTC", "Descending")),
    ]),
    ("TB-6 · Menu", segments(ETAB, ANNEE, ("Catégorie", "C:dim_article.nom_categorie")) + [
        note("Marge : estimée avec les taux de coût par catégorie (hypothèses, A-16)"),
        *tuiles(("Taux de commande (K13)", "M:Texte K13", "M:Texte K13 détail"),
                ("Ajout au panier (K20)", "M:Texte panier", "M:Texte panier détail"),
                ("Articles au menu", "M:Texte articles", "M:Texte articles détail"),
                ("Fiche vue mais peu commandée", "M:Article le moins converti", "M:Article le moins converti détail",
                 True)),
        v("tableEx", 16, 210, 680, 496, "Articles par chiffre d'affaires",
          {"Values": ["C:dim_article.nom_article|Article", "C:dim_article.nom_categorie|Catégorie",
                      "M:Prix TTC actuel|Prix TTC", "M:Vues de fiche|Vues", "M:Commandes de l'article|Cmd",
                      "M:Conversion de la fiche|Conversion", "M:Ventes servies TTC (lignes)|CA (DT)",
                      "M:K22 Marge unitaire estimée|Marge unit.", "M:K22 Classe du plat|Classe (K22)"]},
          sous_titre="Conversion = commandes / vues de la fiche ; elle peut dépasser 100 % (ajout depuis la liste)",
          tri=("M:Ventes servies TTC (lignes)", "Descending")),
        v("scatterChart", 708, 210, 300, 496, "Vues et commandes par article",
          {"Category": ["C:dim_article.nom_article"], "X": ["M:Vues de fiche"], "Y": ["M:Commandes de l'article"]},
          sous_titre="Orange : très vus, peu commandés", couleur_categorie="M:Couleur article"),
        v("funnel", 1020, 210, 244, 496, "Entonnoir de session",
          {"Category": ["C:Étapes de session.etape"], "Y": ["M:Étapes de session valeur"]},
          sous_titre="Formules Commande et Pro", tri=("C:Étapes de session.etape", "Ascending")),
    ]),
    ("TB-7 · Temps", segments(ETAB, ANNEE, ("Période d'activité", "C:dim_date.periode_activite")) + [
        note("Effet du Ramadan programmé dans le générateur : la page le vérifie (A-18)"),
        *tuiles(("Heure de pointe hors Ramadan", "M:Heure de pointe hors Ramadan",
                 "M:Heure de pointe hors Ramadan détail"),
                ("Heure de pointe pendant le Ramadan", "M:Heure de pointe Ramadan", "M:Heure de pointe Ramadan détail",
                 True),
                ("Commandes par jour", "M:Texte commandes par jour", "M:Texte commandes par jour détail", True),
                ("Chiffre d'affaires par jour", "M:Texte CA par jour", "M:Texte CA par jour détail", True)),
        v("pivotTable", 16, 210, 820, 400, "Commandes servies par heure et par jour de la semaine",
          {"Rows": ["C:dim_date.jour_court|Jour"], "Columns": ["C:dim_heure.libelle_court"],
           "Values": ["M:Commandes servies"]},
          sous_titre="Plus la case est foncée, plus il y a de commandes",
          fond_cellules=("M:Commandes servies", "M:Couleur heure")),
        v("lineChart", 848, 210, 416, 400, "Profil horaire : Ramadan et hors Ramadan",
          {"Category": ["C:dim_heure.libelle_court"], "Y": ["M:Part horaire hors Ramadan|Hors Ramadan",
                                                             "M:Part horaire Ramadan|Ramadan"]},
          sous_titre="Part des commandes servies de chaque heure", tri=("C:dim_heure.libelle_court", "Ascending"),
          couleurs_series={"M:Part horaire hors Ramadan": BLEU, "M:Part horaire Ramadan": ORANGE}),
        {"k": "tuile", "x": 16, "y": 620, "w": 1248, "h": 86, "titre": "Été et hors été",
         "valeur": "M:Texte été", "detail": None, "alerte": False, "petite": True},
    ]),
    ("TB-8 · Prix", segments(ETAB, ("Article", "C:dim_article.nom_article"),
                             ("Catégorie", "C:dim_article.nom_categorie"), ANNEE) + [
        note("Volumes faibles : à lire comme une tendance, jamais comme un effet prouvé"),
        *tuiles(("Changements de prix", "M:Texte changements", "M:Texte changements détail"),
                ("Hausse moyenne", "M:Texte hausse", "M:Texte hausse détail"),
                ("Sensibilité au prix par catégorie", "M:Texte phase 7", "M:Texte sensibilité détail")),
        v("lineClusteredColumnComboChart", 16, 210, 640, 400, "M:Titre prix et quantités",
          {"Category": ["C:dim_date.premier_jour_mois"], "Y": ["M:Quantités servies|Quantités servies"],
           "Y2": ["M:Prix moyen pratiqué|Prix TTC moyen"]},
          sous_titre="Barres : quantités servies par mois · ligne : prix TTC moyen pratiqué",
          couleurs_series={"M:Prix moyen pratiqué": ORANGE}),
        v("tableEx", 668, 210, 596, 400, "Changements de prix et quantités avant / après",
          {"Values": ["C:dim_article.nom_article|Article", "C:dim_article.valide_du|Date",
                      "M:Prix avant → après|Prix TTC (DT)", "M:Hausse de prix|Hausse", "M:Fenêtre (jours)|Fenêtre (j)",
                      "M:Quantités avant → après|Qté avant → après", "M:Écart des quantités|Écart"]},
          sous_titre="Choisir un établissement · fenêtre égale avant et après, au plus 30 jours",
          tri=("C:dim_article.valide_du", "Descending")),
        {"k": "texte", "x": 16, "y": 620, "w": 1248, "h": 86, "cadre": True, "taille": 11, "couleur": "#334155",
         "texte": "Plats recommandés : réservés à la formule Pro (EF-12). Liste « souvent pris avec » produite par les "
                  "règles d'association de la phase 7 (support, confiance, lift)."},
    ]),
]

RAPPORTS = {
    "MenuScan_Startup": ("MenuScan TN · Rapport Startup", "Données au 31/12/2026", STARTUP),
    "MenuScan_Etablissement": ("MenuScan TN · Rapport Établissement", "M:Nom de l'établissement", ETABLISSEMENT),
}
