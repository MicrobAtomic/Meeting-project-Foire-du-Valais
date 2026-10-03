# Architecture et choix techniques

> Document de référence pour le jury technique et pour quiconque reprend le projet.
> Tous les chiffres ci-dessous ont été **mesurés** sur ce dépôt (MacBook, Python 3.12) le 3 octobre 2026.

## 1. Le problème, côté technique

Le Club des Affaires de la Foire du Valais compte environ 50 dirigeants. Ils paient 500 CHF par an et se retrouvent
lors de 4 à 5 événements par an, avec 80 % de présence. Leur problème n'est pas de venir : ils **ne se connaissent pas**,
restent entre eux en petits groupes, et entre deux événements la communication va dans un seul sens, de la Foire
vers eux. L'objectif est d'atteindre 100 à 200 membres dans toute la Suisse, y compris en Suisse alémanique.

Les contraintes qui ont guidé l'architecture :

| Contrainte | Conséquence technique |
|---|---|
| Personne pour animer au quotidien | Pas de fil d'actualité ni de chat. La plateforme vit au rythme des événements. |
| Membres pressés, pas tous à l'aise avec le numérique | Web app sans installation, connexion par lien magique, pages légères, tout fonctionne sans JS. |
| Annuaire visible par les membres, jamais de l'extérieur | Tout est fermé par défaut ; coordonnées visibles seulement après une vraie rencontre. |
| Budget d'environ 10 000 CHF, une seule fois | Technologie standard, maintenable par n'importe quelle agence, faible coût d'hébergement. |
| Ambition suisse (FR, DE, EN) | Internationalisation native du framework, contenus traduits en base. |
| Hackathon de 24 h en solo, jugé sur la faisabilité | Un seul framework « batteries incluses », peu de pièces mobiles, des tests automatisés. |

## 2. Vue d'ensemble

```
 Téléphone / ordinateur du membre
        │  HTTPS (HSTS, cookies Secure, CSP stricte)
        ▼
 ┌─────────────────────────────────────────────┐
 │ Django 5.2 LTS (gunicorn)                   │
 │  ├─ Espace membre   : album, QR, profil,    │
 │  │                    événements            │
 │  ├─ Espace staff    : tableau de bord,      │
 │  │                    rencontres, tables    │
 │  ├─ Admin Django    : back-office complet   │
 │  ├─ Vitrine publique + demande d'invitation │
 │  └─ services/       : matching, tables      │
 │                       tournantes, fédération│
 │                       (Python pur, testé)   │
 │  Fichiers statiques : WhiteNoise (pas de CDN)│
 └─────────────────────────────────────────────┘
        │                         │
        ▼                         ▼
   PostgreSQL               SMTP (liens et notifications, activation requise)
   (SQLite en dev)
```

- **Démo** : Render (région Frankfurt), données 100 % fictives.
- **Production visée** : hébergeur suisse (Infomaniak ou Exoscale), données en Suisse.

## 3. Les choix et leurs raisons

