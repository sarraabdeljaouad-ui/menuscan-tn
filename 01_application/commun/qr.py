# -*- coding: utf-8 -*-
"""QR codes des tables : image PNG d'une table et planche PDF imprimable (6 cartes par page A4).

Le QR code encode l'adresse de l'application client : CLIENT_URL/?table=TBL00001.
"""
import io

import qrcode
from PIL import Image, ImageDraw, ImageFont

MARINE, BLEU, CLAIR, GRIS = "#1E3A8A", "#1D4ED8", "#DBE7FF", "#475569"
ZONES = {"terrasse": "Terrasse", "salle": "Salle", "etage": "Étage"}


def url_table(url_client, table_id):
    return f"{url_client.rstrip('/')}/?table={table_id}"


def image_qr(url, taille=600):
    """QR code seul, correction d'erreur moyenne (lisible même un peu abîmé), sur fond blanc."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    q.add_data(url)
    q.make(fit=True)
    img = q.make_image(fill_color=MARINE, back_color="white").convert("RGB")
    return img.resize((taille, taille), Image.NEAREST)


def png(url, taille=600):
    b = io.BytesIO()
    image_qr(url, taille).save(b, format="PNG")
    return b.getvalue()


def _police(taille, gras=False):
    """Police TrueType du système si elle existe (Windows : Arial ; Linux : DejaVu), sinon la police intégrée de Pillow."""
    for nom in (("arialbd.ttf", "DejaVuSans-Bold.ttf") if gras else ("arial.ttf", "DejaVuSans.ttf")):
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    return ImageFont.load_default(size=taille)


def _centre(d, y, texte, police, couleur, largeur):
    l = d.textbbox((0, 0), texte, font=police)[2]
    d.text(((largeur - l) / 2, y), texte, font=police, fill=couleur)


def carte(nom_etablissement, numero_table, zone, url, l=1100, h=1150):
    """Carte d'une table : nom du café, « Scannez pour commander », QR code, numéro et zone de la table."""
    img = Image.new("RGB", (l, h), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((6, 6, l - 6, h - 6), radius=48, outline=CLAIR, width=8)
    d.rounded_rectangle((6, 6, l - 6, 190), radius=48, fill=MARINE)
    d.rectangle((6, 140, l - 6, 190), fill=MARINE)
    _centre(d, 52, nom_etablissement, _police(64, True), "white", l)
    _centre(d, 225, "SCANNEZ POUR COMMANDER", _police(40, True), BLEU, l)
    img.paste(image_qr(url, 620), ((l - 620) // 2, 300))
    _centre(d, 945, f"Table {numero_table}", _police(84, True), MARINE, l)
    _centre(d, 1050, f"{ZONES.get(zone, zone)} · menu, commande et appel du serveur", _police(34), GRIS, l)
    return img


def planche_pdf(nom_etablissement, tables, url_client):
    """tables : liste de dict (table_id, numero_table, zone). Renvoie un PDF A4, 2 × 3 cartes par page, à 150 points par pouce."""
    a4 = (1240, 1754)  # A4 à 150 ppp
    marge, ecart = 50, 24
    ch = (a4[1] - 2 * marge - 2 * ecart) // 3  # 3 rangées dans la hauteur
    cl = ch * 1100 // 1150                    # proportions de la carte
    x0 = (a4[0] - 2 * cl - ecart) // 2        # 2 colonnes centrées
    pages = []
    for i in range(0, len(tables), 6):
        page = Image.new("RGB", a4, "white")
        for j, t in enumerate(tables[i:i + 6]):
            c = carte(nom_etablissement, t["numero_table"], t["zone"], url_table(url_client, t["table_id"])).resize((cl, ch), Image.LANCZOS)
            x = x0 + (j % 2) * (cl + ecart)
            y = marge + (j // 2) * (ch + ecart)
            page.paste(c, (x, y))
        pages.append(page)
    b = io.BytesIO()
    pages[0].save(b, format="PDF", save_all=True, append_images=pages[1:], resolution=150)
    return b.getvalue()
