"""Compare la base de démonstration (chargée mois par mois) à l'entrepôt menuscan_dwh (chargé d'un coup).

Pour chaque table des marts et de la qualité : nombre de lignes et empreinte MD5 de tout le contenu (lignes triées).
Deux tables identiques ont la même empreinte. Écrit 06_orchestration/rapport_demo.md ; code 1 au moindre écart.
Le snapshot n'est pas comparé : ses dates sont celles des lancements de dbt, différentes par construction.
"""
import sys
from datetime import datetime

from commun import BASE_DEMO, RACINE, connexion

SCHEMAS = ("marts", "qualite")


def empreintes(base):
    conn = connexion(base)
    res = {}
    with conn.cursor() as cur:
        cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = ANY(%s) "
                    "AND table_type = 'BASE TABLE' ORDER BY 1, 2", (list(SCHEMAS),))
        for schema, table in cur.fetchall():
            cur.execute(f'SELECT count(*), md5(coalesce(string_agg(t::text, \'|\' ORDER BY t::text), \'\')) FROM "{schema}"."{table}" t')
            res[f"{schema}.{table}"] = cur.fetchone()
    conn.close()
    return res


demo, ref = empreintes(BASE_DEMO), empreintes("menuscan_dwh")
lignes, ecarts = [], 0
for nom in sorted(set(demo) | set(ref)):
    d, r = demo.get(nom), ref.get(nom)
    ok = d is not None and r is not None and d == r
    ecarts += not ok
    lignes.append(f"| `{nom}` | {r[0] if r else '–'} | {d[0] if d else '–'} | {'identique' if ok else '**DIFFÉRENT**'} |")
    print(f"  {'OK ' if ok else 'ÉCART'} {nom}")
verdict = "IDENTIQUES" if ecarts == 0 else f"{ecarts} TABLE(S) DIFFÉRENTE(S)"
rapport = RACINE / "06_orchestration" / "rapport_demo.md"
rapport.write_text("\n".join([
    "# Démonstration mensuelle : comparaison avec l'entrepôt chargé d'un coup", "",
    f"**Généré le :** {datetime.now():%d/%m/%Y à %H:%M} par `06_orchestration/demo/comparer_bases.py`.", "",
    f"Base `{BASE_DEMO}` (36 mois livrés un par un) comparée à `menuscan_dwh` (36 mois chargés d'un coup), "
    "table par table : nombre de lignes et empreinte MD5 du contenu complet.", "",
    f"**Résultat : {verdict}** ({len(lignes)} tables comparées).", "",
    "| Table | Lignes (menuscan_dwh) | Lignes (démonstration) | Contenu |", "|---|---:|---:|---|", *lignes, ""]), encoding="utf-8")
print(f"Résultat : {verdict}. Rapport : {rapport.relative_to(RACINE)}")
sys.exit(1 if ecarts else 0)
