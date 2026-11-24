# -*- coding: utf-8 -*-
"""Thème visuel commun (maquettes validées le 24/11/2026) : polices, couleurs, cartes, barre de panier."""
import html

import streamlit as st

MARINE, BLEU, CLAIR, FOND, BORD = "#1E3A8A", "#1D4ED8", "#DBE7FF", "#F3F6FC", "#E2E8F5"
TEXTE, GRIS, ORANGE = "#0F172A", "#475569", "#F59E0B"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap');
.stApp *:not([data-testid="stIconMaterial"]) {{ font-family: Inter, system-ui, sans-serif; }}
.block-container {{ padding-top: 2.2rem; }}
[class*="st-key-carte"] [data-testid="stHorizontalBlock"], .st-key-barre [data-testid="stHorizontalBlock"], .st-key-entete [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 8px; }}
[class*="st-key-carte"] [data-testid="stColumn"], .st-key-barre [data-testid="stColumn"], .st-key-entete [data-testid="stColumn"] {{ min-width: 0 !important; }}
[class*="st-key-carte"] .stButton button {{ min-height: 38px; padding: 0 6px; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: "Material Symbols Rounded" !important; }}
h1, h2, h3, .titre, .stApp .titre {{ font-family: 'Plus Jakarta Sans', Inter, sans-serif !important; font-weight: 800 !important; color: {TEXTE}; letter-spacing: -0.01em; }}
.stApp {{ background: {FOND}; }}
[data-testid="stSidebar"] {{ background: {MARINE}; }}
[data-testid="stSidebar"] * {{ color: #FFFFFF; }}
[data-testid="stSidebar"] .stButton button {{ background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.3); }}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {{ background: rgba(255,255,255,0.16); }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] input, [data-testid="stSidebar"] [data-testid="stSelectbox"] button, [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] {{ color: {TEXTE} !important; -webkit-text-fill-color: {TEXTE}; background: #FFFFFF; }}
.st-key-entete .stButton button {{ background: transparent !important; border: 1px solid rgba(255,255,255,.45) !important; border-radius: 999px; min-height: 40px; }}
[data-testid="stButtonGroup"] button[data-selected="true"] {{ background: {BLEU} !important; border-color: {BLEU} !important; }}
[data-testid="stButtonGroup"] button[data-selected="true"] p {{ color: #FFFFFF !important; }}
.stButton button, .stFormSubmitButton > button {{ border-radius: 12px; min-height: 42px; font-weight: 600; }}
.stButton button[kind="primary"] {{ background: {BLEU}; border-color: {BLEU}; }}
.stTextInput input, .stTextArea textarea {{ border-radius: 14px; }}
[class*="st-key-carte"] {{ background: #FFFFFF; border-radius: 18px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(15,23,42,0.08); }}
[class*="st-key-colonne"] {{ background: #E8EEFA; border-radius: 22px; padding: 14px; min-height: 260px; }}
.st-key-entete {{ background: {MARINE}; border-radius: 0 0 24px 24px; padding: 18px 18px 22px; }}
.st-key-entete * {{ color: #FFFFFF; }}
.st-key-barre {{ position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%); width: min(680px, calc(100% - 28px)); z-index: 999; background: #FFFFFF; border-radius: 20px; padding: 8px; box-shadow: 0 10px 30px rgba(15,23,42,0.18); }}
.st-key-barre .stButton button[kind="primary"] {{ background: {MARINE}; border-color: {MARINE}; min-height: 52px; font-size: 16px; }}
.espace-bas {{ height: 96px; }}
.badge {{ display: inline-block; font-size: 11px; font-weight: 700; border-radius: 999px; padding: 2px 8px; margin-left: 6px; vertical-align: middle; }}
.kpi {{ background: #FFFFFF; border-radius: 20px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(15,23,42,0.06); height: 100%; }}
.kpi .l {{ font-size: 14px; color: {GRIS}; }}
.kpi .v {{ font-family: 'Plus Jakarta Sans', sans-serif; font-size: 28px; font-weight: 800; color: {MARINE}; line-height: 1.2; }}
.kpi .s {{ font-size: 13px; font-weight: 500; color: {GRIS}; }}
.grille {{ display: grid; gap: 14px; }}
</style>
"""


def appliquer():
    st.markdown(CSS, unsafe_allow_html=True)


def e(x):
    """Échappe un texte venant de la base avant de l'insérer dans du HTML."""
    return html.escape(str(x))


def prix(x):
    return f"{float(x):.3f} DT".replace(".", ",")


def kpis(items, min_px=190):
    """items : liste de (libellé, valeur, sous-titre, couleur du sous-titre ou None)."""
    cartes = "".join(
        f'<div class="kpi"><div class="l">{e(l)}</div><div class="v">{e(v)}</div>'
        f'<div class="s" style="color:{c or GRIS}">{e(s)}</div></div>' for l, v, s, c in items)
    st.markdown(f'<div class="grille" style="grid-template-columns: repeat(auto-fit, minmax({min_px}px, 1fr))">{cartes}</div>',
                unsafe_allow_html=True)


ICONES = {
    "tasse": "M17 8h1a4 4 0 0 1 0 8h-1M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4ZM7 2v2M11 2v2",
    "verre": "M5 3h14l-2 18H7ZM6 9h12",
    "viennoiserie": "M4 16c0-5 4-9 8-9s8 4 8 9ZM8 12l1 4M12 11v5M16 12l-1 4",
    "assiette": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
}
TEINTES = ["#DBE7FF", "#DCF3EC", "#FFEDD5", "#FEF3C7", "#E7F0DC", "#F3E8FF", "#EDE9FE", "#FCE7F3"]


def icone_categorie(nom_categorie, rang):
    n = nom_categorie.lower()
    if any(m in n for m in ("chaud", "café", "thé", "infusion")):
        cle = "tasse"
    elif any(m in n for m in ("boisson", "jus", "fraîch", "soda", "smoothie")):
        cle = "verre"
    elif any(m in n for m in ("viennois", "crêpe", "gaufre", "pâtiss", "dessert", "gâteau")):
        cle = "viennoiserie"
    else:
        cle = "assiette"
    fond = TEINTES[rang % len(TEINTES)]
    return (f'<div style="width:52px;height:52px;flex:none;border-radius:14px;background:{fond};display:flex;align-items:center;justify-content:center">'
            f'<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{MARINE}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="{ICONES[cle]}"/></svg></div>')
