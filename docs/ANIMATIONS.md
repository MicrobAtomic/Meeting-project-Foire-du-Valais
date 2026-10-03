# Animations : briser la glace à chaque soirée

Le Club réunit une cinquantaine de dirigeantes et dirigeants qui, souvent, ne se connaissent pas : on reste
entre habitués, les nouveaux restent seuls. Chaque soirée a donc **son jeu**, adapté à son format. Les
tables tournantes conviennent à un dîner assis, pas à un apéro debout.

Les règles qui ont guidé la liste :

- **Zéro travail pour l'équipe.** Elle coche une case dans l'administration, la plateforme prépare tout.
- **Jamais de business forcé.** On joue pour se rencontrer, pas pour vendre. Pas de pitch commercial.
- **Toujours facultatif et court.** Un seul jeu à la fois, jamais plus de quelques minutes d'explication.
- **Bilingue.** Chaque jeu fonctionne en français et en allemand (l'application est en FR, DE et EN).
- **Mesurable.** Chaque jeu se termine par un scan de QR code : la rencontre entre dans l'album, l'indice
  de fédération monte, les paliers du Club approchent.

## Quel jeu pour quel événement

| Événement | Format | Animations conseillées |
|---|---|---|
| Apéro des membres, Apéro de Noël | debout | 🎯 Bingo des rencontres · 🤝 Tes 3 rencontres |
| Dîner, Soirée Wow | assis (apéritif debout) | 🎯 Bingo à l'apéritif · 🪑 Tables tournantes au repas · 🤝 Tes 3 rencontres |
| Conférence de presse | assis puis apéro | 🤝 Tes 3 rencontres · ❓ La question de la soirée |
| Visite d'entreprise | en petits groupes | 🔄 Trios express pendant la visite |
| Toute l'année | dans l'application | 🏔️ Paliers du Club · 🃏 Album |

## État des animations

| | Animation | Format | Principe | Travail de l'équipe |
|---|---|---|---|---|
| 🤝 | **Tes 3 rencontres** | toutes les soirées | Avant l'événement, chaque inscrit reçoit trois personnes qu'il ne connaît pas encore, avec leurs points communs et une phrase pour lancer la conversation. Un nouveau membre se voit présenter en priorité un pilier du Club. | Un clic : « Générer les rencontres » |
| 🎯 | **Bingo des rencontres** | debout | Chaque inscrit reçoit une grille 3 × 3 « Trouve quelqu'un qui… » : adore le ski de rando, parle allemand, est membre fondateur, déteste les réunions du lundi matin… On trouve la personne, on discute, on scanne son QR code : la case se coche. Une personne = une case. Une ligne = un verre au bar, carton plein = tirage au sort. | Cocher « bingo des rencontres » ; donner la liste des gagnants au bar |
| 🪑 | **Tables tournantes** | dîner assis | À chaque service, chacun change de table pour rencontrer de nouvelles personnes (38 invités, 3 services : environ 250 nouvelles paires et une seule répétition). | Cocher « repas assis », un clic, imprimer le plan |
| 🏔️ | **Paliers du Club** | toute l'année | Un objectif commun : à 20 % de membres qui se connaissent, une tournée de Petite Arvine ; à 35 %, une raclette ; à 50 %, une cuvée aux noms des membres… Chaque membre voit le prochain palier et combien de rencontres il manque. | Annoncer la récompense quand un palier tombe |
| 🃏 | **Album** | toute l'année | Chaque rencontre ajoute une carte ; objectifs personnels à 5, 15 et 30 cartes, puis l'album complet. | Aucun |

Le bingo n'est pas une grille tirée au hasard. Chaque grille est **calculée pour son joueur**
(`club/services/bingo.py`, 49 tests) :

- les cases ne décrivent que des personnes inscrites à la soirée (au moins deux par case quand c'est possible) ;
- elles favorisent les gens que le joueur n'a pas encore rencontrés, et pas son propre secteur ni sa région ;
- au moins une case pousse vers chacune de ses « 3 rencontres », de préférence une passion qu'ils partagent ;
- un carton plein reste toujours possible avec des personnes toutes différentes (vérifié par un algorithme
  de couplage biparti) ;
- au scan, c'est la case la plus rare que la personne peut remplir qui se coche ; le joker du centre ne vaut
  que pour une vraie nouvelle rencontre.

La grille se crée toute seule à la première ouverture, toujours la même pour un même joueur : l'équipe n'a rien
à préparer.

## Idées pour la suite

Effort de développement estimé pour une personne qui connaît le projet.

| | Idée | Format | Principe | Pour | Contre | Effort |
|---|---|---|---|---|---|---|
| 🕵️ | **L'anecdote mystère** | debout | Chacun reçoit l'anecdote d'un membre inconnu (« a traversé l'Atlantique à la voile ») et doit le retrouver, puis scanner son QR code. | Réutilise les anecdotes des cartes ; très drôle | Il faut que les anecdotes soient remplies | ½ jour |
| 🧭 | **Les parrains d'un soir** | toutes les soirées | Chaque nouveau membre est accueilli à l'entrée par un pilier qui lui présente deux personnes. La plateforme prévient le pilier : « Ce soir, tu accueilles Camille ». | Le meilleur levier d'intégration ; le matching sait déjà associer nouveaux et piliers | Dépend de la bonne volonté des piliers | ½ jour |
| 📺 | **Le mur des rencontres** | toutes les soirées | Un écran affiche en direct l'indice de fédération et les rencontres qui se font (« Camille et Lukas viennent de se rencontrer »), et le compte à rebours du prochain palier. | Crée de l'élan, rend le jeu collectif visible | Il faut un écran ; prénoms seulement, et seulement pour ceux qui l'acceptent | 1 jour |
| 🔄 | **Trios express** | debout ou visite | Toutes les 15 minutes, un gong : l'application montre à chacun son trio et un sujet (« ton meilleur souvenir de la Foire »). Même algorithme que les tables tournantes, avec des « tables » de 3. | Mélange même sans places assises | Un peu scolaire pour certains ; quelqu'un doit sonner le gong | 1 jour |
| ❓ | **La question de la soirée** | conférence, apéro | Une question légère (« ton tout premier job ? »), les réponses s'affichent sur l'écran et dans l'application. | Aucun effort, marche aussi à la conférence de presse | Engagement variable | ½ jour |
| 🍷 | **Dégustation à l'aveugle en duo** | debout | Des duos formés par l'application (secteurs différents) goûtent trois vins valaisans et votent ; le meilleur duo gagne une bouteille. | Terroir, conversation naturelle ; partenariat possible avec un exposant de la Foire | Logistique (vins, verres) | ½ jour + partenaire |
| 🗺️ | **La carte des origines** | arrivée | En arrivant, chacun pique une épingle sur une grande carte du Valais et de la Suisse. | Sans téléphone ; parle de l'ouverture au Haut-Valais et au-delà | Hors plateforme | aucun |
| 🎲 | **Le défi secret** | debout | Une seule mission par personne (« apprends un mot de patois à quelqu'un du Haut-Valais »), validée par un scan. | Plus léger que le bingo | Fait doublon avec le bingo | ½ jour |

## Recommandation

1. **Déjà livré, à garder** : les 3 rencontres à chaque soirée, le bingo des rencontres aux apéros, les tables
   tournantes aux dîners assis, les paliers du Club toute l'année.
2. **Prochaine étape** : les parrains d'un soir et l'anecdote mystère. Ils réutilisent ce qui existe
   (matching, anecdotes, QR code) et visent le problème n°1 : les nouveaux qui restent seuls.
3. **Avec un partenaire** : la dégustation à l'aveugle, idéalement avec un vigneron exposant à la Foire.
4. **À tester une fois avant de généraliser** : le mur des rencontres et les trios express. Ils plaisent
   beaucoup ou pas du tout selon les groupes.

Les récompenses (verre au bar, tournée, raclette, cuvée) sont des propositions à valider avec le comité.
Elles se modifient en une ligne dans `club/services/milestones.py`.
