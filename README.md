# Club des Affaires — Foire du Valais

**Plus jamais d'inconnus au Club.** Une web app réservée aux membres du Club des Affaires, qui vit au rythme des
événements :

- **Avant** : l'album de cartes des membres, les affinités (swipe), « tes 3 rencontres » pour la prochaine soirée.
- **Pendant** : on scanne le QR code de quelqu'un pour ajouter sa carte et ses coordonnées ; on change de table à
  chaque service ; les badges sont imprimés par l'équipe.
- **Après** : « ton album 18 / 49 » pour le membre, l'indice de fédération pour le comité.

Projet réalisé pour le hackathon Foire du Valais (3–4 octobre 2026).
Pitch et démo : [docs/PITCH.md](docs/PITCH.md) · Choix techniques : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ·
Plan de réalisation : [docs/PLAN.md](docs/PLAN.md)

Suivi des améliorations livrées (photos, remplaçants, notes privées, emails et cotisation) :
[docs/PLAN_AMELIORATIONS.md](docs/PLAN_AMELIORATIONS.md).
Recette : [docs/RECETTE_AMELIORATIONS.md](docs/RECETTE_AMELIORATIONS.md) ·
Exploitation : [docs/EXPLOITATION.md](docs/EXPLOITATION.md).

## Ce que fait l'application

| Pour… | Fonctionnalités |
|---|---|
| **Les membres** | album de cartes avec recherche et filtres · fiche de chaque membre, points communs · coordonnées et vCard débloquées après une vraie rencontre (scan du QR) · profil et affinités, swipe façon « cartes » · événements : réponse en un clic, **tes rencontres**, ton placement à table, qui vient · parrainage : lien personnel, QR, offre · connexion par mot de passe **ou par lien reçu par e-mail** · interface en français, allemand et anglais |
| **L'équipe événements** | tableau de bord (indice de fédération, membres isolés, demandes d'invitation) · préparation d'un événement : génération des rencontres, **plan de tables tournantes**, badges A4 avec QR code · back-office Django complet (membres, événements, inscriptions, demandes) |
| **Les futurs membres** | vitrine publique sans aucun nom de membre · formulaire « Demander une invitation » (avec ou sans lien de parrainage) |

Les améliorations ajoutent les portraits de démo avec sources/licences, l'upload de photo protégé avec aperçu avant enregistrement,
les notes privées propres à chaque auteur, la langue des communications et l'acceptation d'une invitation avec création du compte.
Le choix de langue est visible dans l'admin pour les emails et les courriers papier ; les options email sont repliées dans le profil.
Les photos JPEG/PNG/WebP/HEIC/HEIF/AVIF sont orientées, recadrées et compressées automatiquement en JPEG ;
les fichiers de téléphone sont acceptés jusqu’à 20 Mio et 50 mégapixels. Les remplaçants validés ont une identité et un QR distincts : leurs rencontres restent les leurs, leur accès expire
et ils ne gonflent pas les compteurs de cotisants. La cotisation configurable est affichée sur la demande d'invitation
(500 CHF par défaut) ; les factures restent gérées manuellement. L'offre commerciale de parrainage est masquée par défaut.

Annoncer un événement prépare des emails et des relances pour les membres sans réponse. Le récapitulatif mensuel
montre des aperçus de nouveaux profils avec consentement et lien vers le site. **Les envois automatiques sont désactivés**
(`NOTIFICATIONS_ENABLED=0`) ; aucun cron n'est installé. L'upload de photos en production attend un stockage privé
persistant (`PROFILE_PHOTO_UPLOADS_ENABLED=0` par défaut en production). Voir l'exploitation avant activation.

## Lancer le projet en 5 minutes (macOS)

```bash
# 1. Outils (une seule fois)
brew install uv

# 2. Python 3.12 et dépendances
cd ~/Meeting-project-Foire-du-Valais
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
export DEBUG=1  # environnement local ; nécessaire si l'IDE définit une autre valeur

# 3. Base de données et données de démo (50 membres fictifs)
python manage.py migrate
python manage.py seed_demo  # première installation sur une base vide

# 4. Démarrer
python manage.py runserver
```

Ouvre ensuite http://127.0.0.1:8000. Le mot de passe des trois comptes de connexion ci-dessous est `club-demo-2026`
(ou la valeur `DEMO_PASSWORD` si définie). Les autres profils fictifs n'ont pas de mot de passe utilisable.

