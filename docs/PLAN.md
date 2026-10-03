# Plan de réalisation — Club des Affaires

> **Pour qui** : l'agent IA qui code, et l'humain qui le supervise.
> **Avant tout** : lis `CLAUDE.md` (règles intouchables) puis ce fichier en entier.
> **Méthode** : prends la première case `- [ ]` non cochée, fais-la, vérifie le « ✅ », coche-la, continue.
> Les étapes marquées 👤 sont faites par l'humain. Prépare-lui les commandes et attends sa confirmation.

## 1. Ce qui est déjà fait (socle vérifié, ne pas refaire)

Le socle a été écrit et vérifié avant toi, et **31 tests passent** (`python manage.py test club`) :

- **Modèles** et migration : `Member`, `Tag`, `MemberTag`, `Event`, `RSVP`, `Connection`, `Match`, `SeatingPlan`,
  `SeatAssignment`, `InvitationRequest` (`club/models.py`).
- **Services testés** (`club/services/`) :

  | Fichier | Contenu |
  |---|---|
  | `matching.py` | « Tes 3 rencontres » |
  | `seating.py` | tables tournantes |
  | `federation.py` | indice de fédération, membres isolés, `collected_ids` |
  | `vcard.py` | carte de contact |
  | `qr.py` | QR code en SVG |
  | `events.py` | `generate_matches`, `generate_seating`, `attendees` |
  | `profile.py` | `save_tag_answers`, `common_tags` |
  | `intros.py` | `intros_for`, `seats_for` |

- **Sécurité** : tout est fermé par défaut (`LoginRequiredMiddleware`). Décorateurs `@member_required` et
  `@staff_required`, CSP stricte, réglages de production. Connexion par e-mail (insensible à la casse),
  lien magique à usage unique, déconnexion en POST.
- **Vues déjà écrites** :

  | Vue | Rôle |
  |---|---|
  | `public.landing` | vitrine |
  | `member.home` | accueil membre |
  | `member.my_qr` | mon QR code |
  | `member.member_detail` | carte d'un membre |
  | `member.member_vcard` | vCard |
  | `member.scan` | cible du QR : GET = confirmation, POST = connexion |
  | `staff.dashboard` | tableau de bord staff |

- **Admin Django complet** (`club/admin.py`) avec les actions « Générer les rencontres » et « Générer le plan de tables ».
- **Données de démo** : `python manage.py seed_demo --reset` crée 50 membres fictifs, 30 affinités en FR/DE/EN,
  5 événements, 180 rencontres (indice 15 %) et 56 « rencontres » proposées.
- **Fichiers pour la suite** :
  - `static/js/swipe.js`, déjà écrit, à brancher en phase 6 ;
  - `assets/css/input.css`, avec les composants `.btn`, `.btn-primary`, `.btn-secondary`, `.card`, `.chip`, `.input` ;
  - `club/ui.py` et les filtres `club_ui` : couleurs, emojis et rangs des cartes ;
  - `build.sh` et `render.yaml` pour la mise en ligne.

**Ce qu'il reste à faire, c'est surtout l'interface** : les templates actuels sont des pages provisoires, marquées
`PLACEHOLDER`, juste assez pour les tests. Tu vas les remplacer par la vraie UI, puis ajouter les pages manquantes.

## 2. Le produit en 30 secondes

Le problème du club : 80 % de présence aux événements, mais les membres ne se connaissent pas et restent entre eux
en petits groupes. La solution : **« Plus jamais d'inconnus au Club »**. La plateforme vit au rythme des événements :

- **Avant** l'événement, on apprend à se connaître : l'album de cartes, les affinités, « tes 3 rencontres ».
- **Pendant**, on se mélange : le scan du QR code, les tables tournantes.
- **Après**, on mesure : « ton album 18 / 49 », l'indice de fédération pour le comité.

Ton : détendu, premium, valaisan (rouge valaisan et or, vins, montagne, apéro). Tutoiement.

**Comptes de démo** (mot de passe local : `club-demo-2026`) :

| Compte | Profil |
|---|---|
| `camille.rey@example.com` | Nouvelle recrue (Tech, Martigny), 2 cartes dans son album. Pour le dîner à venir, sa 1ʳᵉ rencontre proposée est **Lukas**. |
| `lukas.imboden@example.com` | Pilier du Club depuis 2017 (construction bois, Brig, parle DE et FR). |
| `equipe@example.com` | Staff, accès à `/admin/` et `/staff/`. |

## 3. Planning (samedi 3 → dimanche 4 octobre, rendu à 13 h)

| Phase | Contenu | Durée | Créneau visé |
|---|---|---|---|
| 0 | Environnement + CSS | 20 min | sam. 14:00 |
| 1 | Design de base (layout, connexion, accueil, erreurs) | 1 h 15 | 14:20 |
| 2 | Mise en ligne sur Render 👤 | 45 min | 15:35 |
| 3 | Album de cartes, fiche, QR, profil | 2 h | 16:20 |
| 4 | Événements, inscription, rencontres, placement | 1 h 30 | 18:20 |
| 5 | Outils staff (tableau de bord, génération, plan de tables) | 1 h 30 | 19:50 |
| ✂️ | **MVP terminé : on peut faire la démo** | | **~21:30** |
| 6 | Swipe des affinités | 1 h | 21:30 ou dim. 7:00 |
| 7 | Vitrine publique, demande d'invitation, parrainage | 1 h | dim. 8:00 |
| 8 | Trilingue FR/DE/EN | 1 h | dim. 9:00 |
| 9 | Lien magique par e-mail + badges imprimables | 1 h | dim. 10:00 |
| 10 | Préparation de la démo + gel du code | 45 min | dim. 11:00 |

