# Plan des améliorations — profils, remplaçants, notes et emails

> Demande du 3 octobre 2026. Audit du dépôt au commit `b4b0816`.
> Ce document décrit du travail **à réaliser** : ses cases ne signifient pas que les fonctionnalités existent.
> Destinataire : une IA qui a besoin de tâches courtes, de décisions explicites et de vérifications précises.
> Pendant l'exécution de ces améliorations, suivre ce document ; conserver `PLAN.md` comme historique du hackathon.

## Suivi d'exécution

L'exécution a été demandée le 3 octobre 2026. Les commits et push sont autorisés à chaque solution terminée.
Pillow, nécessaire à l'upload décrit dans le plan, fait partie de cette implémentation demandée.
Les envois réels et les changements d'hébergement restent à configurer séparément ; les tests utilisent une base dédiée.

| Phase | État | Vérifications / livraison |
|---|---|---|
| 6 | Terminée ; SMTP/cron non activés | 222 tests SQLite (2 cas PostgreSQL seuls) ; 219 tests PostgreSQL verts, dont publications et réservations concurrentes ; backend mémoire uniquement |
| 5 | Terminée | 206 tests verts ; acceptation idempotente et rollback vérifiés ; préférences et langue enregistrées uniquement pour soi |
| 4 | Livrée ; activation production en attente du volume | 201 tests verts ; normalisation et accès privé vérifiés ; Pillow 12.3 ; upload production désactivé ; procédure dans EXPLOITATION.md |
| 3 | Terminée | 196 tests verts ; isolation des auteurs, CSRF, CSP, échappement, cache, contraintes et absence de fuite vérifiés |
| 2 | Terminée | 189 tests verts ; 3 JPEG 256 × 256 vérifiés ; collectstatic OK ; licence et sources dans docs/demo/PHOTOS.md |
| 1 | Terminée | 187 tests verts ; tarif configurable vérifié sur GET/POST et FR/DE/EN ; offre désactivée par défaut |
| 0 | Terminée | 185 tests SQLite verts ; contrôles Django et migrations verts ; documentation et aides admin corrigées |

## 1. Ce que Claude Code a effectivement livré

L'application fonctionne déjà comme un annuaire privé avec rencontres par QR, événements, réponses de présence,
matching, tables tournantes, espace staff, demandes d'invitation et interface FR/DE/EN.
Les changements récents comprennent les paliers, les outils de remise à zéro de la démo, des modèles pour le bingo
et les remplaçants, ainsi que la traduction des contenus d'événements.

Vérifications réalisées pour cet audit :

- **185 tests passent sur SQLite**, en 34,5 secondes ; le README et l'architecture indiquent encore 170.
- `manage.py check` ne signale aucun problème ; `makemigrations --check --dry-run` ne détecte aucun changement.
- Le répertoire de travail était propre avant la rédaction du présent document.
- Les tests PostgreSQL, le navigateur et le déploiement n'ont pas été rejoués pendant cet audit.

| Sujet | État vérifié dans le code | Conséquence pour la suite |
|---|---|---|
| Photo de profil | Aucun champ photo dans `Member`. `_card.html` affiche les initiales. Pillow est absent. | Ajouter d'abord des illustrations de démo, puis un upload privé et durable. |
| Remplaçant | `Substitute` existe avec une contrainte `(event, member)`. Aucun formulaire, service, écran ni enregistrement admin. `attendees()` ne lit que les RSVP des membres. | Réutiliser le modèle, mais construire le parcours et les autorisations. |
| Notes personnelles | Aucun modèle ni parcours. | Créer une table séparée avec un auteur ; ne pas mettre une note commune sur `Member`. |
| Emails | Seuls les liens de connexion sont envoyés, sur demande ou par action admin. SMTP est configurable. | Ajouter des campagnes, un suivi des envois et une commande périodique. |
| Invitation acceptée | L'admin édite simplement `status`. Les champs `member` et `welcome_sent_at` ne sont pas alimentés. | Le texte d'aide promet à tort une création de compte et un email ; terminer ce parcours avant le récapitulatif des nouveaux membres. |
| Langue d'invitation | Le modèle a un champ `language`, mais `public.join` ne le renseigne pas. | Enregistrer la langue du formulaire pour préparer l'accueil et les emails. |
| Cotisation | `MEMBERSHIP_PRICE = 500` ; tarif montré dans l'espace de parrainage, absent de `/rejoindre/`. | Afficher le montant configuré et préciser la facturation manuelle. |
| Parrainage | Les montants 350 CHF et 100 CHF figurent dans les réglages et dans l'interface, avec un commentaire « à valider ». | Ne pas les présenter comme une offre validée sans confirmation métier. |
| Bingo | Modèles et données d'exemple uniquement ; aucun service de génération ni affichage de grille ni validation au scan. `ANIMATIONS.md` le présente comme livré. | Corriger cette documentation. Implémenter le bingo serait un chantier distinct. |

Points à conserver : Django 5.2, templates, Tailwind local, JS vanilla, fermeture par défaut, CSRF, CSP stricte,
coordonnées débloquées après une rencontre, données fictives et tests existants. Une reconstruction du projet
n'apporterait rien à cette demande.

**Particularité de l'environnement observée :** le shell fournit `DEBUG=release`. Les réglages attendent exactement
`DEBUG=1` pour le développement ; un lancement sans cette valeur provoque des redirections HTTPS et de faux échecs
de tests. Utiliser les commandes explicites ci-dessous, sans changer les réglages de sécurité de production.

## 2. Décisions recommandées

Ces décisions sont des propositions d'implémentation. Les paramètres métier à confirmer sont regroupés en section 12.

### Photos

Pour la démo, ajouter trois portraits de banque d'images, associés à des profils fictifs et servis localement.
Garder les initiales pour les autres profils. Trois portraits suffisent à démontrer le rendu sans fabriquer 50
identités photographiques. Pour les vrais membres, prévoir un upload optionnel, retrait possible et lecture protégée.

