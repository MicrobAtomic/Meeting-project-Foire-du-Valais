# Club des Affaires — Foire du Valais

Web app réservée aux membres du Club des Affaires : album de cartes des membres, QR code pour
« collectionner » les gens rencontrés en vrai, événements avec « tes 3 rencontres » et tables tournantes,
espace staff. Projet de hackathon : rendu le **dimanche 4 octobre 2026 à 13 h**.

## Ta mission

Exécuter `docs/PLAN.md` phase par phase, dans l'ordre. Au début de chaque session : lis `docs/PLAN.md`,
trouve la première case `- [ ]` non cochée, et fais cette tâche.

## Boucle de travail (obligatoire)

1. Lis la tâche en entier, et les fichiers qu'elle cite, avant d'écrire du code.
2. Fais exactement ce qui est demandé. Pas de fonctionnalité bonus, pas de refactor non demandé.
3. Vérifie : `python manage.py test club` doit être vert, puis fais la vérification « ✅ » de la tâche.
4. Coche la case dans `docs/PLAN.md` (`- [x]`).
5. Fin de phase : recompile le CSS (`--minify`), puis `git add -A && git commit -m "<message donné par la phase>"`.
6. Même erreur deux fois de suite : arrête-toi, explique le problème à l'humain et propose deux options.

## Règles intouchables

- **Stack figée** : Django 5.2 LTS, templates Django, Tailwind (CLI standalone), JavaScript vanilla.
  Pas de React, pas d'HTMX, pas de CDN, et aucune nouvelle dépendance Python sans l'accord de l'humain.
- **Code vérifié, à ne pas modifier sans accord** : `club/models.py` (sauf tâche explicite),
  `club/services/*.py`, `club/middleware.py`, `club/decorators.py`, `config/settings.py` et les tests existants.
  Si un test échoue, corrige TON code, jamais l'assertion.
- **Contrôle d'accès**
  - Toute vue membre a `@member_required`, qui fournit `request.member`.
  - Toute vue staff a `@staff_required`.
  - Seules les vues publiques ont `@login_not_required` : vitrine, demande d'invitation, demande de lien magique.
  - Un membre ne modifie que **ses** données. Utilise toujours `request.member`, jamais un id lu dans l'URL.
  - Les coordonnées d'un membre (e-mail, téléphone, LinkedIn) ne s'affichent que si `can_see_contact` est vrai,
    c'est-à-dire pour soi-même ou pour quelqu'un déjà rencontré.
- **Écritures** : toute action qui modifie des données passe par un POST avec `{% csrf_token %}`. Jamais en GET.
- **CSP stricte** : dans les templates, jamais de `<script>` inline, d'attribut `style="…"`, de balise `<style>`
  ni de `onclick=` (et autres `on…=`). Le JavaScript va dans `static/js/*.js`, chargé avec `<script src="…" defer>`.
  Le test `test_csp_header_and_no_inline_code` le vérifie.
  - Une nouvelle page membre sans paramètre s'ajoute à `PAGES_TO_CHECK` dans `club/tests/test_album.py`.
  - Une page avec paramètre (`/evenements/<pk>/`…) se vérifie avec `assert_csp_clean(self, response)`, importé de
    `club/tests/helpers.py`.
- **Tailwind** : écris toujours les classes en entier, dans les templates ou dans `club/ui.py`.
  Jamais de `bg-{{ couleur }}-500` : Tailwind ne verrait pas la classe.
- **Textes** : l'interface est en français (tutoiement, ton détendu). Chaque texte est traduisible dès le début :
  `{% translate %}` ou `{% blocktranslate %}` dans les templates, `gettext` ou `gettext_lazy` en Python.
- **Données** : uniquement des données de démo fictives (e-mails `@example.com`). Jamais de vraies personnes
  ni de vraies entreprises.
- **Git** : `git push` uniquement quand l'humain le demande ou quand une tâche du plan le dit.

## Commandes

```bash
source .venv/bin/activate
python manage.py runserver                       # http://127.0.0.1:8000
python manage.py test club                       # doit rester vert
python manage.py seed_demo --reset               # données de démo (mot de passe local : club-demo-2026)
./tailwindcss -i assets/css/input.css -o static/css/app.css --watch    # pendant le développement
./tailwindcss -i assets/css/input.css -o static/css/app.css --minify   # avant chaque commit
python manage.py makemigrations && python manage.py migrate
```

Comptes de démo : `camille.rey@example.com` (nouvelle membre), `lukas.imboden@example.com` (pilier du Club),
`equipe@example.com` (staff, accès `/admin/` et `/staff/`).

## Où trouver quoi

- `docs/PLAN.md` : les tâches, dans l'ordre.
- `docs/ARCHITECTURE.md` : les choix techniques et leurs raisons. Ils sont arrêtés, ne les remets pas en cause.
- `club/services/` : la logique métier testée (matching, tables tournantes, fédération, vCard, QR, profil, rencontres).
- `club/ui.py` et `club/templatetags/club_ui.py` : couleurs, emojis et libellés des cartes.
