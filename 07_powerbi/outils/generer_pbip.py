"""Génère le projet Power BI complet (format PBIP) de MenuScan TN.

- MenuScan.SemanticModel : modèle partagé (TMDL) lu depuis le schéma marts de PostgreSQL ;
- MenuScan_Startup.pbip et MenuScan_Etablissement.pbip : deux rapports (format PBIR) branchés sur ce modèle.

Usage : python 07_powerbi/outils/generer_pbip.py
Les dossiers générés sont remplacés à chaque exécution.
"""
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path

import psycopg2

DOSSIER = Path(__file__).resolve().parents[1]
RACINE = DOSSIER.parent
sys.path.insert(0, str(RACINE / "04_ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingerer import lire_env, nom_base  # noqa: E402
from modele_def import (COLONNES_CALCULEES, MESURES, RELATIONS, ROLE_FILTRES, ROLE_NOM, SERVEUR, TABLES,  # noqa: E402
                        TABLES_CALCULEES, TRI)
from rapports_def import RAPPORTS  # noqa: E402

MODELE = "MenuScan"
SCH = "https://developer.microsoft.com/json-schemas/fabric"
S_VISUEL = f"{SCH}/item/report/definition/visualContainer/2.9.0/schema.json"
TYPES = {"text": "string", "character varying": "string", "integer": "int64", "smallint": "int64", "bigint": "int64",
         "numeric": "decimal", "double precision": "double", "boolean": "boolean", "date": "dateTime",
         "timestamp without time zone": "dateTime", "timestamp with time zone": "dateTime"}


def ident(graine, n=20):
    """Identifiant stable (même résultat à chaque génération, donc diffs Git propres)."""
    return hashlib.sha1(graine.encode("utf-8")).hexdigest()[:n]


def guid(graine):
    return str(uuid.UUID(hashlib.md5(graine.encode("utf-8")).hexdigest()))


def nom_tmdl(nom):
    if nom.replace("_", "").isalnum() and nom.isascii() and not nom.startswith("_"):
        return nom
    return "'" + nom.replace("'", "''") + "'"


def ecrire(chemin, contenu):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(contenu, str):
        contenu = json.dumps(contenu, ensure_ascii=False, indent=2) + "\n"
    chemin.write_text(contenu, encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ modèle sémantique
def colonnes_marts():
    e = lire_env()
    con = psycopg2.connect(host=e.get("POSTGRES_HOST", "localhost"), port=e.get("POSTGRES_PORT", "5432"),
                           user=e["POSTGRES_USER"], password=e["POSTGRES_PASSWORD"], dbname=nom_base())
    cur = con.cursor()
    cur.execute("select table_schema, table_name, column_name, data_type from information_schema.columns "
                "where table_schema in ('marts', 'ml') order by table_schema, table_name, ordinal_position")
    res = {}
    for sch, t, c, ty in cur.fetchall():
        if sch == "ml" and c == "publie_le":
            continue
        res.setdefault(t if sch == "marts" else f"ml_{t}", []).append((c, ty))
    con.close()
    manquantes = [t for t in TABLES if t not in res]
    if manquantes:
        sys.exit(f"Tables absentes des schémas marts et ml (lancer 04_publication_resultats pour ml) : {manquantes}")
    return res


def source(t):
    """(schéma, table PostgreSQL) d'une table du modèle : les tables « ml_xxx » viennent du schéma ml (phase 7)."""
    return ("ml", t[3:]) if t.startswith("ml_") else ("marts", t)


def format_colonne(t, c, ty, dt):
    if dt == "dateTime":
        return "Short Date" if ty == "date" else "General Date"
    if dt == "decimal":
        return "#,0.000"
    if dt == "int64" and not c.endswith("_id") and c != "heure":
        return "#,0" if t.startswith("fait_") else "0"
    return None


def table_tmdl(t, cols, cles):
    L = [f"table {t}"]
    if t == "dim_date":
        L.append("\tdataCategory: Time")
    L.append("")
    for c, ty in cols:
        dt = TYPES[ty]
        L += [f"\tcolumn {nom_tmdl(c)}", f"\t\tdataType: {dt}"]
        if t == "dim_date" and c == "date":
            L.append("\t\tisKey")
        if (t, c) in cles:
            L.append("\t\tisHidden")
        f = format_colonne(t, c, ty, dt)
        if f:
            L.append(f"\t\tformatString: {f}")
        somme = t.startswith("fait_") and (dt in ("decimal", "double") or (dt == "int64" and f))
        L += [f"\t\tsummarizeBy: {'sum' if somme else 'none'}", f"\t\tsourceColumn: {c}"]
        if (t, c) in TRI:
            L.append(f"\t\tsortByColumn: {TRI[(t, c)]}")
        L.append("")
    for tc, c, dt, f, expr in COLONNES_CALCULEES:
        if tc != t:
            continue
        L += expression_tmdl(f"\tcolumn {nom_tmdl(c)} =", expr, 1)
        L.append(f"\t\tdataType: {dt}")
        if f:
            L.append(f"\t\tformatString: {f}")
        L.append("\t\tsummarizeBy: none")
        if (t, c) in TRI:
            L.append(f"\t\tsortByColumn: {TRI[(t, c)]}")
        L.append("")
    L += [f"\tpartition {t} = m", "\t\tmode: import", "\t\tsource =",
          "\t\t\t\tlet", "\t\t\t\t\tSource = PostgreSQL.Database(Serveur, Base),",
          f'\t\t\t\t\tDonnees = Source{{[Schema = "{source(t)[0]}", Item = "{source(t)[1]}"]}}[Data]'
          + ("," if t.startswith("ml_") else ""),
          *(['\t\t\t\t\tColonnes = Table.RemoveColumns(Donnees, {"publie_le"})',
             "\t\t\t\tin", "\t\t\t\t\tColonnes", ""] if t.startswith("ml_") else
            ["\t\t\t\tin", "\t\t\t\t\tDonnees", ""])]
    return "\n".join(L)


def expression_tmdl(entete, expr, niveau):
    """Objet suivi d'une expression DAX : sur une ligne, ou sur plusieurs entre ``` (indentation par tabulations)."""
    lignes = expr.strip("\n").split("\n")
    if len(lignes) == 1:
        return [f"{entete} {lignes[0]}"]
    res = [f"{entete} ```"]
    for l in lignes:
        n = len(l) - len(l.lstrip(" "))
        res.append("\t" * (niveau + 2) + "\t" * (n // 4) + l.lstrip(" "))
    res.append("\t" * (niveau + 2) + "```")
    return res


def table_calculee_tmdl(nom, colonnes, tri, expr):
    L = [f"table {nom_tmdl(nom)}", ""]
    for c, dt in colonnes:
        L += [f"\tcolumn {nom_tmdl(c)}", f"\t\tdataType: {dt}", "\t\tsummarizeBy: none", "\t\tisNameInferred",
              f"\t\tsourceColumn: [{c}]"]
        if tri and tri[0] == c:
            L.append(f"\t\tsortByColumn: {tri[1]}")
        L.append("")
    source = " ".join(l.strip() for l in expr.strip().split("\n"))
    L += [f"\tpartition {nom_tmdl(nom)} = calculated", "\t\tmode: import", f"\t\tsource = {source}", ""]
    return "\n".join(L)


def mesures_tmdl():
    L = ["table _Mesures", ""]
    for dossier, nom, fmt, expr in MESURES:
        lignes = expr.strip("\n").split("\n")
        if len(lignes) == 1:
            L.append(f"\tmeasure {nom_tmdl(nom)} = {lignes[0]}")
        else:
            L.append(f"\tmeasure {nom_tmdl(nom)} = ```")
            for l in lignes:
                n = len(l) - len(l.lstrip(" "))
                L.append("\t\t\t" + "\t" * (n // 4) + l.lstrip(" "))
            L.append("\t\t\t```")
        if fmt:
            L.append(f"\t\tformatString: {fmt}")
        L += [f"\t\tdisplayFolder: {dossier}", ""]
    L += ["\tcolumn Value", "\t\tisHidden", "\t\tformatString: 0", "\t\tsummarizeBy: none", "\t\tisNameInferred",
          "\t\tsourceColumn: [Value]", "", "\tpartition _Mesures = calculated", "\t\tmode: import",
          "\t\tsource = {BLANK()}", ""]
    # le nom de table commence par « _ » : apostrophes
    return "\n".join(L).replace("table _Mesures", "table '_Mesures'").replace(
        "partition _Mesures =", "partition '_Mesures' =")


def generer_modele(cols):
    d = DOSSIER / f"{MODELE}.SemanticModel"
    shutil.rmtree(d, ignore_errors=True)
    ecrire(d / ".platform", {"$schema": f"{SCH}/gitIntegration/platformProperties/2.0.0/schema.json",
                             "metadata": {"type": "SemanticModel", "displayName": MODELE},
                             "config": {"version": "2.0", "logicalId": guid("menuscan-modele")}})
    ecrire(d / "definition.pbism", {"$schema": f"{SCH}/item/semanticModel/definitionProperties/1.0.0/schema.json",
                                    "version": "4.2", "settings": {}})
    ecrire(d / "definition" / "database.tmdl",
           f"database {guid('menuscan-base')}\n\tcompatibilityLevel: 1601\n\tcompatibilityMode: powerBI\n")
    refs = "".join(f"ref table {nom_tmdl(t)}\n" for t in TABLES + [n for n, *_ in TABLES_CALCULEES]) + "ref table '_Mesures'\n"
    ecrire(d / "definition" / "model.tmdl",
           "model Model\n\tculture: fr-FR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
           "\tsourceQueryCulture: fr-FR\n\n\tannotation __PBI_TimeIntelligenceEnabled = 0\n\n"
           f"{refs}\nref role {nom_tmdl(ROLE_NOM)}\n")
    ecrire(d / "definition" / "expressions.tmdl",
           f'expression Serveur = "{SERVEUR}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n\n'
           f'expression Base = "{nom_base()}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n')
    cles = {(f, c) for f, c, _, _ in RELATIONS}
    for t in TABLES:
        ecrire(d / "definition" / "tables" / f"{t}.tmdl", table_tmdl(t, cols[t], cles))
    ecrire(d / "definition" / "tables" / "_Mesures.tmdl", mesures_tmdl())
    for nom, colonnes, tri, expr in TABLES_CALCULEES:
        ecrire(d / "definition" / "tables" / f"{nom}.tmdl", table_calculee_tmdl(nom, colonnes, tri, expr))
    ecrire(d / "definition" / "relationships.tmdl", "\n".join(
        f"relationship {f}_{c}\n\tfromColumn: {f}.{c}\n\ttoColumn: {dt}.{k}\n" for f, c, dt, k in RELATIONS))
    ecrire(d / "definition" / "roles" / "Gerant_demo.tmdl", "\n".join(
        [f"role {nom_tmdl(ROLE_NOM)}", "\tmodelPermission: read", ""] +
        [f"\ttablePermission {t} = {f}" for t, f in ROLE_FILTRES]) + "\n")


# ------------------------------------------------------------------ rapports
FOND_PAGE, BANDEAU, BORDURE, GRIS_TEXTE, BLANC = "#F3F6FB", "#1E3A8A", "#E2E8F0", "#64748B", "#FFFFFF"


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def txt(s):
    return lit("'" + s.replace("'", "''") + "'")


def couleur(hexa):
    return {"solid": {"color": txt(hexa)}}


def champ(spec):
    spec = spec.split("|")[0]
    genre, nom = spec.split(":", 1)
    if genre == "M":
        ent, prop, cle = "_Mesures", nom, "Measure"
    else:
        ent, prop = nom.split(".", 1)
        cle = "Column"
    return {cle: {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}}, f"{ent}.{prop}", prop


def mesure_expr(spec):
    return {"expr": champ(spec)[0]}


def projection(spec, actif=False):
    f, ref, natif = champ(spec)
    p = {"field": f, "queryRef": ref, "nativeQueryRef": natif}
    if "|" in spec:
        p["displayName"] = spec.split("|", 1)[1]
    if actif:
        p["active"] = True
    return p


def texte_ou_mesure(t):
    return mesure_expr(t) if t.startswith("M:") else txt(t)


def padding(n):
    return [{"properties": {k: lit(f"{n}D") for k in ("top", "bottom", "left", "right")}}]


def cadre_blanc():
    return {"background": [{"properties": {"show": lit("true"), "color": couleur(BLANC), "transparency": lit("0D")}}],
            "border": [{"properties": {"show": lit("true"), "color": couleur(BORDURE), "radius": lit("8D")}}]}


def sans_cadre():
    return {"background": [{"properties": {"show": lit("false")}}],
            "border": [{"properties": {"show": lit("false")}}]}


class Page:
    def __init__(self, rapport, pid):
        self.rapport, self.pid, self.visuels, self.n = rapport, pid, [], 0

    def ajouter(self, x, y, w, h, visual):
        self.n += 1
        nom = ident(f"{self.rapport}-{self.pid}-{self.n}")
        self.visuels.append((nom, {"$schema": S_VISUEL, "name": nom,
                                   "position": {"x": x, "y": y, "z": 1000 + self.n, "height": h, "width": w,
                                                "tabOrder": 1000 + self.n},
                                   "visual": visual}))


def textbox(page, x, y, w, h, texte, taille=10, coul="#0F172A", gras=False, align="left", vco=None):
    style = {"fontFamily": "Segoe UI Semibold" if gras else "Segoe UI", "fontSize": f"{taille}pt", "color": coul}
    page.ajouter(x, y, w, h, {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": texte, "textStyle": style}], "horizontalTextAlignment": align}]}}]},
        "visualContainerObjects": {**(vco or sans_cadre()), "padding": padding(4)}})


def forme(page, x, y, w, h, fond):
    page.ajouter(x, y, w, h, {"visualType": "shape", "objects": {
        "shape": [{"properties": {"tileShape": txt("rectangle")}}],
        "fill": [{"properties": {"fillColor": couleur(fond), "transparency": lit("0D")}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}]},
        "visualContainerObjects": {**sans_cadre(), "padding": padding(0)}})


def carte(page, x, y, w, h, spec, titre=None, taille=18, coul=BANDEAU, vco=None, pad=10):
    objets = {"value": [{"properties": {"fontSize": lit(f"{taille}D"), "fontColor": couleur(coul)},
                         "selector": {"id": "default"}}],
              "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}]}
    if titre:
        objets["label"] = [{"properties": {"show": lit("true"), "text": txt(titre), "fontSize": lit("10D"),
                                           "fontColor": couleur("#334155")}, "selector": {"id": "default"}}]
    else:
        objets["label"] = [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}]
    page.ajouter(x, y, w, h, {"visualType": "cardVisual",
                              "query": {"queryState": {"Data": {"projections": [projection(spec)]}}},
                              "objects": objets,
                              "visualContainerObjects": {**(vco or cadre_blanc()), "padding": padding(pad)}})


def bandeau(page, titre, droite, pages, actif):
    forme(page, 0, 0, 1280, 52, BANDEAU)
    textbox(page, 16, 10, 32, 32, "M", 14, BANDEAU, True, "center",
            vco={"background": [{"properties": {"show": lit("true"), "color": couleur(BLANC),
                                                "transparency": lit("0D")}}],
                 "border": [{"properties": {"show": lit("true"), "color": couleur(BLANC), "radius": lit("6D")}}]})
    textbox(page, 56, 10, 344, 32, titre, 13, BLANC, True)
    largeur = min(160, (1070 - 404) // len(pages) - 6)
    x0 = 404
    for i, (pid, nom) in enumerate(pages):
        est_actif = pid == actif
        page.ajouter(x0 + i * (largeur + 6), 8, largeur, 36, {
            "visualType": "actionButton",
            "objects": {
                "text": [{"properties": {"show": lit("true")}},
                         {"properties": {"text": txt(nom if largeur >= 150 else nom.split(" · ")[-1]),
                                         "fontSize": lit("10D"),
                                         "fontColor": couleur(BANDEAU if est_actif else BLANC),
                                         "horizontalAlignment": txt("center")}, "selector": {"id": "default"}}],
                "icon": [{"properties": {"show": lit("false")}}],
                "fill": [{"properties": {"show": lit("true" if est_actif else "false")}},
                         {"properties": {"fillColor": couleur(BLANC), "transparency": lit("0D")},
                          "selector": {"id": "default"}}],
                "outline": [{"properties": {"show": lit("false")}}],
                "shape": [{"properties": {"tileShape": txt("rectangleRounded")}},
                          {"properties": {"tileShape": txt("rectangleRounded")}, "selector": {"id": "default"}}]},
            "visualContainerObjects": {**sans_cadre(), "visualLink": [{"properties": {
                "show": lit("true"), "type": txt("PageNavigation"), "navigationSection": txt(pid),
                "tooltip": txt(nom)}}]},
            "drillFilterOtherVisuals": True})
    if droite.startswith("M:"):
        carte(page, 1080, 8, 184, 36, droite, taille=9, coul=BANDEAU, pad=2,
              vco={"background": [{"properties": {"show": lit("true"), "color": couleur(BLANC),
                                                  "transparency": lit("0D")}}],
                   "border": [{"properties": {"show": lit("false")}}]})
    else:
        textbox(page, 1076, 14, 188, 26, droite, 10, BLANC, align="right")


def segment(page, e):
    page.ajouter(e["x"], e["y"], e["w"], e["h"], {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [projection(e["champ"])]}}},
        "objects": {"data": [{"properties": {"mode": txt("Dropdown")}}],
                    "header": [{"properties": {"show": lit("true"), "text": txt(e["titre"])}}]},
        "visualContainerObjects": {"padding": padding(2)}})


def tuile(page, e):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    if e.get("petite"):
        carte(page, x, y, w, h, e["valeur"], titre=e["titre"], taille=12)
        return
    carte(page, x, y, w, h, e["valeur"], titre=e["titre"], taille=15)
    if e["detail"]:
        carte(page, x + 4, y + h - 21, w - 8, 18, e["detail"], taille=8,
              coul=ORANGE_TEXTE if e["alerte"] else GRIS_TEXTE, vco=sans_cadre(), pad=0)


ORANGE_TEXTE = "#C2410C"


def visuel(page, e):
    vtype, roles = e["type"], e["roles"]
    q = {"queryState": {r: {"projections": [projection(s, actif=(r == "Category" and vtype != "scatterChart"))
                                            for s in specs]} for r, specs in roles.items()}}
    if e.get("tri"):
        q["sortDefinition"] = {"sort": [{"field": champ(e["tri"][0])[0], "direction": e["tri"][1]}],
                               "isDefaultSort": False}
    objets = {}
    if vtype not in ("tableEx", "pivotTable"):
        lab = {"show": lit("true" if e.get("etiquettes") else "false")}
        if e.get("etiquettes") and vtype != "scatterChart":
            lab["labelDisplayUnits"] = lit("1D")
        objets["labels"] = [{"properties": lab}]
    if vtype == "scatterChart" and e.get("etiquettes"):
        objets["categoryLabels"] = [{"properties": {"show": lit("true")}}]
    if vtype == "tableEx" and e.get("totaux") is False:
        objets["total"] = [{"properties": {"totals": lit("false")}}]
    if vtype == "pivotTable":
        objets["subTotals"] = [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}]
    if e.get("couleur_categorie"):
        objets["dataPoint"] = [{"properties": {"fill": {"solid": {"color": mesure_expr(e["couleur_categorie"])}}},
                                "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]
    elif e.get("couleurs_series"):
        objets["dataPoint"] = [{"properties": {"fill": couleur(c)}, "selector": {"metadata": champ(s)[1]}}
                               for s, c in e["couleurs_series"].items()]
    elif vtype not in ("tableEx", "pivotTable", "funnel", "waterfallChart"):
        objets["dataPoint"] = [{"properties": {"fill": couleur("#1D4ED8")}}]
    if e.get("fond_cellules"):
        cible, coul = e["fond_cellules"]
        props = {"backColor": {"solid": {"color": mesure_expr(coul)}}}
        if e.get("texte_cellules"):
            props["fontColor"] = {"solid": {"color": mesure_expr(e["texte_cellules"][1])}}
        objets["values"] = [{"properties": props,
                             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                          "metadata": champ(cible)[1]}}]
    vco = {**cadre_blanc(), "padding": padding(10),
           "title": [{"properties": {"show": lit("true"), "text": texte_ou_mesure(e["titre"]),
                                     "fontSize": lit("12D"), "fontColor": couleur("#0F172A")}}]}
    if e.get("sous_titre"):
        vco["subTitle"] = [{"properties": {"show": lit("true"), "text": texte_ou_mesure(e["sous_titre"]),
                                           "fontSize": lit("9D"), "fontColor": couleur(GRIS_TEXTE)}}]
    else:
        vco["subTitle"] = [{"properties": {"show": lit("false")}}]
    vis = {"visualType": vtype, "query": q, "visualContainerObjects": vco}
    if objets:
        vis["objects"] = objets
    page.ajouter(e["x"], e["y"], e["w"], e["h"], vis)


def generer_rapport(nom, titre, droite, pages):
    d = DOSSIER / f"{nom}.Report"
    shutil.rmtree(d, ignore_errors=True)
    ecrire(DOSSIER / f"{nom}.pbip", {"$schema": f"{SCH}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                                     "artifacts": [{"report": {"path": f"{nom}.Report"}}],
                                     "settings": {"enableAutoRecovery": True}})
    ecrire(d / ".platform", {"$schema": f"{SCH}/gitIntegration/platformProperties/2.0.0/schema.json",
                             "metadata": {"type": "Report", "displayName": nom},
                             "config": {"version": "2.0", "logicalId": guid(nom)}})
    ecrire(d / "definition.pbir", {"$schema": f"{SCH}/item/report/definitionProperties/2.0.0/schema.json",
                                   "version": "4.0",
                                   "datasetReference": {"byPath": {"path": f"../{MODELE}.SemanticModel"}}})
    df = d / "definition"
    ecrire(df / "version.json", {"$schema": f"{SCH}/item/report/definition/versionMetadata/1.0.0/schema.json",
                                 "version": "2.0.0"})
    ecrire(df / "report.json", {
        "$schema": f"{SCH}/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "Fluent2-CY26SU10", "type": "SharedResources",
                                          "reportVersionAtImport": {"visual": "2.11.0", "report": "3.4.0",
                                                                    "page": "2.3.1"}}},
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}})
    ids = [(ident(f"{nom}-{t}"), t) for t, _ in pages]
    for (pid, t), (_, elements) in zip(ids, pages):
        page = Page(nom, pid)
        bandeau(page, titre, droite, ids, pid)
        for e in elements:
            {"segment": segment, "tuile": tuile, "visuel": visuel,
             "texte": lambda p, e: textbox(p, e["x"], e["y"], e["w"], e["h"], e["texte"], e.get("taille", 10),
                                           e.get("couleur", "#0F172A"), align=e.get("align", "left"),
                                           vco=cadre_blanc() if e.get("cadre") else None)}[e["k"]](page, e)
        ecrire(df / "pages" / pid / "page.json", {
            "$schema": f"{SCH}/item/report/definition/page/2.1.0/schema.json", "name": pid, "displayName": t,
            "displayOption": "FitToPage", "height": 720, "width": 1280,
            "objects": {"background": [{"properties": {"color": couleur(FOND_PAGE), "transparency": lit("0D")}}],
                        "outspace": [{"properties": {"color": couleur(FOND_PAGE), "transparency": lit("0D")}}]}})
        for vn, contenu in page.visuels:
            ecrire(df / "pages" / pid / "visuals" / vn / "visual.json", contenu)
    ecrire(df / "pages" / "pages.json", {"$schema": f"{SCH}/item/report/definition/pagesMetadata/1.1.0/schema.json",
                                         "pageOrder": [p for p, _ in ids], "activePageName": ids[0][0]})


def verifier_champs(cols):
    """Chaque champ utilisé dans un visuel doit exister dans le modèle."""
    mesures = {m[1] for m in MESURES}
    colonnes = {t: {c for c, _ in cols[t]} for t in TABLES}
    for t, c, *_ in COLONNES_CALCULEES:
        colonnes[t].add(c)
    for t, cs, _, _ in TABLES_CALCULEES:
        colonnes[t] = {c for c, _ in cs}
    specs = []
    for _, droite, pages in RAPPORTS.values():
        specs.append(droite)
        for _, elements in pages:
            for e in elements:
                specs += [e.get(k) for k in ("champ", "valeur", "detail", "titre", "sous_titre", "couleur_categorie")]
                specs += [s for l in e.get("roles", {}).values() for s in l]
                specs += list(e.get("couleurs_series", {}))
                specs += list(e.get("fond_cellules", ())) + list(e.get("texte_cellules", ()))
                specs += [e["tri"][0]] if e.get("tri") else []
    erreurs = []
    for s in specs:
        if not s or not isinstance(s, str) or not (s.startswith("M:") or s.startswith("C:")):
            continue
        genre, nom = s.split("|")[0].split(":", 1)
        if genre == "M" and nom not in mesures:
            erreurs.append(s)
        if genre == "C":
            t, c = nom.split(".", 1)
            if t not in colonnes or c not in colonnes[t]:
                erreurs.append(s)
    if erreurs:
        sys.exit(f"Champs inconnus : {sorted(set(erreurs))}")


def main():
    cols = colonnes_marts()
    verifier_champs(cols)
    generer_modele(cols)
    for nom, (titre, droite, pages) in RAPPORTS.items():
        generer_rapport(nom, titre, droite, pages)
    print(f"{MODELE}.SemanticModel : {len(TABLES)} tables importées, {len(TABLES_CALCULEES)} tables calculées, "
          f"{len(RELATIONS)} relations, {len(MESURES)} mesures, 1 rôle")
    print(f"Rapports : {', '.join(RAPPORTS)} ; {sum(len(p[2]) for p in RAPPORTS.values())} pages")


if __name__ == "__main__":
    main()
