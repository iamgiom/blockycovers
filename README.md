# Blocky Covers

Génère chaque jour un carrousel Instagram : une pochette d'album pixelisée en
3 paliers (8, 16, 32 pixels), puis la réponse avec l'original et les crédits.

## Comment ça marche

1. `data/albums.csv` est la file d'attente : une ligne par album (`artist,title`).
2. Chaque jour, GitHub lance `run_daily.py`, qui prend le premier album pas encore traité.
3. `discogs.py` cherche l'album sur Discogs, récupère l'année, le label et la pochette.
4. `pixel_carousel.py` fabrique les 4 slides en 1080×1350 et une planche d'aperçu.
5. Les slides sont enregistrées dans `posts/AAAA-MM-JJ/`, consultables directement sur GitHub,
   et l'album est noté dans `data/history.json` pour ne jamais ressortir.
6. `instagram.py` publie le carrousel sur Instagram (si la case « Publier sur Instagram »
   est cochée au lancement manuel, ou systématiquement en mode planifié).

La planification quotidienne est en pause : voir le haut de `.github/workflows/daily.yml`.

## Secrets nécessaires

Dans Settings > Secrets and variables > Actions :

- `DISCOGS_TOKEN` : jeton personnel Discogs.
- `INSTAGRAM_TOKEN` : jeton d'accès du compte Instagram, généré dans l'application Meta.

Le dépôt doit être public pour que Meta puisse télécharger les slides.

## Mise en place (une seule fois)

1. **Créer le dépôt** : sur github.com, bouton **New**, nom `blockycovers`,
   visibilité **Private**, sans README. Clique **Create repository**.
2. **Envoyer les fichiers** : sur la page du dépôt vide, clique **uploading an existing file**,
   glisse tout le contenu de ce dossier, puis **Commit changes**.
   Attention : le dossier `.github` est masqué par défaut sur Mac (Cmd + Maj + .
   pour l'afficher) et sous Windows (Affichage > Éléments masqués).
3. **Créer le jeton Discogs** : sur discogs.com, Settings > Developers >
   **Generate new token**. Copie-le.
4. **Enregistrer le jeton dans GitHub** : dans le dépôt, Settings > Secrets and variables >
   Actions > **New repository secret**. Nom : `DISCOGS_TOKEN`. Valeur : le jeton. Enregistre.
5. **Premier lancement** : onglet **Actions** > **Daily carousel** > **Run workflow**.
   Au bout d'une minute environ, ouvre l'exécution et télécharge `carousel-...` en bas de page.

Ensuite, le flux tourne seul tous les jours vers 17h23 (heure de Paris en hiver).

## Au quotidien

- **Ajouter des albums** : modifie `data/albums.csv` directement sur GitHub (icône crayon).
- **Changer l'heure** : ligne `cron` dans `.github/workflows/daily.yml` (heure en UTC).
- **Changer le wording** : constantes `TXT_...` en haut de `pixel_carousel.py`,
  et la légende `CAPTION` dans `run_daily.py`.
- **Changer le design** : constantes de couleurs et de positions en haut de `pixel_carousel.py`.

## Tester sur son ordinateur

```bash
pip install -r requirements.txt
python3 run_daily.py --image ma_pochette.png   # sans Discogs
```
