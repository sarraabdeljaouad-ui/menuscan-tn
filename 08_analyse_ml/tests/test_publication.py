import re

from menuscan_analytics import publication


def test_toutes_les_tables_publiees_existent_dans_le_script():
    ddl = publication.SCRIPT_DDL.read_text(encoding="utf-8")
    tables = set(re.findall(r"create table if not exists ml\.(\w+)", ddl))
    assert set(publication.ORDRE) | {"journal_publication"} == tables


def test_controle_journal_compte_toutes_les_tables():
    """P8 attend autant de lignes de journal que de tables publiées."""
    p8 = dict((c, sql) for c, _, sql in publication.CONTROLES)["P8"]
    assert p8.startswith(f"select {len(publication.ORDRE)} - count(*)")
