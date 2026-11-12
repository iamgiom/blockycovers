#!/usr/bin/env python3
"""Publie un carrousel sur Instagram via l'API officielle (Instagram Login).

    python3 instagram.py posts/2026-11-12             # publie
    python3 instagram.py posts/2026-11-12 --dry-run   # affiche les URL, ne publie rien

Variables d'environnement :
    INSTAGRAM_TOKEN   jeton d'accès du compte (secret)
    MEDIA_BASE_URL    adresse publique du dépôt, ex.
                      https://raw.githubusercontent.com/iamgiom/blockycovers/main

Meta télécharge chaque image depuis son URL : elles doivent être en JPEG et
accessibles publiquement au moment de la publication.
Doc : https://developers.facebook.com/docs/instagram-platform/content-publishing/
"""
import argparse
import glob
import os
import sys
import time

import requests

API = "https://graph.instagram.com"
HERE = os.path.dirname(os.path.abspath(__file__))


class InstagramError(RuntimeError):
    pass


def _call(method, path, token, **params):
    params["access_token"] = token
    r = requests.request(method, f"{API}/{path}", params=params, timeout=60)
    try:
        data = r.json()
    except ValueError:
        raise InstagramError(f"Réponse illisible d'Instagram ({r.status_code}).")
    if r.status_code != 200 or "error" in data:
        err = data.get("error", {})
        raise InstagramError(
            f"Instagram a refusé {method} /{path.split('/')[-1]} : "
            f"{err.get('message', r.status_code)} (code {err.get('code')})")
    return data


def wait_public(urls, timeout=180):
    """Attend que les images soient en ligne (délai de propagation après le push)."""
    deadline = time.time() + timeout
    pending = list(urls)
    while pending:
        pending = [u for u in pending if requests.head(u, timeout=30).status_code != 200]
        if not pending:
            return
        if time.time() > deadline:
            raise InstagramError(
                "Images inaccessibles publiquement (le dépôt est-il bien public ?) : "
                + pending[0])
        time.sleep(10)


def wait_ready(container_id, token, timeout=120):
    deadline = time.time() + timeout
    while True:
        status = _call("GET", container_id, token, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED") or time.time() > deadline:
            raise InstagramError(f"Préparation du média échouée (statut {status}).")
        time.sleep(5)


def publish_carousel(urls, caption, token):
    """Crée les médias, le carrousel, puis publie. Retourne l'identifiant du post."""
    me = _call("GET", "me", token, fields="user_id,username")
    user = me["user_id"]
    children = []
    for url in urls:
        c = _call("POST", f"{user}/media", token, image_url=url, is_carousel_item="true")
        children.append(c["id"])
    for c in children:
        wait_ready(c, token)
    carousel = _call("POST", f"{user}/media", token, media_type="CAROUSEL",
                     children=",".join(children), caption=caption)
    wait_ready(carousel["id"], token)
    post = _call("POST", f"{user}/media_publish", token, creation_id=carousel["id"])
    return me.get("username", ""), post["id"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("post_dir", help="dossier du post, ex. posts/2026-11-12")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    post_dir = os.path.abspath(a.post_dir)
    slides = sorted(glob.glob(os.path.join(post_dir, "slide_*.jpg")))
    if len(slides) < 2:
        print(f"Aucun carrousel dans {a.post_dir}.")
        return 1
    with open(os.path.join(post_dir, "caption.txt"), encoding="utf-8") as f:
        caption = f.read().strip()

    base = os.environ.get("MEDIA_BASE_URL", "").rstrip("/")
    if not base:
        print("Variable MEDIA_BASE_URL absente.")
        return 1
    urls = [f"{base}/{os.path.relpath(s, HERE).replace(os.sep, '/')}" for s in slides]

    if a.dry_run:
        print("\n".join(urls))
        print("---\n" + caption)
        return 0

    token = os.environ.get("INSTAGRAM_TOKEN")
    if not token:
        print("Variable INSTAGRAM_TOKEN absente.")
        return 1
    try:
        wait_public(urls)
        username, post_id = publish_carousel(urls, caption, token)
    except InstagramError as e:
        print(f"ÉCHEC : {e}")
        return 1
    print(f"Publié sur @{username} (post {post_id}, {len(urls)} slides).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
