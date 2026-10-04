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
- [x] S2 — Séquences de diapositives, notes adaptées, PowerPoint/PDF/HTML statiques.
- [x] S3 — Documentation actualisée, vérifications des notes/ordre/cadrage/navigation et livraison poussée.

Chaque étape terminée est cochée, commitée et poussée sur main. La refonte initiale concernait uniquement la présentation ; la correction des portraits ci-dessous autorise maintenant un changement ciblé du template de l’application. Ne pas toucher à `db.sqlite3` ; le serveur 8000 de l’utilisateur reste indépendant. Captures sur une base jetable et un serveur 8010 appartenant au script ; refuser un port déjà occupé. Aucun email réel.

## Sources et reprise

- Source graphique commune par chapitre : `pitch/template.html` ; conducteur par écran : `pitch/story.json`.
- `pitch/build_deck.mjs` produit `pitch/deck.html`, les PNG et le PDF ; `pitch/build_pptx.py` produit le PowerPoint et ses notes.
- Captures réelles : `pitch/screens/` ; outils `capture_screens.mjs` et `make_screens.py`.
- `DEBUG=release` dans l’environnement : forcer `DEBUG=1` pour Django. python-pptx via uv isolé, sans dépendance ajoutée à l’application.
- Deux tests existants dépendent de l’heure/date : scan invité avant 01 h suisse et date allemande littérale. La recette complète utilise l’horloge du 3 octobre 2026 12:00 UTC, comme [le journal précédent](archive/PLAN_PITCH_VIDEO.md#tests-sensibles-au-passage-de-minuit), sans changer les assertions.

Le fichier temporaire PowerPoint `~$…pptx` présent au départ appartient à la session de l’utilisateur ; il n’est ni supprimé ni ajouté à Git.

### S1 — Captures terminées

Seize PNG réels : vitrine, connexion, accueil de Camille, album, synergies, cinq écrans rencontre, trois parrainage et trois staff. L’accueil personnel est capturé avant le scan : 2 / 49 cartes et paliers du Club visibles. Les coordonnées et la case bingo de Lukas sont vérifiées. La base jetable `pitch/.build/screens.sqlite3` et le serveur du script sont indépendants de la base utilisateur. Aucun email envoyé.

### S2 — Diapositives et notes terminées

18 diapositives principales fixes, séparation et sept annexes : 26 pages. Une capture distincte par diapositive, avec le texte anglais commun à chaque chapitre ; ordre demandé en couverture et aux diapositives 3–6. Les notes françaises sont propres à chaque écran, synchronisées avec `story.json` et PITCH. PNG identiques intégrés au PPTX, aucune animation ou vidéo intégrée et aucune avance chronométrée. Le PDF et le lecteur HTML présentent les mêmes captures ; clic ou clavier pour avancer.

Contrôles fichiers et navigateur réussis : 16 captures uniques, ordre, texte invariant par chapitre, notes, PDF/PPTX, image stable entre deux actions, navigation et annexes. Couverture, accueil personnel et synergies inspectés. Lecture synthétique locale Thomas à 150 mots/min : **226 mots, 93,77 s** de parole ; chaque morceau entre dans son repère. Le conducteur garde 118 s, soit environ 24 s pour les clics et pauses. Répétition personnelle à effectuer.

### S3 — Recette finale et livraison

Reconstruction complète depuis la base jetable réussie. Vérifications : 18 principales + séparation + 7 annexes, 26 pages PDF/PPTX, 16 captures distinctes, accueil public en couverture, ordre connexion / accueil Camille / album / rencontres. Texte anglais identique dans chaque séquence, notes françaises identiques entre conducteur / HTML / PowerPoint. Aucun média animé, aucune avance chronométrée. Image stable jusqu’à une action ; clic, clavier, notes, annexes et redimensionnement vérifiés dans Chrome hors ligne. Aucun texte coupé ou superposé aux captures ; aucun appel externe ni erreur JavaScript.

Documentation et références de reconstruction mises à jour. Anciens outils et assets GIF retirés du dossier actif ; historique conservé dans Git (`e41c8fd`) et le journal archivé. Tous les liens Markdown locaux restent valides. Fichier de verrouillage PowerPoint de l’utilisateur conservé et ignoré par Git.

Contrôle Django sans erreur. Recette SQLite avec horloge de référence : **401 tests en 94,58 s, OK, 6 cas PostgreSQL ignorés**. Les fixtures temporelles préexistantes restent inchangées. Aucune modification du code de l’application ; empreinte de `db.sqlite3` identique avant/après ; serveur de capture arrêté. Aucun email réel.

Les 226 mots ont été mesurés à **93,77 s** en lecture synthétique locale ; chaque morceau tient dans son repère. La répétition personnelle avec les 17 changements d’écran reste nécessaire. Les exports contiennent uniquement des PNG fixes ; réouvrir le fichier dans PowerPoint pour charger cette nouvelle version.

## Sauvegardes

### Correction des portraits — demande du 4 octobre

- [x] P1 — Afficher le même portrait dans l’album, les rencontres de l’accueil et celles de l’événement ; vérifier les accès et le repli sur les initiales.
- [x] P2 — Refaire la capture des rencontres et actualiser les exports ; conserver les modifications et notes du PowerPoint existant.

Cause : `_intro.html` affichait toujours les initiales. Le correctif réutilise `member_portrait`, comme les cartes de l’album : photo privée via sa route protégée, portrait de démo autorisé ou initiales si aucun portrait disponible. Les règles d’accès et les données restent inchangées.

P1 vérifiée : même URL de portrait, image chargée dans Chrome sur les trois pages, en FR/DE/EN et aux largeurs 390 / 1120 px. Rendu court et complet contrôlé pour portrait de démo, photo privée, fichier manquant et mode hors démo sans photo. CSS recompilé. Contrôle Django sans erreur ; **401 tests en 93,67 s, OK, 6 cas PostgreSQL ignorés**, avec l’horloge de référence documentée ci-dessus. Aucun test existant modifié.

P2 vérifiée : capture réelle `screens/web/004.png` refaite sur la base jetable ; portrait de Lukas chargé avant la prise. PNG de la diapositive 6 et PDF reconstruits ; HTML réutilise cette même capture. Dans le PowerPoint déjà retouché par l’utilisateur, seul `ppt/media/image6.png` a été remplacé : tous les autres contenus, notamment les dernières notes, sont conservés octet pour octet. Sauvegarde locale antérieure à ce remplacement : `pitch/.build/pitch-before-image-refresh.pptx`. Les notes retouchées dans PowerPoint restent propres à ce fichier ; elles ne sont pas écrasées par celles du conducteur.

Contrôles exports réussis : 26 pages, 18 principales, 16 captures, ordre et progression manuelle ; contrôle des notes conservées et de tous les autres contenus du PPTX contre sa sauvegarde. Chrome : image stable jusqu’au clic, navigation, notes, annexes, redimensionnement et absence de texte coupé ou superposé. Capture et diapositive inspectées visuellement. Empreinte de `db.sqlite3` inchangée ; serveur 8010 arrêté ; aucun email réel. Réouvrir le PowerPoint pour charger l’image corrigée.

| Étape | Commit | État |
|---|---|---|
| S1 — captures et accueil de Camille | `6a27fd7` | Poussé sur main |
| S2 — diapositives fixes et notes | `3504b6b` | Poussé sur main |
| S3 — reconstruction et recette finales | Commit contenant cette ligne | Poussé avec les livrables finaux |
| P1 — portraits dans les rencontres du site | `8a4ca7e` | Poussé sur main |
| P2 — capture et exports, notes conservées | Commit contenant cette ligne | Poussé avec les livrables corrigés |

Livraison : [PowerPoint](pitch/Club-des-Affaires-pitch.pptx), [PDF](pitch/Club-des-Affaires-pitch.pdf), [HTML local](pitch/deck.html), [conducteur](PITCH.md). Toutes les étapes de cette demande sont terminées.
