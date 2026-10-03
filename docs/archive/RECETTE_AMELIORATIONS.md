# Recette des améliorations — 3 octobre 2026

> **Archive du 3 octobre 2026.** Ce document conserve les décisions et les preuves de l’époque ; ce n’est pas une liste de tâches à exécuter automatiquement. Pour l’état actuel : [index de documentation](../README.md) et [exploitation](../EXPLOITATION.md).

Le code des phases 0 à 8 est livré par commits séparés. Cette recette clôt la préparation technique de la phase 9.
Les envois réels, le cron et le volume privé durable de production restent à configurer et valider ; ils ne sont pas activés.

## Tests automatisés

| Environnement isolé | Résultat |
|---|---|
| SQLite en mémoire | 262 tests, 69,3 s, OK ; 6 tests de concurrence réservés à PostgreSQL |
| PostgreSQL dédié sur `127.0.0.1:55439` | 262 tests, 74,1 s, OK, sans test ignoré |
| Contrôles Django | `check` OK ; `makemigrations --check --dry-run` sans changement |
| Réglages de production de recette | `check --deploy` sans problème (2 contrôles HSTS du domaine partagé explicitement désactivés) ; `collectstatic` OK, 531 fichiers dans un répertoire temporaire |
| Traductions/CSS | Catalogues FR/DE/EN extraits et compilés, aucune traduction manquante ; CSS Tailwind recompilé ; `git diff --check` OK |

Les six tests PostgreSQL exécutent deux opérations simultanées : réservation d'un email, publication d'un événement,
validation de la même demande de remplacement, validation du même invité pour deux titulaires au même événement,
acceptation d'une invitation et préparation d'un récapitulatif mensuel. Une seule création/réservation aboutit selon l'invariant.

La matrice classe toutes les routes et conserve les contrôles anonyme/membre/staff. Elle est complétée par les accès
invité actif et expiré, y compris les URL directes de fiche, photo, note, vCard, événement et scan. Les tests couvrent :

- Blocage immédiat d'une session invitée ouverte après expiration, avant passage du job ; refus d'un nouveau lien
  magique et d'un jeton présenté après expiration ; réponse publique sans révélation d'identité.
- Rencontres entre personnes présentes, sans connexion ni coordonnées transmises au titulaire absent ; coparticipation
  sans déblocage automatique des contacts ; scans avec contexte vérifié lorsque plusieurs événements ont lieu le même jour.
- Notes sentinelles visibles seulement par leur auteur, absentes des réponses des autres rôles et des sorties partagées.
- Présence réelle dans les tables et badges, langues propres à l'invité, retrait des plans périmés ; historique conservé
  après veille et même profil/QR réactivé par une nouvelle invitation.
- Photo normalisée sans métadonnées, contrôle de visibilité, retrait/remplacement/suppression, nettoyage après rollback
  du profil et de l'admin ; une erreur de suppression de l'ancien fichier après commit conserve la nouvelle photo.
- Relances arrêtées après réponse, préférences revérifiées avant envoi, résultats SMTP incertains sans renvoi automatique,
  consentements mensuels et désabonnement signé avec confirmation POST/CSRF.
- Blocage des backends de messagerie réels en mode démo, pour la file et les liens de connexion directs.

Le diagnostic « Missing private portrait » observé dans les tests correspond au cas volontaire de fichier manquant.
Il ne fait pas échouer la lecture d'une fiche : l'avatar revient aux initiales.

## Copie de la base et migrations

Une sauvegarde SQLite privée a été prise avant la correction de l'erreur locale `no such column: club_member.demo_photo_key`.
Les migrations 0004 à 0011 ont ensuite été appliquées à la base locale ; le serveur existant répond HTTP 200 sur `/`.
Aucune commande de réinitialisation n'a été utilisée sur cette base.

La même sauvegarde a servi à une recette distincte : copie isolée du schéma arrêté à 0003, migrations jusqu'à 0011,
puis comparaison de **toutes les colonnes initiales et de toutes les lignes** des douze tables `club_*` existantes.
Toutes les valeurs initiales ont été conservées, dont :

| Données | Lignes conservées |
|---|---:|
| Profils | 50 |
| Connexions réelles | 181 |
| Réponses de présence | 200 |
| Événements | 5 |
| Demandes d'invitation | 3 |
| Propositions de rencontres | 56 |
| Affinités de profils | 307 |
| Étiquettes d'affinité | 30 |

Aucune campagne rétroactive n'a été créée. Tous les profils existants ont conservé leur qualité de membre régulier.
Les tables de plans, places, bingo et remplaçants étaient vides dans cette copie ; leurs schémas ont été migrés.

## Recette navigateur

Chrome 154.0.8037.93, données fictives dans une base séparée, serveur de recette sur le port 8877.
Les sessions et uploads de cette recette n'utilisent pas la base locale du serveur de l'utilisateur.

90 pages ont été ouvertes : 15 parcours × FR/DE/EN × 390/1 280 px. Parcours : demande d'invitation avec tarif,
accueil/album/profil membre, fiche avec note personnelle, formulaire de remplacement, accueil/album/profil/événement
invité, tableau de bord et préparation staff, demandes de remplacement et compteurs de campagnes dans l'admin, badges.

Les contrôles ont trouvé zéro débordement horizontal, image chargée cassée, erreur JavaScript/CSP et requête externe.
Les captures de la demande d'invitation anglaise, du profil allemand, de l'événement invité français et des badges
ont été inspectées. Les libellés natifs du sélecteur de fichier suivent la langue du navigateur/système.
Le PDF de badges contient une page A4 (`MediaBox` environ 595 × 842 points), avec l'identité et le QR propres à l'invité.

30 aperçus d'emails HTML ont aussi été ouverts : bienvenue, annonce, relance, récapitulatif et accès invité,
en FR/DE/EN aux deux largeurs. Aucun débordement, erreur ni requête externe ; aucune note privée dans ces rendus.
Les liens de connexion utilisés dans ces fichiers sont factices. Aucun email n'a été envoyé pendant cette recette.
Cela vérifie les rendus HTML locaux, pas leur affichage dans chaque logiciel de messagerie ni leur réception réelle.

Artefacts locaux temporaires : `/tmp/club-browser-artifacts/` (captures, PDF, résultats des deux parcours),
`/tmp/club-delivery-sqlite.log`, `/tmp/club-delivery-postgres.log`. Aucun cookie, jeton ou sauvegarde n'est ajouté au dépôt.

## Jobs préparés et limites d'exploitation

Le lanceur `scripts/run-job.sh` et `docs/cron.example` préparent les passages toutes les 15 minutes et chaque heure.
Les deux commandes ont été exécutées via ce lanceur avec `--dry-run` sur la base fictive : deux accès en attente,
aucun rappel ni récapitulatif dû, aucun email envoyé, aucun changement des profils/utilisateurs/campagnes/envois.

Restent à faire avant activation réelle :

- Configurer le fournisseur et l'expéditeur SMTP, vérifier SPF/DKIM/DMARC, tester une adresse d'équipe explicitement autorisée.
- Activer un seul ordonnanceur et les variables nécessaires après cet essai. Aucun cron n'a été installé.
- Provisionner le stockage privé durable et ses sauvegardes, puis tester upload/redémarrage/restauration avant l'ouverture en production.
- Confirmer les paramètres métier : tarif, règles de remplacement, délai de 48 h et conservation des invités en veille.

La tâche 9.6 reste ouverte pour l'essai et l'activation externes. La procédure d'exploitation, d'export/suppression et
de restauration figure dans [EXPLOITATION.md](../EXPLOITATION.md). Les paiements restent sur facture manuelle.