La [licence Pexels](https://www.pexels.com/fr-fr/license/) autorise l'utilisation gratuite et les modifications,
avec des restrictions, notamment sur le soutien publicitaire implicite et les représentations offensantes.
Les [conditions Pexels](https://www.pexels.com/fr-fr/terms-of-service/) rappellent que les droits de tiers,
dont ceux des personnes représentées, peuvent subsister. La gratuité ne suffit donc pas à garantir tous les usages.
Pour la démo, signaler « profils fictifs, portraits illustratifs » et ne pas présenter ces personnes comme de vrais
membres ou comme des témoins recommandant le Club. Si le contexte d'usage ne peut pas être établi, garder les initiales.

### Absence et remplacement

Retenir **une personne distincte, un QR distinct et un accès temporaire**, puis mettre le compte invité en veille.
Les rencontres appartiennent à la personne présente. Ne pas créer de `Connection` entre le titulaire absent et les
personnes rencontrées par son remplaçant : cela ouvrirait leurs coordonnées au titulaire et fausserait les statistiques.

| Solution | Intérêt | Limite | Choix |
|---|---|---|---|
| Le remplaçant utilise le compte du titulaire | Peu de développement | Identité, coordonnées, notes et historique mélangés ; partage de compte | Écartée |
| On copie toutes les rencontres au titulaire | Le titulaire récupère un carnet d'adresses | Déblocage de contacts sans rencontre réelle ; compteurs inexacts | Écartée |
| Profil invité séparé, accès borné dans le temps | Identité exacte, QR et algorithmes réutilisables | Il faut gérer la fin d'accès et les règles de visibilité | Retenue |
| Compte invité + bilan de contacts pour le titulaire | Peut servir ultérieurement à un suivi d'entreprise | Nécessite une politique de partage acceptée par les personnes concernées | Hors de cette version |

Proposition de durée : accès dès la validation du staff, jusqu'à **48 heures après le début de l'événement**.
La mise en veille bloque la connexion ; elle conserve temporairement la fiche et les vraies rencontres.
Une nouvelle invitation peut réactiver la même personne, sans fusionner deux individus par leur nom.
La durée de conservation après mise en veille doit être décidée avant de traiter de vraies données.

### Notes

Une note est le mémo de **A sur B**, visible seulement par A dans l'application.
Exemple : « Reprendre la discussion sur le projet de rénovation en novembre. »
La note n'est visible ni par B, ni par les autres membres, ni dans les écrans du staff.
Le titulaire d'un remplaçant ne reçoit jamais les notes de celui-ci.

La protection proposée porte sur les accès dans l'application. Un opérateur qui dispose des accès serveur ou base
peut techniquement accéder aux données ; il ne s'agit pas d'un coffre avec chiffrement de bout en bout.
Prévoir des droits d'exploitation limités et des sauvegardes protégées. Les notes sur autrui peuvent aussi constituer
des données personnelles : ne pas promettre leur exclusion absolue d'une demande légale d'accès. Voir le
[PFPDT sur le droit d'accès](https://www.edoeb.admin.ch/fr/droit-dacces).

### Emails

- Une annonce par événement, lorsque le staff le **publie**, pas à chaque sauvegarde de l'admin.
- Deux relances maximum pour les personnes sans réponse : J−14 et J−3, espacées d'au moins 72 heures de tout
  précédent email de cet événement. Une réponse « non » arrête aussi les relances.
- Un récapitulatif des nouveaux membres par mois, uniquement si de nouveaux profils peuvent être présentés.
- Des réglages séparés pour annonces/relances et récapitulatif mensuel ; les emails de connexion restent disponibles.
- Un destinataire par message, aucune liste de membres dans `To` ou `Cc`.
- Une file persistante en base et une commande Django planifiée ; aucune infrastructure Celery/Redis pour 50–200 membres.

Pour le récapitulatif : prénom, nom, entreprise, secteur et une courte accroche choisie par le membre, puis un lien
vers sa fiche. Ne pas inclure téléphone, email personnel, LinkedIn, QR, notes, ni carte complète.
La première version peut utiliser les initiales dans l'email : les photos privées restent sur le site.

### Paiements et tarif

Conserver la facturation et le paiement manuels. Afficher sur la demande d'invitation :

> Cotisation annuelle : 500 CHF. Paiement sur facture, géré par l'équipe du Club.
> Envoyer une demande d'invitation ne déclenche aucun paiement.

Le `500` doit provenir de `settings.MEMBERSHIP_PRICE`. Le montant existe dans le dépôt ; sa validité commerciale
reste à confirmer. Aucune intégration Stripe, TWINT ou création de facture dans cette version.

## 3. Mode d'emploi pour l'IA exécutante

Lire `CLAUDE.md`, ce document, puis les fichiers de la tâche en cours avant d'écrire du code.
La mission historique de finir `PLAN.md` ne s'applique pas lorsqu'on demande explicitement d'exécuter ce nouveau plan.
Les modifications de modèles, services et réglages décrites ici sont nécessaires aux tâches correspondantes ;
elles ne donnent pas carte blanche pour refactorer le reste.

1. Faire une seule tâche numérotée à la fois, dans l'ordre. Ne pas commencer une autre fonctionnalité au milieu.
2. Ajouter les tests métier et de confidentialité utiles, puis faire passer les tests de la phase.
3. Avant de terminer une phase, lancer la suite complète, contrôler le diff et cocher seulement les tâches terminées.
4. Conserver les assertions existantes. Ajouter des cas et classer les nouvelles routes dans la matrice d'accès.
5. Chaque nouveau texte visible est traduit en FR, DE suisse et EN ; recompiler les `.mo`.
6. Si des classes CSS changent, recompiler Tailwind avec `--minify`. Ne pas assouplir la CSP pour une image ou un widget.
7. Aucun `seed_demo --reset` sur une base contenant des données réelles ; aucune migration destructive.
8. Pousser chaque solution vérifiée comme demandé pour cette exécution. Les envois réels et l'activation du cron restent à configurer séparément.
9. Ne pas introduire une dépendance Python sans l'accord prévu par `CLAUDE.md`. La phase upload nécessite Pillow ;
   préparer le changement et ses raisons avant cette étape. Les portraits statiques de démo n'en ont pas besoin.
10. Reporter dans ce document le résultat des vérifications et les questions métier restantes après chaque phase.

Commandes de référence pour le développement et les tests :

```bash
env DEBUG=1 DATABASE_URL=sqlite:///:memory: .venv/bin/python manage.py test club
env DEBUG=1 DATABASE_URL=sqlite:///:memory: .venv/bin/python manage.py check
env DEBUG=1 DATABASE_URL=sqlite:///:memory: .venv/bin/python manage.py makemigrations --check --dry-run
./tailwindcss -i assets/css/input.css -o static/css/app.css --minify
```

La base en mémoire convient aux tests et aux contrôles de schéma. Pour un serveur de développement persistant,
utiliser une base locale dédiée. Ne pas appliquer `migrate` sur une base en mémoire dans l'espoir de la retrouver
dans la commande suivante. Les commandes de test de chaque phase doivent aussi être précédées de `env DEBUG=1`.

## 4. Ordre de livraison et points d'arrêt

| Phase | Livrable | Dépendance | Effort indicatif, développement et vérification |
|---|---|---|---|
| 0 | Point de départ vérifié et documentation honnête | — | 30–60 min |
| 1 | Cotisation et mention de facture manuelle | 0 | 1–2 h |
| 2 | Portraits illustratifs de démo | 1 | 2–4 h |
| 3 | Notes privées par auteur | 2 | 4–8 h |
| 4 | Upload de photo avec stockage privé | 3, accord Pillow et stockage | 1–2 jours |
| 5 | Parcours d'acceptation, langue et préférences | 4 | ½–1 jour |
| 6 | File d'emails, publication et relances | 5 | 1–2 jours |
| 7 | Récapitulatif mensuel des nouveaux membres | 6 | ½–1 jour |
| 8 | Remplaçants : identité, présence, droits et veille | 7 | 2–4 jours |
| 9 | Recette, documentation et préparation à l'exploitation | 8 | 1–2 jours |

Ces durées sont des estimations, pas une promesse pour une IA donnée. Après la phase 2, la démo est améliorée
sans toucher au calcul des rencontres. Les phases suivantes sont des lots supplémentaires : ne pas les précipiter
avant le rendu du hackathon. Si le temps manque, laisser les cases ouvertes et décrire le périmètre effectivement livré.

## 5. Phases 0 à 2 — socle, tarif et portraits de démo

### Phase 0 — Fixer le point de départ

- [x] **0.1** Lire `club/models.py`, `club/decorators.py`, `club/views/member.py`, `club/views/events.py`,
  `club/services/events.py`, `club/admin.py`, `club/views/public.py`, les tests d'accès et `config/settings.py`.
  Relever le commit courant et les changements locaux ; ne pas écraser des modifications humaines.
- [x] **0.2** Exécuter les trois premières commandes de la section 3. Si un échec est déjà présent,
  le diagnostiquer avant d'ajouter une fonctionnalité. Ne pas modifier une assertion pour obtenir du vert.
- [x] **0.3** Dans `docs/ANIMATIONS.md`, marquer le bingo comme « modèle préparé, parcours à réaliser » et retirer
  les affirmations de génération et de validation déjà opérationnelles. Dans `Member`/`InvitationRequest`, vérifier
  que les textes d'aide décrivent l'état actuel jusqu'à la phase 5. Corriger le nombre de tests documenté après mesure.

L'ajout de routes et de champs peut nécessiter d'étendre les fixtures, la matrice d'accès et les catalogues de traduction
existants. Ces extensions sont prévues : conserver les assertions de sécurité et les comportements déjà vérifiés.
Par exemple, le test générique qui attend 200 pour toute route membre doit fournir une photo à sa cible de test,
ou tester explicitement le 404 attendu en l'absence de photo ; il ne doit pas dispenser cette route de contrôle d'accès.

**Validation :** suite existante verte, schéma sans dérive, documentation qui distingue livré et prévu.
**Commit suggéré :** `docs: clarifier les fonctionnalités livrées et le plan des améliorations`.

### Phase 1 — Afficher le tarif et le fonctionnement du paiement

Fichiers : `club/views/public.py`, `club/context_processors.py` si nécessaire, `templates/public/join.html`,
`templates/club/invite.html`, `club/tests/test_join.py`, `club/tests/test_landing_invite.py`, traductions.

- [x] **1.1** Passer `membership_price` depuis `settings.MEMBERSHIP_PRICE` au template de demande d'invitation.
  Employer une seule source pour le tarif ; aucun montant copié dans une chaîne Python ou un template.
- [x] **1.2** Afficher le montant annuel et les deux phrases sur la facture et l'absence de paiement au dépôt
  de la demande, au-dessus du bouton. Conserver le formulaire, le parrainage, le CSRF et le champ anti-bot.
- [x] **1.3** Si les réductions ne sont pas validées, faire dépendre leur affichage d'un réglage
  `REFERRAL_OFFER_ENABLED` explicitement désactivable ; conserver le lien de parrainage indépendamment de l'offre.
  Ne pas inventer TVA, échéance, conditions de résiliation ou prestations incluses.
- [x] **1.4** Vérifier les versions FR/DE/EN. Avec `override_settings(MEMBERSHIP_PRICE=720)`, la page doit afficher
  720 CHF ; elle doit aussi conserver le prix et le formulaire sur un POST invalide. Contrôler le cas `?ref=CODE`.

**Validation :** tests de demande/parrainage et suite complète ; page mobile lisible, aucun formulaire de paiement.
**Commit suggéré :** `feat: afficher la cotisation et la facturation manuelle`.

### Phase 2 — Ajouter quelques portraits illustratifs pour la démo

Pages sources vérifiées pendant l'étude, candidates à l'import ; les fichiers n'ont pas été téléchargés :

| Profil fictif proposé | Photo candidate | Auteur affiché sur la page |
|---|---|---|
| Camille | [Portrait professionnel, Pexels 30468665](https://www.pexels.com/photo/professional-headshot-of-a-young-businesswoman-30468665/) | Augusto Carneiro Junior |
| Lukas | [Portrait professionnel, Pexels 30004315](https://www.pexels.com/photo/professional-headshot-of-smiling-businessman-30004315/) | Daniel & Hannah Snipes |
| Joëlle | [Portrait en salon, Pexels 33867520](https://www.pexels.com/photo/elegant-salon-portrait-of-a-woman-entrepreneur-33867520/) | Daniel & Hannah Snipes |

Fichiers : `static/img/demo/`, `docs/demo/PHOTOS.md`, `club/models.py`, nouvelle migration, `club/demo_data.py`,
`club/management/commands/seed_demo.py`, `club/templatetags/club_ui.py`, `templates/club/_card.html`, `templates/base.html`.

- [x] **2.1** Télécharger uniquement les candidats retenus depuis leur page officielle. Pour chaque fichier,
  conserver dans `PHOTOS.md` la page source, l'auteur, la licence, la date d'acquisition et les transformations.
  Vérifier visuellement le portrait et son recadrage. Ne pas importer une image sponsorisée ou d'une autre banque.
- [x] **2.2** Préparer des JPEG ou WebP carrés d'environ 256 × 256, avec un objectif de moins de 80 Ko chacun.
  Retirer les métadonnées personnelles. Employer un outil local disponible ; si aucun outil approprié n'existe,
  conserver les initiales et noter le blocage au lieu d'ajouter une dépendance implicite.
- [x] **2.3** Ajouter `Member.demo_photo_key`, `CharField(max_length=32, blank=True, editable=False)`.
  Utiliser une liste fermée telle que `camille`, `lukas`, `joelle`, associée à des chemins statiques connus dans
  un filtre de template. Aucun chemin, nom de fichier ou domaine fourni par un formulaire utilisateur.
- [x] **2.4** Dans le seed, assigner les clés aux adresses fictives connues ; ne pas utiliser le générateur
  aléatoire existant pour attribuer les photos. Ne changer ni l'ordre des membres ni les identifiants ni les affinités.
  La photo n'est montrée que si `DEMO_MODE` est vrai et la clé connue. Garder les initiales sinon.
- [x] **2.5** Dans `_card.html`, afficher l'image carrée recadrée avec dimensions explicites, chargement différé
  et `alt=""` puisque le nom figure juste à côté. Garder les classes Tailwind complètes et les rangs de carte.
  Mettre à jour le bandeau de démo pour préciser le caractère illustratif des portraits, dans les trois langues.
- [x] **2.6** Vérifier : fichiers locaux disponibles via `collectstatic`, aucune requête vers Pexels dans le
  navigateur, CSP inchangée, mode hors ligne utilisable. Contrôler aussi une clé inconnue et `DEMO_MODE=False`.
  Les tests de reproductibilité du seed doivent toujours annoncer 50 membres et les mêmes propositions pour Camille.

**Validation :** trois cartes illustrées, autres cartes avec initiales, crédits conservés, suite complète verte.
Les portraits de démo sont des fichiers statiques publics ; aucun portrait réel de membre ne doit prendre ce chemin.
**Commit suggéré :** `feat: illustrer les profils fictifs de la démo`.

## 6. Phase 3 — Notes personnelles avec séparation des auteurs

Fichiers à créer : `club/services/notes.py`, `club/tests/test_notes.py`.
Fichiers à modifier : `club/models.py`, migration, `club/forms.py`, `club/views/member.py`, `club/urls.py`,
`templates/club/member_detail.html`, matrice d'accès, traductions.

### Contrat de données et d'accès

Créer `PersonalNote` : `owner` et `target` sont des FK vers `Member`, `text` est un `TextField(max_length=2000)`,
`updated_at` vaut `auto_now=True`. Utiliser `CASCADE` sur les deux FK.
Contraintes en base : une note par `(owner, target)` ; `owner != target`.
Ne pas utiliser le nom `note` sur `Member` : une seule valeur serait partagée par tous les lecteurs de la fiche.

Le corps de note est du texte brut échappé par Django. Pas de HTML, Markdown rendu, éditeur riche ou `|safe`.
Une note est possible sur une fiche que l'auteur est autorisé à ouvrir ; elle ne débloque jamais les coordonnées.

- [x] **3.1** Ajouter modèle et migration. Tester les contraintes de doublon et d'auto-note.
  Ne pas enregistrer `PersonalNote` dans l'admin, ni en inline, recherche, export ou tableau de bord.
- [x] **3.2** Créer `PersonalNoteForm` avec **seulement** `text`, facultatif, limité à 2 000 caractères.
  Créer `get_personal_note(owner, target)` et `save_personal_note(owner, target, text)` dans le service.
  Un texte vide ou fait d'espaces supprime la note ; pas de ligne vide conservée.
- [x] **3.3** Extraire au besoin un helper de contrôle d'ouverture de fiche, réutilisé par `member_detail` et
  la vue de sauvegarde. Le helper doit conserver les cas : soi-même, profil visible, profil masqué mais déjà rencontré,
  cible inexistante ou désactivée. Il sera étendu pour les invités en phase 8.
- [x] **3.4** Ajouter `club:member_note`, `/membres/<pk>/note/`, avec `@member_required` et `@require_POST`.
  Déduire `owner` **uniquement** de `request.member` ; `pk` désigne la personne annotée.
  Appliquer le contrôle de visibilité côté serveur avant lecture ou écriture. Ignorer tout `owner`, `note_id`,
  `author` ou `user` envoyé dans le POST. Valider le formulaire avant toute écriture et rediriger vers la fiche.
- [x] **3.5** Dans `member_detail`, charger uniquement `PersonalNote.objects.filter(owner=request.member, target=target)`.
  Montrer sur les fiches d'autrui un bloc « Ma note personnelle » et « Visible uniquement par toi dans l'application ».
  Ajouter CSRF et bouton « Enregistrer ». Un texte vide efface le mémo. Sur erreur de formulaire, réafficher la fiche
  avec les données saisies et les erreurs ; ne pas afficher le contenu dans un message flash.
- [x] **3.6** Utiliser `never_cache` sur les pages contenant la note et prévoir `Vary: Cookie`.
  Ne pas mettre son texte dans les logs, URL, attributs `data-*`, JS, emails, QR ou vCard.
  Une recherche dans l'album reste limitée aux champs de profil, sans recherche parmi les notes.
- [x] **3.7** Classer la route comme membre et POST dans la matrice d'accès ; ajouter les arguments requis.
  Couvrir le CSRF et la CSP du bloc. Ajouter uniquement les cas nécessaires aux tests existants.

Tests métier obligatoires, avec un texte sentinelle facile à retrouver :

| Scénario | Résultat attendu |
|---|---|
| A écrit sur B, puis revient | A retrouve sa note |
| B ouvre sa propre fiche ; C ouvre celle de B | Ni B ni C ne voit le texte ou un champ caché contenant la note de A |
| C écrit aussi sur B | La note de C est distincte ; celle de A reste intacte |
| C poste `owner=A`, ou un identifiant de note de A | Seule la note de C peut être modifiée ; la note de A reste intacte |
| A annote un profil masqué non rencontré | 404, aucune écriture |
| Texte trop long, GET sur l'action, POST sans CSRF | Rejet sans écriture |
| Texte contenant `<script>` | Texte échappé, aucun script exécuté |
| Note effacée, profil/auteur supprimé | Suppression prévue, sans note orpheline |
| Staff sans profil consulte l'admin, badges ou tableau de bord | Aucun texte de note ; aucun modèle de notes enregistré dans l'admin |
| vCard, album, page publique et emails | Aucune note dans le contenu |

**Validation :** `test_notes`, matrice d'accès et suite complète verts ; note de A absente de tout HTML reçu par B ou C.
La conservation et les procédures d'accès/suppression de données doivent intégrer cette nouvelle table avant production.
**Commit suggéré :** `feat: ajouter des notes personnelles réservées à leur auteur`.

## 7. Phase 4 — Upload et lecture privée des photos réelles

Cette phase dépend de l'accord sur **Pillow** et d'un stockage persistant pour l'environnement cible.
`ImageField` [nécessite Pillow](https://docs.djangoproject.com/en/5.2/ref/models/fields/#imagefield).
Sur Render, le [système de fichiers est éphémère par défaut](https://render.com/docs/disks) ; les fichiers ajoutés
à l'exécution disparaissent au redéploiement ou redémarrage sans disque persistant. Un disque est proposé pour
les services payants. Conserver les portraits statiques de phase 2 si le budget de stockage n'est pas encore décidé.

Fichiers à créer : `club/services/photos.py`, `club/tests/test_photos.py`.
Fichiers à modifier : dépendances après accord, `club/models.py`, migration, `club/forms.py`, `club/admin.py`,
`club/views/member.py`, `club/urls.py`, `config/settings.py`, `templates/club/profile_edit.html`, `_card.html`, tests d'accès.

- [x] **4.1** Ajouter `Member.photo`, facultatif. Fixer `MEDIA_ROOT` dans un répertoire privé ignoré par Git.
  Stocker avec un nom aléatoire généré par le serveur, sous `member_photos/`, en JPEG normalisé.
  Ne pas placer les uploads dans `static/`, `STATIC_ROOT` ou un répertoire directement servi par le proxy.
  Ne pas ajouter de route publique automatique `/media/`, même en développement.
- [x] **4.2** Écrire une fonction `normalize_member_photo(upload)` avec les limites proposées :
  2 Mio, JPEG/PNG/WebP uniquement, image non animée, dimensions au plus 4 096 × 4 096 et 16 millions de pixels.
  Vérifier le format réellement décodé, pas seulement le nom ou `content_type`. Rejeter SVG, GIF, fichiers tronqués,
  faux JPEG et formats non pris en charge avec un message traduisible. Conserver les protections contre les
  bombes de décompression décrites par [Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html).
- [x] **4.3** Après vérification, rouvrir/décoder l'image, appliquer l'orientation EXIF, recadrer au centre
  et redimensionner vers 512 × 512. Recréer une image RGB propre et l'encoder en JPEG ; ne pas recopier EXIF, GPS,
  commentaires ni octets ajoutés au fichier d'origine. Fond blanc pour la transparence. L'original n'est pas conservé.
  Référence pour l'orientation et le recadrage : [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html).
- [x] **4.4** Ajouter `photo` et un booléen `remove_photo` au formulaire de profil ; utiliser `request.FILES`
  et `enctype="multipart/form-data"`, conformément au
  [parcours d'upload Django](https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/).
  Utiliser un widget fichier qui n'affiche pas `photo.url`. Afficher l'aperçu via la route protégée décrite ci-dessous.
  Rejeter la combinaison upload + suppression ; le service commun est utilisé aussi par le formulaire admin.
- [x] **4.5** Écrire le service de remplacement/retrait. Valider avant d'écrire. La nouvelle photo ne remplace
  le champ que si le formulaire entier est valide. Après validation de la transaction, supprimer l'ancien fichier.
  En cas d'échec de sauvegarde, supprimer uniquement le nouveau fichier créé et garder l'ancien.
  Prévoir aussi le nettoyage lors de la suppression d'un profil, sans supprimer un fichier encore référencé.
- [x] **4.6** Ajouter `club:member_photo`, `/membres/<pk>/photo/`, GET seulement, avec `@member_required`.
  Appliquer **le même contrôle d'ouverture que la fiche**, puis servir le fichier normalisé avec `FileResponse`,
  `Content-Type: image/jpeg`, `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store` et `Vary: Cookie`.
  Le serveur ne lit aucun chemin reçu du navigateur. Sans photo ou sans droit, renvoyer 404.
- [x] **4.7** Dans les cartes, privilégier la photo réelle, puis l'illustration de démo si autorisée, puis
  les initiales. Aucune utilisation de `member.photo.url` dans les templates. L'absence physique d'un fichier ne
  doit pas provoquer de 500 ; détecter ce cas côté serveur et revenir aux initiales, avec un diagnostic sans donnée privée.
- [x] **4.8** Préparer la configuration du stockage persistant : volume privé sauvegardé sur un serveur suisse,
  ou disque persistant si Render est retenu. Documenter le chemin, les droits et la restauration.
  Un passage à un stockage objet privé serait une variante ultérieure avec dépendances et URLs à contrôler.
  Tant que le stockage durable n'est pas disponible, ne pas ouvrir l'upload en ligne à de vrais membres.
- [x] **4.9** Tester upload valide, orientation, métadonnées retirées, fichier trop gros, dimensions excessives,
  format interdit, upload malformé, retrait et remplacement. Employer un répertoire temporaire isolé pour les tests.
  Vérifier l'anonyme, le membre autorisé, le profil masqué non rencontré, un utilisateur tentant de modifier B,
  un fichier manquant et l'absence de route publique permettant de contourner le contrôle.

**Validation :** photo réelle persistante après redémarrage de l'environnement choisi, accès direct contrôlé,
suite complète verte. La validation `ImageField` seule ne constitue pas tout le dispositif : voir les
[précautions Django sur les fichiers utilisateurs](https://docs.djangoproject.com/en/5.2/topics/security/#user-uploaded-content).
**Commit suggéré :** `feat: permettre les photos de profil avec accès privé`.

## 8. Phase 5 — Terminer l'adhésion et préparer les préférences

Fichiers à créer : `club/services/membership.py`, `club/tests/test_membership.py`, `club/tests/test_email_preferences.py`.
Fichiers à modifier : modèles et migrations, `club/forms.py`, `club/views/public.py`, `club/admin.py`, profil et traductions.

### Modèle minimal

| Ajout | Définition | Raison |
|---|---|---|
| `Member.preferred_language` | FR/DE/EN, vide par défaut | Choix explicite pour les emails ; sinon conserver le fallback actuel de `email_language()` |
| `Member.admitted_at` | Date/heure nullable, gérée par le service d'admission, non éditable par le membre | Repérer une vraie admission, sans confondre année d'adhésion, création technique et remise à zéro de démo |
| `Member.digest_teaser` | Texte facultatif, 120 caractères | Accroche choisie pour la présentation mensuelle |
| `EmailPreferences` | Relation unique vers `Member` | Préférences séparées des données visibles de la carte |
| Préférences | `event_announcements=True`, `event_reminders=True`, `monthly_digest=False`, `allow_member_spotlight=False` | Permettre les emails fonctionnels et un choix explicite pour le récapitulatif et la présentation |

En migration, laisser `admitted_at=NULL` pour les profils existants. Le premier envoi mensuel ne doit pas présenter
tout l'annuaire comme nouvellement inscrit. Une préférence manquante suit les mêmes défauts, sans erreur.

- [x] **5.1** Ajouter ces champs et `EmailPreferences`. Ne pas l'afficher dans l'album ou dans une vCard.
  Ajouter les choix de langue, l'accroche et les préférences au profil personnel ; seuls les champs destinés
  à l'autoédition figurent dans le formulaire. Les valeurs `admitted_at` et les statuts restent staff/service.
- [x] **5.2** Dans `public.join`, sauvegarder la langue active FR/DE/EN de la demande validée.
  Garder honeypot, normalisation d'adresse et protection anti-doublon. L'offre de prix n'est pas une preuve de paiement.
- [x] **5.3** Écrire `accept_invitation(invitation_id, actor)` dans une transaction. Vérifier `actor.is_staff`
  et `is_active`. Verrouiller la demande. Sur une première acceptation, créer `User` avec username/email normalisé,
  mot de passe inutilisable, puis `Member` avec `Sector.OTHER`, `member_since` courant, `onboarding_done=False`,
  langue préférée de la demande et `admitted_at=now`. Relier la demande au profil et passer à `ACCEPTED`.
- [x] **5.4** Si la demande est déjà liée au compte créé, retourner ce compte sans doublon ni nouvel email.
  Si l'adresse correspond à un autre compte ou à plusieurs données ambiguës, bloquer l'acceptation avec une erreur
  staff et demander un rapprochement manuel ; ne pas rattacher automatiquement une identité existante.
  Gérer aussi l'unicité du username en cas de concurrence. Toute erreur laisse la demande et la base cohérentes.
- [x] **5.5** Remplacer l'édition libre de `ACCEPTED` par une action admin « Accepter et créer le compte ».
  `member`, `admitted_at` et `welcome_sent_at` sont en lecture seule. Autoriser séparément « contactée » et « refusée »
  sur les demandes non acceptées. Ne pas permettre de redescendre un compte accepté au statut « nouvelle » par hasard.
- [x] **5.6** Jusqu'à la phase 6, proposer une action explicite pour envoyer l'accès via `send_login_link` après
  création du compte. La création ne doit pas dépendre d'une réponse SMTP. Ne pas renseigner `welcome_sent_at` comme
  si un email de bienvenue avait été envoyé. Modifier le texte d'aide : le parcours utilise un lien de connexion,
  il ne permet pas encore de choisir un mot de passe dans une page qui n'existe pas.
- [x] **5.7** Faire utiliser la préférence de langue explicite par `email_language(member)`, puis son fallback
  actuel si elle est vide. La langue de lecture du navigateur et les langues parlées restent distinctes.
  Tester un membre bilingue qui choisit l'allemand pour ses emails.
- [x] **5.8** Tester acceptation une fois/deux fois, compte préexistant, erreur de création, utilisateur non staff,
  langue DE/EN du formulaire, création de compte sans mot de passe utilisable et préservation des demandes existantes.
  Tester aussi qu'un membre modifie seulement ses propres préférences et ne peut pas poster `admitted_at`.

**Validation :** accepter une demande crée exactement un compte lié ; une répétition ne crée rien de plus ;
les préférences sont enregistrées, traduites et absentes des vues d'autrui. Suite complète verte.
**Commit suggéré :** `feat: terminer l'acceptation des invitations et les préférences email`.

## 9. Phase 6 — Annonce d'événement et relances automatiques

Fichiers à créer : `club/services/notifications.py`, `club/management/commands/process_notifications.py`,
`templates/emails/`, `club/tests/test_notifications.py`, `club/tests/test_event_publication.py`.
Fichiers à modifier : modèles, migrations, réglages email, admin, vues publiques/membres/staff d'événements,
`club/services/events.py`, seed et traductions.

### 6A. État de publication et file persistante

Ajouter à `Event` : `is_published=False` pour les nouveaux événements, `published_at` nullable,
`cancelled_at` nullable et `rsvp_deadline` nullable. Une migration explicite conserve visibles les événements existants
en les marquant publiés **sans préparer d'annonce rétroactive**. `is_published` est piloté par les actions du service.

Créer les deux modèles suivants ; les noms de champs peuvent être ceux-ci, sans inventer un framework de campagnes :

| Modèle | Champs principaux et invariants |
|---|---|
| `NotificationCampaign` | `kind`, `scope_key` unique, `event` nullable avec `SET_NULL`, `month` nullable, `created_at`, `cancelled_at` nullable ; sortes `welcome`, `event_announcement`, `event_reminder`, `new_members` |
| `NotificationDelivery` | FK `campaign` protégée contre suppression accidentelle, FK `recipient` vers `Member` avec `CASCADE`, `status`, `attempts`, `next_attempt_at`, `claimed_at`, `sent_at`, `last_error_code` court ; unicité `(campaign, recipient)` |

Statuts de livraison : `pending`, `sending`, `sent`, `skipped`, `failed`, `uncertain`.
`sent` signifie « accepté par le serveur SMTP », pas « lu » ni « arrivé dans la boîte de réception ».
Conserver seulement les références nécessaires et les codes d'erreur, sans copies des notes, secrets ni corps d'emails.
Le contenu est rendu au moment de l'envoi, après vérification des droits et préférences.

- [x] **6.1** Ajouter les champs, modèles, contraintes et index utiles : statut/date de tentative et campagne/destinataire.
  Les événements brouillons n'apparaissent ni sur l'accueil, ni dans la liste, ni par accès direct, ni au scan,
  ni aux membres invités ultérieurs. Le staff peut les préparer. Classer et tester les éventuelles routes ajoutées.
  Adapter les fixtures de nouveaux événements pour déclarer explicitement ceux qui sont publiés ; préserver les
  assertions de comportement des tests existants.
- [x] **6.2** Écrire `publish_event(event_id, actor)`. Dans une transaction, verrouiller l'événement, vérifier staff,
  titre, date future, lieu, échéance cohérente et absence d'annulation. Marquer publié, puis créer une campagne
  `event:<pk>:announcement` et une livraison par membre actif avec annonces autorisées.
  Une sauvegarde ordinaire, une deuxième publication ou deux appels concurrents ne crée aucune seconde campagne.
- [x] **6.3** Ajouter les actions staff/admin « Publier et préparer l'annonce » et « Annuler l'événement ».
  Après publication, montrer « annonce préparée » et les compteurs. L'envoi part dans la commande, pas dans la requête.
  L'annulation retire les futures inscriptions et relances ; garder l'historique visible avec une mention « annulé ».
  La notification exceptionnelle d'annulation est un lot ultérieur : l'équipe doit contacter les inscrits via son
  processus habituel tant qu'elle n'existe pas. Ne pas créer un nouveau mail d'annonce en éditant une date ou un lieu.
- [x] **6.4** Utiliser une requête commune des événements visibles dans `home`, `event_list`, `event_detail`,
  `event_rsvp` et `current_event`. Refuser un RSVP après `rsvp_deadline`, après le début ou après annulation.
  Quand l'échéance est vide, prendre le début de l'événement. Les fenêtres et comparaisons utilisent des datetimes
  conscients du fuseau ; les dates affichées et le mois métier utilisent `Europe/Zurich`.

### 6B. Envoi, reprise et langue

Ajouter `PUBLIC_BASE_URL` validée, HTTPS en production, sans chemin ni paramètres, pour générer les URLs depuis le cron.
Ne pas dépendre de `request.build_absolute_uri()` dans une commande sans requête.
En développement, la valeur peut être `http://127.0.0.1:8000` ; en production, refuser une valeur absente ou invalide.
Ajouter un timeout SMTP explicite, par exemple 10 secondes. Le backend console reste le défaut en local.
Ajouter `NOTIFICATIONS_ENABLED=False` par défaut pour rendre l'activation de l'envoi automatique explicite.
La préparation et le mode aperçu restent disponibles quand ce réglage est désactivé ; l'envoi réel est refusé.
Les tests activent ce réglage uniquement avec le backend mémoire.

- [x] **6.5** Créer des templates texte + HTML pour bienvenue, annonce et relance, dans la langue du destinataire.
  Utiliser [EmailMultiAlternatives](https://docs.djangoproject.com/en/5.2/topics/email/) et une connexion SMTP réutilisée
  par lot. L'email d'événement montre titre, date, lieu et un bouton vers la page privée de l'événement.
  Le clic n'inscrit jamais quelqu'un : connexion si nécessaire, puis réponse par POST/CSRF sur le site.
- [x] **6.6** Pour la bienvenue, générer le lien magique **au moment de l'envoi** : un jeton préparé des heures
  avant serait périmé. Préparer la campagne `invitation:<pk>:welcome` dans la transaction d'acceptation de phase 5.
  Renseigner `welcome_sent_at` uniquement lorsque SMTP accepte le message. Une panne mail ne défait pas le compte.
  Ne pas ajouter des liens magiques valables 15 minutes aux annonces et récapitulatifs destinés à être lus plus tard.
- [x] **6.7** Écrire `process_notifications --dry-run --limit 50`, avec exécution unique et sortie résumée.
  Le mode `--dry-run` ne modifie ni campagne, livraison, dates ni compteur, et n'envoie rien.
  Une exécution réelle prépare les travaux dus puis traite au plus le nombre demandé.
  Les [commandes Django](https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/) peuvent être déclenchées
  par un ordonnanceur ; la commande elle-même ne doit pas lancer une boucle infinie.
- [x] **6.8** Réserver chaque livraison dans une transaction courte par une transition conditionnelle
  `pending/failed → sending`, avec heure et compteur. Envoyer hors de la transaction, puis enregistrer le résultat.
  Deux processus ne peuvent réserver la même ligne. En PostgreSQL, tester les verrous avec `TransactionTestCase` ;
  [`select_for_update()` n'a pas d'effet sur SQLite](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
  La contrainte unique et la transition conditionnelle restent nécessaires.
- [x] **6.9** Distinguer rejet SMTP établi et résultat ambigu. Pour un refus avant acceptation, garder `failed`
  et proposer au plus trois essais avec délais progressifs, par exemple 15 min puis 1 h.
  Pour une coupure après une tentative dont l'acceptation est inconnue, passer `uncertain` et demander une revue staff.
  Une ligne `sending` abandonnée depuis plus de 15 minutes devient aussi `uncertain`, sans renvoi automatique.
  Ne pas promettre un envoi « exactement une fois » : une interruption après SMTP mais avant l'écriture en base
  rend cette garantie impossible avec SMTP seul. La prudence sur les cas ambigus limite le risque de doublons.
- [x] **6.10** Juste avant chaque envoi, vérifier utilisateur actif, adresse disponible, préférence toujours autorisée,
  campagne non annulée et événement encore valable. Sinon passer `skipped`, sans email.
  Aucune relance ne part après une réponse ou après l'échéance. Logs : type, identifiants, compteurs et code d'erreur ;
  pas d'adresse en clair, jeton de connexion, contenu de profil ou note.
  Les vérifications sont propres au type : la bienvenue ne dépend pas d'un événement ni de l'accord newsletter.
  Une campagne liée à un événement supprimé ne peut plus être envoyée. Le mode aperçu ne crée pas implicitement
  une ligne de préférences via `get_or_create`.

### 6C. Relances sans spam

- [x] **6.11** Faire préparer par la commande les campagnes `event:<pk>:reminder:14` et `event:<pk>:reminder:3`
  lorsque leur date est atteinte. Prévoir uniquement les membres actifs sans **aucune** ligne RSVP, avec annonces
  et relances autorisées, auxquels l'annonce de cet événement a été acceptée par SMTP.
  Un `YES` ou un `NO`, un remplacement demandé ultérieurement, une désactivation ou un désabonnement exclut le membre.
- [x] **6.12** Relancer au plus deux fois et attendre au moins 72 h après le dernier email réussi de l'événement.
  Un événement annoncé à J−5 ne doit pas déclencher une relance J−14 rattrapée immédiatement ; supprimer les paliers
  antérieurs à la publication. Si l'ordonnanceur reprend à J−2 après une panne, préparer seulement le dernier palier
  pertinent, sans deux emails rapprochés. Si la fin des réponses est dépassée, ne rien envoyer.
- [x] **6.13** Présenter dans l'admin la campagne, les compteurs et les états en lecture seule.
  Une action explicite de reprise peut relancer un échec confirmé. Pour un résultat `uncertain`, afficher qu'un email
  a peut-être déjà été envoyé ; ne pas inclure ces lignes dans une action « tout renvoyer ».
  Pas de bouton de campagne accessible aux membres et pas de pixels d'ouverture.

Tests obligatoires : publication répétée ; sauvegarde sans envoi ; brouillon invisible ; migration sans campagne
rétroactive ; un message par destinataire ; FR/DE/EN ; réponse oui/non avant préparation **et** avant envoi ;
J−14/J−3 ; annonce tardive ; reprise après panne ; événement passé/annulé ; préférence retirée ; erreur SMTP ;
réservation concurrente ; état ambigu ; nouvelle exécution sans doublon ; `--dry-run` strictement sans écriture.
Les tests utilisent le backend mémoire de Django et une horloge contrôlée, jamais de vrais destinataires.

**Validation :** publier prépare une seule annonce ; la commande l'envoie puis n'envoie plus rien en répétition ;
seuls les non-répondants éligibles sont relancés. Suite complète verte ; concurrence validée sur PostgreSQL avant production.
**Commit suggéré :** `feat: annoncer les événements et relancer les membres sans réponse`.

## 10. Phase 7 — Récapitulatif mensuel des nouveaux membres

Fichiers : `club/services/notifications.py`, commande périodique, `templates/emails/`, modèles/migration pour
`DigestEntry`, `club/tests/test_new_member_digest.py`, préférences et traductions.

### Règles de sélection

Le récapitulatif du mois M est préparé à partir du **1er jour du mois M à 09:00, heure suisse**.
Il présente les membres admis avant le début de M qui n'ont encore été réservés pour aucune présentation.
Cela permet à un profil complété avec retard d'apparaître le mois suivant, sans présenter les 50 profils historiques.

Une personne présentée doit avoir `admitted_at` renseigné, compte actif, `onboarding_done=True`,
`visible_in_directory=True` et `allow_member_spotlight=True`. Les invités temporaires seront exclus en phase 8.
Les destinataires sont les membres actifs avec `monthly_digest=True` ; ne pas envoyer à une personne un récapitulatif
qui ne présenterait qu'elle-même. Sans profil présentable ou sans destinataire, ne pas créer de campagne vide.

- [ ] **7.1** Ajouter `DigestEntry`, lien unique du membre présenté vers sa campagne mensuelle.
  Une FK campagne protégée contre une suppression accidentelle évite de représenter les mêmes profils par erreur.
  Ne pas utiliser uniquement `created_at`, `member_since` ou « inscrits dans les 30 derniers jours ».
- [ ] **7.2** Préparer atomiquement une campagne `new-members:<YYYY-MM>` et réserver les profils retenus avec
  `DigestEntry`. Cette association signifie « réservé pour cette présentation », pas « lu par tous les membres ».
  Réexécuter la commande pendant le même mois ne crée aucune seconde campagne, même si d'autres personnes arrivent.
  Les personnes admises pendant M attendent la présentation de M+1.
- [ ] **7.3** Rendre pour chaque destinataire au plus **quatre aperçus** : prénom, nom, entreprise, secteur,
  accroche volontaire raccourcie à 80 caractères et lien protégé vers la fiche.
  S'il y en a davantage, donner le nombre restant et un lien vers l'album. Ne pas réutiliser `_card.html` : il contient
  davantage de données et pourrait évoluer sans contrôle du périmètre email.
- [ ] **7.4** Recontrôler à l'envoi la visibilité, l'activité et l'accord de présentation de chaque profil.
  Retirer ceux qui ont changé d'avis entre préparation et envoi. S'il ne reste personne pour un destinataire,
  passer sa livraison `skipped`. Pas de coordonnées, affinités détaillées, anecdotes non choisies ni notes privées.
  Une personne cachée après envoi n'est plus accessible sur le site ; un email déjà reçu ne peut pas être rappelé.
- [ ] **7.5** Ajouter un lien « Mes préférences email » vers une page authentifiée, modifiable par POST.
  Pour permettre aussi un désabonnement sans connexion, ajouter une route publique avec un jeton signé dédié
  à l'objet `monthly_digest`, une page GET de confirmation et un POST qui désactive cette préférence.
  Le GET ne modifie rien et ne connecte personne. Ne pas réutiliser un lien magique de connexion pour cet usage.
  Utiliser une signature dédiée incluant identifiant du membre et objet du désabonnement ; proposer une validité
  de 90 jours, puis renvoyer vers les préférences authentifiées. Les liens invalides ne révèlent ni nom ni adresse ;
  classer cette route et tester le CSRF, la signature, la portée et l'expiration.
- [ ] **7.6** Prévoir sujet au singulier/pluriel et contenu dans la langue du destinataire.
  Aucun pixel, script, pièce jointe de contact ou chargement d'image privée dans l'email.
  Tester texte et HTML, pas seulement le sujet.
- [ ] **7.7** Couvrir : zéro/un/dix nouveaux profils, absence d'accord, profil incomplet complété tardivement,
  profil masqué ou désactivé entre préparation et envoi, compte historique avec `admitted_at=NULL`, inscrit ce mois,
  membre déjà présenté, destinataire retirant son accord et deux exécutions le même mois.
  Vérifier par sentinelles qu'email/phone/LinkedIn/notes/QR de la personne présentée n'apparaissent jamais dans le message.

Exemple de contenu, à traduire et adapter au nombre :

> Un nouveau visage au Club !
>
> Camille Rey · Alpes Digital · Tech & digital
> « Parle-moi de la transition numérique. »
>
> Découvre son profil et fais connaissance avant le prochain événement.
> [Découvrir Camille] — lien vers la fiche privée.

**Validation :** au plus une campagne mensuelle, plusieurs inscriptions regroupées, aperçu limité,
préférences respectées et aucune donnée de contact exposée. Suite complète verte.
**Commit suggéré :** `feat: présenter les nouveaux membres dans un récapitulatif mensuel`.

## 11. Phase 8 — Remplaçants avec accès temporaire et identité propre

C'est le lot le plus délicat. Ne pas se contenter d'un champ nom dans le formulaire : badges, QR, statistiques,
tables, matching, coordonnées et droits doivent tous désigner la personne réellement présente.
Garder les algorithmes purs `matching.py` et `seating.py` ; adapter les données qui leur sont fournies.

Fichiers à créer : `club/services/substitutions.py`, `club/services/access.py` si le contrôle n'est pas déjà extrait,
`club/management/commands/expire_guest_access.py`, `club/tests/test_substitutions.py`, `club/tests/test_guest_access.py`,
`templates/club/substitute_form.html`.
Fichiers à modifier : `models.py`, migrations, `decorators.py`, `forms.py`, vues membre/événements/staff/public,
services événements/fédération/intros/notifications, admin, cartes, navigation, badges et tests d'accès.

### 8A. Données et invariants

| Modification | Contrat |
|---|---|
| `Member.kind` | Choix `member`/`guest`, défaut `member` pour conserver tous les profils existants |
| `Member.guest_access_until` | Date/heure nullable, gérée par le service ; obligatoire pour un invité ayant accès |
| `Substitute.guest` | FK nullable vers `Member`, `SET_NULL`, permet de réutiliser une même personne pour plusieurs événements |
| `Substitute.status` | `pending`, `approved`, `cancelled`, défaut `pending` pour les anciennes lignes |
| `Substitute.approved_at` | Date/heure nullable, renseignée lors de la validation staff |
| Contraintes existantes | Garder une ligne maximum par `(event, member)` ; réutiliser cette ligne en cas de nouvelle demande pour le même événement |
| Contraintes supplémentaires | Unicité conditionnelle `(event, guest)` au statut approuvé ; titulaire et invité différents lorsque `guest` est renseigné |

Le service exige un `guest` non nul avant de passer à `approved`. Ne pas ajouter un CHECK permanent qui empêcherait
`SET_NULL` lors d'une suppression légitime de la personne. Dans ce cas, anonymiser aussi les données d'identité
recopiées dans la demande, retirer les présences futures et conserver seulement l'historique nécessaire.

`Substitute.member` conserve son sens : **le titulaire remplacé**. Ne pas le renommer pour désigner l'invité.
Les champs prénom/nom/email/entreprise existants restent la demande initiale, visible par le titulaire et le staff,
pas la source publique des coordonnées de l'invité. Après validation, le profil `guest` est la source des cartes et QR.

Pour la première version, accepter un collègue de la même entreprise, avec confirmation staff.
Un titulaire qui redevient présent doit d'abord annuler son remplacement. L'application interdit la double présence.
Un invité n'est ni « nouveau membre », ni « fondateur », ni une cotisation supplémentaire.

- [ ] **8.1** Ajouter les champs et migrations. Les anciens `Member` restent `kind=member` ; ne pas créer
  un compte invité pour chaque ancienne ligne `Substitute` sans validation humaine de son identité.
  La migration de contrainte doit accepter les anciennes lignes `pending` avec `guest=NULL`.
- [ ] **8.2** Ajouter `SubstituteForm` avec prénom, nom, email et fonction. L'entreprise est déduite du titulaire
  puis contrôlée par le staff. Demander aussi les langues parlées et la langue souhaitée pour l'accès ; valider
  au moins une langue parlée. Ces données concernent l'invité et ne sont pas copiées du titulaire.
  `member`, `guest`, `status`, `is_staff`, `kind`, année d'adhésion et durée d'accès
  n'appartiennent jamais aux champs autoéditables.
- [ ] **8.3** Écrire `request_substitute(event_id, principal, data)` et `cancel_substitute(event_id, principal)`.
  Dans une transaction, vérifier titulaire régulier actif, événement publié/futur/non annulé et échéance ouverte.
  `principal` provient exclusivement de `request.member`. Une demande valide crée/met à jour la ligne `pending`
  et met le RSVP du titulaire à `NO`. Ne pas créer de compte ni de présence invitée avant validation du staff.
- [ ] **8.4** Écrire `approve_substitute(substitute_id, actor)` : staff actif, ligne et événement verrouillés,
  contrôles d'échéance, titularité et absence de conflit. Créer un `User` distinct et un `Member(kind=guest)` avec
  mot de passe inutilisable, ou réutiliser une personne invitée déjà identifiée par son adresse normalisée.
  Si l'adresse correspond à un membre régulier, au staff, au titulaire ou à des données ambiguës, bloquer et
  expliquer le conflit au staff ; ne pas convertir ni fusionner ces comptes automatiquement.
- [ ] **8.5** Pour un invité réutilisé, vérifier que les noms correspondent et que son identité a été confirmée
  par le staff. Réactiver son `User`, borner l'accès à la dernière date des invitations approuvées pertinentes
  plus 48 h, garder son QR individuel, son historique et ses notes. Ne pas écraser ses coordonnées déjà complétées
  avec une demande faite par un autre titulaire. Un QR peut être régénéré pour raison de sécurité via l'action existante.
- [ ] **8.6** À validation, lier `Substitute.guest`, passer `approved` et créer le RSVP `YES` de l'invité.
  Le titulaire reste `NO`. La contrainte unique de présence et les contrôles service empêchent de compter un invité
  deux fois. Préparer dans la file d'emails un accès invité avec une clé unique `substitute:<pk>:access`, un type
  `guest_access` et un lien magique généré à l'envoi. Ce message est distinct de la newsletter des nouveaux membres.

### 8B. Écrans et autorisations

Ajouter `/evenements/<pk>/remplacant/`, GET formulaire et POST de demande, et
`/evenements/<pk>/remplacant/annuler/`, POST seulement. Les deux concernent uniquement le titulaire connecté.
Le staff valide/refuse depuis l'administration ; afficher les demandes en attente dans les outils d'événement.

- [ ] **8.7** Dans `event_detail`, après « Je ne viens pas », proposer « Proposer un remplaçant » et afficher
  l'état de sa propre demande. Les autres membres voient la carte de la personne présente, avec « Invité » et
  « Représente [entreprise] », sans adresse de demande ni détails d'approbation.
  Le bouton « Je viens » refuse proprement si un remplacement `pending/approved` existe ; guider vers son annulation.
- [ ] **8.8** Enregistrer `Substitute` dans l'admin, avec données d'identité et statut contrôlés par les actions
  du service. Aucun changement manuel de `guest/status` qui contournerait les invariants.
  Proposer validation et annulation/refus sur POST. Une annulation enlève le RSVP invité de cet événement, ne touche
  pas ses autres invitations et invalide les propositions/places de l'événement. Le titulaire reste `NO` jusqu'à
  ce qu'il réponde de nouveau. Les anciens événements conservent leur historique.
- [ ] **8.9** Étendre `@member_required` pour rejeter immédiatement un invité dont la date d'accès est expirée
  ou dont aucune invitation valide ne donne accès, **même avec une session déjà ouverte**.
  Utiliser `timezone.now()` à chaque requête ; ne pas dépendre du passage du cron pour la confidentialité.
  Ajouter un contrôle « membre régulier » pour les actions de parrainage, remplacement et réponse de présence.
  Ne pas se fier uniquement à des boutons masqués dans les templates.
- [ ] **8.10** Centraliser la visibilité dans `services/access.py`, puis l'appliquer aux fiches, photos, notes,
  vCards, liste de participants, introductions et scans. Proposer les règles précises du tableau ci-dessous.
  Toute sortie de périmètre renvoie 404 pour une cible, ou 403 pour une action interdite.

| Ressource | Membre régulier actif | Invité avec accès valide |
|---|---|---|
| Événements | Événements publiés du Club | Seulement ceux pour lesquels il est remplaçant approuvé |
| Accueil | Fonctionnement normal | Prochain événement autorisé et historique personnel, aucun autre événement |
| Album | Membres réguliers visibles + personnes réellement rencontrées | Participants visibles de ses événements autorisés + personnes déjà rencontrées |
| Fiche / photo | Règles actuelles pour les réguliers ; invité visible si coparticipant autorisé ou déjà rencontré | Sa fiche, coparticipants visibles et personnes déjà rencontrées ; aucun autre membre |
| Fiche d'un invité en veille | Visible seulement aux personnes qui l'ont rencontré, avec statut « invité, accès terminé » | Pas de connexion ni de requête privée possible si l'invité lecteur est en veille |
| Coordonnées / vCard | Soi-même ou `Connection` réelle, après contrôle d'accès à la fiche | Même règle ; appartenir au même événement ne débloque aucun contact |
| Notes | Uniquement les siennes, sur une fiche accessible | Uniquement les siennes, sur une fiche accessible |
| Profil, affinités, mon QR | Ses données | Ses données et son QR propre |
| Parrainage / proposer un remplaçant | Autorisé | Interdit côté serveur |
| Inscription/désinscription | Via RSVP, en respectant un remplacement existant | Gérée via le remplacement, pas par un POST RSVP libre |
| Staff / admin | Selon le rôle staff déjà existant | Interdit |

Pour les cartes d'invités non encore rencontrés, la coparticipation se vérifie sur les événements publiés et
non annulés pour lesquels le remplacement donne encore accès. Un invité en veille ne reste pas dans l'annuaire
général. Les profils masqués ne redeviennent pas visibles au seul motif d'une coparticipation.
Une personne déjà rencontrée reste soumise à la politique de suppression/conservation décidée par le Club.

- [ ] **8.11** Appliquer ces règles également aux liens magiques : aucune nouvelle demande de lien pour un
  invité expiré, même si la commande de veille n'est pas encore passée. Garder la réponse publique identique
  pour les adresses connues/inconnues. Un jeton ancien ne doit permettre aucune action privée hors durée.
  La navigation invitée retire les liens interdits, et les vues contrôlent aussi les URLs saisies directement.

### 8C. Présence réelle, rencontres et statistiques

- [ ] **8.12** Faire de `attendees(event)` la source commune des personnes présentes : réguliers RSVP `YES`
  sans remplacement en cours, et invités RSVP `YES` liés à un remplacement `approved` de cet événement.
  Pas d'invité en `pending`. Pour un événement passé, conserver les invités qui étaient approuvés et présents,
  même si leur connexion est maintenant désactivée. Une annulation retire leur présence future, pas les autres événements.
- [ ] **8.13** Utiliser cette source dans cartes de participants, compteurs, tableaux staff, admin et badges.
  Remplacer les compteurs directs de `rsvps__status=YES` qui ignoreraient les invariants d'invitation.
  Les badges et placements montrent le nom et QR de l'invité ; aucune impression au nom du titulaire absent.
- [ ] **8.14** Fournir l'invité à `compute_matches` et `compute_seating` avec ses propres langues, affinités
  et secteur. Ne pas hériter des goûts ou langues du titulaire. Pour le score, un invité n'est ni pilier ni nouvelle
  recrue cotisante. Sa carte affiche un libellé « Invité » au lieu d'un rang calculé à partir d'une fausse ancienneté.
  Masquer aussi la mention « membre depuis » pour les invités. Le champ requis `member_since` peut recevoir l'année
  courante à la création technique, mais n'est jamais utilisé pour présenter une ancienneté d'adhésion d'invité.
- [ ] **8.15** Sur changement de présence/remplacement, effacer les `Match` et `SeatAssignment` devenus obsolètes,
  ainsi que le plan agrégé de cet événement ; afficher « à régénérer » au staff et une attente claire aux membres.
  Aucun ancien placement du titulaire absent ne doit rester présenté comme valable. La régénération utilise les présents.
  Filtrer aussi toute introduction vers un profil auquel le lecteur n'a pas accès.
- [ ] **8.16** Lors d'un scan confirmé, créer `Connection(invité, personne rencontrée)` et **aucune** connexion
  avec le titulaire. Pour les invités, vérifier le périmètre avant GET et POST du scan.
  Ne pas utiliser `current_event().first()` pour attribuer au hasard une rencontre lorsque plusieurs événements
  ont lieu le même jour : identifier un événement commun du jour avec contexte validé ; si un membre régulier
  n'a pas de contexte non ambigu, laisser `Connection.event=None`. Pour un invité, exiger un événement commun autorisé.
- [ ] **8.17** Séparer les compteurs du Club et l'historique de rencontres : `active_members()` et l'indice
  portent sur `kind=member`, et l'indice compte seulement les connexions entre ces membres réguliers actifs.
  Les invités ne gonflent ni le nombre de cotisants ni le dénominateur des paliers.
  Pour « X / Y cartes membres », calculer X et Y sur les mêmes réguliers actifs ; montrer les invités rencontrés
  dans une rubrique ou un compteur complémentaire. Aujourd'hui le numérateur prend toutes les connexions :
  le conserver tel quel pourrait produire X > Y après l'ajout d'invités ou des désactivations.
- [ ] **8.18** Exclure `kind=guest` des chiffres de vitrine, des nouvelles recrues, du parrainage, des destinataires
  de campagnes générales et des profils présentés dans le récapitulatif mensuel.
  Un invité reçoit seulement son accès et les messages liés à ses événements autorisés.
  Le titulaire avec RSVP `NO` ne reçoit pas de relance, même si son invité n'a pas encore complété son profil.

### 8D. Mise en veille et tests de bout en bout

- [ ] **8.19** Écrire `expire_guest_access --dry-run`, déclenchable périodiquement.
  Pour les invités dont la dernière autorisation est terminée, désactiver `User.is_active`, sans effacer leurs vraies
  rencontres. Ne jamais désactiver un membre régulier. Recalculer la borne d'accès après annulation/réactivation
  et prolonger seulement si une autre invitation approuvée la justifie.
  La commande de notifications d'accès doit recontrôler cette borne avant envoi.
- [ ] **8.20** Ajouter un scénario de démo **opt-in**, par exemple `seed_substitute_demo`, qui utilise un membre
  fictif secondaire absent et un invité `@example.com` ; ne pas modifier le scénario Camille–Lukas ni le seed de base.
  La commande ne change aucune donnée hors de cette démo et se réexécute sans créer de doublons.
- [ ] **8.21** Tester toute la chaîne décrite ci-dessous sur SQLite ; utiliser PostgreSQL pour la validation
  simultanée d'une demande et des contraintes de présence. Étendre la matrice d'accès avec un invité actif et expiré.

Scénario de recette obligatoire :

1. A, membre régulier, répond `NO`, propose G ; B ne peut ni voir la demande privée ni la modifier.
2. Le staff approuve ; G possède un compte et un QR différents de A, une invitation valable et un RSVP `YES`.
3. Le compteur reste celui d'une place remplacée ; la table et le badge montrent G. A n'a ni place ni badge.
4. G ouvre seulement les événements autorisés ; une URL d'un autre événement, profil ou photo ne contourne pas la règle.
5. G et C confirment leur rencontre. G/C voient leurs coordonnées ; A/C n'ont aucune nouvelle `Connection`.
6. G écrit une note sur C. A et C ne la voient jamais, y compris dans HTML, email, vCard et admin.
7. L'accès de G expire alors que sa session est ouverte. Toute vue privée/action lui est refusée immédiatement.
8. C garde la vraie rencontre avec G, selon la conservation décidée ; l'indice entre membres réguliers reste exact.
9. Une nouvelle invitation valide réactive G avec le même historique. Aucun second profil à la même identité.
10. Annuler un remplacement retire la présence G de cet événement, conserve ses autres invitations,
    invalide les tables/propositions obsolètes et permet à A de répondre de nouveau.
11. Deux titulaires tentent de faire approuver G pour le même événement : une seule validation aboutit.
12. Aucun compte staff/régulier ne peut être transformé en invité par un email saisi dans le formulaire.

**Validation :** tous ces parcours et refus passent ; aucune transmission automatique de contacts ou notes au titulaire ;
suite complète verte et scénario de pitch original préservé.
**Commit suggéré :** `feat: gérer les remplaçants avec identité et accès temporaires`.

## 12. Paramètres métier à confirmer avant l'exploitation réelle

L'IA peut préparer et tester le code avec ces valeurs de démonstration. Elle ne doit pas transformer les hypothèses
en décisions commerciales ou activer des envois réels tant que la configuration de production n'est pas établie.

| Question métier | Valeur proposée pour préparer la solution | Effet sur le travail |
|---|---|---|
| Cotisation annuelle exacte | 500 CHF, valeur déjà présente | Tarif configurable ; faire confirmer avant communication réelle |
| Réductions de parrainage | 350 CHF nouveau membre / 100 CHF de remise au parrain, actuellement provisoires | Affichage désactivable si non validées |
| Qui peut remplacer un membre ? | Collègue de la même entreprise, validation staff | Contrôles du formulaire et du service |
| Fin d'accès invité | 48 h après le début de l'événement | Borne configurable ; expiration contrôlée à chaque requête |
| Conservation de l'invité en veille | Proposition : revue après 12 mois depuis la dernière participation | Pas de purge automatique avant décision ; prévoir suppression avec dépendances et fichiers |
| Notes et exploitation | Privées entre utilisateurs ; opérateurs techniques soumis à des accès limités | Politique de conservation, sauvegardes et traitement des demandes d'accès |
| Relances | J−14 et J−3, au moins 72 h entre emails de l'événement | Réglages modifiables sans toucher aux algorithmes |
| Récapitulatif mensuel | 1er du mois, 09:00 Europe/Zurich, réception et présentation volontaires | Fuseau, planification et préférences |
| Envoi réel | Adresse du Club, serveur SMTP et domaine choisis par l'équipe | Secrets hors Git ; configuration et vérification du domaine |
| Photos réelles | Stockage privé persistant, sauvegardé | Pas d'ouverture des uploads réels sur stockage éphémère |

Ne pas ajouter une phase de paiement en ligne à ce plan. Le futur chantier de facturation devra partir des règles
comptables et du processus de facture manuelle du Club, après une demande explicite.

## 13. Phase 9 — Recette et exploitation

Fichiers : `README.md`, `docs/ARCHITECTURE.md`, `docs/ANIMATIONS.md`, nouveau `docs/EXPLOITATION.md`, traductions,
configuration d'hébergement préparée selon le prestataire retenu.

- [ ] **9.1** Exécuter la suite complète sur SQLite, puis les tests de concurrence pertinents et la suite sur
  une base **PostgreSQL de test dédiée**, jamais la base de production. Contrôler les migrations depuis une copie
  du schéma existant, avec conservation des profils, connexions, invitations et événements déjà présents.
- [ ] **9.2** Vérifier à 390 px et 1 280 px, FR/DE/EN : invitation avec prix, photo/initiales, édition de profil,
  note et suppression, préférences email, aperçu des campagnes staff, remplaçant et compte invité, impression A4.
  Contrôler console, réseau, débordements et CSP. Refaire la démonstration Camille–Lukas d'origine.
- [ ] **9.3** Tester les accès anonyme, membre A, membre B, staff sans profil, invité actif et invité expiré.
  Vérifier aussi les URL directes de photo, note, vCard, événement et scan ; ne pas limiter la recette aux liens visibles.
  Tester une note sentinelle dans les réponses reçues par les autres rôles et un désabonnement avant l'envoi.
- [ ] **9.4** Documenter dans `EXPLOITATION.md` : variables `PUBLIC_BASE_URL`, email/timeout, stockage privé,
  sauvegardes, restauration, préférences, publication, états d'envoi et reprise des échecs/états ambigus.
  Documenter que SMTP accepté ne signifie pas livré, que les notes ne sont pas chiffrées de bout en bout et que
  mettre un compte en veille n'est pas supprimer ses données.
- [ ] **9.5** Préparer la planification toutes les 15 minutes de `process_notifications --limit 50` et chaque
  heure de `expire_guest_access`. Le calendrier mensuel et les relances sont décidés par les services avec l'heure
  suisse ; ils ne reposent pas sur le fuseau implicite de l'hébergeur. Les jobs utilisent le même code et la même
  base que le site. Activer un seul ordonnanceur ; les réservations protègent néanmoins les chevauchements.
- [ ] **9.6** Avant les envois réels, exécuter le mode `--dry-run`, vérifier les compteurs et faire un essai
  à une adresse de l'équipe explicitement autorisée. Vérifier l'expéditeur et SPF/DKIM/DMARC avec le prestataire,
  puis rendre l'activation de l'automatisation explicite dans la configuration de production.
  Le mode démo ne doit envoyer qu'en console/mémoire ; bloquer un backend réel en démo hors essai autorisé.
- [ ] **9.7** Ajouter une procédure d'export/suppression : données de profil, photo, préférences, invitations,
  notes dont la personne est auteur/cible, rencontres, accès invités et historique d'emails minimal.
  Pour une demande d'accès portant sur des notes écrites par autrui, transmettre à l'équipe responsable du traitement
  pour examen ; ne pas produire automatiquement un export de notes privées destiné à leur cible.
  Ne pas prétendre que l'admin standard offre déjà un export/suppression complet de toutes ces données.
- [ ] **9.8** Mettre à jour l'architecture, le README et les chiffres de tests selon la mesure finale.
  Documenter ce qui est opérationnel et ce qui reste désactivé. Recompiler traductions et CSS, contrôler le diff.
  Ne pas cocher une tâche de déploiement si seuls les fichiers de configuration ont été préparés.

**Validation :** recette de confidentialité et de présence passée ; migrations vérifiées ; documentation exploitable ;
envoi réel et hébergement activés seulement dans le périmètre demandé et configuré par l'équipe.
**Commit suggéré :** `docs: documenter la recette et l'exploitation des améliorations`.

## 14. Liste des fichiers et commandes pour ne pas se perdre

Routes nouvelles prévues ; conserver le namespace `club` et compléter les arguments de test correspondants :

| Nom | Chemin | Méthodes | Accès |
|---|---|---|---|
| `club:member_note` | `/membres/<pk>/note/` | POST | Auteur connecté, cible accessible |
| `club:member_photo` | `/membres/<pk>/photo/` | GET | Lecteur connecté, cible accessible |
| `club:email_unsubscribe` | `/emails/desabonnement/<token>/` | GET confirmation, POST désactivation | Public, jeton signé dédié |
| `club:member_substitute` | `/evenements/<pk>/remplacant/` | GET formulaire, POST demande | Titulaire régulier connecté |
| `club:member_substitute_cancel` | `/evenements/<pk>/remplacant/annuler/` | POST | Titulaire régulier connecté |

Le lien authentifié de préférences peut pointer vers `/moi/#preferences-email` ; aucune page supplémentaire n'est
nécessaire si les champs sont regroupés dans le formulaire de profil. Les actions d'acceptation/publication/validation
utilisent les POST de l'admin ou de l'espace staff déjà existant.

Nouveaux services prévus :

| Fichier | Responsabilité unique |
|---|---|
| `club/services/notes.py` | Lecture/écriture d'une note pour son auteur |
| `club/services/photos.py` | Validation, normalisation et cycle de vie d'une photo |
| `club/services/membership.py` | Acceptation atomique d'une demande et création du compte |
| `club/services/notifications.py` | Sélection, campagnes, réservation, rendu et envoi des notifications |
| `club/services/substitutions.py` | Demande, validation, annulation et durée d'accès d'un remplaçant |
| `club/services/access.py` | Visibilité d'une fiche et périmètre des invités |

Commandes nouvelles prévues :

```bash
# Prévisualiser les notifications dues : aucune écriture ni aucun email
env DEBUG=1 .venv/bin/python manage.py process_notifications --dry-run --limit 50

# Traiter localement un lot avec le backend console, sur une base de développement
env DEBUG=1 NOTIFICATIONS_ENABLED=1 EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend .venv/bin/python manage.py process_notifications --limit 50

# Prévisualiser la mise en veille des invités
env DEBUG=1 .venv/bin/python manage.py expire_guest_access --dry-run
```

Ces commandes n'existent pas encore au moment de la rédaction. Ne pas les remplacer par du SQL manuel ou une
commande de reset. Elles prendront la base de l'environnement courant ; utiliser une base locale explicitement dédiée.

## 15. Message de démarrage à donner à l'IA

```text
Exécute docs/PLAN_AMELIORATIONS.md, une tâche numérotée à la fois.
Commence par la première case non cochée de ce document, pas celle de l'ancien docs/PLAN.md.
Lis CLAUDE.md pour les contraintes techniques, puis le plan complet et les fichiers de ta tâche.
Garde Django, templates, Tailwind local, JS vanilla et les protections existantes.
N'ajoute ni paiement en ligne, ni partage de compte, ni transfert de rencontres du remplaçant au titulaire.
Les notes appartiennent à leur auteur et ne doivent jamais figurer dans les réponses reçues par autrui.
Utilise env DEBUG=1 pour les tests locaux et une base de test dédiée ; ne touche pas aux données réelles.
Ne change pas les assertions existantes pour faire passer un test. Ajoute les cas de contrôle d'accès nécessaires.
À chaque fin de phase, exécute les vérifications indiquées, rapporte les résultats, puis coche les tâches terminées.
Prépare les fichiers avant de demander un choix externe ; ne pousse, ne déploie et n'envoie aucun email réel
sans que cela fasse partie de la demande en cours.
```
