# Pitch — Club des Affaires (5 minutes + questions)

> **Pour qui** : toi, qui présentes seul devant un jury technique.
> **Fiabilité** : tout ce qui est chiffré ici a été **mesuré sur ce dépôt** (voir [ARCHITECTURE.md](ARCHITECTURE.md)).
> Les parties « à dire » sont des propositions : reformule-les à ta façon, garde les chiffres.

## 1. L'idée en une phrase

> « Le Club se retrouve quatre à cinq fois par an, mais ses membres ne se connaissent pas. On leur donne un album,
> des rencontres suggérées et des tables qui tournent, sans leur demander d'effort. »

Slogan : **« Plus jamais d'inconnus au Club. »**

## 2. Déroulé (5 minutes)

| Temps | Partie | Ce que tu montres |
|---|---|---|
| 0:00 – 0:35 | Le problème | la vitrine publique |
| 0:35 – 1:05 | La solution : avant, pendant, après | la vitrine (les trois promesses) |
| 1:05 – 3:15 | **Démo en direct** (§3) | téléphone + écran du staff |
| 3:15 – 4:15 | Pourquoi c'est solide | rien : tu parles, ou une seule diapositive |
| 4:15 – 4:45 | Échelle, coûts, suite | idem |
| 4:45 – 5:00 | Conclusion | la vitrine |

**Le problème (35 s).**
« Le Club des Affaires de la Foire du Valais, c'est environ 50 dirigeants qui paient 500 francs par an. Les soirées
marchent : 80 % de présence. Mais ils arrivent en inconnus, restent entre eux en petits groupes, et entre deux
soirées, la communication va dans un seul sens : de la Foire vers eux. Et l'équipe n'a pas le temps d'animer une
communauté au quotidien. Une application avec un fil d'actualité serait vide en trois semaines. »

**La solution (30 s).**
« Alors on a fait l'inverse : une application qui vit au rythme des événements. *Avant* la soirée, on apprend à se
connaître : un album de cartes, des affinités, et trois rencontres suggérées à chacun. *Pendant*, on se mélange :
un QR code pour garder le contact, des tables qui changent à chaque service. *Après*, on mesure : chaque membre voit
son album se remplir, et le comité voit si le Club se resserre. »

**Pourquoi c'est solide (1 min), pour un jury technique.**
« Quatre choix. *Un*, Django : l'authentification, la protection CSRF, l'échappement, l'internationalisation et
l'administration sont dans le framework, donc moins de code à écrire et moins de failles possibles. *Deux*, la
sécurité est fermée par défaut : toute page demande une connexion, les coordonnées d'un membre ne s'affichent qu'après
une vraie rencontre, la politique de sécurité du navigateur interdit tout script ou style en ligne, et un test parcourt
toutes les routes pour s'en assurer. *Trois*, les deux algorithmes sont mesurés : pour 200 inscrits, les rencontres se
calculent en 49 millisecondes et le plan de tables en moins d'une seconde, sans que personne ne se retrouve deux fois à
la même table. *Quatre*, 170 tests automatisés, sur SQLite et sur PostgreSQL, y compris un test qui vérifie qu'aucune
phrase française ne reste sur les pages allemandes. »

**Échelle, coûts, suite (30 s).**
« L'application est sans état : pour passer de 50 à 200 membres, on ajoute des processus. Le fonctionnement coûte moins
de 500 francs par an, soit moins de 2 % des cotisations. La mise en production prend environ 6 à 8 jours, dans le
budget de 10 000 francs. Ensuite : une bourse « je cherche, je propose », le paiement des cotisations, et la même
plateforme pour d'autres clubs. »

**Conclusion (15 s).**
« Un club qui se connaît se retrouve. Merci. »

## 3. La démo, mot à mot (environ 2 min 10)