**Règles de coupe** :

- Samedi 23:00 : si le MVP n'est pas fini, on finit la phase en cours, on pousse et on dort.
- Dimanche : phases 6 → 9 dans l'ordre, et **à 10:30 on passe à la phase 10 quoi qu'il arrive**.
- Une tâche qui bloque plus de 30 minutes : on la saute, on note pourquoi dans ce fichier et on passe à la suivante.

## 4. Référence

### 4.1 Routes (finales)

| Nom | Chemin | Vue | Accès | État |
|---|---|---|---|---|
| `club:landing` | `/` | `public.landing` | public | ✅ |
| `login` | `/connexion/` | `LoginView` + `EmailAuthenticationForm` | public | ✅ |
| `magic_login` | `/connexion/lien/` | django-sesame | public | ✅ |
| `club:magic_link_request` | `/connexion/recevoir-un-lien/` | `public.magic_link_request` | public | ✅ |
| `logout` | `/deconnexion/` | `LogoutView` (POST) | connecté | ✅ |
| `set_language` | `/i18n/setlang/` | `set_language` (POST) | public | ✅ |
| `club:join` | `/rejoindre/` | `public.join` | public | ✅ fait en avance (lien sous la connexion) |
| `club:join_thanks` | `/rejoindre/merci/` | `public.join_thanks` | public | ✅ fait en avance |
| `club:home` | `/accueil/` | `member.home` | membre | ✅ (à enrichir) |
| `club:album` | `/album/` | `member.album` | membre | phase 3 |
| `club:member_detail` | `/membres/<pk>/` | `member.member_detail` | membre | ✅ (template à refaire) |
| `club:member_vcard` | `/membres/<pk>/vcard/` | `member.member_vcard` | membre déjà rencontré | ✅ |
| `club:my_qr` | `/moi/qr/` | `member.my_qr` | membre | ✅ (template à refaire) |
| `club:profile_edit` | `/moi/` | `member.profile_edit` | membre | phase 3 |
| `club:invite` | `/moi/inviter/` | `member.invite` | membre | ✅ |
| `club:onboarding` | `/bienvenue/` | `member.onboarding` | membre | ✅ |
| `club:scan` | `/m/<token>/` | `member.scan` | membre | ✅ (template à refaire) |
| `club:event_list` | `/evenements/` | `events.event_list` | membre | phase 4 |
| `club:event_detail` | `/evenements/<pk>/` | `events.event_detail` | membre | phase 4 |
| `club:event_rsvp` | `/evenements/<pk>/rsvp/` | `events.event_rsvp` (POST) | membre | phase 4 |
| `club:staff_dashboard` | `/staff/` | `staff.dashboard` | staff | ✅ (à enrichir) |
| `club:staff_event` | `/staff/evenements/<pk>/` | `staff.event_tools` | staff | ✅ |
| `club:staff_badges` | `/staff/evenements/<pk>/badges/` | `staff.badges` | staff | ✅ |

Les routes se déclarent dans `club/urls.py`, et les nouvelles vues d'événements vont dans `club/views/events.py` (à créer).

### 4.2 Design

- **Couleurs** :
  - primaire `red-700` (rouge valaisan), survol `red-800` ;
  - accent `amber-400` (or) ;
  - fond `stone-50`, texte `stone-900`, texte secondaire `stone-600`, bordures `stone-200` ;
  - succès `emerald-600`.
- **Police** : celle du système (`font-sans` par défaut). Aucune police externe : la CSP bloquerait Google Fonts.
- **Composants** déjà définis dans `assets/css/input.css` : `btn btn-primary`, `btn btn-secondary`, `card`, `chip`,
  `input`, et `<progress class="bar">` pour les barres de progression.
- **Mobile d'abord** : tout doit être parfait à 390 px de large. Barre de navigation en bas sur mobile
  (`md:hidden`), liens en haut sur ordinateur (`hidden md:flex`).
- **Emojis** : bienvenus (secteurs, affinités), c'est l'ADN « décontracté ». Pas de bibliothèque d'icônes.

### 4.3 La carte membre (composant central)

C'est le fichier `templates/club/_card.html`, inclus ainsi :
`{% include "club/_card.html" with member=m collected=True size="compact" %}`.

Les données viennent des filtres `{% load club_ui %}` :

| Filtre ou tag | Donne |
|---|---|
| `member\|sector_emoji` | l'emoji du secteur |
| `member\|sector_classes` | les classes de couleur de l'avatar |
| `member\|rank_label` | le libellé du rang |
| `member\|rank_ring` | le contour de la carte selon le rang |
| `member\|rank_badge` | les classes du badge de rang |
| `{% tags_with member "like" as likes %}` / `"dislike"` | les affinités et agacements |
| `member.get_sector_display` | le nom du secteur |
| `member.seniority_years` | l'ancienneté en années |
| `member.languages` | les langues parlées |

Contenu de haut en bas :

1. **Contour** : `card` + `member|rank_ring` (doré pour les fondateurs, vert pour les nouvelles recrues).
2. **En-tête** :
   - avatar rond de 48 px (`member|sector_classes`) avec `member.initials` ;
   - à droite, le nom en `font-semibold`, puis `job_title · company` en `text-sm text-stone-600`.
3. **Badges** (`chip`) :
   - le rang (`member|rank_badge`) ;
   - `{{ member|sector_emoji }} {{ member.get_sector_display }}` ;
   - « Membre depuis 2017 · 9 ans », ou « Membre depuis 2026 » quand l'ancienneté est de 0 an ;
   - les langues en majuscules (FR · DE · EN).
