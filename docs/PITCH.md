# Pitch — Club des Affaires (2 minutes + 7 minutes de questions)

> **Pour qui** : toi, qui présentes seul.
> **Format officiel** : deck **en anglais** (le jury doit comprendre la solution), pitch oral **en français**, démo en
> **vidéo MP4 intégrée** au deck, puis 7 minutes de questions.
> **Critères** : compréhension du défi · innovation et originalité · faisabilité · impact potentiel · qualité du pitch.
> **Fichiers** : [pitch/Club-des-Affaires-pitch.pptx](pitch/Club-des-Affaires-pitch.pptx) (vidéo intégrée, texte dans les
> notes de l'orateur) · [pitch/Club-des-Affaires-pitch.pdf](pitch/Club-des-Affaires-pitch.pdf) (secours) ·
> [pitch/demo.mp4](pitch/demo.mp4) (42 s) · description courte : [SUBMISSION.md](SUBMISSION.md).

## 1. Le message en une phrase

> « Le Club se retrouve quatre à cinq fois par an, mais ses membres ne se connaissent pas. On leur donne de quoi se
> trouver, se rencontrer pour de vrai et se retrouver, sans demander d'effort à une équipe qui a peu de temps. »

Slogan : **« Plus jamais d'inconnus au Club. »** · *Never a stranger at the Club again.*

## 2. Le texte, diapositive par diapositive (2 minutes)

Environ 290 mots : un débit posé. Le même texte est dans les notes de l'orateur du `.pptx`.

| Temps | Diapo | À dire |
|---|---|---|
| 0:00 – 0:10 | 1 · Titre | « Bonjour ! Le Club des Affaires de la Foire du Valais, c'est une cinquantaine de dirigeantes et de dirigeants qui paient 500 francs par an pour quatre à cinq soirées. » |
| 0:10 – 0:30 | 2 · Le défi | « Ils viennent : 80 % de présence. Mais ils arrivent en inconnus, restent entre habitués, et entre deux soirées, le réseau n'existe pas. Le client nous a posé ses règles : pas de business forcé, une équipe qui a très peu de temps, des membres francophones et germanophones, et un club qui reste premium. » |
| 0:30 – 0:50 | 3 · La solution | « Notre réponse : une web app qui suit le rythme du Club, sur les quatre piliers du défi. Se trouver : chaque membre a sa carte, ses passions, ce qu'il peut offrir et ce qu'il cherche. Repérer les synergies : avant chaque soirée, trois personnes à rencontrer, et pourquoi. Le soir même, on scanne un badge, et un jeu brise la glace. Et toute l'année, le Club se resserre. » |
| 0:50 – 1:32 | 4 · **Vidéo** | « Voici Camille, nouvelle membre. Avant le dîner, elle sait déjà qui rencontrer : Lukas. Ils aiment tous deux la Petite Arvine et le ski de randonnée ; il cherche du digital, son métier à elle, et elle veut s'ouvrir au marché alémanique, le sien. Au dîner, elle scanne son badge : la carte entre dans son album, ses coordonnées se débloquent, une case de son bingo se coche. Et côté équipe : un clic, et 38 invités changent de table à chaque service. » |
| 1:32 – 1:47 | 5 · Ce qui est nouveau | « Ce qui est nouveau : chaque vraie rencontre compte, et se compte. Le Club est connecté à 15 % aujourd'hui ; au prochain palier, une tournée de Petite Arvine pour tous. Mesurable pour le comité, motivant pour les membres. » |
| 1:47 – 2:00 | 6 · Faisabilité | « Et c'est faisable : ça tourne aujourd'hui, en trois langues, sécurisé, testé, pour moins de 500 francs par an. Un club qui se connaît se retrouve. Merci ! » |

Les diapositives 7 à 11 sont des **annexes** pour les questions : architecture, algorithmes, sécurité, conquête des
membres, coûts et feuille de route. Ne les montre que si une question y mène.

## 3. Ce que le jury note, et où il le trouve

| Critère | Où | La preuve |
|---|---|---|
| Compréhension du défi | diapos 2 et 3 | le problème du brief (« le réseau n'existe pas entre les rencontres ») et les règles du client ; les quatre piliers du défi repris un par un |
| Innovation et originalité | diapo 5, vidéo | l'album qu'on remplit en se rencontrant pour de vrai ; l'indice de fédération et les paliers à récompense valaisanne ; un bingo calculé pour chaque invité ; des tables tournantes qui mélangent vraiment |
| Faisabilité | diapo 6, vidéo, annexes 7 à 9 | ça tourne (vidéo, démo en ligne, code public) ; tests automatisés ; sécurité fermée par défaut ; coûts et délais chiffrés |
| Impact potentiel | diapos 5 et 6, annexe 10 | intégration des nouveaux dès la première soirée ; de 50 à 100 membres par invitation, sans publicité ; la même plateforme pour d'autres clubs |
| Qualité du pitch | tout | une seule histoire (Camille), une vidéo de 42 s, six diapositives, deux minutes chronométrées |

## 4. Avant de monter sur scène

- [ ] Ouvrir le `.pptx` sur l'ordinateur de présentation et **vérifier que la vidéo démarre** (diapo 4). Dans
      PowerPoint : onglet *Lecture* → *Démarrer : automatiquement*. Dans Keynote : clic sur la vidéo → *Lecture
      automatique*.
- [ ] Mode présentateur : les notes (ton texte) à l'écran de l'ordinateur, les diapositives au projecteur.
- [ ] Répéter **cinq fois avec un chronomètre**, viser 1 min 50. Apprendre par cœur la première et la dernière phrase.
- [ ] Le PDF et la vidéo seule sur une clé USB, au cas où.
- [ ] Pour les questions : la démo en ligne ouverte dans un onglet (l'offre gratuite de Render se met en veille après
      15 minutes : l'ouvrir 2 minutes avant), connecté en Camille, et un onglet en staff.
- [ ] Données fraîches en ligne : `seed_demo --reset` (voir le README), ou en local `python manage.py demo_reset`.

## 5. Chiffres à citer

| Chiffre | Source |
|---|---|
| ~50 membres, 500 CHF par an, 80 % de présence, 4 à 5 soirées par an, objectif 100 à 200+ | le client |
| **15 %** : indice de fédération des données de démo (180 paires sur 1 225) ; prochain palier à 20 % | `seed_demo` |
| **49 ms** pour les rencontres de 200 inscrits · **0,8 s** pour le plan de tables de 200 invités | mesuré ([ARCHITECTURE §7](ARCHITECTURE.md)) |
| **251 nouvelles paires, 1 répétition** : dîner de démo, 38 inscrits, tables de 6, 3 services | la vidéo, en direct |
| **400 tests automatisés**, SQLite et PostgreSQL | `python manage.py test club` |
| **≈ 30 CHF par mois** de fonctionnement, **≈ 20 CHF** de mise en place hors développement | estimation ([ARCHITECTURE §9](ARCHITECTURE.md)) |

## 6. Les 7 minutes de questions

**Pourquoi Django plutôt que Next.js et Supabase ?**
L'équipe a besoin d'un back-office (membres, événements, inscriptions) dès le premier jour : Django le fournit, sécurisé.
L'authentification, le CSRF, l'échappement automatique, les migrations et l'internationalisation sont inclus : moins de
code, moins de failles. Rendu côté serveur : pas d'API exposée à protéger, pages légères sur mobile. Hébergeable en Suisse
chez n'importe quel hébergeur, maintenable par n'importe quelle agence, version à support long terme jusqu'en avril 2028.

**Pourquoi une web app et pas une application native ?**
Rien à installer pour 50 dirigeants pressés, un QR code ouvre directement la bonne page, une seule base de code au lieu de
trois. Le peu de JavaScript (swipe, copier, imprimer, aperçu de photo) est une amélioration : sans lui, tout fonctionne.

**Comment fonctionne « Tes 3 rencontres » ?**
Chaque paire d'inscrits reçoit un score : +3 par affinité commune, +2 par agacement commun, +2 si les secteurs sont
différents, +3 pour une nouvelle recrue avec un pilier du Club, et un bonus quand l'un peut répondre à ce que l'autre
cherche (deux synergies au plus : les affinités restent le cœur). Deux règles absolues : jamais deux personnes qui se
connaissent déjà, jamais sans langue commune. Attribution gloutonne et équitable, déterministe, en O(n²).

**Les compétences et les besoins, ce n'est pas du business forcé ?**
Non : c'est facultatif, trois thèmes au plus, présenté comme « une porte ouverte, pas une vitrine commerciale ». Les
coordonnées ne se débloquent qu'après une vraie rencontre : personne ne peut démarcher tout le Club.

**Et le bingo ?**
Une grille 3 × 3 « Trouve quelqu'un qui… », calculée pour chaque invité à partir des seules personnes présentes ce
soir-là. Elle privilégie les gens qu'il n'a pas encore rencontrés et pousse vers ses 3 rencontres. Un algorithme de
couplage biparti garantit qu'un carton plein reste possible avec des personnes toutes différentes. Au scan, c'est la case
la plus rare qui se coche. L'équipe n'a rien à préparer, seulement la liste des gagnants à donner au bar.

**Et les tables tournantes ?**
C'est une variante du *Social Golfer Problem*, NP-difficile. Recherche locale avec redémarrages : on échange deux invités
de tables différentes et on garde l'échange s'il ne dégrade pas le coût (déjà assis ensemble : 10, aucune langue commune : 4,
se connaissent déjà : 3, même secteur : 1). Seulement pour les repas assis : un apéro debout a son bingo.

**Comment mesurez-vous le succès ?**
L'indice de fédération (part des paires de membres qui se connaissent) avec ses paliers, le nombre de rencontres par
événement, et la liste des membres isolés sur laquelle l'équipe peut agir. Côté recrutement : les demandes d'invitation
par parrain, le taux d'adhésion des invités et des remplaçants ([MARKETING](MARKETING.md)).

**Qu'en est-il de la sécurité ?**
Fermé par défaut (un middleware exige la connexion partout) ; une **matrice d'accès testée** (toute nouvelle route doit être
classée, sinon la suite échoue) ; CSP stricte, aucun style ni script en ligne, aucun service tiers ; CSRF sur tous les
formulaires ; QR avec un jeton aléatoire de 128 bits ; liens de connexion à usage unique ; photos servies seulement à ceux
qui ont le droit de voir la fiche ; notes privées visibles par leur seul auteur ; accès des remplaçants limité dans le temps.

**Et la protection des données (nLPD) ?**
L'annuaire n'est visible que par les membres, les coordonnées ne sont partagées qu'après une rencontre, chaque membre peut
masquer sa carte, on ne collecte que le minimum professionnel. Données fictives pour la démo ; production visée en Suisse.

**Comment l'équipe, qui a peu de temps, l'utilise-t-elle ?**
Pas de fil d'actualité à animer. Dans l'administration, un mode d'emploi et un encart par langue : créer l'événement,
cocher ses animations (bingo pour un apéro, tables pour un dîner), puis « Préparer » génère rencontres, plan de tables et
badges. Accepter une demande d'invitation crée le compte en un clic.

**Et si un membre ne peut pas venir ?**
Il propose un remplaçant de son entreprise. L'équipe le valide ; le remplaçant reçoit une identité et un QR code à lui,
avec un accès qui expire après la soirée.

**Que se passe-t-il si les membres ne remplissent pas leur profil ?**
Le swipe des affinités prend deux minutes et une bannière le rappelle. Le score garde des critères qui ne demandent rien
aux membres : secteurs différents, nouvelle recrue avec un pilier, langue commune.

**Est-ce que ça tient à l'échelle ?**
L'application est sans état : on ajoute des processus. 200 inscrits : moins d'une seconde pour les algorithmes. Au-delà de
quelques milliers de membres, on déporterait les calculs en tâche de fond. Une possibilité ultérieure : plusieurs clubs sur la même plateforme, si la demande existe.

**Comment gérez-vous les langues ?**
L'internationalisation de Django pour l'interface, des champs traduits pour les affinités, les thèmes et les événements (un
encart FR, DE et EN dans l'administration), l'allemand en orthographe suisse. Un test parcourt les pages en allemand et en
anglais et échoue si une phrase française d'interface subsiste.

**Pourquoi pas WhatsApp, Hivebrite ou Brella ?**
WhatsApp : tout le monde voit le numéro de chacun, aucun annuaire. Hivebrite et consorts : licence annuelle, données hors
de Suisse, un fil d'actualité vide sans animateur. Brella et consorts : pensés pour des rendez-vous commerciaux, la
« vente forcée » que le client ne veut pas.

**Combien ça coûte, et en combien de temps ?**
Environ 30 francs par mois de fonctionnement en Suisse (hébergement avec base de données, sauvegardes, e-mails,
domaine), soit 300 à 450 francs par an ; une vingtaine de francs de mise en place hors développement (le nom de
domaine). Du développement ne s'ajoute que si le Club veut de nouvelles fonctionnalités, sur devis.

**Qu'est-ce qui n'est pas fait ?** *(réponds franchement)*
Le paiement des cotisations (facturation manuelle aujourd'hui), l'activation des envois automatiques (SMTP et tâche
planifiée prêts mais désactivés), l'hébergement suisse et le stockage des photos en production, la double authentification
du staff, l'import des membres existants.

**Comment puis-je tester moi-même ?**
Le code est public sur GitHub ; la démo en ligne avec les comptes du README ; en local : `seed_demo --reset` puis
`runserver`, et `python manage.py test club`.
