# Le pitch

**Format du hackathon** : 2 minutes de pitch en français sur un deck en anglais, puis 7 minutes de questions.
**Critères** : compréhension du défi, innovation et originalité, faisabilité, impact potentiel, qualité du pitch.

Le deck ([PowerPoint](pitch/Club-des-Affaires-pitch.pptx) · [PDF](pitch/Club-des-Affaires-pitch.pdf)) compte
19 diapositives principales, une par écran de l'application, puis 7 annexes pour les questions. **Un clic = un écran.**
Mon texte est dans les notes de l'orateur ; la fabrication du deck est expliquée dans [pitch/README.md](pitch/README.md).

## Le texte (1 min 58)

| Temps | Diapo · écran | À dire |
|---|---|---|
| 0:00–0:08 | 1 · Promesse | « Bonjour. Ma promesse au Club des Affaires : plus jamais d'inconnus, même pour une nouvelle membre. » |
| 0:08–0:24 | 2 · Défi et quatre piliers | « Cinquante dirigeants se retrouvent quatre à cinq fois par an, mais restent entre habitués. Ma réponse suit quatre étapes : se trouver, repérer les synergies, se rencontrer et garder le lien. » |
| 0:24–0:28 | 3 · Connexion | « Voici Camille. Elle se connecte, sans rien installer. » |
| 0:28–0:32 | 4 · Accueil de Camille | « Son accueil montre l'album et les paliers du Club. » |
| 0:32–0:35 | 5 · Album | « Dans l'album, elle découvre les membres. » |
| 0:35–0:46 | 6 · Rencontres proposées | « Trois rencontres sont proposées, avec une raison : Lukas cherche du digital et peut l'aider sur le marché alémanique. Leurs passions lancent la conversation. » |
| 0:46–0:50 | 7 · QR de Lukas | « Le soir même, Lukas lui montre son QR code. » |
| 0:50–0:54 | 8 · Confirmation | « Camille confirme leur rencontre. » |
| 0:54–0:57 | 9 · Carte ajoutée | « Sa carte rejoint son album. » |
| 0:57–1:01 | 10 · Coordonnées | « Ses coordonnées se débloquent. » |
| 1:01–1:14 | 11 · Bingo et paliers | « Son bingo coche une case : le jeu pousse à parler à de nouvelles personnes. Chaque rencontre fait aussi avancer le Club vers un palier collectif, avec une récompense valaisanne. » |
| 1:14–1:19 | 12 · Entre les soirées | « Entre les soirées : annonces, relances et récapitulatif des nouveaux membres. » |
| 1:19–1:23 | 13 · Parrainage | « Le parrainage permet d'inviter une personne de confiance. » |
| 1:23–1:26 | 14 · Demande parrainée | « L'invité demande à rejoindre le Club. » |
| 1:26–1:31 | 15 · Tableau de bord | « L'équipe voit les membres, les rencontres et les personnes isolées. » |
| 1:31–1:35 | 16 · Préparer | « Elle prépare les soirées et les tables tournantes. » |
| 1:35–1:40 | 17 · Tables | « Ici, trente-huit invités sont mélangés sur trois services. » |
| 1:40–1:44 | 18 · Badges | « Elle imprime les badges QR des inscrits. » |
| 1:44–1:58 | 19 · Coût et lancement | « Pour lancer : hébergement suisse, import des membres, activation des e-mails. Environ trente francs par mois, hors développement. Un club qui se connaît se retrouve. Merci. » |

## Ce que le jury note, et où il le voit

| Critère | Où | La preuve |
|---|---|---|
| Compréhension du défi | diapo 2 | les quatre piliers du défi et les règles du client ([SOLUTION](SOLUTION.md)) |
| Innovation et originalité | diapos 6 à 11 | des rencontres expliquées, le QR qui prouve la rencontre, un bingo calculé pour chacun, des paliers collectifs |
| Faisabilité | tout le parcours, annexes | ce sont des captures de l'application réelle ; 403 tests ; [ARCHITECTURE](ARCHITECTURE.md) |
| Impact potentiel | diapos 13 à 19 | le parrainage, l'équipe autonome, un coût d'environ 30 CHF par mois ([MARKETING](MARKETING.md)) |
| Qualité du pitch | tout | une histoire, celle de Camille, en moins de deux minutes |

## Avant de monter sur scène

- [ ] Répéter cinq fois au chronomètre avec les 18 changements d'écran ; viser 1 min 55.
- [ ] Ouvrir le PowerPoint en mode présentateur : les notes à l'écran, les diapositives au projecteur.
- [ ] Garder le PDF sur une clé USB, au cas où.
- [ ] Pour les questions : la démo ouverte dans un onglet, connecté en Camille, et un onglet en équipe.