| Compte | Rôle |
|---|---|
| `camille.rey@example.com` | Nouvelle recrue, 2 cartes dans son album : **le compte du pitch** |
| `lukas.imboden@example.com` | Pilier du Club depuis 2017 (parle français et allemand) |
| `equipe@example.com` | Équipe événements (staff) : `/staff/` et `/admin/` |

La fois suivante : `cd ~/Meeting-project-Foire-du-Valais && source .venv/bin/activate && env DEBUG=1 python manage.py migrate && env DEBUG=1 python manage.py runserver`
(`migrate` applique les éventuelles évolutions de la base après une mise à jour du code, sans rien effacer).
`python manage.py seed_demo --reset` remet les données de démo à zéro (les comptes sont recréés : tu devras te reconnecter).
Une erreur `no such column: club_member.demo_photo_key` après mise à jour se corrige avec `migrate`, après sauvegarde,
sans réinitialiser la démo. La procédure est dans [EXPLOITATION.md](docs/EXPLOITATION.md).
Le CSS est déjà compilé (`static/css/app.css`) : le binaire Tailwind n'est utile que pour modifier le design
(voir [CLAUDE.md](CLAUDE.md)).

## Parcourir la démo (2 minutes)

1. **Vitrine** : http://127.0.0.1:8000 (déconnecté) → « Demander une invitation » : aucun nom de membre n'est visible.
2. **Camille** (téléphone) : l'accueil montre « 2 / 49 cartes » et le prochain dîner, avec **ses 3 rencontres**, dont
   Lukas (Petite Arvine, ski de rando, trail, et les réunions du lundi matin en commun).
3. **L'album** : rangs (fondateur doré, nouvelle recrue verte), filtre « Germanophones ».
4. **La rencontre** : connectée en Camille, ouvre le QR code de Lukas (ci-dessous) → « Ajouter Lukas à mon album » →
   ses coordonnées et sa vCard se débloquent, l'album passe à 3 / 49 et le Club se rapproche de son prochain palier.
5. **Le staff** (`equipe@example.com`) : tableau de bord (rencontres +1, membres isolés, demande d'invitation) →
   « Dîner d'automne » → « Préparer » → **plan de tables généré en direct** (38 invités, 3 services, environ 1 répétition).
6. **Bascule en allemand** (FR · DE · EN en haut de page) : interface, dates, affinités et phrases d'accroche.

Le déroulé complet, avec le texte à dire, est dans [docs/PITCH.md](docs/PITCH.md).

### Le QR code de Lukas, pour jouer la rencontre

<img src="docs/demo/qr-lukas.svg" alt="QR code de Lukas Imboden (démo)" width="160">

- **En local** (connecté·e en Camille) : http://127.0.0.1:8000/m/demo-lukas/
- **En ligne** : `https://<adresse-du-site>/m/demo-lukas/`. Pour que l'image ci-dessus se scanne avec un téléphone,
  régénère-la avec l'adresse publique : `python manage.py demo_qr https://<adresse-du-site>` (elle remplace
  `docs/demo/qr-lukas.svg`).

Ce lien ne change pas d'une remise à zéro à l'autre : dans les données de démo, le QR code de Lukas est fixe
(celui des autres membres est aléatoire).

**Refaire la manipulation** : `python manage.py demo_reset` remet Camille à son point de départ (2 cartes, grilles de
bingo vierges) et rend à Lukas le QR code ci-dessus. Le reste des données ne bouge pas, personne n'est déconnecté.
Sur le site en ligne, sans terminal : connecte-toi en équipe → Administration → Rencontres → cherche « Imboden » →
coche la rencontre Camille Rey – Lukas Imboden → action « Supprimer ».

**Bonus : scanner avec ton vrai téléphone.** Laisse `runserver` tourner et, dans un 2ᵉ terminal :

```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:8000
```

Ouvre l'URL `https://….trycloudflare.com` affichée : le QR code affiché via cette URL se scanne avec l'appareil photo.
Pour le QR code de Lukas du README : `python manage.py demo_qr https://….trycloudflare.com`.

## Démo en ligne

URL : *à renseigner une fois le déploiement fait (tâche 2.4 du plan).*

1. Sur https://dashboard.render.com : **New → Blueprint**, autoriser le dépôt GitHub (privé) et le sélectionner.
2. Render lit `render.yaml` (un service web et une base PostgreSQL gratuits, à Frankfurt). Saisir une valeur pour
   `DEMO_PASSWORD` (le mot de passe de démo), puis **Apply**. Premier build : environ 5 minutes.
3. Chaque `git push` sur `main` redéploie automatiquement. Les données de démo ne sont créées que si la base est vide.

