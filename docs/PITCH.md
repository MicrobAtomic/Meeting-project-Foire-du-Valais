# Présenter le Club des Affaires en deux minutes

Le pitch suit Camille : découvrir le Club, rencontrer Lukas, garder le lien. **Sept diapositives principales**, puis une séparation et sept annexes pour les questions. Les quatre piliers de l’ancienne A1 font partie de la diapositive 2.

- [PowerPoint avec quatre GIF intégrés et notes françaises](pitch/Club-des-Affaires-pitch.pptx).
- [Présentation HTML locale](pitch/deck.html) : fonctionne sans connexion ; conserver le dossier `pitch/` complet.
- [PDF de secours](pitch/Club-des-Affaires-pitch.pdf) : images fixes choisies pour montrer chaque preuve.
- [Ancienne vidéo autonome](pitch/demo.mp4), environ 77 s : alternative disponible, absente du nouveau PowerPoint.

Les diapositives sont en anglais ; le texte parlé est en français. Le conducteur vise **1 min 58 s**, avec avance manuelle. Les 241 mots ont été mesurés par lecture synthétique française : environ 98 s de parole, laissant 20 s de pauses et de transitions. Une répétition personnelle reste nécessaire. Les GIF bouclent et ne changent jamais la diapositive. Il n’est pas nécessaire d’attendre la fin d’une boucle.

## Conducteur et texte à dire

Le texte est également dans les notes de l’orateur du PowerPoint. `pitch/story.json` contient le conducteur vérifié avec les exports.

| Temps | Diapo | Texte français |
|---|---|---|
| 0:00–0:08 | 1 · Promesse | « Bonjour. Notre promesse au Club des Affaires : plus jamais d’inconnus, même pour une nouvelle membre. » |
| 0:08–0:24 | 2 · Défi → quatre piliers | « Cinquante dirigeants se retrouvent quatre à cinq fois par an, mais restent entre habitués. Notre réponse suit quatre étapes : se trouver, repérer les synergies, se rencontrer et garder le lien. » |
| 0:24–0:46 | 3 · Avant · web | « Voici Camille. Rien à installer : elle se connecte et découvre l’album des membres. Avant le dîner, trois rencontres lui sont proposées, avec une raison. Lukas cherche du digital, son métier à elle ; il peut l’aider à découvrir le marché alémanique. Leurs passions donnent un premier sujet de conversation. » |
| 0:46–1:14 | 4 · Pendant · rencontres | « Le soir même, Lukas lui montre son QR code. Camille confirme leur rencontre : sa carte rejoint son album et ses coordonnées se débloquent. Son bingo coche une case : le jeu pousse à parler à de nouvelles personnes. Chaque rencontre fait aussi avancer le Club vers un palier collectif, avec une récompense valaisanne. » |
| 1:14–1:26 | 5 · Entre · fidélisation | « Entre les soirées : annonces et relances ciblées, puis un récapitulatif mensuel des nouveaux membres. Le parrainage permet d’inviter une personne de confiance. » |
| 1:26–1:44 | 6 · Équipe · tableau de bord | « Pour l’équipe, ce tableau de bord montre les membres et les rencontres. Elle prépare les soirées, génère les badges et les tables tournantes. Ici, trente-huit invités sont mélangés sur trois services. Elle peut aussi repérer les membres isolés. » |
| 1:44–1:58 | 7 · Coût et lancement | « Pour lancer : hébergement suisse, import des membres, activation des emails. Environ trente francs par mois, hors développement. Un club qui se connaît se retrouve. Merci. » |

## Pourquoi ce découpage

La connexion ne mérite que deux secondes d’image : ce qui distingue la solution, ce sont les synergies, le scan après une vraie rencontre et le jeu qui mélange les invités. Les annonces, relances et nouveaux membres forment une seule idée : garder le lien. Le tableau de bord explique comment une petite équipe fait vivre ce parcours. La conclusion conserve le coût et trois étapes de lancement ; les autres fonctionnalités restent dans les annexes.

| GIF | Boucle | Ce qui apparaît |
|---|---|---|
| Web | 22 s | Vitrine 2,5 s → connexion 2 s → album 5 s → synergies 12,5 s |
| Rencontre | 28 s | QR 4 s → confirmation 4 s → carte 3 s → coordonnées 4 s → bingo 13 s |
| Parrainage | 12 s | Invitation personnelle 4 s → QR 4 s → demande parrainée 4 s |
| Équipe | 18 s | Tableau de bord 5 s → préparation 4 s → tables 9 s |

Les emails sont préparés mais **SMTP et cron restent à activer**. Le récapitulatif mensuel requiert le consentement. Aucune remise de parrainage n’est activée. Les factures de cotisation restent manuelles. L’hébergement suisse est une étape de lancement.

## Utilisation avant scène

- PowerPoint **installé** sur Mac ou Windows : lancer le diaporama pour voir les GIF ; ils restent fixes dans le mode d’édition. [Microsoft indique que PowerPoint web ne les anime pas en diaporama](https://support.microsoft.com/en-gb/powerpoint/add-an-animated-gif-to-a-slide?nochrome=true).
- HTML : ouvrir `pitch/deck.html` dans Chrome. **← / → ou Espace** pour avancer ; **F** plein écran ; **N** notes ; **R** rejouer le GIF ; **A** annexes / retour à la conclusion. L’avance s’arrête après la diapo 7, avant les annexes. Les commandes s’effacent quand la souris reste immobile.
- PDF : toutes les images sont fixes. Copier aussi le dossier `pitch/` complet pour utiliser le lecteur HTML hors ligne.
- Répéter au chronomètre sur l’ordinateur de présentation. Viser 1:55–1:58 ; le conducteur n’impose aucun compte à rebours.

La [page publique du hackathon](https://ai-weeks.ch/events/hack-vs) ne précise pas de contrainte sur les médias. L’exigence « MP4 uniquement » citée dans l’ancien plan n’a pas de source publique retrouvée ; la vidéo existante reste disponible comme alternative. La limite de deux minutes et le choix des GIF viennent de la demande actuelle.

## Reconstruction et preuves

Depuis la racine, avec Chrome, ffmpeg, Node, uv et `npm install` dans `docs/pitch/` :

```bash
.venv/bin/python docs/pitch/make_gifs.py
# Réexporter rapidement en conservant les captures :
.venv/bin/python docs/pitch/make_gifs.py --reuse-captures
cd docs/pitch
node verify_browser.mjs
UV_CACHE_DIR=/tmp/club-pitch-uv uv run --no-project --with python-pptx python verify_pitch.py
```

Le script crée uniquement `pitch/.build/gifs.sqlite3`, refuse un port 8010 déjà occupé et arrête son propre serveur en cas d’erreur. Le code métier, la base locale, le serveur 8000 et les réglages d’envoi ne sont pas modifiés. Les GIF originaux sont intégrés au PowerPoint ; le PDF utilise des posters explicites. Le journal de vérification et les limites connues sont dans [PLAN_PITCH](PLAN_PITCH.md).

Chiffres du client : environ 50 membres, cotisation de 500 CHF/an, 4–5 soirées/an. Démo : 15 % de paires connectées, prochain palier à 20 %, dîner de 38 invités sur trois services. Coût de fonctionnement **estimé** à ≈ 30 CHF/mois (300–450 CHF/an), mise en place ≈ 20 CHF hors développement ; détails et sources dans [ARCHITECTURE](ARCHITECTURE.md).

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