> Comptes : mot de passe `club-demo-2026` (ou celui que tu as mis dans `DEMO_PASSWORD` en ligne).
> Prépare **trois fenêtres** : Camille sur le téléphone (ou une fenêtre à largeur de mobile), Lukas en fenêtre privée,
> le staff sur l'ordinateur. Ce déroulé a été **rejoué automatiquement** de bout en bout, sans erreur.

| # | Tu fais | Tu dis |
|---|---|---|
| 1 | Vitrine, déconnecté. Montre « Demander une invitation ». | « Voilà ce que voit quelqu'un de l'extérieur : un club sur invitation, et aucun nom de membre. » |
| 2 | Connexion de **Camille** (`camille.rey@example.com`). Accueil. | « Camille vient de rejoindre le Club. Elle voit son album : 2 cartes sur 49, et le prochain dîner. » |
| 3 | Fais défiler « Tes rencontres » sur l'accueil, puis ouvre l'événement. | « L'appli lui propose trois personnes à rencontrer, avec la raison : Lukas et elle aiment la Petite Arvine, le ski de randonnée, la course à pied, et détestent les réunions du lundi matin. Et une phrase pour lancer la conversation. » |
| 4 | Album : montre le contour doré (fondateur) et vert (nouvelle recrue), puis le filtre **Germanophones**. | « Chaque membre a sa carte, avec son rang. On peut filtrer par langue : c'est un club qui veut s'ouvrir à toute la Suisse. » |
| 5 | **Lukas** (fenêtre privée) : « Mon QR ». **Camille** : ouvre le lien du QR → « Ajouter Lukas à mon album ». *(Avec le badge imprimé : scanne-le avec l'appareil photo.)* | « Pendant la soirée, on se scanne. Avant ça, les coordonnées de Lukas étaient verrouillées. » |
| 6 | Montre les coordonnées débloquées, « Ajouter à mes contacts » (la vCard s'ouvre), puis l'accueil : **3 / 49**. | « Elles se débloquent, et la carte de visite part directement dans le répertoire. L'album passe à 3 sur 49. » |
| 7 | **Staff** (`equipe@example.com`) : tableau de bord. | « Côté équipe : l'indice de fédération, c'est la part des paires de membres qui se connaissent. 15 % aujourd'hui. Et ces membres encore isolés : à présenter lors du prochain événement. » |
| 8 | Dîner d'automne → **Préparer** → « Générer le plan de tables ». | « Pour le dîner : 38 invités, trois services. L'algorithme répartit les tables pour que chacun rencontre de nouvelles personnes à chaque service : un clic. » |
| 9 | Retour sur Camille, event → « Ton placement ». Bascule **DE**. | « Camille voit sa table pour chaque service. Et tout passe en allemand, dates et affinités comprises. » |

**Si tu as 30 secondes de plus** : Profil → « Refaire le swipe » (les cartes à glisser), ou « Inviter quelqu'un » (lien
personnel, QR, offre de parrainage), ou « Ouvrir les badges » (feuille A4 prête à imprimer).

## 4. Avant de monter sur scène

- [ ] Ouvrir l'URL de production **2 minutes avant** (l'offre gratuite de Render se met en veille après 15 minutes).
- [ ] Données fraîches : `DATABASE_URL='<External Database URL>' DEMO_PASSWORD='<le même que sur Render>' python manage.py seed_demo --reset`.
- [ ] Camille est connectée sur le téléphone, Lukas en fenêtre privée, le staff sur l'ordinateur.
- [ ] Badge de Lukas **imprimé depuis la production** (`/staff/evenements/4/badges/`) : le QR contient l'adresse du site.
- [ ] Vidéo de secours de la démo sur le bureau (QuickTime → Nouvel enregistrement de l'écran).
- [ ] Réseau : un partage de connexion du téléphone prêt ; mode « Ne pas déranger » activé ; luminosité au maximum.
- [ ] Navigateur en français au départ (la bascule en allemand fait partie de la démo).
- [ ] Plan B si le site ne répond pas : le tunnel (`cloudflared tunnel --url http://localhost:8000`) ou la vidéo.

## 5. Chiffres à citer

| Chiffre | Source |
|---|---|
| ~50 membres, 500 CHF par an, 80 % de présence, 4 à 5 soirées par an, objectif 100 à 200+ | le client |
| **49 ms** pour calculer les rencontres de 200 inscrits | mesuré (ARCHITECTURE §7) |
| **0,76 s** pour le plan de tables de 200 invités, aucune répétition de voisin | mesuré |
| **0 répétition** pour 40 invités, tables de 6, 3 services | mesuré |
| **15 %** : indice de fédération des données de démo (180 paires sur 1 225) | `seed_demo` |
| **170 tests**, SQLite et PostgreSQL, mode production vérifié | `python manage.py test club` |
| **48 pages** contrôlées à 390 px et 1 280 px, en FR / DE / EN, sans débordement ni erreur de sécurité | balayage automatique |
| **< 500 CHF par an** de fonctionnement, **6 à 8 jours** de mise en production | estimation (ARCHITECTURE §9) |

## 6. Questions probables du jury technique

**Pourquoi Django plutôt que Next.js et Supabase ?**
L'équipe a besoin d'un back-office (membres, événements, inscriptions) dès le premier jour : Django le fournit, sécurisé.
L'authentification, le CSRF, l'échappement automatique, les migrations et l'internationalisation sont inclus : moins de
code, moins de failles. Rendu côté serveur : pas d'API exposée à protéger, pages légères sur mobile. Hébergeable en Suisse
chez n'importe quel hébergeur, maintenable par n'importe quelle agence, version à support long terme jusqu'en avril 2028.

**Pourquoi une web app et pas une application native ?**
Rien à installer pour 50 dirigeants pressés, un QR code ouvre directement la bonne page, une seule base de code au lieu de
trois. Le seul JavaScript (swipe, copier, imprimer) est une amélioration : sans lui, tout fonctionne.

**Comment fonctionne « Tes 3 rencontres » ?**
Chaque paire d'inscrits reçoit un score : +3 par affinité commune, +2 par agacement commun, +2 si les secteurs sont
différents, +3 pour une nouvelle recrue avec un pilier du Club. Deux règles absolues : jamais deux personnes qui se
connaissent déjà, jamais sans langue commune. Attribution gloutonne et équitable (tout le monde a une première rencontre
avant que quiconque en ait une deuxième), déterministe, en O(n²).

**Et les tables tournantes ?**
C'est une variante du *Social Golfer Problem*, NP-difficile. Recherche locale avec redémarrages : on échange deux invités
de tables différentes et on garde l'échange s'il ne dégrade pas le coût (déjà assis ensemble : 10, aucune langue commune : 4,
se connaissent déjà : 3, même secteur : 1). Avec 5 tables de 8 pour 40 invités, des répétitions sont mathématiquement
inévitables : d'où le réglage par défaut de **tables de 6**.

**Comment mesurez-vous le succès ?**
L'indice de fédération (part des paires de membres qui se connaissent), le nombre de rencontres par événement, et la liste
des membres isolés (deux rencontres ou moins) sur laquelle l'équipe peut agir. Un test sur les données de démo vérifie ces chiffres.

**Qu'en est-il de la sécurité ?**
Fermé par défaut (un middleware exige la connexion partout, la vitrine et deux formulaires sont les seules exceptions) ;
une **matrice d'accès testée** (toute nouvelle route doit être classée, sinon la suite échoue) ; CSP stricte (`script-src 'self'`,
aucun style ou script en ligne, aucun service tiers) ; CSRF sur tous les formulaires (un test le vérifie dans les templates) ;
cookies `HttpOnly`, `Secure`, `SameSite`, HSTS ; ORM (pas d'injection SQL) ; vCard échappée selon la RFC 6350 ; QR avec un
jeton aléatoire de 128 bits (jamais un identifiant prévisible) ; liens de connexion à usage unique, valables 15 minutes ;
même réponse pour une adresse inconnue ; formulaire public protégé (champ piège, anti-doublon). `check --deploy` : aucune alerte.

**Et la protection des données (nLPD) ?**
Protection dès la conception : l'annuaire n'est visible que par les membres, les coordonnées ne sont partagées qu'après une
rencontre (le scan du QR vaut consentement), chaque membre peut masquer sa carte, on ne collecte que le minimum professionnel.
La démo est hébergée dans l'Union européenne avec des données fictives ; la production visée est hébergée en Suisse.

**Que se passe-t-il si les membres ne remplissent pas leur profil ?**
L'équipe peut pré-remplir depuis l'administration (import CSV prévu en V1.1), le swipe prend deux minutes, une bannière
rappelle de le faire. Et le score garde des critères qui ne demandent rien aux membres : secteurs différents, nouvelle
recrue avec un pilier, langue commune.

**Est-ce que ça tient à l'échelle ?**
L'application est sans état : on ajoute des processus. Les contraintes uniques créent les index utiles, les requêtes N+1 sont
évitées. 200 inscrits : moins d'une seconde pour les deux algorithmes. Au-delà de quelques milliers de membres, on déporterait
le calcul en tâche de fond. La V3 prévoit plusieurs clubs sur la même plateforme.

**Comment gérez-vous les langues ?**
L'internationalisation de Django pour l'interface (303 textes), des champs traduits en base pour les affinités et les phrases
d'accroche, l'allemand en orthographe suisse. Un test parcourt toutes les pages en allemand et en anglais et échoue si une
phrase française d'interface subsiste. Ajouter l'italien : un fichier de traduction et trois colonnes.

**Pourquoi pas WhatsApp, Hivebrite ou Brella ?**
WhatsApp : tout le monde voit le numéro de chacun, aucun annuaire, aucune donnée exploitable. Hivebrite et consorts : licence
annuelle, données hors de Suisse, et un fil d'actualité qui serait vide sans animateur. Brella et consorts : facturés par
événement et pensés pour des rendez-vous commerciaux, la « vente forcée » que le client ne veut pas.

**Combien ça coûte, et en combien de temps ?**
Moins de 500 CHF par an de fonctionnement (estimation : hébergement suisse, e-mails, nom de domaine), soit moins de 2 % des
cotisations. Environ 6 à 8 jours pour passer du prototype à la production (hébergement suisse, e-mails, charte graphique,
import des membres, double authentification du staff, politique de confidentialité), dans l'enveloppe de 10 000 CHF.

**Comment l'équipe, qui a peu de temps, l'utilise-t-elle ?**
Pas de fil d'actualité à animer : les événements donnent le rythme. L'équipe fait trois gestes par événement : créer
l'événement, générer les rencontres et le plan de tables, imprimer les badges. Les rappels automatiques sont prévus en V2.

**Pourquoi des sessions de six mois ?**
Les membres sont pressés et pas tous à l'aise avec le numérique : se reconnecter le soir d'un événement est le pire moment.
La session est renouvelée à chaque visite, le cookie est protégé, et la double authentification du staff est prévue en V1.1.

**Qu'est-ce qui n'est pas fait ?** *(réponds franchement)*
Le paiement des cotisations, les notifications, l'import CSV des membres, la double authentification du staff, l'export et la
suppression de données en libre-service (possibles aujourd'hui via l'administration). Pour la connexion par lien, une étape
de confirmation par bouton est prévue : certaines passerelles de sécurité e-mail ouvrent les liens à l'avance et consomment le
lien à usage unique. Les titres et descriptions d'événements restent dans la langue saisie par l'équipe.

**Comment puis-je tester moi-même ?**
Ouvre l'URL de démo (compte Camille), ou en local : `seed_demo --reset` puis `runserver` ; la suite se lance avec
`python manage.py test club`.
