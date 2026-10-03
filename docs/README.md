# Documentation du Club des Affaires

| Besoin | Document actuel |
|---|---|
| Présenter en deux minutes, ouvrir les livrables, préparer les questions ou soumettre le projet | [PITCH.md](PITCH.md) — conducteur, PowerPoint/GIF, lecteur hors ligne, PDF, textes FR/EN |
| Reprendre le travail de présentation et voir ce qui a été livré | [PLAN_PITCH.md](PLAN_PITCH.md) — plan coché, journal, vérifications et limites |
| Comprendre le code, les accès, les algorithmes, les performances et les coûts | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Exploiter, configurer les emails, stocker les photos et restaurer les données | [EXPLOITATION.md](EXPLOITATION.md), [exemple de cron](cron.example) |
| Recruter, fidéliser et choisir les animations d’une soirée | [MARKETING.md](MARKETING.md) — stratégie et jeux regroupés |
| Retrouver les droits des portraits de démonstration | [demo/PHOTOS.md](demo/PHOTOS.md) |

## État actuel et lancement

L’application propose les cartes, les synergies, les rencontres QR, le bingo, les tables, les paliers et les outils d’équipe. Photos normalisées avec aperçu, notes privées, remplaçants temporaires et langue de communication sont implémentés.

Les emails sont préparés ; SMTP et ordonnanceur restent à configurer et à tester avant activation. Les photos de production nécessitent un stockage privé durable. Hébergement suisse, import des membres, sauvegardes/restauration et contrôles de production font partie du lancement. Les cotisations sont facturées manuellement. Les montants promotionnels du parrainage restent désactivés par défaut.

Le deck comprend **7 diapositives principales + séparation + 7 annexes**, quatre GIF et un conducteur de **1:58**. Une répétition personnelle et une vérification des GIF dans PowerPoint installé sur l’ordinateur de scène restent à faire. Le lecteur HTML est vérifié hors ligne dans Chrome ; le PDF montre des images fixes.

## Historique conservé

Les décisions et preuves anciennes restent disponibles, sans encombrer les documents actifs :

- [Plan du hackathon](archive/PLAN_HACKATHON.md).
- [Plan des améliorations](archive/PLAN_AMELIORATIONS.md).
- [Recette des améliorations, 3 octobre](archive/RECETTE_AMELIORATIONS.md).
- [Ancienne présentation avec vidéo et son journal](archive/PLAN_PITCH_VIDEO.md).

Ces archives ne sont pas des listes de tâches à relancer automatiquement. Les textes de soumission ont été regroupés dans PITCH ; les animations dans MARKETING. Les captures temporaires et bases de reconstruction restent dans `pitch/.build/`, ignoré par Git.