4. **Affinités** :
   - ❤️ et l'emoji et le libellé de chaque `tag` aimé (4 au maximum en `compact`) ;
   - 💀 pour les agacements (2 au maximum en `compact`).
5. **Uniquement en `size="full"`** :
   - l'anecdote en italique ;
   - « Parle-moi de… » ;
   - la région.
6. **Pied de carte** :
   - si `collected` : ✅ « Dans ton album » ;
   - sinon : 🔒 « À rencontrer ».
   - En `compact`, toute la carte est un lien vers `club:member_detail`.

Pour éviter les requêtes N+1, toute liste de cartes charge les membres avec
`.select_related("user").prefetch_related("tag_links__tag")`.

## 5. Phases

### Phase 0 — Environnement (20 min)

- [x] **0.1** 👤 Installer les outils : `brew install uv gettext`. Gettext ne servira qu'en phase 8.
- [x] **0.2** Créer l'environnement et installer les dépendances :
  ```bash
  uv venv --python 3.12 .venv
  source .venv/bin/activate
  uv pip install -r requirements.txt
  python manage.py migrate
  python manage.py seed_demo --reset
  python manage.py test club
  ```
  ✅ Le seed affiche `50 members, 180 connections, federation index 15%…` et les tests sont `OK` (31 tests ou plus).
- [x] **0.3** Installer Tailwind (binaire autonome, sans Node) et compiler le CSS :
  ```bash
  curl -sL -o tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
  chmod +x tailwindcss
  ./tailwindcss -i assets/css/input.css -o static/css/app.css --minify
  ```
  ✅ `static/css/app.css` pèse plus de 10 Ko. Le binaire `tailwindcss` est ignoré par git (`.gitignore`).
- [x] **0.4** 👤 Premier commit, si l'humain ne l'a pas déjà fait :
  `git add -A && git commit -m "chore: socle vérifié (modèles, services, sécurité, admin, seed, tests)"`.

### Phase 1 — Design de base, connexion, accueil (1 h 15)

- [x] **1.1** `templates/base.html`, la mise en page commune :
  - `<html lang="{{ LANGUAGE_CODE }}">`, viewport mobile, `<title>{% block title %}{{ SITE_NAME }}{% endblock %}</title>`,
    `{% static 'css/app.css' %}`, et `<script src="{% static 'js/swipe.js' %}" defer>` (à garder).
  - `<body class="min-h-screen bg-stone-50 text-stone-900 antialiased">`.
  - **Bandeau de démo** si `DEMO_MODE` : « Démo — toutes les personnes et entreprises sont fictives »
    (`bg-amber-100 text-amber-900 text-xs text-center py-1`).
  - **En-tête** blanc, collé en haut (`sticky top-0`) :
    - à gauche, « 🍷 {{ SITE_NAME }} » ;
    - à droite, le sélecteur de langue : un formulaire POST vers `{% url 'set_language' %}` avec `{% csrf_token %}`,
      un champ caché `next` = `{{ request.get_full_path }}` et 3 boutons
      `<button name="language" value="fr">FR</button>` (puis DE, EN). Aucun JavaScript.
    - Si l'utilisateur est connecté, un formulaire POST de déconnexion. **Jamais de lien GET** : la déconnexion
      refuse le GET avec une erreur 405.
  - **Navigation** si `request.member` existe : Accueil 🏠 (`club:home`), Album 🃏 (`club:album`, à partir de la
    phase 3), Événements 📅 (`club:event_list`, phase 4), Mon QR 🔳 (`club:my_qr`), Profil 👤 (`club:profile_edit`,
    phase 3). Lien Staff ⚙️ si `user.is_staff`.
    Mets en commentaire les liens dont la route n'existe pas encore, sinon `{% url %}` plante.
    - Sur mobile : `fixed bottom-0 inset-x-0`, 5 icônes avec un libellé de `text-[11px]`.
    - Sur ordinateur : des liens dans l'en-tête.
  - **Messages** Django : une `card` par message (vert pour un succès, bleu pour une info).
  - `<main class="mx-auto max-w-5xl px-4 pt-6 pb-28">{% block content %}{% endblock %}</main>`.
  - ✅ Aucun `style=`, aucun `<script>` sans `src`, aucun `onclick` (le test CSP le vérifie).
- [x] **1.2** `templates/registration/login.html` : une `card` centrée qui affiche le titre `{{ SITE_NAME }}`,
  un sous-titre « Espace membres du Club des Affaires », les champs (e-mail, mot de passe) en classe `input`,
  les erreurs du formulaire et un bouton `btn btn-primary w-full`.
  Le champ s'appelle `username` mais son libellé est « E-mail » : c'est voulu, la connexion se fait par e-mail.
- [x] **1.3** `templates/club/home.html` (accueil membre) :
  - « Salut {{ request.member.first_name }} 👋 ».
  - Une `card` « Ton album » : `{{ collected }} / {{ total }} cartes`, `<progress class="bar">`, et des boutons
    « Montrer mon QR » (`club:my_qr`) et « Voir l'album » (à partir de la phase 3).
  - Une `card` « Le Club est connecté à X % ». L'indice vient de `club_stats()["index"]` : ajoute-le au contexte dans
    `member.home` et affiche-le avec `|percent`. Sous l'indice : « Chaque rencontre compte. ».
  - Un emplacement « Prochain événement », rempli en phase 4.
