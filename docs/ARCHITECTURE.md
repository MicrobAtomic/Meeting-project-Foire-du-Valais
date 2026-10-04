# Les choix techniques

> Pour le jury technique et pour quiconque reprend le projet. Les chiffres ont été mesurés sur ce dépôt (MacBook,
> Python 3.12) les 3 et 4 octobre 2026.

Mon fil rouge : **peu de pièces mobiles, sécurité et confidentialité par défaut, et des choix que je peux expliquer.**
Je préfère une technologie éprouvée à une technologie à la mode.

## 1. Les contraintes qui ont décidé

| Contrainte | Conséquence technique |
|---|---|
| Personne pour animer au quotidien | Pas de fil d'actualité ni de messagerie : la plateforme vit au rythme des événements |
| Membres pressés, pas tous à l'aise avec le numérique | Web app sans installation, connexion par lien reçu par e-mail, pages légères, tout fonctionne sans JavaScript |
| Annuaire visible des membres, jamais de l'extérieur | Fermé par défaut ; coordonnées visibles seulement après une vraie rencontre |
| Ambition suisse (FR, DE, EN) | Traductions natives du framework et contenus traduits en base |
| Coût d'exploitation à garder bas | Technologie standard, maintenable par n'importe quelle agence, hébergement bon marché |
| Hackathon de 24 h, seul, jugé sur la faisabilité | Un seul framework « piles incluses », des tests automatisés partout |

## 2. Vue d'ensemble

```
 Téléphone ou ordinateur
        │  HTTPS (HSTS, cookies sécurisés, CSP stricte)
        ▼
 ┌──────────────────────────────────────────────────────────┐
 │ Django 5.2 LTS (gunicorn)                                │
 │  ├─ vitrine publique + demande d'invitation              │
 │  ├─ espace membre : accueil, album, profil, événements,  │
 │  │                  bingo, scan du QR, parrainage        │
 │  ├─ espace équipe : tableau de bord, préparation         │
 │  ├─ administration Django guidée                         │
 │  └─ services/ : matching, tables tournantes, bingo,      │
 │                fédération et paliers, notifications      │
 │  Fichiers statiques servis par l'application (WhiteNoise)│
 └──────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
   PostgreSQL (SQLite en dév.)    SMTP (e-mails, à activer)
```

Démo : Render (Frankfurt), données 100 % fictives. Production visée : un hébergeur suisse.

## 3. Mes choix, les options écartées et pourquoi

### La forme : une web app

| Option | Pourquoi je l'ai écartée |
|---|---|
| App native iOS + Android | Deux bases de code de plus, publication sur les stores, téléchargement obligatoire pour 50 dirigeants pressés. Le seul vrai gain, les notifications push, ne justifie pas ce coût. |
| Plateforme communautaire (Hivebrite, Circle, Mighty Networks) | Licence annuelle, données hors de Suisse, tout repose sur un fil d'actualité à animer. Ni matching, ni plan de tables, ni QR qui prouve la rencontre. |
| App d'événementiel (Brella, Swapcard, Grip) | Facturée par événement et pensée pour les rendez-vous commerciaux : le « business forcé » que le client refuse. |
| Groupe WhatsApp ou LinkedIn | Chacun voit le numéro de tous, pas d'annuaire ni de matching, rien de premium. |

Une web app s'ouvre directement depuis l'appareil photo quand on scanne un QR code : rien à installer.

### Le framework : Django 5.2 LTS

Il me donne d'emblée **une administration complète et sécurisée**, l'authentification, la protection CSRF,
l'échappement contre le XSS, l'ORM, les migrations et les traductions. C'est moins de code à écrire et moins de failles.
La version est supportée jusqu'en avril 2028, et beaucoup d'agences suisses savent la maintenir.

| Option | Pourquoi je l'ai écartée |
|---|---|
| Next.js + Supabase ou Firebase | Administration à coder entièrement ; sécurité reposant sur des règles d'accès en base faciles à mal écrire ; deux fournisseurs ; données chez un acteur américain même en région européenne. |
| Ruby on Rails, Laravel | Sérieux et « piles incluses », mais sans administration générée aussi complète, et Python reste le meilleur choix pour les algorithmes. |
| FastAPI, Node / Express | Pensés pour des API : il faudrait ajouter un front, une administration et l'authentification, donc plus de pièces et plus de risques. |

