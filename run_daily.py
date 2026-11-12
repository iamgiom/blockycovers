#!/usr/bin/env python3
"""Tâche quotidienne : prend le prochain album de la file, récupère la pochette
sur Discogs, génère le carrousel et la légende, puis note l'album comme traité.

    python3 run_daily.py                     # flux normal (DISCOGS_TOKEN requis)
    python3 run_daily.py --image cover.png   # test hors ligne avec une image locale
"""
import argparse
import csv
import datetime
import json
import os
import sys
import tempfile

import pixel_carousel

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "data", "albums.csv")      # file d'attente (artist,title)
HISTORY = os.path.join(HERE, "data", "history.json")  # albums déjà traités
OUTPUT = os.path.join(HERE, "posts")             # un dossier par date, enregistré dans le dépôt

CAPTION = """Can you name this album from its pixels? 🎵

Swipe for hints: 8, 16, then 32 pixels. The answer is on the last slide.
Tell us which slide you got it on 👇

#blockycovers #pixelart #albumcover #albumart #vinyl #musicquiz #guessthealbum"""


def load_history():
    if os.path.exists(HISTORY):
        with open(HISTORY, encoding="utf-8") as f:
            return json.load(f)
    return []


def next_album(history):
    done = {(h["artist"].lower(), h["title"].lower()) for h in history}
    with open(QUEUE, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["artist"].strip().lower(), row["title"].strip().lower())
            if key not in done:
                return row["artist"].strip(), row["title"].strip()
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", help="image locale : saute Discogs (test hors ligne)")
    a = p.parse_args()

    history = load_history()
    album = next_album(history)
    if album is None:
        print("File d'attente vide : ajoute des albums dans data/albums.csv.")
        return 1
    artist, title = album
    today = datetime.date.today().isoformat()
    outdir = os.path.join(OUTPUT, today)
    os.makedirs(outdir, exist_ok=True)

    if a.image:
        meta = {"title": title, "artist": artist, "year": "", "label": ""}
        cover = a.image
    else:
        import discogs
        meta = discogs.find_album(artist, title)
        cover = discogs.download_image(meta["image_url"],
                                       os.path.join(tempfile.mkdtemp(), "cover_source.jpg"))

    slides = pixel_carousel.build(cover, outdir, meta["title"], meta["artist"],
                                  meta["year"], meta["label"])
    with open(os.path.join(outdir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(CAPTION + "\n")

    history.append({"date": today, "artist": artist, "title": title,
                    "year": meta["year"], "label": meta["label"]})
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    gh_out = os.environ.get("GITHUB_OUTPUT")          # transmet le dossier à l'étape de publication
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"post_dir={os.path.relpath(outdir, HERE)}\n")
    print(f"{today} : {artist} - {title} ({len(slides)} slides) -> {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