⚠️ L'offre gratuite se met en veille après 15 minutes : **ouvrir l'URL 2 minutes avant le pitch**.
Plan B : le tunnel `cloudflared` ci-dessus.

## Tests

```bash
env DEBUG=1 python manage.py test club    # 270 tests, environ 70 s ; 6 cas de concurrence réservés à PostgreSQL
```

Ils couvrent les algorithmes, la **matrice d'accès** (qui peut ouvrir quelle page : toute nouvelle route doit être
classée), la CSP stricte, le CSRF, les formulaires, le lien de connexion, les badges, la reproductibilité des données
de démo et les traductions (aucune phrase française sur les pages allemandes et anglaises). La suite passe sur SQLite
et sur PostgreSQL (`env DEBUG=1 DATABASE_URL=postgresql://… python manage.py test club`), sur une base de test dédiée.
Les tests incluent confidentialité des notes/photos, expiration des sessions invitées, validations concurrentes,
relances, consentements mensuels et désabonnement. La recette du 3 octobre 2026 est documentée avec ses limites.

## E-mails (lien de connexion)

Un membre peut se connecter **sans mot de passe** : « Recevoir un lien de connexion par e-mail » sur la page de connexion, ou
l'équipe lui envoie un lien (admin → Membres → cocher → action « Envoyer un lien de connexion »). Le lien est valable 15 minutes
et ne sert qu'une fois ; l'e-mail est rédigé dans la langue du membre.

En local, les e-mails s'**affichent dans la console** du serveur. Pour envoyer de vrais e-mails (compte SMTP Brevo, Mailjet,
Infomaniak…), définir ces variables d'environnement (sur Render : onglet *Environment*) :

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.exemple.ch   EMAIL_PORT=587   EMAIL_USE_TLS=1
EMAIL_HOST_USER=…            EMAIL_HOST_PASSWORD=…
DEFAULT_FROM_EMAIL="Club des Affaires <club@exemple.ch>"
```

Le mode démo (`DEMO_MODE=1` par défaut) bloque les backends réels, y compris pour les liens de connexion.
Après configuration et essai autorisé, passer à `DEMO_MODE=0`. L'automatisation des campagnes exige en plus
`NOTIFICATIONS_ENABLED=1` et un ordonnanceur ; la procédure est dans [EXPLOITATION.md](docs/EXPLOITATION.md).

## Traductions (FR · DE · EN)

L'interface suit la langue du navigateur (ou le choix FR / DE / EN en haut de page, mémorisé). Les catalogues sont dans
`locale/<langue>/LC_MESSAGES/django.po`, les fichiers compilés `.mo` sont commités (l'hébergeur n'a pas gettext).
Après avoir ajouté ou modifié un texte (`{% translate %}` dans un template, `gettext` en Python) :

```bash
export PATH="$(brew --prefix gettext)/bin:$PATH"
python manage.py makemessages -l fr -l de -l en --no-wrap --no-location --ignore=.venv --ignore=staticfiles --ignore="club/tests/*"
# traduire les msgstr vides de locale/de/... et locale/en/... (allemand suisse : « ss », tutoiement), copier la source dans locale/fr/...
python manage.py compilemessages --ignore=.venv --ignore=.claude
python manage.py test club.tests.test_i18n     # aucun texte non traduit, aucune phrase française sur les pages DE/EN
```

## Sécurité en bref

Fermé par défaut (toute page demande une connexion, sauf la vitrine, la connexion et la demande d'invitation) · coordonnées
visibles seulement après une rencontre · CSP stricte (aucun script ni style en ligne, aucun service tiers) · CSRF sur tous
les formulaires · HTTPS, HSTS et cookies sécurisés en production · liens de connexion à usage unique · même réponse pour une
adresse inconnue. Détails et mesures : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Structure

```
config/                  réglages Django (sécurité, i18n, base de données par variable d'environnement), routes
club/models.py           membres, affinités, événements, inscriptions, rencontres, plans de tables, demandes d'invitation
club/services/           logique métier testée : matching, tables tournantes, fédération, vCard, QR, e-mails de connexion…
club/views/              public · member · events · staff
club/admin.py            back-office de l'équipe événements
club/management/         seed_demo : données de démo fictives et reproductibles
templates/ static/       pages (FR/DE/EN), JS sans dépendance (swipe, copier, imprimer), CSS compilé
assets/css/input.css     sources Tailwind
locale/                  traductions fr / de / en (.po et .mo)
docs/                    PITCH.md · ARCHITECTURE.md · PLAN.md
render.yaml build.sh     déploiement Render
```