## Les questions probables (réponses courtes)

Les réponses détaillées sont dans [ARCHITECTURE](ARCHITECTURE.md).

- **Pourquoi Django ?** Il me donne une administration sécurisée dès le premier jour, et l'authentification, la
  protection CSRF et les traductions intégrées : moins de code, moins de failles, support jusqu'en 2028.
- **Pourquoi pas une app native ?** Rien à installer pour 50 dirigeants pressés ; un QR code ouvre directement la bonne
  page ; une seule base de code au lieu de trois.
- **Comment sont choisies les 3 rencontres ?** Un score lisible (passions communes, secteurs complémentaires, nouveau
  membre avec un pilier, synergie) et deux règles absolues : jamais deux personnes qui se connaissent, jamais sans langue
  commune.
- **Les compétences et besoins, ce n'est pas du business forcé ?** C'est facultatif et limité à trois thèmes, et les
  coordonnées ne se débloquent qu'après une vraie rencontre : personne ne peut démarcher tout le Club.
- **Et le bingo ?** Une grille calculée pour chaque invité, à partir des seules personnes présentes ; un algorithme de
  couplage garantit qu'un carton plein reste possible.
- **Et la sécurité ?** Fermé par défaut, une matrice d'accès testée pour chaque page, une CSP stricte, aucun service tiers,
  des QR à jeton aléatoire, des coordonnées visibles seulement après une rencontre.
- **Et les données personnelles ?** Annuaire réservé aux membres, minimum professionnel, chacun peut masquer sa carte,
  production visée en Suisse.
- **L'équipe a peu de temps : comment fait-elle ?** Pas de fil à animer : créer l'événement, cocher ses animations,
  cliquer sur « Préparer ». L'administration s'ouvre sur un mode d'emploi en six gestes.
- **Et si un membre ne peut pas venir ?** Il propose un remplaçant ; l'équipe le valide et le remplaçant reçoit un accès
  qui expire après la soirée.
- **Combien ça coûte ?** Environ 30 CHF par mois en Suisse, une vingtaine de francs de mise en place hors développement ;
  du développement seulement si le Club veut de nouvelles fonctionnalités.
- **Qu'est-ce qui n'est pas fait ?** Le paiement des cotisations, l'activation des envois automatiques, l'hébergement
  suisse et le stockage des photos en production, la double authentification de l'équipe, l'import des membres.

## Textes de soumission

**Links.** GitHub: https://github.com/MicrobAtomic/Meeting-project-Foire-du-Valais · Pitch deck:
[PowerPoint](pitch/Club-des-Affaires-pitch.pptx), [PDF](pitch/Club-des-Affaires-pitch.pdf) · Demo accounts:
`camille.rey@example.com`, `lukas.imboden@example.com`, `equipe@example.com` (password given with the submission).

**Short description (English).** *Club des Affaires — Never a stranger at the Club again.* A members-only web app that
keeps the Foire du Valais business club alive between its four or five evenings a year. Members **find** each other
through cards: sector, passions, what they can help with and what they are looking for. Before each event, the platform
**introduces** every member to three people and explains why. At the event, scanning a badge adds the card to your album
and unlocks contact details, while a **people bingo** computed for each guest, or rotating tables at seated dinners,
breaks the ice. All year long, shared Valais-flavoured milestones show the Club growing closer. Built for a small team,
trilingual FR / DE / EN, secure by default, covered by automated tests, and about CHF 30 a month to run.

**Description courte (français).** *Club des Affaires — Plus jamais d'inconnus au Club.* Une web app réservée aux
membres, qui fait vivre le Club des Affaires de la Foire du Valais entre ses quatre ou cinq soirées annuelles. Les
membres **se trouvent** grâce à leurs cartes : secteur, passions, ce qu'ils peuvent offrir et ce qu'ils cherchent. Avant
chaque soirée, la plateforme **présente** à chacun trois personnes à rencontrer, et explique pourquoi. Le soir même,
scanner un badge ajoute la carte à son album et débloque les coordonnées, pendant qu'un **bingo des rencontres** calculé
pour chaque invité, ou des tables tournantes aux dîners assis, brise la glace. Toute l'année, des paliers aux récompenses
valaisannes montrent le Club qui se resserre. Pensée pour une petite équipe, en français, allemand et anglais,
sécurisée par défaut, couverte par des tests automatisés, pour environ 30 CHF par mois.