### L'affichage : des pages générées par le serveur

Une seule application, aucune API exposée à sécuriser, des pages légères sur mobile. Le peu de JavaScript (swipe des
affinités, copier, imprimer, aperçu photo) est un plus : sans lui, tout fonctionne. C'est ce qui me permet une CSP
stricte, sans aucun script ni style écrit dans les pages.

| Option | Pourquoi je l'ai écartée |
|---|---|
| Application d'une seule page (React, Vue) + API | Logique en double, API à protéger (jetons, CORS), JavaScript lourd sur mobile. |
| HTMX | Bon compromis, mais une dépendance pour un besoin absent : aucune page n'a besoin de se mettre à jour par morceaux. |

Le design utilise **Tailwind**, compilé une fois et versionné : aucun Node.js en production. Bootstrap aurait donné un
rendu générique, peu premium.

### Les données : PostgreSQL

Les données sont très relationnelles, et je laisse la base garantir les règles : une rencontre A-B n'existe qu'une
fois, une personne ne remplit qu'une case par grille de bingo, une seule réponse par membre et par événement. Une base
NoSQL (MongoDB, Firestore) aurait laissé ces garanties au code, où un bug les casse. SQLite évite toute installation en
développement, et la suite de tests passe sur les deux.

### La connexion

| Mon choix | Options écartées |
|---|---|
| Mot de passe **ou** lien reçu par e-mail (15 minutes, usage unique), session de 6 mois renouvelée à chaque visite | Connexion LinkedIn ou Google : tout le monde n'a pas LinkedIn, et les données partent chez lui. Auth0 ou Clerk : un fournisseur et un coût de plus. Passkeys : excellents mais liés à un appareil, à garder pour plus tard. |

Une limite connue : certains filtres anti-spam ouvrent les liens à l'avance et « consomment » le lien à usage unique.
La correction prévue est un bouton de confirmation avant la connexion.

### Le QR code et les contacts

- Le QR contient un **jeton aléatoire de 128 bits**, pas l'identifiant du membre : impossible de deviner les codes
  des autres pour « collectionner » tout le Club sans rencontrer personne.
- Il est **généré sur le serveur** (SVG), plutôt que par un service QR en ligne qui pourrait suivre les scans.
- Le scan ouvre une **page de confirmation** ; la rencontre s'enregistre seulement à la validation. Ouvrir un lien ne
  modifie jamais rien.
- Les coordonnées partent en **vCard**, qui marche sur iPhone comme sur Android, sans passer par LinkedIn.
- Des badges NFC auraient été plus chics, mais tous les téléphones ne les lisent pas ; un badge papier coûte quelques
  centimes.

### Les langues, les e-mails, les photos

- **Langues** : les traductions de Django pour l'interface, un champ par langue pour les contenus (affinités, thèmes,
  événements), avec le français comme référence. J'ai écarté la traduction automatique (coût, données envoyées à un
  tiers, qualité incertaine pour l'allemand de Suisse).
- **E-mails** : un simple SMTP configurable, valable chez n'importe quel fournisseur. Les envois passent par une file
  d'attente en base, traitée par une commande planifiée. Celery et Redis auraient ajouté de l'infrastructure pour
  quelques dizaines d'e-mails par mois.
- **Photos** : redimensionnées, orientées et débarrassées de leurs métadonnées par Pillow, stockées hors du dossier
  public et servies seulement à ceux qui ont le droit de voir la fiche. Pas de stockage S3 : un tiers de plus, hors de
  Suisse.

### L'hébergement

Démo sur Render, gratuit et redéployé à chaque `git push` (limite : il se met en veille après 15 minutes). En
production, un hébergeur suisse pour garder les données en Suisse. J'ai écarté AWS, GCP et Azure (complexes,
juridiction américaine), Vercel (pensé pour d'autres frameworks) et un serveur à gérer soi-même (mises à jour et
sauvegardes à la charge du Club).

