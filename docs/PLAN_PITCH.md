# Présentation avec captures fixes — suivi et reprise

Demande actuelle : remplacer chaque image des GIF par une diapositive fixe, conserver le même texte anglais dans chaque séquence, répartir les notes françaises selon l’écran et garder l’avance entièrement manuelle. Cette version remplace [les GIF](archive/PLAN_PITCH_GIFS.md).

## Ordre et timing indicatif

**18 diapositives principales, 118 s prévues**, puis séparation et sept annexes (26 pages au total).

| Diapos | Images / rôle | Temps du chapitre |
|---|---|---|
| 1 | Promesse + accueil public, ancienne première image du GIF de la diapo 3 | 0:00–0:08 |
| 2 | Défi et quatre piliers | 0:08–0:24 |
| 3–6 | Connexion → accueil personnel de Camille → album → rencontres proposées | 0:24–0:46 |
| 7–11 | QR de Lukas → confirmation → carte ajoutée → coordonnées → bingo | 0:46–1:14 |
| 12–14 | Lien de parrainage → QR de parrainage → demande parrainée | 1:14–1:26 |
| 15–17 | Tableau de bord staff → préparation → tables | 1:26–1:44 |
| 18 | Coût et lancement | 1:44–1:58 |

La deuxième image de l’ancien GIF web (connexion) devient la première de la séquence web ; sa première image (vitrine) passe en couverture. Le nouvel accueil personnel est capturé avant la rencontre, pour montrer la progression initiale de Camille. Aucun changement automatique d’image, aucune attente de boucle.

## Livraison

- [x] S1 — Plan et captures fixes ; nouvel accueil de Camille, manifestes et reconstruction isolée.
- [ ] S2 — Séquences de diapositives, notes adaptées, PowerPoint/PDF/HTML statiques.
- [ ] S3 — Documentation actualisée, vérifications des notes/ordre/cadrage/navigation et livraison poussée.

Chaque étape terminée est cochée, commitée et poussée sur main. Ne pas toucher à l’application ni à `db.sqlite3` ; le serveur 8000 de l’utilisateur reste indépendant. Captures sur une base jetable et un serveur 8010 appartenant au script ; refuser un port déjà occupé. Aucun email réel.

## Sources et reprise

- Source graphique commune par chapitre : `pitch/template.html` ; conducteur par écran : `pitch/story.json`.
- `pitch/build_deck.mjs` produit `pitch/deck.html`, les PNG et le PDF ; `pitch/build_pptx.py` produit le PowerPoint et ses notes.
- Captures réelles : `pitch/screens/` ; outils `capture_screens.mjs` et `make_screens.py`.
- `DEBUG=release` dans l’environnement : forcer `DEBUG=1` pour Django. python-pptx via uv isolé, sans dépendance ajoutée à l’application.
- Deux tests existants dépendent de l’heure/date : scan invité avant 01 h suisse et date allemande littérale. La recette complète utilise l’horloge du 3 octobre 2026 12:00 UTC, comme [le journal précédent](archive/PLAN_PITCH_VIDEO.md#tests-sensibles-au-passage-de-minuit), sans changer les assertions.

Le fichier temporaire PowerPoint `~$…pptx` présent au départ appartient à la session de l’utilisateur ; il n’est ni supprimé ni ajouté à Git.

### S1 — Captures terminées

Seize PNG réels : vitrine, connexion, accueil de Camille, album, synergies, cinq écrans rencontre, trois parrainage et trois staff. L’accueil personnel est capturé avant le scan : 2 / 49 cartes et prochain dîner visibles. Les coordonnées et la case bingo de Lukas sont vérifiées. La base jetable `pitch/.build/screens.sqlite3` et le serveur du script sont indépendants de la base utilisateur. Aucun email envoyé.