| Choix | Pourquoi |
|---|---|
| **Web app responsive** plutôt qu'une app native | Rien à installer pour 50 personnes pressées. Un QR code scanné avec l'appareil photo ouvre directement la bonne page. Une seule base de code, au lieu de trois (iOS, Android, web). |
| **Django 5.2 LTS** | Le framework fournit tout ce qu'il faut : authentification, sessions, protection CSRF, échappement automatique contre le XSS, ORM contre l'injection SQL, migrations, i18n et **admin**. Ça fait moins de code à écrire et moins de failles possibles. Il est supporté jusqu'en **avril 2028** et beaucoup d'agences suisses le maintiennent. |
| **Rendu serveur (templates)** plutôt qu'une SPA + API | Une seule application, aucun build JavaScript, et pas d'API exposée à sécuriser. Les pages sont rapides sur mobile, et une CSP stricte reste possible. Le seul JS (le swipe) est une amélioration : sans lui, tout fonctionne. |
| **Admin Django** pour l'équipe événements | Un back-office complet et sécurisé dès le premier jour : membres, événements, inscriptions, demandes d'invitation. Il propose recherche, filtres et actions groupées, comme « générer les rencontres » ou « régénérer un QR code ». |
| **Tailwind CSS** (CLI autonome, CSS compilé et versionné) | Un design cohérent et rapide à produire, sans Node.js ni npm en production. |
| **PostgreSQL** en production, **SQLite** en développement | Le passage de l'un à l'autre se fait avec une variable d'environnement (`DATABASE_URL`). PostgreSQL est le standard pour la robustesse et les sauvegardes. |
| **Profil `Member` séparé du `User` Django** | L'identité (authentification) est séparée du profil métier. Le staff peut ainsi exister sans profil membre, et le modèle `User` reste standard. |
| **Lien magique** (django-sesame) en plus du mot de passe | Moins de friction pour des membres peu technophiles. Le lien est signé, expire en 15 minutes et ne sert qu'une fois. |
| **QR code en SVG généré côté serveur** (segno) | Pas d'image tierce ni de service externe, et le QR reste net à toutes les tailles. |
| **vCard 3.0** générée côté serveur | Le bouton « Ajouter à mes contacts » fonctionne nativement sur iPhone comme sur Android. |
| **Algorithmes en Python pur** (`club/services/`) | Ils ne dépendent pas de Django, ce qui les rend testables unitairement et réutilisables. Ils sont déterministes : une même graine donne toujours le même résultat. |

### Alternatives écartées

| Alternative | Pourquoi non |
|---|---|
| Next.js + Supabase/Firebase | L'admin serait à coder entièrement et l'authentification côté serveur est délicate. Ça fait deux fournisseurs, et des données confiées à un cloud américain même en région européenne. En 24 h, plus de code veut dire plus de risques. |
| Plateforme communautaire sous licence (Hivebrite, Circle…) | Licence annuelle et dépendance au fournisseur, données hors de Suisse. Ces outils tournent autour d'un fil d'actualité qui resterait vide avec 50 membres sans animateur. Aucun matching ni plan de tables. |
| Apps de networking événementiel (Brella, Swapcard…) | Facturées par événement et pensées pour des rendez-vous commerciaux, c'est-à-dire la « vente forcée » que le client ne veut pas. |
| Groupe WhatsApp | Le numéro de chacun est visible par tous. Pas d'annuaire, pas de matching, aucune donnée exploitable, rien de premium. |
| App native iOS/Android | Coût doublé, publication sur les stores, téléchargement obligatoire : trop de friction pour 50 utilisateurs. |

## 4. Modèle de données

```
User (Django) 1──1 Member ──< MemberTag >── Tag            (affinités : j'adore / bof / je déteste)
                    │
                    ├──< RSVP >── Event ──1 SeatingPlan ──< SeatAssignment >── Member
                    │               │
                    │               └──< Match (event, member_a < member_b, score, raisons)
                    │
                    └──< Connection (member_a < member_b, event?, source)   ← « on s'est rencontrés »

InvitationRequest ──> Member (parrain, optionnel)
```

