"""Accès à l'API Discogs : recherche d'un album, métadonnées et pochette.

Le jeton est lu dans la variable d'environnement DISCOGS_TOKEN (jamais dans le code).
Doc : https://www.discogs.com/developers
"""
import os
import time

import requests

API = "https://api.discogs.com"
USER_AGENT = "BlockyCovers/1.0"


class DiscogsError(RuntimeError):
    pass


def _headers():
    token = os.environ.get("DISCOGS_TOKEN")
    if not token:
        raise DiscogsError("Variable d'environnement DISCOGS_TOKEN absente.")
    return {"User-Agent": USER_AGENT, "Authorization": f"Discogs token={token}"}


def _get(url, **params):
    for attempt in range(3):
        r = requests.get(url, headers=_headers(), params=params or None, timeout=30)
        if r.status_code == 429:            # limite de débit : on attend et on réessaie
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise DiscogsError(f"Discogs a répondu {r.status_code} pour {url}")
        return r
    raise DiscogsError("Limite de débit Discogs atteinte après 3 essais.")


def find_album(artist, title):
    """Retourne {title, artist, year, label, image_url} pour un album."""
    results = []
    for kind in ("master", "release"):      # la fiche « master » d'abord, sinon une édition
        data = _get(f"{API}/database/search", artist=artist, release_title=title,
                    type=kind, per_page=5).json()
        results = data.get("results", [])
        if results:
            break
    if not results:
        raise DiscogsError(f"Aucun résultat Discogs pour « {artist} - {title} ».")
    hit = results[0]

    detail = _get(hit["resource_url"]).json()
    images = detail.get("images") or []
    primary = [i for i in images if i.get("type") == "primary"] or images
    image_url = primary[0]["uri"] if primary else hit.get("cover_image")
    if not image_url:
        raise DiscogsError(f"Pas de pochette pour « {artist} - {title} ».")

    labels = hit.get("label") or []
    return {
        "title": detail.get("title") or title,
        "artist": artist,
        "year": str(detail.get("year") or hit.get("year") or ""),
        "label": labels[0] if labels else "",
        "image_url": image_url,
    }


def download_image(url, dest):
    """Télécharge la pochette (requête authentifiée, URL signée à ne pas modifier)."""
    r = _get(url)
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest
