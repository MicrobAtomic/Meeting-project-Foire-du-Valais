# Fabriquer le deck

Le deck est fait de **captures réelles de l'application** (données fictives), une par diapositive, avec une avance
manuelle : un clic, un écran. Le texte anglais de chaque chapitre vient de `template.html`, le texte français de chaque
écran (notes de l'orateur) de `story.json`.

| Fichier | Rôle |
|---|---|
| `Club-des-Affaires-pitch.pptx` | Le PowerPoint : une image par diapositive, les notes en français |
| `Club-des-Affaires-pitch.pdf` | Les mêmes pages, en secours |
| `deck.html` + `presenter.js` | La version navigateur : ← / → ou Espace pour avancer, **F** plein écran, **N** notes, **A** annexes |
| `demo.mp4` | Une vidéo autonome de la démo (environ 77 s), en alternative |
| `template.html`, `story.json` | Les sources : chapitres en anglais, notes en français |
| `screens/` | Les captures de l'application |

## Reconstruire

Prérequis : Google Chrome, Node.js (`npm install` dans ce dossier), `uv`, et le `.venv` du projet. Les captures se font
sur une base jetable (`.build/screens.sqlite3`) et un serveur sur le port 8010, jamais sur `db.sqlite3`.

```bash
# depuis la racine du dépôt : nouvelles captures, puis deck, PDF et PowerPoint
.venv/bin/python docs/pitch/make_screens.py
# ou sans refaire les captures
.venv/bin/python docs/pitch/make_screens.py --reuse-captures

cd docs/pitch
node verify_browser.mjs
uv run --no-project --with python-pptx python verify_pitch.py
```

Pour **garder des notes déjà retouchées dans PowerPoint** et ne remplacer que les images, ferme PowerPoint, puis :

```bash
cd docs/pitch
node build_deck.mjs --tests 403
uv run --no-project --with python-pptx python build_pptx.py --refresh-images
```

L'original est sauvegardé dans `.build/pitch-before-image-refresh.pptx`. La chaîne de la vidéo autonome est dans
[`video/`](video/) (`make_pitch.sh`).
