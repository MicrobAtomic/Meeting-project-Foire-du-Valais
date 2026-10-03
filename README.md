# Club des Affaires — Foire du Valais

**Plus jamais d'inconnus au Club.** Une web app réservée aux membres, qui vit au rythme des événements :

- **Avant** : l'album de cartes des membres, les affinités, « tes 3 rencontres » pour la prochaine soirée.
- **Pendant** : on scanne le QR code de quelqu'un pour ajouter sa carte et ses coordonnées ; on change de table
  à chaque service.
- **Après** : « ton album 18 / 49 » pour le membre, l'indice de fédération pour le comité.

Projet réalisé pour le hackathon Foire du Valais (3–4 octobre 2026).
Choix techniques : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · Plan de réalisation : [docs/PLAN.md](docs/PLAN.md)

## Lancer le projet en 5 minutes (macOS)

```bash
# 1. Outils (une seule fois)
brew install uv

# 2. Python 3.12 et dépendances
cd ~/Meeting-project-Foire-du-Valais
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 3. Base de données et données de démo (50 membres fictifs)
python manage.py migrate
python manage.py seed_demo --reset

# 4. Démarrer
python manage.py runserver
```

Ouvre ensuite http://127.0.0.1:8000. Le mot de passe de tous les comptes de démo est `club-demo-2026`.

| Compte | Rôle |
|---|---|
| `equipe@example.com` | Équipe événements (staff) : `/admin/` et `/staff/` |
| `camille.rey@example.com` | Nouvelle recrue, 2 cartes dans son album |
| `lukas.imboden@example.com` | Pilier du Club depuis 2017 |

Pour arrêter le serveur : `Ctrl+C`. La fois suivante, il suffit de :
`cd ~/Meeting-project-Foire-du-Valais && source .venv/bin/activate && python manage.py runserver`.

## Ce que tu peux voir

> Les pages membres sont encore **provisoires** (HTML brut) : le design arrive avec les phases 1 à 5 de
> [docs/PLAN.md](docs/PLAN.md). Le back-office, les données, le QR code et la sécurité sont déjà fonctionnels.

1. **Back-office** : http://127.0.0.1:8000/admin/ avec `equipe@example.com`.
   - **Membres** : les 50 cartes, les filtres par secteur et par langue, les affinités de chacun.
   - **Événements** : coche « Dîner d'automne », choisis l'action **« Générer le plan de tables »** puis **Envoyer**.
     Le résultat s'affiche (environ 248 nouvelles paires, 1 répétition), et le détail est dans **Seating plans**.
   - **Matchs** : filtre sur « Dîner d'automne ». Camille ↔ Lukas a un score de 16 (Petite Arvine, ski de rando,
     trail et réunions du lundi en commun).
2. **Le parcours QR, avec deux fenêtres** :
   1. Fenêtre privée : connecte-toi avec `lukas.imboden@example.com` sur http://127.0.0.1:8000/connexion/, puis ouvre
      http://127.0.0.1:8000/moi/qr/. Tu vois son QR code et le lien qu'il contient.
   2. Fenêtre normale : connecte-toi avec `camille.rey@example.com`. L'accueil affiche « Ton album : 2 / 49 ».
   3. Dans la fenêtre de Camille, colle le lien du QR de Lukas, puis **« Ajouter Lukas à mon album »**.
   4. Ses coordonnées apparaissent, avec « Ajouter à mes contacts », qui télécharge la vCard.
      L'accueil de Camille passe à 3 / 49.
3. **Staff** : http://127.0.0.1:8000/staff/ (indice de fédération, provisoire).

**Bonus : scanner avec ton vrai téléphone.** Laisse `runserver` tourner et, dans un 2ᵉ terminal :

```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:8000
```

Ouvre l'URL `https://….trycloudflare.com` affichée. Le QR de Lukas, affiché via cette URL, se scanne avec l'appareil
photo du téléphone, connecté en Camille.

## Tests

```bash
python manage.py test club    # 31 tests : algorithmes, contrôle d'accès, QR, vCard, CSP, admin…
```

## Traductions (FR · DE · EN)

L'interface suit la langue du navigateur (ou le choix FR / DE / EN en haut de page, mémorisé). Les catalogues sont dans
`locale/<langue>/LC_MESSAGES/django.po`, les fichiers compilés `.mo` sont commités (l'hébergeur n'a pas gettext).
Après avoir ajouté ou modifié un texte (`{% translate %}` dans un template, `gettext` en Python) :

```bash
export PATH="$(brew --prefix gettext)/bin:$PATH"
python manage.py makemessages -l fr -l de -l en --no-wrap --no-location --ignore=.venv --ignore=staticfiles --ignore="club/tests/*"
# traduire les msgstr vides de locale/de/... et locale/en/... (allemand suisse : « ss », tutoiement), copier la source dans locale/fr/...
python manage.py compilemessages --ignore=.venv
python manage.py test club.tests.test_i18n     # aucun texte non traduit, aucune phrase française sur les pages DE/EN
```

## Structure

```
config/            réglages Django (sécurité, i18n, base de données par variable d'environnement)
club/models.py     membres, affinités, événements, inscriptions, rencontres, plans de tables
club/services/     logique métier testée : matching, tables tournantes, fédération, vCard, QR
club/views/        public · member · staff (events à venir)
club/admin.py      back-office de l'équipe événements
templates/         pages (provisoires pour l'instant)
static/ assets/    JS (swipe) et CSS (Tailwind)
docs/              PLAN.md (tâches) · ARCHITECTURE.md (choix techniques)
```

## Démo en ligne

À venir (phase 2 du plan : Render).