- [x] **1.4** `templates/403.html` et `templates/404.html` : une `card` sympathique, par exemple
  « Cette porte est réservée 🍷 » ou « Cette page s'est perdue en montagne 🏔️ », avec un lien vers l'accueil.
- [x] **1.5** `templates/staff/dashboard.html` (version simple, enrichie en phase 5) : 3 tuiles (`card`) pour les
  membres, les rencontres enregistrées et l'indice de fédération (`stats.index|percent`), plus un lien vers `/admin/`.
- ✅ **Fin de phase** :
  - `python manage.py test club` est vert.
  - Dans le navigateur à 390 px de large (outils de développement Chrome, mode mobile) : connexion avec Camille,
    accueil, changement de langue (l'interface reste en français tant que la phase 8 n'est pas faite, c'est normal),
    déconnexion.
  - Connexion avec `equipe@example.com` : `/accueil/` redirige vers `/staff/`.
- Commit : `feat: design de base, connexion, accueil`.

### Phase 2 — Mise en ligne (45 min, 👤 avec l'humain)

> On met en ligne tôt : ensuite, chaque `git push` redéploie automatiquement.

- [x] **2.1** 👤 Créer le dépôt GitHub (privé) et pousser. *Fait : dépôt privé `MicrobAtomic/Meeting-project-Foire-du-Valais`, `origin/main` à jour.*
- [ ] **2.2** 👤 Sur render.com, créer un compte puis **New → Blueprint** et choisir le dépôt. Render lit
  `render.yaml` : un service web et une base PostgreSQL gratuits, à Frankfurt. Quand Render la demande, saisir une
  valeur pour `DEMO_PASSWORD` (un mot de passe de démo, à noter). Lancer, puis attendre la fin du build (environ 5 min).
- [ ] **2.3** Vérifier, sur l'URL `https://club-des-affaires-xxxx.onrender.com` :
  - la page d'accueil publique s'affiche ;
  - la connexion avec Camille et `DEMO_PASSWORD` fonctionne ;
  - `/admin/` fonctionne avec `equipe@example.com` ;
  - dans les logs de build, on lit `50 members…`.
- [ ] **2.4** Noter l'URL de production dans `README.md`, section « Démo en ligne ».
- ✅ **Validation locale déjà faite** (3 octobre) : les 40 tests passent sur PostgreSQL 17, `build.sh` (collectstatic, migrate, seed) tourne en `DEBUG=0` sur PostgreSQL avec les mêmes chiffres qu'en local (50 membres, 180 rencontres, 15 %), et gunicorn répond correctement (redirection HTTPS, en-têtes de sécurité, CSS versionné, hôte invalide refusé, connexion et CSRF OK). Reste uniquement ce qui demande un compte Render (2.2 à 2.4).
- ⚠️ L'offre gratuite se met en veille après 15 minutes d'inactivité : **ouvrir l'URL 2 minutes avant le pitch**.
- 🆘 **Plan B** si Render bloque : le site tourne en local, et un tunnel HTTPS public permet d'y accéder depuis un
  téléphone. `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` acceptent déjà `*.trycloudflare.com`.
  ```bash
  brew install cloudflared
  python manage.py runserver &
  cloudflared tunnel --url http://localhost:8000
  ```
- Commit, s'il y a eu des changements : `chore: mise en ligne`.

### Phase 3 — L'album de cartes, la fiche, le QR, le profil (2 h)

- [x] **3.1** Le composant `templates/club/_card.html`, conforme au § 4.3.
- [x] **3.2** La vue `member.album`, route `club:album`, `/album/` :
  - Membres affichés : visibles (`visible_in_directory=True`), actifs (`user__is_active=True`), sauf soi-même.
    Avec `select_related` et `prefetch_related`.
  - Filtres GET (un formulaire GET, sans JavaScript) :

    | Paramètre | Effet |
    |---|---|
    | `q` | `first_name`, `last_name` ou `company` contient `q` (`icontains`, combinés avec `Q(...) \| Q(...)`) |
    | `secteur` | une valeur de `Sector` |
    | `langue` | `fr`, `de` ou `en`, qui filtre sur `speaks_fr`, `speaks_de` ou `speaks_en` |
    | `statut` | `toutes` (par défaut), `album` (`pk__in=collected_ids(me)`), `a-rencontrer` (`exclude(pk__in=…)`), `nouveaux` (`member_since=timezone.localdate().year`) |

  - Contexte : `members`, `collected` (le résultat de `collected_ids(request.member)`, un ensemble d'id),
    `progress` (le résultat de `collection_progress`), `stats` (`club_stats()`), `sectors` (`Sector.choices`)
    et les filtres actifs.
  - Template `templates/club/album.html` :
    - en-tête « L'album du Club », `<progress class="bar">` « X / Y cartes » ;
    - le formulaire de filtres ;
    - une grille `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4` de `_card.html` en `compact`, avec
      `collected=` à `True` si `m.pk in collected`. Comme on ne peut pas tester l'appartenance à un ensemble dans
      un `{% include %}`, prépare dans la vue une liste de tuples `(member, is_collected)`.
  - Ajoute `"club:album"` à `PAGES_TO_CHECK` dans `club/tests/test_album.py`.
  - ✅ Avec Camille : 49 cartes, filtre `statut=album` → 2 cartes, filtre `langue=de` → seulement des
    germanophones, `q=Lukas` → 1 carte.
- [x] **3.3** Refaire `templates/club/member_detail.html` :
  - `_card.html` en `full` ;
  - « Vos points communs » si ce n'est pas moi : `common_tags(request.member, target)` (dans
    `club/services/profile.py`), à ajouter au contexte de la vue, affiché en chips ❤️ et 💀 ;
  - **si `can_see_contact`** :
    - l'e-mail (`mailto:`), le téléphone (`tel:`), LinkedIn ;
    - un bouton `btn btn-primary` « 📇 Ajouter à mes contacts » vers `club:member_vcard` ;
  - **sinon** : 🔒 « Scanne son QR code lors d'un événement pour débloquer ses coordonnées. » ;
  - si `is_me` : des boutons « Modifier mon profil » et « Mon QR code ».
  - ✅ Le test `test_contact_details_only_after_meeting` reste vert.
- [x] **3.4** Refaire `templates/club/my_qr.html` : une grande `card` centrée qui contient le QR
  (`{{ qr_svg|safe }}` dans un `div` blanc arrondi, `[&>svg]:mx-auto [&>svg]:h-64 [&>svg]:w-64`), le nom, le texte
  « Fais scanner ce code pour échanger vos cartes » et l'astuce « Fais une capture d'écran pour l'avoir même sans
  réseau ». Garde le lien `scan_url` en petit : il sert en démo.
- [x] **3.5** Refaire `templates/club/scan_confirm.html` : la carte `compact` de `target`, la question
  « Vous venez de vous rencontrer ? » et un formulaire POST (avec `{% csrf_token %}`) contenant un bouton
  `btn btn-primary w-full` « Ajouter {{ target.first_name }} à mon album ».
- [x] **3.6** Édition du profil, vue `member.profile_edit`, route `club:profile_edit`, `/moi/` :
  - `MemberProfileForm(ModelForm)` dans `club/forms.py`. Champs autorisés **et seulement eux** : `first_name`,
    `last_name`, `company`, `job_title`, `sector`, `region`, `speaks_fr`, `speaks_de`, `speaks_en`, `fun_fact`,
    `talk_to_me_about`, `phone`, `linkedin_url`, `visible_in_directory`.
    `member_since`, `is_founder`, `qr_token`, `referral_code` et `user` sont **interdits** : seul le staff les gère.
  - La vue utilise toujours `instance=request.member`. En POST valide, elle appelle aussi
    `save_tag_answers(request.member, request.POST)`, affiche le message « Profil enregistré ✅ » et redirige vers
    `club:member_detail` avec `request.member.pk`.
  - Template `club/profile_edit.html` :
    - les champs en classe `input` ;
    - puis, pour chaque catégorie de `Tag` (`Tag.Category`), chaque tag avec 3 boutons radio
      `name="tag_{{ tag.slug }}"` et les valeurs `like` (❤️ J'adore), `neutral` (😐 Bof), `dislike` (💀 Je déteste),
      pré-cochés selon les `MemberTag` existants. Passe à la vue un dictionnaire `{slug: sentiment}`.
  - Ajoute `"club:profile_edit"` à `PAGES_TO_CHECK`.
  - Ajoute `club/tests/test_profile_edit.py` avec deux tests :
    1. un POST qui inclut `member_since=1990` ne change **pas** `member_since` ;
    2. un POST modifie bien le profil du membre connecté, et seulement le sien.
- [x] **3.7** Décommenter les liens Album et Profil dans `base.html`. Dans `home.html`, ajouter le bouton
  « Voir l'album ».
- ✅ **Fin de phase** :
  - Les tests sont verts.
  - Parcours complet dans deux navigateurs : Camille dans une fenêtre normale, Lukas dans une fenêtre privée.
    1. Lukas ouvre `/moi/qr/`.
    2. Camille ouvre le lien `scan_url` et confirme.
    3. La carte de Lukas est débloquée, la vCard se télécharge, l'album de Camille passe à 3 / 49.
- Commit et push : `feat: album de cartes, QR, profil`.

### Phase 4 — Événements (1 h 30)

- [x] **4.1** Créer `club/views/events.py` et déclarer les 3 routes.
  - **`event_list`** : les événements à venir (`starts_at >= now`, par ordre croissant), puis les passés (par ordre
    décroissant). Pour chacun : la date en français (`{{ e.starts_at|date:"l j F, H:i" }}`), le lieu, le nombre
    d'inscrits (annotation `Count` filtrée sur `status="yes"`), et ma réponse (un dictionnaire
    `{event_id: status}` construit dans la vue).
  - **`event_detail`** :
    - les infos de l'événement ;
    - **ma réponse** avec deux boutons POST vers `club:event_rsvp` (« Je viens ✅ » / « Je ne viens pas »),
      affichés seulement si l'événement est à venir ;
    - **« Qui vient ? »** : la grille de cartes `compact` des inscrits (`attendees(event)` + `prefetch`) ;
    - **« Tes rencontres »**, seulement si je suis inscrit : `intros_for(request.member, event)`. Chaque rencontre
      est une `card` avec l'avatar et le nom de `intro.other` (lien vers sa fiche), les chips ❤️ `intro.likes` et
      💀 `intro.dislikes`, la chip « 🔀 Secteurs complémentaires » si `intro.cross_sector`, la chip
      « 🌱 Accueille une nouvelle recrue » si `intro.welcomes_newcomer`, puis « 💬 {{ intro.icebreaker }} ».
      S'il n'y en a aucune : « Tes rencontres arrivent bientôt 🍷 ».
    - **« Ton placement »** si `seats_for(request.member, event)` n'est pas vide : par exemple
      « Entrée : table 3 · Plat : table 5 · Dessert : table 1 ».
  - **`event_rsvp`** :
    - `@require_POST`, `@member_required` ;
    - `status` doit valoir `yes` ou `no`, sinon erreur 400 ;
    - événement passé : message d'erreur et redirection ;
    - sinon `RSVP.objects.update_or_create(event=event, member=request.member, defaults={"status": status})`,
      puis un message et une redirection vers `event_detail`.
- [x] **4.2** Accueil : la `card` « Prochain événement » avec le prochain événement à venir et ma réponse.
  Si je suis inscrit, elle affiche aussi les 3 rencontres en version courte (nom, première affinité commune,
  icebreaker) et un lien vers l'événement.
- [x] **4.3** Ajouter `club/tests/test_events.py` :
  - un POST d'inscription crée ou modifie **seulement** mon RSVP ;
  - le GET sur `event_rsvp` renvoie 405 ;
  - l'inscription à un événement passé est refusée ;
  - `club:event_list` est ajouté à `PAGES_TO_CHECK`. Pour la page d'un événement (elle a un paramètre), appelle
    `assert_csp_clean(self, response)` (dans `club/tests/helpers.py`) dans ton propre test.
- [x] **4.4** Décommenter le lien Événements dans `base.html`.
- ✅ **Fin de phase** :
  - Avec Camille, l'accueil montre « Dîner d'automne » et les rencontres **Lukas Imboden**, Joëlle Moret et
    Olivier Gay, avec leurs raisons (❤️ Petite Arvine, ⛷️ Ski de randonnée…).
  - Le changement de réponse à l'inscription fonctionne.
- Commit et push : `feat: événements, inscriptions, rencontres`.

### Phase 5 — Outils staff (1 h 30)

- [x] **5.1** Enrichir `staff.dashboard` et `templates/staff/dashboard.html` :
  - **Tuiles** :
    - membres ;
    - indice de fédération, en grand ;
    - rencontres des 30 derniers jours (`Connection.objects.filter(created_at__gte=…)`) ;
    - nouvelles recrues de l'année.
  - **« Membres isolés »** : `isolated_members()`, triés, avec un lien vers leur fiche admin
    (`{% url 'admin:club_member_change' m.pk %}`) et la phrase « À présenter lors du prochain événement ».
  - **« Événements à venir »** : le nombre d'inscrits et un bouton « Préparer » vers `club:staff_event`.
  - **« Rencontres par événement passé »** : `Count("connections")` par événement.
- [x] **5.2** La vue `staff.event_tools`, route `club:staff_event`, `/staff/evenements/<pk>/`, avec `@staff_required` :
  - **POST `action=matches`** : `generate_matches(event)`, puis le message « N rencontres générées ».
  - **POST `action=seating`** :
    - un petit `forms.Form` valide `rounds` (de 1 à 4, 3 par défaut) et `table_size` (de 4 à 10, **6 par défaut**) ;
    - puis `generate_seating(event, rounds, table_size)` ;
    - message : « Plan généré : X nouvelles paires, Y répétition(s) ».
  - **GET**, deux colonnes :
    1. la liste des `Match` (les deux noms, le score, les affinités communes) ;
    2. le plan de tables : une section par service (libellé `round_label(i)` de `club/ui.py`), une `card` par table
       avec les noms et l'emoji du secteur, et les statistiques du plan.
    - Plus un bouton « Imprimer » (`no-print` sur le reste de la page ; JavaScript `static/js/print.js` qui appelle
      `window.print()` sur un clic `[data-print]`).
- [x] **5.3** Ajouter `club/tests/test_staff.py` :
  - un membre reçoit une erreur 403 sur les pages staff ;
  - un POST `matches` du staff crée des `Match` ;
  - un POST `seating` crée `nb_inscrits × rounds` `SeatAssignment` ;
  - un `table_size=50` est refusé.
- ✅ **Fin de phase** :
  - Avec `equipe@example.com`, le tableau de bord affiche 15 %.
  - « Dîner d'automne » → générer le plan (tables de 6) → environ « 248 nouvelles paires, 1 répétition ».
  - Puis avec Camille, la page de l'événement affiche « Ton placement ».
- Commit et push : `feat: outils staff, tables tournantes`.

## ✂️ MVP terminé : la démo complète est possible. Tout ce qui suit est du bonus, dans cet ordre.

### Phase 6 — Swipe des affinités (1 h)

- [x] **6.1** La vue `member.onboarding`, route `club:onboarding`, `/bienvenue/` :
  - en GET : tous les `Tag` et les réponses actuelles ;
  - en POST : `save_tag_answers(request.member, request.POST)`, puis `onboarding_done=True`, le message
    « Profil complété 🎉 » et une redirection vers l'accueil.
- [x] **6.2** Template `club/onboarding.html`. Il **doit** respecter le contrat de `static/js/swipe.js` :
  ```html
  <form method="post" id="swipe-form">{% csrf_token %}
    <div class="swipe-deck">
      {% for tag in tags %}
      <fieldset class="swipe-card card flex flex-col items-center justify-center gap-4 text-center">
        <div class="text-7xl">{{ tag.emoji }}</div>
        <legend class="text-2xl font-semibold">{{ tag.label }}</legend>
        <p class="chip">{{ tag.get_category_display }}</p>
        <div class="swipe-choices flex gap-3">  <!-- radios visibles seulement sans JS -->
          <label><input type="radio" name="tag_{{ tag.slug }}" value="dislike"> 💀 {% translate "Je déteste" %}</label>
          <label><input type="radio" name="tag_{{ tag.slug }}" value="neutral" checked> 😐 {% translate "Bof" %}</label>
          <label><input type="radio" name="tag_{{ tag.slug }}" value="like"> ❤️ {% translate "J'adore" %}</label>
        </div>
      </fieldset>
      {% endfor %}
    </div>
    <div id="swipe-controls" hidden> <!-- boutons visibles seulement avec JS -->
      <button type="button" data-answer="dislike">💀</button>
      <button type="button" data-answer="neutral">😐</button>
      <button type="button" data-answer="like">❤️</button>
    </div>
    <p id="swipe-progress"></p>
    <button type="submit" class="btn btn-secondary">{% translate "Enregistrer" %}</button>
  </form>
  ```
  - Dans la vraie version, `checked` doit refléter la réponse existante.
  - Style les boutons de `#swipe-controls` en gros ronds : `h-16 w-16 rounded-full text-3xl bg-white shadow`.
- [x] **6.3** Sur l'accueil, si `not request.member.onboarding_done` : une bannière « Complète ton profil en
  2 minutes 👉 » vers `club:onboarding`. Sur la page profil, un lien « Refaire le swipe ».
- [x] **6.4** Les tests : un POST enregistre les réponses, les valeurs invalides sont ignorées, et la page fait
  partie de `PAGES_TO_CHECK`.
- ✅ **Fin de phase**, sur téléphone (ou en mode mobile) :
  - glisser à droite = ❤️, à gauche = 💀, vers le bas = 😐 ;
  - les boutons marchent ;
  - avec le JavaScript désactivé, le formulaire à boutons radio fonctionne.
- Commit et push : `feat: swipe des affinités`.

### Phase 7 — Vitrine publique, demande d'invitation, parrainage (1 h)

- [x] **7.1** Refaire `templates/public/landing.html` (page publique, **aucun nom de membre**) :
  - **Hero** : « Le Club des Affaires de la Foire du Valais », le slogan « Plus jamais d'inconnus au Club. »,
    un bouton `btn-primary` « Demander une invitation » (vers `club:join`) et un bouton `btn-secondary`
    « Espace membres » (vers `club:home`).
  - **Trois promesses** : Se rencontrer (avant), Se mélanger (pendant), Grandir ensemble (après).
  - **Chiffres** calculés dans la vue : nombre de membres actifs, nombre de secteurs distincts, et « 4 à 5 soirées
    par an ».
  - **« Comment ça marche »** : l'album, le QR, les tables tournantes, en 3 étapes illustrées d'emojis.
- [x] **7.2** *(fait en avance à la demande de l'utilisateur : lien « Demander une invitation » sous la page de connexion ; formulaire réduit à prénom, nom, e-mail, entreprise et poste, sans champ message ; une même adresse n'est enregistrée qu'une fois par 24 h ; 15 tests dans `club/tests/test_join.py`)* Les vues `public.join` (`/rejoindre/`) et `public.join_thanks` (`/rejoindre/merci/`), avec
  `@login_not_required` :
  - `InvitationRequestForm(ModelForm)` avec `first_name`, `last_name`, `company`, `job_title`, `email`, `message`.
  - Un **champ piège** `website` (`CharField(required=False)`) caché avec la classe `hidden`. S'il est rempli,
    on n'enregistre rien mais on redirige quand même vers « merci ».
  - `?ref=CODE` : on cherche le `Member` qui a ce `referral_code`. S'il existe, on affiche « Invité·e par
    Prénom N. » et on remplit `referred_by`. Un code invalide est ignoré **sans message**, pour ne rien révéler.
- [x] **7.3** La vue `member.invite`, `/moi/inviter/` :
  - le lien personnel
    `request.build_absolute_uri(reverse("club:join")) + "?ref=" + request.member.referral_code`,
    son QR (`qr_svg`) et un bouton « Copier ». JavaScript `static/js/copy.js` : au clic sur `[data-copy]`,
    `navigator.clipboard.writeText(...)` ;
  - l'offre, avec les montants lus dans `settings` :
    « Ton invité·e : 1ʳᵉ année à {{ REFERRAL_NEW_MEMBER_PRICE }} CHF au lieu de {{ MEMBERSHIP_PRICE }} CHF ·
    toi : −{{ REFERRAL_SPONSOR_DISCOUNT }} CHF sur ta cotisation ». Montants à valider avec le client ;
  - la liste de mes filleuls (`request.member.referrals`) avec leur statut.
  - Ajoute un lien « Inviter quelqu'un » sur l'accueil et sur le profil.
- [x] **7.4** Les tests :
  - un visiteur anonyme peut afficher la page et envoyer le formulaire ;
  - le champ piège bloque l'enregistrement ;
  - `?ref=` remplit `referred_by` ;
  - `/moi/inviter/` exige une connexion ;
  - la landing ne contient aucun nom de membre (`assertNotContains(response, "Imboden")`).
- Commit et push : `feat: vitrine publique et parrainage`.

### Phase 8 — Trilingue FR/DE/EN (1 h)

- [x] **8.1** *(fait : 303 textes extraits ; les formats de date et le pourcentage passent aussi par les catalogues via les filtres `datetime_short`, `datetime_long`, `date_long`, `date_short` et `percent` de `club_ui` ; un catalogue **français** identique à la source apporte la bonne règle de pluriel, « 0 inscrit » ; 13 tests dans `club/tests/test_i18n.py`, dont un qui parcourt toutes les pages en allemand et en anglais pour vérifier qu'aucune phrase française d'interface ne reste)* Vérifie que tous les textes d'interface passent par `{% translate %}` ou `{% blocktranslate %}`
  (templates) et par `gettext` ou `gettext_lazy` (Python).
- [x] **8.2** `python manage.py makemessages -l de -l en --ignore=.venv` crée `locale/de/LC_MESSAGES/django.po`
  et `locale/en/…`.
- [x] **8.3** Traduire tous les `msgstr`, puis supprimer les marques `#, fuzzy`.
  - Allemand : **suisse** (« ss », jamais « ß ») et tutoiement (« du »), comme en français.
  - Anglais : simple et chaleureux.
- [x] **8.4** `python manage.py compilemessages --ignore=.venv`, puis **commiter les `.po` et les `.mo`**
  (Render n'a pas gettext).
- ✅ **Fin de phase** : FR → DE sur l'accueil, l'album, une fiche et un événement. L'interface, les affinités et les
  phrases d'accroche passent en allemand. Celles-ci sont déjà en base grâce à `Tag.label` et `Tag.icebreaker`.
- Commit et push : `feat: interface trilingue FR/DE/EN`.

### Phase 9 — Lien magique et badges imprimables (1 h)

- [x] **9.1** *(fait : service `club/services/auth_links.py`, e-mail rédigé dans la langue du membre, SMTP configurable par variables d'environnement, page claire quand un lien a expiré)* Ajouter l'action admin « Envoyer un lien de connexion » dans `MemberAdmin` :
  - pour chaque membre : `link = request.build_absolute_uri(reverse("magic_login")) + get_query_string(member.user)`
    (`from sesame.utils import get_query_string`) ;
  - `send_mail` avec le sujet « Ton accès au Club des Affaires » et un texte qui précise que le lien est valable 15 minutes
    et ne sert qu'une fois ;
  - message final : « N liens envoyés ».
  - En local, l'e-mail s'affiche dans la console : `EMAIL_BACKEND` vaut `console`.
- [x] **9.2** La vue `public.magic_link_request`, `/connexion/recevoir-un-lien/`, avec `@login_not_required` :
  - un formulaire avec un seul champ e-mail ;
  - si un membre actif a cet e-mail, on lui envoie le lien ;
  - **dans tous les cas**, on affiche le même message : « Si cette adresse est connue, un lien vient d'être
    envoyé. » Ainsi personne ne peut tester quelles adresses sont membres.
  - Ajouter un lien vers cette page sur la page de connexion.
- [x] **9.3** La vue `staff.badges`, `/staff/evenements/<pk>/badges/`, avec `@staff_required`.
  - Une grille A4 de 2 × 4 badges, un par inscrit. Chaque badge affiche :
    - le prénom en très grand ;
    - le nom et l'entreprise ;
    - l'emoji du secteur ;
    - « Parle-moi de : {{ talk_to_me_about }} » ;
    - le QR (`qr_svg` de l'URL de scan, calculé dans la vue).
  - Un bouton « Imprimer » qui réutilise `print.js`, et `no-print` sur la navigation.
- [x] **9.4** Les tests :
  - un e-mail inconnu donne le même message et `mail.outbox` reste vide ;
  - un e-mail connu envoie exactement 1 e-mail qui contient `/connexion/lien/?sesame=` ;
  - un membre reçoit une erreur 403 sur la page des badges.
- Commit et push : `feat: lien magique et badges`.

### Phase 10 — Préparation de la démo et gel du code (45 min, dimanche 11:00)

- [ ] **10.1** Réinitialiser les données de production, en local et en ligne. Il faut le **même** mot de passe que
  sur Render, et l'« External Database URL » se copie depuis le tableau de bord Render de la base.
  ```bash
  DATABASE_URL='<External Database URL>' DEMO_PASSWORD='<le même que sur Render>' python manage.py seed_demo --reset
  ```
- [ ] **10.2** Imprimer 2 badges, Lukas et un autre membre, depuis `/staff/evenements/<id>/badges/`.
- [ ] **10.3** 👤 Répéter le scénario ci-dessous **deux fois** sur un vrai téléphone et un ordinateur.
- [ ] **10.4** 👤 Enregistrer une vidéo de secours du scénario complet (QuickTime → Nouvel enregistrement de l'écran),
  environ 2 minutes.
- [ ] **10.5** Gel :
  - `./tailwindcss … --minify` ;
  - les tests sont verts ;
  - `git push` ;
  - vérifier l'URL de production ;
  - `git tag v1.0-hackathon && git push --tags`.

## 6. Scénario de démo (2 minutes, à répéter)

1. **Vitrine** : la page publique et « Demander une invitation ». Aucun nom de membre n'est visible de l'extérieur.
2. **Camille, nouvelle recrue**, sur le téléphone :
   - l'accueil affiche « 2 / 49 cartes » et le prochain dîner ;
   - **« Tes 3 rencontres »** : Lukas, parce qu'ils partagent ❤️ la Petite Arvine, ⛷️ le ski de rando, 🏃 le trail,
     et 💀 les réunions du lundi matin. On voit aussi la phrase pour engager la conversation.
3. **L'album** : les cartes, les rangs (fondateur doré, nouvelle recrue en vert) et le filtre « germanophones ».
4. **La rencontre en vrai** :
   - Camille scanne le badge imprimé de Lukas → « Ajouter Lukas à mon album » ;
   - les coordonnées sont débloquées → « Ajouter à mes contacts » → la vCard s'ouvre dans Contacts ;
   - l'album passe à 3 / 49.
5. **Le staff** :
   - le tableau de bord affiche l'indice de fédération (il a bougé) et les membres isolés ;
   - « Dîner d'automne » → plan de tables généré en direct : 38 invités, 3 services, environ 1 répétition.
6. **Bascule en DE** : l'interface et les affinités passent en allemand, ce qui sert l'ambition suisse.
