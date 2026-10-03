# Plan — retouches de la présentation (pitch, deck, vidéo)

> Destinataire : une IA qui exécute (ChatGPT / Codex), tâche par tâche, sans rediscuter les décisions.
> Rédigé le 3 octobre 2026 au soir, après les retours de l'humain sur le deck. État de départ : commit qui ajoute
> ce fichier ; 401 tests verts.
> **Format officiel du hackathon** : 2 minutes de pitch **en français**, deck **en anglais**, démo uniquement en **vidéo
> MP4 intégrée au deck**, puis 7 minutes de questions. Critères : compréhension du défi, innovation et originalité,
> faisabilité, impact potentiel, qualité du pitch.

## 0. Règles et outils

- Ne modifie pas le code de l'application : ce plan ne touche que `docs/` (deck, vidéo, textes). Exception : aucune.
- Ne travaille pas en même temps qu'une autre IA sur le dépôt : vérifie `git status` et `git log --oneline -5` avant de commencer.
- Fichiers du pitch :
  - `docs/pitch/deck.html` : la **source** du deck (sections 1920 × 1080, `data-notes` = texte de l'orateur) ;
  - `docs/pitch/build_deck.mjs` (PNG par diapositive + PDF) et `docs/pitch/build_pptx.py` (PPTX avec la vidéo et les notes) ;
  - `docs/pitch/video/` : `record_demo.mjs` (enregistre le parcours sur l'application réelle), `captions.json` (sous-titres),
    `video_assets.mjs` + `compose.py` (montage 1920 × 1080), `shot_slide1.mjs` (image de la diapositive 1),
    `make_pitch.sh` (refait **tout**).
- Outils (une seule fois) : Google Chrome, `brew install ffmpeg`, `cd docs/pitch && npm install`, `uv` (déjà là),
  `.venv` du projet.
- Tout refaire, depuis la racine du dépôt : `docs/pitch/video/make_pitch.sh 401` (401 = nombre de tests affiché sur les
  diapositives). Le script utilise une base jetable (`docs/pitch/.build/`, ignorée par Git), **jamais `db.sqlite3`**, lance
  le serveur sur le port 8010 avec `DEMO_BANNER=0` (bandeau « Démo » masqué dans les captures) et l'arrête à la fin.
- Après chaque tâche : `git add` des fichiers touchés, commit en français (« docs(pitch): … »), push.

## 1. Décisions (déjà prises)

| # | Décision |
|---|---|
| D1 | Le pitch suit **le parcours** de Camille, avec une démo plus lente : **vidéo de 70 à 80 s** (au lieu de 42 s, jugée deux fois trop rapide). |
| D2 | **4 diapositives principales** pour les 2 minutes : 1 Titre · 2 Le défi · 3 La démo (vidéo) · 4 Impact : feuille de route et coûts. |
| D3 | Puis une **diapositive de séparation « Appendix — for the Q&A »** et 8 annexes **clairement marquées** (bandeau gris « APPENDIX », numéros A1 à A8). |
| D4 | **Plus aucune mention des 10 000 CHF** (c'était une possibilité évoquée par le client, pas un objectif). À la place : le **coût réel de mise en place hors développement** et le coût de fonctionnement, avec la mention que du développement peut s'ajouter **si de nouvelles fonctionnalités sont demandées**. |
| D5 | Feuille de route de la diapositive 4 : **Now / Launch / Next season**. La « V3 » (même plateforme pour d'autres clubs) quitte la diapositive principale et devient **une ligne « possible later » dans l'annexe A8** (l'humain hésitait ; si il préfère la garder, ajouter une 4ᵉ colonne « Later » à la diapositive 4). |
| D6 | Diapositive 1 : l'image est **l'album** (en anglais, format téléphone, **sans bandeau « Démo »**), déjà produite par `shot_slide1.mjs`. Variante possible : la vitrine publique (`shot_slide1.mjs OUT.png landing`). |
| D7 | Diapositive 2 : « What the client asked for » devient **une liste de 4 points**, simple. |

## 2. Chiffres à utiliser pour les coûts (vérifiés le 3 octobre 2026)

- Hébergement suisse : Infomaniak Jelastic Cloud démarre à **CHF 6.31 par mois** (un petit conteneur, Django et PostgreSQL
  pris en charge) ; une application + sa base PostgreSQL avec de la marge : **CHF 20 à 35 par mois**.
  Source : https://www.infomaniak.com/en/hosting/dedicated-and-cloud-servers/jelastic-cloud
- Alternative plus chère : Exoscale (Suisse), base PostgreSQL « Hobbyist-2 » seule ≈ **CHF 48 par 30 jours**.
  Source : https://www.exoscale.ch/static/files/price-list.pdf
- Nom de domaine `.ch` : environ **CHF 15 à 20 par an** ; certificat HTTPS : gratuit ; e-mails transactionnels : offre gratuite
  ou quelques francs par mois.
- **Total retenu** : mise en place hors développement ≈ **CHF 20** (le nom de domaine) ; fonctionnement ≈ **CHF 30 par mois**,
  soit **CHF 300 à 450 par an** ; développement : **seulement si de nouvelles fonctionnalités sont demandées** (sur devis).

## 3. Tâches

### T1 — Point de départ

1. `source .venv/bin/activate && env DEBUG=1 python manage.py test club` → `OK (skipped=6)`, 401 tests.
2. `docs/pitch/video/make_pitch.sh 401` → finit par « Pitch rebuilt… ». Si le port 8010 est occupé, le script l'arrête.

✅ Les deux commandes passent avant toute modification.

### T2 — Diapositive 2 : une liste simple

Dans `docs/pitch/deck.html`, section « 2 · The challenge », remplace la carte « What the client asked for » par :

```html
<div class="card"><h3>What the client asked for</h3>
  <ul class="clean in-card">
    <li>No forced selling: business is a door, not the core</li>
    <li>Several languages: French, German, English</li>
    <li>Help people actually meet</li>
    <li>A premium feeling</li>
  </ul>
</div>
```

et raccourcis la carte de gauche : `<p>Members come, but arrive as strangers and stay in small groups. Between two evenings,
the network goes quiet.</p>`. Ajoute dans le `<style>` :
`ul.clean.in-card li { font-size: 27px; padding: 12px 0 12px 44px; }`

✅ La diapositive 2 se lit en 5 secondes : 4 chiffres, une phrase d'observation, 4 points.

### T3 — Nouvelle structure : 4 diapositives + annexes marquées

Ordre final des `<section class="slide">` dans `deck.html` (13 au total) :

| N° | Section | Origine |
|---|---|---|
| 1 | Titre | inchangée (l'image `img/home.png` est déjà l'album sans bandeau) |
| 2 | The challenge | T2 |
| 3 | Demo video | ancienne n° 4 ; kicker « Demo · Camille's evening » (plus de durée écrite) |
| 4 | **Impact : roadmap & costs** | **nouvelle**, code ci-dessous |
| 5 | Séparation « Appendix — for the Q&A » | **nouvelle**, code ci-dessous |
| 6 | A1 · The solution | ancienne n° 3 (les 4 piliers) |
| 7 | A2 · What is new | ancienne n° 5 |
| 8 | A3 · Feasibility | ancienne n° 6, **sans** la ligne coût / 10k (voir T5) |
| 9 | A4 · Architecture | ancienne n° 7 |
| 10 | A5 · Algorithms | ancienne n° 8 |
| 11 | A6 · Security & privacy | ancienne n° 9 |
| 12 | A7 · Go-to-market | ancienne n° 10 |
| 13 | A8 · Costs in detail | ancienne n° 11, réécrite (voir T5) |

Nouvelle diapositive 4 (à placer juste après la vidéo) :

```html
<section class="slide" data-notes="(voir T6)">
  <p class="kicker">Impact · roadmap &amp; costs</p>
  <h2>Ready to launch, light to run.</h2>
  <div class="grid g3" style="margin-top:40px">
    <div class="card pillar"><small>Now</small><h3>Shown today</h3><p>Cards &amp; album, introductions with synergies, QR meetings, people bingo, rotating tables, Club milestones, guided admin, FR / DE / EN.</p></div>
    <div class="card pillar"><small>Launch</small><h3>Before the next evening</h3><p>Swiss hosting, import of the current members, e-mail sending switched on.</p></div>
    <div class="card pillar"><small>Next season</small><h3>If the Club wants more</h3><p>Membership payment (TWINT, QR-bill), an “I'm looking for / I offer” board, event photo albums.</p></div>
  </div>
  <div class="grid g3" style="margin-top:28px">
    <div><p class="stat">≈ 30</p><p class="stat-label">CHF a month to run: Swiss hosting, database, backups, e-mails</p></div>
    <div><p class="stat">≈ 20</p><p class="stat-label">CHF to set up, excluding development: a .ch domain</p></div>
    <div><p class="stat" style="font-size:56px;line-height:84px">On request</p><p class="stat-label">development, only if new features are wanted</p></div>
  </div>
  <div class="foot"><span><b>__TESTS__ automated tests</b> · secure by default · works today</span><span>“A club that knows itself comes back together.”</span></div>
</section>
```

(`__TESTS__` est remplacé par le nombre passé à `build_deck.mjs --tests`.)

Diapositive de séparation, juste après :

```html
<section class="slide divider" data-notes="Annexes : à n'ouvrir que si une question y mène.">
  <p class="kicker">Appendix</p>
  <h1 style="margin-top:24px">For the questions.</h1>
  <p class="lead">A1 The solution · A2 What is new · A3 Feasibility · A4 Architecture · A5 Algorithms · A6 Security &amp; privacy · A7 Go-to-market · A8 Costs in detail</p>
</section>
```

Annexes clairement marquées :
- ajoute `class="slide appendix"` aux 8 annexes (A1 à A8) ;
- remplace leur kicker par « A1 · The solution », « A2 · What is new », etc. ;
- dans le `<style>`, supprime la règle `.appendix .kicker::after` et ajoute :

```css
.divider { background: var(--ink); color: #fafaf9; justify-content: center; }
.divider .kicker { color: #fca5a5; } .divider .lead { color: #d6d3d1; }
.appendix { background: #fff; padding-top: 120px; }
.appendix::before { content: "APPENDIX — FOR THE Q&A"; position: absolute; top: 0; left: 0; right: 0; height: 56px;
  background: #f5f5f4; color: #78716c; font-size: 20px; font-weight: 700; letter-spacing: .14em;
  display: flex; align-items: center; padding-left: 120px; }
```

✅ `node build_deck.mjs --tests 401` affiche « 13 slides » ; les 8 annexes ont le bandeau gris ; la diapositive 5 annonce
la liste A1 à A8.

### T4 — Vidéo de 70 à 80 s, sans bandeau

Le bandeau est déjà masqué (`DEMO_BANNER=0` dans `make_pitch.sh`). Il faut ralentir et structurer par piliers.

1. Dans `docs/pitch/video/record_demo.mjs`, remplace la partie **téléphone** (de `await phone.goto(base + '/accueil/'…`
   jusqu'à `const phoneResult = await rp.stop();`) par :

```js
await phone.goto(base + '/album/?aide=marche-alemanique', { waitUntil: 'networkidle0' });
const rp = await record(phone, 'phone', { w: 780, h: 1688 });
rp.mark('find');
await sleep(4500);
await scrollBy(phone, 420);
await sleep(5500);

rp.mark('intros');
await phone.goto(base + '/evenements/4/', { waitUntil: 'networkidle0' });
await sleep(1500);
await scrollTo(phone, 'section h2.text-lg', 'start');  // "Your introductions"
await sleep(10000);

rp.mark('scan');
await phone.goto(base + '/m/demo-lukas/', { waitUntil: 'networkidle0' });
await sleep(5500);
await tap(phone, 'main form button[type=submit]');
rp.mark('unlocked');
await sleep(4000);
await scrollBy(phone, 520);
await sleep(5000);

rp.mark('bingo');
await phone.goto(base + '/evenements/4/bingo/', { waitUntil: 'networkidle0' });
await sleep(1200);
await scrollTo(phone, 'main ol', 'center');
await sleep(8000);

rp.mark('counts');
await phone.goto(base + '/accueil/', { waitUntil: 'networkidle0' });
await sleep(2000);
await scrollBy(phone, 330);
await sleep(7000);
const phoneResult = await rp.stop();
```

   et dans la partie **bureau**, double les attentes : `sleep(1600)` → `sleep(3000)`, `sleep(800)` → `sleep(1500)`,
   `sleep(900)` → `sleep(2000)`, `sleep(3200)` → `sleep(7000)`.

2. Remplace `docs/pitch/video/captions.json` par (6 sous-titres téléphone = 6 marqueurs, dans le même ordre) :

```json
{
  "phone": [
    {"kicker": "Find each other", "title": "Meet Camille, a new member", "text": "The album: every member's card, passions, what they can help with and what they look for."},
    {"kicker": "Spot synergies", "title": "She already knows who to meet", "text": "Lukas shares her love of Petite Arvine, and they can help each other: digital for him, the Swiss German market for her."},
    {"kicker": "Meet for real", "title": "At the dinner, she scans his badge", "text": "One tap adds his card to her album. Her bingo shows which square he can tick."},
    {"kicker": "Meet for real", "title": "Contacts unlock after a real meeting", "text": "Phone, LinkedIn and a vCard for her address book. No cold messages."},
    {"kicker": "Meet for real", "title": "People bingo, computed for each guest", "text": "Find someone who loves trail running, founded the Club, comes from Visp… A full line? Show it at the bar."},
    {"kicker": "Belong", "title": "Every real encounter counts", "text": "3 of 49 cards, and the whole Club gets closer to its next milestone: a round of Petite Arvine at 20&nbsp;%."}
  ],
  "desk": [
    {"title": "For the team: one click", "text": "rotating tables for 38 guests over 3 courses"}
  ]
}
```

3. Dans `make_pitch.sh`, l'image d'affiche est prise à `-ss 12` : passe à `-ss 20` (scène « synergies »).

✅ `make_pitch.sh` affiche une durée entre 70 et 80 s. Contrôle visuel : extrais une image par scène
(`ffmpeg -ss <t> -i docs/pitch/demo.mp4 -frames:v 1 /tmp/f<t>.png` pour t = 5, 18, 32, 40, 50, 60, 70) : aucun bandeau
jaune « Demo » en haut du téléphone ; chaque sous-titre correspond à l'écran (l'album filtré montre Lukas, la scène
synergies montre les deux lignes 🤝, le bingo montre la case cochée par Lukas).

### T5 — Les coûts, sans les 10 000 CHF

1. Cherche : `grep -rn "10k\|10 000\|10,000\|10'000\|enveloppe" docs/ README.md --include=*.md --include=*.html | grep -v "PLAN.md\|PLAN_AMELIORATIONS.md\|PLAN_PITCH.md"`
   (`PLAN.md` et `PLAN_AMELIORATIONS.md` sont des historiques : n'y touche pas).
2. Remplace chaque mention des 10 000 CHF comme objectif ou enveloppe :
   - `deck.html` A3 (ancienne 6) : supprime la ligne « < CHF 500 a year to run · 6–8 days to production, within the CHF 10k budget »
     (les coûts sont maintenant sur la diapositive 4) ;
   - `deck.html` A8 : réécris la carte « Cost » ainsi : « Running: about CHF 30 a month (Swiss hosting with database,
     backups, e-mails, .ch domain), i.e. CHF 300–450 a year. Setup, excluding development: about CHF 20 (the domain).
     Development: only if new features are requested, on quote. Prices checked on Infomaniak Jelastic Cloud (from
     CHF 6.31 a month per container); Exoscale is a pricier Swiss alternative (database alone ≈ CHF 48 a month). » ;
     carte « Roadmap » : garde V1.1 et V2, et remplace V3 par « Possible later: the same platform for other clubs of
     the Foire network. » ;
   - `docs/PITCH.md` : la réponse « Combien ça coûte, et en combien de temps ? » devient : « Environ 30 francs par mois de
     fonctionnement en Suisse (hébergement avec base de données, sauvegardes, e-mails, domaine), soit 300 à 450 francs par
     an ; une vingtaine de francs de mise en place hors développement (le nom de domaine). Du développement ne s'ajoute
     que si le Club veut de nouvelles fonctionnalités, sur devis. » ; et dans « Chiffres à citer », remplace la ligne
     « < 500 CHF par an … 6 à 8 jours » par « ≈ 30 CHF par mois de fonctionnement, ≈ 20 CHF de mise en place hors
     développement ».
   - `docs/ARCHITECTURE.md` §9 : la ligne « Mise en production depuis ce MVP … dans l'enveloppe de 10 000 CHF » devient
     « Mise en place hors développement : ≈ 20 CHF (nom de domaine). Développement supplémentaire (double authentification
     du staff, import des membres, nouvelles fonctionnalités) : seulement sur demande, sur devis. » ; ajuste le total en
     « environ 30 CHF par mois, soit 300 à 450 CHF par an ».
   - `docs/SUBMISSION.md` : « under CHF 500 a year to run » → « about CHF 30 a month to run ».

✅ La commande de recherche ne trouve plus « 10k » ni « 10 000 » hors des deux historiques.

### T6 — Le texte de l'orateur (2 minutes)

Mets ces textes dans les `data-notes` des diapositives 1 à 4 de `deck.html`, et le même tableau dans la section 2 de
`docs/PITCH.md` (remplace l'ancien tableau à 6 diapositives) :

| Temps | Diapo | À dire |
|---|---|---|
| 0:00 – 0:12 | 1 · Titre | « Bonjour ! Le Club des Affaires de la Foire du Valais, c'est une cinquantaine de dirigeantes et de dirigeants qui se retrouvent quatre à cinq fois par an. Notre promesse : plus jamais d'inconnus au Club. » |
| 0:12 – 0:30 | 2 · Le défi | « Aujourd'hui, ils viennent, mais arrivent en inconnus, restent entre habitués, et entre deux soirées, le réseau n'existe pas. Le client a quatre exigences : pas de business forcé, plusieurs langues, aider les gens à se rencontrer, et garder un esprit premium. » |
| 0:30 – 1:45 | 3 · **Vidéo** (lancée automatiquement) | « Voici Camille, nouvelle membre. Dans l'album, elle découvre les cartes des membres : leur métier, leurs passions, ce qu'ils peuvent offrir et ce qu'ils cherchent. — Avant le dîner, l'application lui présente trois personnes, et pourquoi. Lukas : ils aiment tous deux la Petite Arvine ; il cherche du digital, son métier à elle, et elle veut s'ouvrir au marché alémanique, le sien. — Le soir même, elle scanne son badge : sa carte rejoint son album, ses coordonnées se débloquent, une case de son bingo des rencontres se coche. — Chaque rencontre fait avancer tout le Club : il est connecté à 15 %, et au prochain palier, une tournée de Petite Arvine. — Et pour l'équipe, un clic : trente-huit invités changent de table à chaque service. » |
| 1:45 – 2:00 | 4 · Impact | « C'est prêt à lancer : une trentaine de francs par mois d'hébergement en Suisse, du développement seulement si vous voulez aller plus loin. Un club qui se connaît se retrouve. Merci ! » |

Dans `docs/PITCH.md`, mets aussi à jour : l'en-tête (vidéo de 70 à 80 s), la section 3 (critères → diapositives : la
compréhension du défi = diapo 2 et la vidéo par piliers ; l'innovation = vidéo et annexe A2 ; la faisabilité = vidéo,
diapo 4 et annexes A3 à A6 ; l'impact = diapo 4 et annexe A7 ; la qualité du pitch = 4 diapositives, une histoire), et la
section 4 (régler la vidéo en lecture automatique ; les annexes commencent à la diapositive 5).

✅ Lu à voix haute avec un chronomètre : 1 min 55 à 2 min ; la parole suit les scènes de la vidéo.

### T7 — Fabrication et vérification

1. `docs/pitch/video/make_pitch.sh 401`.
2. Vérifie :
   - `uv run --no-project --with python-pptx python -c "from pptx import Presentation as P; d=P('docs/pitch/Club-des-Affaires-pitch.pptx'); print(len(d.slides))"` → 13 ;
   - la diapositive 3 contient la vidéo : `unzip -l docs/pitch/Club-des-Affaires-pitch.pptx | grep media1.mp4` ;
   - `ffprobe -v error -show_entries format=duration -of csv=p=0 docs/pitch/demo.mp4` → entre 70 et 80 ;
   - ouvre `docs/pitch/slides/slide-01.png` à `slide-05.png` : aucun bandeau « Demo », annexes bien séparées ;
   - les notes de l'orateur des diapositives 1 à 4 contiennent le texte de T6.
3. `env DEBUG=1 python manage.py test club` reste vert (rien dans l'application n'a changé).

### T8 — Livraison

`git add docs/ && git commit -m "docs(pitch): 4 diapositives + annexes, vidéo de 75 s, coûts réels" && git push`.
Dis à l'humain : régler la vidéo en lecture automatique dans PowerPoint ou Keynote, répéter 5 fois au chronomètre.
