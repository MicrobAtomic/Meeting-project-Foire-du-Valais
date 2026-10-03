# Présentation en deux minutes — suivi et reprise

Demande du 4 octobre 2026 : intégrer A1 au récit principal, remplacer la vidéo imposant son rythme par des GIF lents, conserver le contrôle manuel, alléger les Markdown. Ce plan remplace [la version vidéo](archive/PLAN_PITCH_VIDEO.md).

## Décisions

Sept diapositives principales, anglais à l'écran et français dans les notes, **118 secondes prévues** :

| Diapo | Temps | Preuve / rôle |
|---|---|---|
| 1 — Promesse | 0–8 s | Plus jamais d'inconnus au Club |
| 2 — Problème et solution | 8–24 s | ≈ 50 membres, 4–5 soirées ; les quatre piliers de A1 intégrés |
| 3 — Avant la soirée | 24–46 s | GIF : accueil, connexion, album, synergies avec Lukas |
| 4 — Pendant la soirée | 46–74 s | GIF : badge, confirmation de rencontre, bingo ; coordonnées et progrès collectif |
| 5 — Entre les soirées | 74–86 s | GIF parrainage ; relances et récapitulatif mensuel regroupés en une idée |
| 6 — Pour l'équipe | 86–104 s | GIF tableau de bord, préparation, tables ; trois explications courtes |
| 7 — Lancement | 104–118 s | Coût estimatif ≈ 30 CHF/mois, étapes de lancement, factures manuelles |

Critique du découpage initial : une visite exhaustive des écrans et trois sous-parties marketing n'entrent pas en deux minutes. Connexion très courte ; priorité aux synergies et aux rencontres, qui distinguent le produit. Les fonctionnalités secondaires restent dans les annexes. Pas de diapositive A1 supplémentaire : ses quatre piliers sont la réponse au problème, sur la diapositive 2.

## Vérifications externes

- [Microsoft](https://support.microsoft.com/en-gb/powerpoint/add-an-animated-gif-to-a-slide?nochrome=true), consulté le 4 octobre : GIF pris en charge en diaporama dans PowerPoint installé Mac/Windows ; PowerPoint web ne les anime pas en diaporama. Une lecture HTML locale avec clavier sera fournie.
- La [page publique du hackathon](https://ai-weeks.ch/events/hack-vs) annonce les présentations mais ne précise pas de contrainte MP4. La mention « uniquement MP4 » vient de l'ancien plan, sans source publique confirmée. Le MP4 existant sera conservé comme alternative, sans imposer son rythme à cette nouvelle version.
- Aucun email réel ; SMTP/cron non activés. Parrainage montré sans remise promotionnelle (offre désactivée). Hébergement suisse et import sont des étapes de lancement, pas une production déjà déployée.

## Livraisons

- [x] G1 — Récit, timing, contraintes et plan de reprise enregistrés.
- [ ] G2 — Quatre GIF de l'application réelle, lents, sur base jetable ; manifestes et reconstruction documentés.
- [ ] G3 — Deck, GIF intégrés au PPTX, PDF avec images fixes, lecture HTML manuelle et notes synchronisées.
- [ ] G4 — Documents regroupés, anciens plans archivés, liens corrigés, index utile.
- [ ] G5 — Vérification des exports, cadrages, animations et durée orale ; recette et livraison poussées.

Chaque étape terminée est cochée, commitée et poussée sur `main`. L'application et `db.sqlite3` restent intactes. Les captures utilisent uniquement `docs/pitch/.build/` (ignoré par Git).

## Reprise

État initial : `4dde623`, dépôt propre. Chrome, ffmpeg, Node, puppeteer-core et uv disponibles. `DEBUG=release` dans l'environnement : forcer `DEBUG=1` pour Django. python-pptx s'exécute via uv isolé, sans dépendance ajoutée à l'application. Port de capture 8010 ; refuser un port déjà utilisé.

Deux tests existants sont dépendants de l'heure/date : `GuestAccessTests.test_scan_attaches_only_real_people_and_notes_never_reach_the_principal` (scan simulé la veille avant 01 h suisse) et `NoFrenchLeftTests.test_german_pages_really_are_german` (date littérale 15 octobre). La suite précédente passe avec horloge figée au 3 octobre 2026 12:00 UTC : 401 tests, 6 réservés à PostgreSQL ignorés. Diagnostic et commande dans [l'ancien journal](archive/PLAN_PITCH_VIDEO.md#tests-sensibles-au-passage-de-minuit). Ne pas modifier les assertions pour cette tâche de présentation.