| Table | Rôle | Invariants garantis par la base |
|---|---|---|
| `Member` | Carte du membre : entreprise, secteur, année d'adhésion, langues, anecdote, « parle-moi de… » | `qr_token` unique (128 bits aléatoires), `referral_code` unique |
| `Tag` / `MemberTag` | Affinités, avec libellés et phrases d'accroche en FR, DE et EN | Un seul avis par membre et par tag |
| `Event` / `RSVP` | Événements et inscriptions | Une seule réponse par membre et par événement |
| `Connection` | Deux membres qui se sont rencontrés (scan du QR) | Paire unique **et** `member_a < member_b` (contrainte CHECK) : pas de doublon A-B / B-A |
| `Match` | « Tes 3 rencontres » proposées pour un événement | Paire ordonnée et unique par événement |
| `SeatingPlan` / `SeatAssignment` | Tables tournantes | Une seule place par membre et par service |
| `InvitationRequest` | Demande d'adhésion depuis la vitrine, avec parrain éventuel | — |
| `PersonalNote` | Mémo privé d'un auteur sur une cible accessible | Une note par auteur/cible, auteur différent de la cible ; aucun écran admin |
| `EmailPreferences` | Langue sur le profil, réception des annonces/relances et consentements mensuels distincts | Un jeu de préférences par profil |
| `NotificationCampaign` / `NotificationDelivery` | File persistante : bienvenue, annonce, relance, récapitulatif, accès invité | Campagne unique par portée ; destinataire unique par campagne ; réservation atomique |
| `DigestEntry` | Réservation des profils présentés au récapitulatif | Un profil présenté dans une seule campagne |
| `Substitute` | Titulaire absent et invité distinct pour un événement, statut contrôlé par service staff | Une demande par titulaire/événement ; un invité approuvé par événement ; invité différent du titulaire |

Le rang d'un membre (Membre fondateur, Pilier du Club, Membre, Nouvelle recrue) est **calculé** à partir de son année
d'adhésion. Il ne peut donc pas être falsifié par le membre.
Un profil `kind=guest` affiche « Invité », sans ancienneté d'adhésion. `guest_access_until` est calculé d'après ses
invitations approuvées (48 h après le début par défaut). Une nouvelle invitation peut réactiver le même compte.

`services/access.py` centralise le périmètre des fiches, photos, notes, contacts et scans ; `@member_required`
recontrôle l'expiration à chaque requête. `attendees(event)` fournit les personnes réellement présentes aux
rencontres proposées, tables, badges et compteurs. Ces générations verrouillent l'événement, et une modification
de présence/remplacement invalide les plans. `Connection` relie les deux personnes rencontrées, jamais le titulaire
absent. Le scan invité exige un contexte commun du jour vérifié. L'indice de fédération porte sur les membres réguliers actifs.

Les photos privées sont normalisées par Pillow puis stockées hors du répertoire public. La lecture authentifiée
est sans cache ; les parcours profil/admin nettoient les nouveaux fichiers après rollback et les anciens après commit.
Un arrêt brutal peut laisser un fichier orphelin à traiter par l'exploitant. Le volume durable de production reste à provisionner.

Les notifications sont préparées en transaction, puis traitées par une commande limitée à 50 envois par passage.
Les préférences, réponses et autorisations sont revérifiées à l'envoi. Une remise incertaine au serveur SMTP ne donne
lieu à aucune relance automatique. Les résumés mensuels sont volontaires et partiels. Voir [EXPLOITATION.md](EXPLOITATION.md)
pour les états, la reprise et les réglages : SMTP réel et ordonnanceur restent désactivés.

## 5. Sécurité

