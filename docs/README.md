# Documentation du Club des Affaires

| Besoin | Document actuel |
|---|---|
| Présenter en deux minutes, ouvrir les livrables, préparer les questions ou soumettre le projet | [PITCH.md](PITCH.md) — conducteur, PowerPoint statique, lecteur hors ligne, PDF, textes FR/EN |
| Reprendre le travail de présentation et voir ce qui a été livré | [PLAN_PITCH.md](PLAN_PITCH.md) — plan coché, journal, vérifications et limites |
| Comprendre le code, les accès, les algorithmes, les performances et les coûts | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Exploiter, configurer les emails, stocker les photos et restaurer les données | [EXPLOITATION.md](EXPLOITATION.md), [exemple de cron](cron.example) |
| Recruter, fidéliser et choisir les animations d’une soirée | [MARKETING.md](MARKETING.md) — stratégie et jeux regroupés |
| Retrouver les droits des portraits de démonstration | [demo/PHOTOS.md](demo/PHOTOS.md) |

## État actuel et lancement

L’application propose les cartes, les synergies, les rencontres QR, le bingo, les tables, les paliers et les outils d’équipe. Photos normalisées avec aperçu, notes privées, remplaçants temporaires et langue de communication sont implémentés.

Les emails sont préparés ; SMTP et ordonnanceur restent à configurer et à tester avant activation. Les photos de production nécessitent un stockage privé durable. Hébergement suisse, import des membres, sauvegardes/restauration et contrôles de production font partie du lancement. Les cotisations sont facturées manuellement. La démo montre l’offre de parrainage : 350 CHF la première année, puis 500 CHF/an. Hors démo, elle reste désactivée par défaut ; `REFERRAL_OFFER_ENABLED` permet de l’activer ou de la désactiver explicitement.

Le deck suit **7 chapitres sur 19 diapositives fixes + séparation + 7 annexes** (27 pages), avec un conducteur de **1:58**. Chaque changement d’écran est manuel, dans PowerPoint, HTML et PDF. Une répétition personnelle avec les 18 changements reste à faire sur l’ordinateur de scène.

## Historique conservé

Les décisions et preuves anciennes restent disponibles, sans encombrer les documents actifs :

- [Plan du hackathon](archive/PLAN_HACKATHON.md).
- [Plan des améliorations](archive/PLAN_AMELIORATIONS.md).
- [Recette des améliorations, 3 octobre](archive/RECETTE_AMELIORATIONS.md).
- [Ancienne présentation avec vidéo et son journal](archive/PLAN_PITCH_VIDEO.md).
- [Version intermédiaire avec GIF et sa recette](archive/PLAN_PITCH_GIFS.md).

Ces archives ne sont pas des listes de tâches à relancer automatiquement. Les textes de soumission ont été regroupés dans PITCH ; les animations dans MARKETING. Les captures temporaires et bases de reconstruction restent dans `pitch/.build/`, ignoré par Git.