## 4. Modèle de données

```
User 1──1 Member ──< MemberTag >── Tag                      affinités : j'adore / bof / je déteste
             │   ──< MemberExpertise >── Expertise          je peux aider sur / je cherche
             ├──< RSVP >── Event ──1 SeatingPlan ──< SeatAssignment
             │               ├──< Match                     « tes 3 rencontres », avec leurs raisons
             │               ├──< BingoSquare               grilles du bingo
             │               └──< Substitute                remplaçants d'un soir
             └──< Connection                                « on s'est rencontrés » (scan du QR)

InvitationRequest ──> Member (parrain)      PersonalNote · EmailPreferences · NotificationCampaign · DigestEntry
```

| Table | Rôle | Règle garantie par la base |
|---|---|---|
| `Member` | La carte du membre | Jeton QR unique (128 bits aléatoires), code de parrainage unique |
| `Tag`, `Expertise` | Affinités et thèmes d'entraide, en FR, DE et EN | Un seul avis par membre et par sujet |
| `Event`, `RSVP` | Événements (textes en trois langues, animations) et réponses | Une réponse par membre et par événement |
| `Connection` | Deux membres qui se sont rencontrés | Paire unique, toujours rangée dans le même ordre (contrainte CHECK) |
| `Match` | Les rencontres proposées, avec leurs raisons et synergies | Paire unique par événement |
| `SeatingPlan`, `SeatAssignment` | Tables tournantes | Une place par personne et par service |
| `BingoSquare` | Une case de bingo | Une personne ne remplit qu'une case par grille |
| `Substitute` | Un remplaçant d'un soir, avec son propre accès temporaire | Une demande par membre et par événement |
| `InvitationRequest` | Une demande d'adhésion, avec parrain éventuel | — |
| `PersonalNote` | Une note privée sur une personne rencontrée | Visible de son seul auteur |
| `NotificationCampaign` | Annonces, relances, récapitulatif mensuel, accès | Un destinataire une seule fois par campagne |

Le rang d'un membre (fondateur, pilier, membre, nouvelle recrue) est **calculé** à partir de son année d'entrée : il ne
peut pas être falsifié. Un remplaçant est un compte invité dont l'accès expire 48 h après le début de la soirée. Le module
`services/access.py` centralise qui peut voir quelle fiche, photo, note ou coordonnée.

## 5. Sécurité

| Menace (OWASP) | Ce que j'ai mis en place |
|---|---|
| Contrôle d'accès défaillant | **Fermé par défaut** : toute page exige une connexion, sauf la vitrine, la connexion et la demande d'invitation. Une **matrice d'accès testée** oblige à classer chaque nouvelle page : un oubli fait échouer la suite. Un membre ne modifie que ses propres données. |
| Énumération (IDOR) | QR à jeton aléatoire ; le jeton se régénère depuis l'administration. |
| Fuite de données | Coordonnées, vCard et photos visibles seulement après une rencontre ; une carte peut être masquée de l'album. |
| CSRF et effets de bord | Toute écriture passe par un formulaire protégé ; ouvrir un lien ne modifie jamais rien. |
| XSS | Échappement automatique et **CSP stricte** (aucun script ni style en ligne, aucun cadre), vérifiée par un test. |
| Injection | ORM paramétré ; champs vCard échappés selon la RFC 6350. |
| Authentification | Mots de passe hachés ; liens de connexion à usage unique ; même réponse pour une adresse inconnue (impossible de tester qui est membre) ; un e-mail par minute au plus ; pas d'inscription libre, seulement une demande d'invitation protégée contre les robots. |
| Mauvaise configuration | Mode debug coupé et clé secrète obligatoire en production, HTTPS forcé, HSTS, cookies sécurisés ; `check --deploy` sans alerte. |
| Fuite vers des tiers | Aucun CDN, aucune police externe, aucun outil d'analyse : la CSP l'interdit. |

