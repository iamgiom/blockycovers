#!/usr/bin/env python3
"""Blocky Covers — générateur de carrousel Instagram.

Usage en ligne de commande (test sur une image locale) :
    python3 pixel_carousel.py IMAGE DOSSIER_SORTIE "Title" "Artist" YEAR [--credit LABEL] [--levels 8,16,32]

Produit N slides pixelisées (de la plus dure à la plus facile) + 1 slide réponse
(original + crédits), au format 1080x1350 (4:5), plus une planche d'aperçu.
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

# --- Design (à remplacer quand la maquette Figma sera prête) -----------------
W, H = 1080, 1350
ART = 960                       # côté de l'œuvre
ART_X, ART_Y = (W - ART) // 2, 170
BG = (13, 13, 16)
FG = (240, 240, 235)
MUTED = (120, 120, 128)
ACCENT = (255, 214, 10)
DEFAULT_LEVELS = (8, 16, 32)

# --- Wording (anglais) -------------------------------------------------------
TXT_HEADER = "BLOCKY COVERS"
TXT_PIXELS = "{n} x {n} PIXELS"
TXT_HINT = "SWIPE FOR A HINT >"
TXT_TO_ANSWER = "SWIPE FOR THE ANSWER >"
TXT_ANSWER = "ANSWER"
TXT_CREDIT = "COVER (C) {credit}"
TXT_CTA = "WHICH SLIDE DID YOU GET IT ON?"

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "fonts", "PressStart2P.woff")
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.truetype(FALLBACK, size)


def square(im):
    """Recadre au centre en carré."""
    w, h = im.size
    s = min(w, h)
    l, t = (w - s) // 2, (h - s) // 2
    return im.crop((l, t, l + s, t + s))


def pixelate(im, n):
    """Vrai filtre pixel : moyenne par bloc (n x n), puis agrandissement net."""
    return im.resize((n, n), Image.BOX).resize((ART, ART), Image.NEAREST)


def fit_text(draw, text, max_w, start, minimum=14):
    size = start
    while size > minimum:
        f = font(size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(minimum)


def centered(draw, y, text, f, fill):
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, y), text, font=f, fill=fill)


def base(art):
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    centered(d, 70, TXT_HEADER, font(30), FG)
    canvas.paste(art, (ART_X, ART_Y))
    return canvas, d


def level_slide(im, n, idx, total):
    canvas, d = base(pixelate(im, n))
    y = ART_Y + ART + 50
    box, gap = 34, 14           # jauge : carrés pleins = indices déjà donnés
    x0 = (W - (total * box + (total - 1) * gap)) // 2
    for i in range(total):
        x = x0 + i * (box + gap)
        if i <= idx:
            d.rectangle([x, y, x + box, y + box], fill=ACCENT)
        else:
            d.rectangle([x, y, x + box, y + box], outline=MUTED, width=4)
    centered(d, y + 62, TXT_PIXELS.format(n=n), font(26), FG)
    centered(d, y + 112, TXT_HINT if idx < total - 1 else TXT_TO_ANSWER, font(18), MUTED)
    return canvas


def answer_slide(im, title, artist, year, credit=""):
    canvas, d = base(im.resize((ART, ART), Image.LANCZOS))
    y = ART_Y + ART + 36
    centered(d, y, TXT_ANSWER, font(20), ACCENT)
    centered(d, y + 44, title.upper(), fit_text(d, title.upper(), W - 100, 34), FG)
    sub = f"{artist.upper()} - {year}" if year else artist.upper()
    centered(d, y + 100, sub, fit_text(d, sub, W - 100, 22), MUTED)
    last = TXT_CREDIT.format(credit=credit.upper()) if credit else TXT_CTA
    centered(d, y + 146, last, fit_text(d, last, W - 100, 16, 10), MUTED)
    return canvas


def contact_sheet(slides):
    tw, pad = 432, 16
    th = int(tw * H / W)
    sheet = Image.new("RGB", (len(slides) * (tw + pad) + pad, th + 2 * pad), (40, 40, 44))
    for i, s in enumerate(slides):
        sheet.paste(s.resize((tw, th), Image.LANCZOS), (pad + i * (tw + pad), pad))
    return sheet


def build(image_path, outdir, title, artist, year, credit="", levels=DEFAULT_LEVELS):
    """Génère le carrousel complet dans outdir. Retourne la liste des fichiers."""
    im = square(Image.open(image_path).convert("RGB"))
    os.makedirs(outdir, exist_ok=True)
    slides = [level_slide(im, n, i, len(levels)) for i, n in enumerate(levels)]
    slides.append(answer_slide(im, title, artist, year, credit))
    paths = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(outdir, f"slide_{i}.png")
        s.save(p)
        paths.append(p)
    contact_sheet(slides).save(os.path.join(outdir, "preview.png"))
    return paths


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("outdir")
    p.add_argument("title")
    p.add_argument("artist")
    p.add_argument("year")
    p.add_argument("--credit", default="")
    p.add_argument("--levels", default="8,16,32")
    a = p.parse_args()
    out = build(a.image, a.outdir, a.title, a.artist, a.year, a.credit,
                [int(x) for x in a.levels.split(",")])
    print(f"{a.outdir}: {len(out)} slides")
