"""Configuration commune des tests : le module menuscan_analytics est dans 00_commun.

Lancement (depuis 08_analyse_ml) : python -m pytest -q tests
Les tests n'utilisent pas la base : ils travaillent sur de petites données fabriquées.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_commun"))