À ajouter avant la production : la double authentification pour l'équipe, la limitation des tentatives de connexion,
un journal des actions de l'équipe.

## 6. Protection des données (nLPD)

- **Par défaut** : l'annuaire est réservé aux membres ; les coordonnées ne sont partagées qu'après une rencontre, et
  c'est le scan du QR qui vaut consentement ; chacun peut masquer sa carte.
- **Minimisation** : ni date de naissance ni adresse privée, seulement le profil professionnel et ce que le membre
  choisit de partager ; le récapitulatif mensuel ne présente que les membres qui l'acceptent.
- **Hébergement** : démo en Europe avec des données fictives, production visée en Suisse.
- **Droits des personnes** : export et suppression traités par l'équipe (procédure dans
  [EXPLOITATION](EXPLOITATION.md)) ; le libre-service est prévu.

## 7. Les algorithmes

### « Tes 3 rencontres » (`services/matching.py`)

| Critère | Points |
|---|---|
| Une passion commune | +3 par passion |
| Un agacement commun | +2 par agacement |
| Des secteurs différents (pas de concurrents face à face) | +2 |
| Une nouvelle recrue avec un pilier du Club | +3 |
| Une synergie : l'un peut aider sur ce que l'autre cherche (deux au plus) | +4 |

Deux règles absolues : jamais deux personnes qui se connaissent déjà, jamais deux personnes sans langue commune.
L'attribution est gloutonne et équitable (tout le monde reçoit une 1ʳᵉ rencontre avant qu'un autre en reçoive une 2ᵉ),
déterministe : 49 ms pour 200 inscrits.

*Options écartées* : une IA ou des embeddings (aucune donnée pour l'entraîner, un résultat opaque : « pourquoi lui ? »,
excessif pour 50 personnes) ; un couplage optimal pondéré (un peu meilleur sur le papier, mais plus complexe, alors que
le glouton donne déjà la raison de chaque rencontre).

### Les tables tournantes (`services/seating.py`)

Répartir les invités à chaque service pour multiplier les nouvelles rencontres est une variante du *Social Golfer
Problem*, un problème combinatoire réputé difficile. J'utilise une recherche locale avec redémarrages : j'échange deux
invités de tables différentes et je garde l'échange s'il n'aggrave pas le coût (déjà assis ensemble : 10 ; aucune
langue commune : 4 ; se connaissent déjà : 3 ; même secteur : 1).

| Cas mesuré (3 services) | Répétitions | Temps |
|---|---|---|
| 40 invités, tables de 6 | 0 | 0,15 s |
| 200 invités, tables de 8 | 0 | 0,76 s |
| Dîner de démo : 38 invités, tables de 6, avec langues, secteurs et connaissances | 1, pour environ 250 nouvelles paires | < 0,2 s |

*Options écartées* : un solveur exact (programmation par contraintes) : grosse dépendance, lent, inutile à cette
taille ; le hasard : des répétitions garanties.

### Le bingo des rencontres (`services/bingo.py`)

Une grille 3 × 3 « Trouve quelqu'un qui… » par invité, créée à la première ouverture puis figée. Les cases viennent des
**autres personnes attendues ce soir-là**. Elles poussent d'abord vers les « 3 rencontres » du joueur, puis vers des gens
qu'il n'a jamais rencontrés, avec de la variété. Un **couplage biparti** (chemins augmentants) vérifie qu'un carton plein
reste possible avec des personnes toutes différentes. Au scan, c'est la case la plus rare qui se coche ; le joker du
centre ne vaut que pour une vraie nouvelle rencontre. *Options écartées* : des grilles au hasard (des cases impossibles),
une grille générique (elle ne pousse pas vers les bonnes personnes).

### L'indice de fédération et les paliers (`services/federation.py`, `services/milestones.py`)

L'indice est la part des paires de membres qui se sont déjà rencontrées : 15 % dans la démo. Il mesure l'objectif du
Club, que les membres se connaissent, et pas l'usage de l'application (connexions, pages vues). Des paliers à 10, 20,
35, 50, 75 et 100 % portent chacun une récompense collective, à valider par le comité : une tournée de Petite Arvine à
20 %, une raclette à 35 %… Le tableau de bord liste aussi les membres isolés, que l'équipe peut présenter aux autres.