| Menace (OWASP) | Mesure | Où |
|---|---|---|
| Contrôle d'accès défaillant (A01) | **Fermé par défaut** : `LoginRequiredMiddleware` exige une connexion partout. Seules les pages publiques sont marquées `@login_not_required`. Les décorateurs `@member_required` et `@staff_required` font le reste. Un membre ne modifie que `request.member`. | `config/settings.py`, `club/decorators.py` |
| Énumération et accès indirect (IDOR) | Le QR contient un jeton aléatoire de 128 bits, pas un identifiant : impossible de « collectionner » tout le monde sans rencontrer les gens. Le jeton peut être régénéré depuis l'admin. | `Member.qr_token`, `views/member.py:scan` |
| Fuite de données personnelles | Les coordonnées (e-mail, téléphone, LinkedIn, vCard) ne sont visibles qu'après une rencontre. Un profil peut être masqué de l'album. | `member_detail`, `member_vcard` |
| CSRF / effets de bord | Toute écriture passe par un POST avec jeton CSRF. Scanner un QR (GET) n'écrit rien : on confirme d'abord. La déconnexion se fait en POST. | templates, `scan` |
| XSS (A03) | Échappement automatique des templates, **CSP stricte** (`script-src 'self'`, pas de JavaScript ni de style inline, `frame-ancestors 'none'`), contrôlée par un test. | `club/middleware.py`, `test_album.py` |
| Injection SQL / vCard | ORM paramétré. Les champs vCard sont échappés selon la RFC 6350 (testé avec une tentative d'injection). | `services/vcard.py` |
| Authentification (A07) | Mots de passe hachés (PBKDF2) et validateurs de robustesse. Lien magique à usage unique, valable 15 minutes : la demande publique répond **la même chose** pour une adresse inconnue (personne ne peut tester qui est membre), limite à un e-mail par adresse et par minute, page claire quand le lien a expiré, e-mail dans la langue du membre. Les profils fictifs hors comptes de connexion de la démo n'ont aucun mot de passe utilisable. Session de **6 mois d'inactivité** (renouvelée à chaque visite) pour ne pas obliger des dirigeants pressés à se reconnecter, cookie `HttpOnly`, `Secure`, `SameSite=Lax`. Pas de création de compte publique : on « demande une invitation » via un mini-formulaire protégé (CSRF, champ piège anti-bot, anti-doublon), sans qu'aucune donnée de membre ne soit exposée. | settings, `seed_demo` |
| Mauvaise configuration (A05) | `DEBUG` désactivé en production, `SECRET_KEY` obligatoire, HTTPS forcé, HSTS, cookies `Secure` et `HttpOnly`, `X-Frame-Options: DENY`. `check --deploy` ne signale **aucun problème**, seuls deux avertissements sont désactivés de façon justifiée (HSTS sur les sous-domaines et preload, inapplicables sur un domaine PaaS partagé). | `config/settings.py` |
| Fuite vers des tiers | Aucun CDN, aucune police externe, aucun outil d'analyse : rien ne transmet l'adresse IP d'un membre à un tiers. La CSP le garantit (`default-src 'self'`). | `club/middleware.py` |

**À ajouter avant la production** (prévu dans le budget) : double authentification pour le staff, limitation des
tentatives de connexion (django-axes), journal d'audit des actions du staff.

## 6. Protection des données (nLPD)

- **Protection des données dès la conception et par défaut** (art. 7 nLPD). L'annuaire est réservé aux membres.
  Les coordonnées ne sont partagées qu'après une rencontre, et c'est le scan du QR code qui vaut consentement.
  Chaque membre peut masquer son profil.
- **Minimisation** : pas de date de naissance ni d'adresse privée. Le minimum professionnel et ce que le membre
  choisit de partager.
- **Hébergement** : démo en Union européenne (pays adéquat au sens de la nLPD) avec des données 100 % fictives.
  Production visée en Suisse.
- **Droits des personnes** : procédure d'export/suppression à exécuter et contrôler par l'équipe dans
  [EXPLOITATION.md](EXPLOITATION.md). L'admin standard ne fournit pas un export complet. Les notes des autres auteurs
  font l'objet d'un examen par l'équipe responsable. Self-service non implémenté.

## 7. Algorithmes

### « Tes 3 rencontres » (`club/services/matching.py`)

Chaque paire d'inscrits reçoit un score :

| Critère | Points |
|---|---|
| Affinité commune (« j'adore » des deux côtés) | +3 par affinité |
| Agacement commun (« je déteste » des deux côtés) | +2 par agacement |
| Secteurs différents (complémentarité, pas de concurrents face à face) | +2 |
| Une nouvelle recrue avec un pilier (intégration) | +3 |

Deux règles sont absolues : jamais deux personnes **qui se connaissent déjà**, ni deux personnes **sans langue
commune**. L'attribution est gloutonne et équitable : tout le monde reçoit une 1ʳᵉ rencontre avant que quiconque en
reçoive une 2ᵉ. Le résultat est déterministe et de complexité O(n²).

| Inscrits | Temps mesuré |
|---|---|
| 40 | 2 ms |
| 120 | 16 ms |
| 200 | 49 ms |

### Tables tournantes (`club/services/seating.py`)

Le but est de répartir les invités à chaque service (entrée, plat, dessert) pour multiplier les nouvelles
rencontres. C'est une variante du **Social Golfer Problem**, un problème NP-difficile. On utilise une recherche locale :
on échange deux invités de tables différentes et on garde l'échange s'il ne dégrade pas le coût. On relance plusieurs
fois depuis un départ aléatoire. Le coût pénalise :

- d'être déjà assis ensemble à un service précédent (10) ;
- de n'avoir aucune langue commune (4) ;
- de se connaître déjà (3) ;
- d'être du même secteur (1).

| Cas mesuré (3 services) | Personnes déjà assises ensemble | Temps |
|---|---|---|
| 40 invités, tables de 6 | **0** | 0,15 s |
| 40 invités, tables de 8 (5 tables < 8 places : des répétitions sont mathématiquement inévitables) | 45 (tables au hasard : 62) | 0,15 s |
| 120 invités, tables de 8 | **0** | 0,44 s |
| 200 invités, tables de 8 | **0** | 0,76 s |
| Dîner de démo : 38 inscrits, tables de 6, avec langues, secteurs et connaissances | 1, et 248 nouvelles paires | < 0,2 s |

D'où le réglage par défaut de l'interface : **tables de 6**.

### Indice de fédération (`club/services/federation.py`)

C'est la part des paires de membres qui se sont déjà rencontrées (densité du graphe « qui connaît qui »). Les données
de démo partent de **15 %**. C'est l'indicateur de succès proposé au comité : il passe chaque fois que deux membres
scannent leur QR. Le tableau de bord staff liste aussi les **membres isolés** (2 rencontres ou moins) pour que l'équipe
puisse les présenter aux autres.

## 8. Scalabilité

- **Technique** : l'application est sans état (on ajoute des workers gunicorn ou des instances derrière un load
  balancer). Les contraintes uniques créent les index utiles, et les requêtes N+1 sont évitées
  (`select_related`, `prefetch_related`). Les algorithmes tiennent 200 inscrits en moins d'une seconde. Jusqu'à
  quelques milliers de membres, aucun cache ni file de tâches n'est nécessaire. Au-delà, on lancerait le calcul en
  tâche de fond.
- **Langues** : le français, l'allemand et l'anglais sont gérés par l'i18n de Django (interface) et par des champs
  traduits en base (affinités, phrases d'accroche). Ajouter l'italien revient à créer un fichier et trois colonnes.
- **Métier** : le même code peut servir d'autres clubs ou d'autres foires en ajoutant un modèle `Club`
  (marque blanche). C'est la piste V3.

## 9. Exploitation et coûts (ordres de grandeur)

| Poste | Estimation |
|---|---|
| Hébergement suisse (petit serveur + PostgreSQL managé) | de l'ordre de 10 à 30 CHF/mois |
| E-mails transactionnels, au volume d'un club | gratuit à quelques CHF/mois |
| Nom de domaine `.ch` | environ 15 CHF/an |
| **Total de fonctionnement** | **moins de 500 CHF/an, soit moins de 2 % des cotisations** (50 × 500 CHF) |
| Mise en production depuis ce MVP (hébergement suisse, e-mails, charte graphique, import des membres, double authentification staff, politique de confidentialité, formation) | environ 6 à 8 jours de développement, dans l'enveloppe de 10 000 CHF |

- **Au quotidien**, l'équipe événements gère tout depuis l'admin : membres, événements, génération des rencontres
  et des tables. Aucun développeur n'est nécessaire.
- **Maintenance technique** : une mise à jour de sécurité Django par mois (`pip install -U "Django>=5.2,<5.3"`),
  des sauvegardes quotidiennes de la base, une surveillance de disponibilité.

## 10. Qualité

- **262 tests automatisés** (`env DEBUG=1 python manage.py test club`, environ 70 s).
  Recette des améliorations sur SQLite (6 cas de concurrence réservés à PostgreSQL) et PostgreSQL dédié :
  - les algorithmes (rencontres, tables tournantes) et leurs règles absolues ;
  - la **matrice d'accès** : chaque route est classée (publique, membre, staff) et testée anonyme / membre / staff ; une nouvelle
    route non classée fait échouer la suite ; les actions qui modifient des données refusent le GET ;
  - la CSP stricte sur chaque page, le CSRF dans chaque formulaire des templates, l'absence de script ou de style en ligne ;
  - le QR, la vCard, le lien de connexion (usage unique, expiration, même réponse pour une adresse inconnue, un envoi par minute),
    le formulaire public (champ piège, doublons, parrainage), les badges ;
  - les traductions : catalogues complets, mêmes textes dans les trois langues, et **aucune phrase française sur les pages
    allemandes et anglaises** ;
  - la reproductibilité des données de démo après chaque réinitialisation.
  - la confidentialité des notes/photos, les rollbacks des uploads dans le profil et l'admin ;
  - les invités actifs/expirés, l'identité des rencontres, les refus sur URL directe et les liens magiques ;
  - les états de notifications, relances, consentements et désabonnement, ainsi que six cas de concurrence PostgreSQL.
- **Mode production vérifié** : `python manage.py check --deploy` sans alerte, `build.sh` (fichiers statiques versionnés,
  migrations, données de démo si la base est vide) sur PostgreSQL, gunicorn derrière un proxy HTTPS : redirection HTTPS, en-têtes
  de sécurité, cookies `Secure`, CSS et JS en cache immuable, hôte invalide refusé.
- **Recette navigateur des améliorations** : 90 pages parcourues à 390 px et 1 280 px, en FR/DE/EN, avec membre,
  invité, staff sans profil et anonyme. Aucun débordement, image cassée, erreur JavaScript/CSP ni appel externe détecté.
  Badges générés en PDF A4. Voir [RECETTE_AMELIORATIONS.md](RECETTE_AMELIORATIONS.md) pour les preuves et limites.
- **Scénario du pitch rejoué automatiquement** de bout en bout (vitrine, rencontres, album, scan du QR, vCard, tableau de bord,
  plan de tables en direct, bascule en allemand).
- Les données de démo sont reproductibles (graine fixe, identifiants d'événements fixes). La commande `seed_demo` **vérifie
  elle-même** le scénario du pitch : Camille, nouvelle recrue, doit se voir présenter Lukas, pilier du Club.

## 11. Feuille de route

| Version | Contenu |
|---|---|
| **V1 — hackathon** | Album de cartes, QR et vCard, profil et affinités, événements avec rencontres et tables tournantes, tableau de bord staff, vitrine et parrainage, FR/DE/EN |
| **Améliorations livrées** | Portraits de démo, photos privées (production désactivée), notes personnelles, cotisation configurable/facture manuelle, acceptation des invitations, préférences et campagnes email (envois désactivés), récapitulatif mensuel volontaire, remplaçants avec identité propre et accès temporaire |
| **V1.1 — production** | Hébergement suisse, **connexion par lien : étape de confirmation par bouton** (certaines passerelles de sécurité e-mail ouvrent les liens à l'avance et consomment le lien à usage unique), domaine, e-mails, charte graphique du Club, import des membres existants (CSV), consentement et politique de confidentialité, export et suppression en libre-service, double authentification staff |
| **V2** | Bourse « je cherche / je propose », groupes de codéveloppement, paiement des cotisations (TWINT, QR-facture), photos d'événements |
| **V3** | Plusieurs clubs sur la même plateforme (marque blanche pour d'autres associations ou foires) |