## 8. Montée en charge

L'application est sans état : on ajoute des processus derrière un répartiteur. Les contraintes créent les index utiles
et les pages évitent les requêtes en cascade. 200 inscrits se calculent en moins d'une seconde ; au-delà de quelques
milliers de membres, je déporterais les calculs en tâche de fond. Ajouter l'italien revient à créer un fichier de
traduction et quelques colonnes. Plus tard, si la demande existe, la même plateforme pourrait servir d'autres clubs.

## 9. Coûts

| Poste | Estimation |
|---|---|
| Hébergement suisse : application + PostgreSQL, avec une marge | 20 à 35 CHF par mois |
| E-mails transactionnels, au volume d'un club | gratuit à quelques CHF par mois |
| Nom de domaine `.ch` | 15 à 20 CHF par an |
| Certificat HTTPS | gratuit |
| **Fonctionnement** | **environ 30 CHF par mois, soit 300 à 450 CHF par an** |
| Mise en place, hors développement | environ 20 CHF (le nom de domaine) |
| Développement supplémentaire | seulement si le Club veut de nouvelles fonctionnalités, sur devis |

Tarifs relevés le 4 octobre 2026 : [Infomaniak Jelastic Cloud](https://www.infomaniak.com/en/hosting/dedicated-and-cloud-servers/jelastic-cloud)
démarre à 6,31 CHF par mois pour la plus petite configuration ; [Exoscale](https://www.exoscale.com/pricing/) est une
alternative suisse plus chère (sa base PostgreSQL seule coûte environ 42 CHF par mois). Au quotidien, l'équipe gère tout
depuis l'administration ; la maintenance technique se résume à une mise à jour de sécurité de Django par mois et aux
sauvegardes.

## 10. Qualité

- **403 tests automatisés** (`env DEBUG=1 python manage.py test club`), verts sur SQLite et sur PostgreSQL :
  - les algorithmes et leurs règles absolues ;
  - la matrice d'accès : chaque page est testée en anonyme, membre et équipe, et les actions qui modifient des données
    refusent les simples liens ;
  - la CSP sur chaque page, la protection CSRF dans chaque formulaire ;
  - le QR, la vCard, les liens de connexion, la demande d'invitation, le parrainage, les badges ;
  - les traductions : catalogues complets, et aucune phrase française sur les pages allemandes et anglaises ;
  - la confidentialité des notes et des photos, l'expiration des accès invités, les notifications et les désabonnements ;
  - six cas de concurrence (deux requêtes simultanées), exécutés sur PostgreSQL.
- **Mode production vérifié** : `check --deploy` sans alerte, déploiement sur PostgreSQL, redirection HTTPS, en-têtes de
  sécurité, fichiers statiques en cache.
- **Contrôle visuel automatique** : 60 pages par langue, en FR, DE et EN, au format téléphone et ordinateur ; aucun
  débordement, aucune erreur de console, de réseau ou de sécurité.
- **Données de démo reproductibles** : `seed_demo` vérifie elle-même le scénario de la démo (Camille doit se voir présenter
  Lukas, avec leur double synergie).

## 11. Feuille de route

| Étape | Contenu |
|---|---|
| **Aujourd'hui** | Cartes et album, rencontres avec synergies, rencontres par QR, bingo, tables tournantes, paliers, parrainage, remplaçants, notes privées, photos, annonces et récapitulatif (envois à activer), administration guidée, FR / DE / EN |
| **Lancement** | Hébergement suisse, import des membres actuels, activation des e-mails et du stockage des photos, confirmation par bouton des liens de connexion, double authentification de l'équipe, politique de confidentialité |
| **Saison suivante** | Paiement des cotisations (TWINT, QR-facture), bourse « je cherche / je propose », groupes de codéveloppement, albums photo des soirées |
| **Plus tard, si utile** | La même plateforme pour d'autres clubs de la Foire |
