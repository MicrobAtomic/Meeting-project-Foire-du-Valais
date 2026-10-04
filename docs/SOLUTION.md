# Le sujet et la solution

> **▶ En vidéo** : [la démo commentée, 3 min 15](pitch/demo-long.mp4) ([lecture directe](https://github.com/MicrobAtomic/Meeting-project-Foire-du-Valais/raw/main/docs/pitch/demo-long.mp4)) montre tout ce
> qui suit en action, du premier contact d'un futur membre jusqu'au plan de tables de l'équipe.

## Le défi

Le Club des Affaires de la Foire du Valais réunit une cinquantaine de dirigeantes et de dirigeants. Ils paient
500 CHF par an et se retrouvent quatre à cinq fois par an, avec 80 % de présence. Le problème n'est pas de venir :
**ils ne se connaissent pas**. Ils arrivent en inconnus, restent entre habitués, et entre deux soirées le réseau
n'existe pas. La communication va dans un seul sens, de la Foire vers eux.

Le défi du hackathon : **une plateforme de networking qui active le réseau toute l'année**, autour de quatre piliers :
se trouver (secteur, profil, compétences, besoins), identifier des synergies, créer des collaborations, appartenir à la
Foire.

## Ce que le client m'a dit

| Ce que j'ai entendu | Ce que j'en ai fait |
|---|---|
| Pas de business forcé : les affaires sont une porte, pas le cœur | Les passions passent avant le métier ; les coordonnées ne se débloquent qu'après une vraie rencontre |
| Une équipe avec très peu de temps | Pas de fil d'actualité à animer ; une administration guidée ; tout le reste est calculé |
| Des membres pressés, pas tous à l'aise avec le numérique | Rien à installer, un QR code suffit, connexion par lien reçu par e-mail |
| Francophones et germanophones, ouverture au-delà du Valais | Interface et contenus en français, allemand et anglais |
| Un club premium : la qualité des gens et des soirées | Sur invitation, liste des membres jamais publique, design sobre |
| Grandir : de 50 vers 100 à 200 membres | Parrainage, vitrine sans nom de membre, plan de recrutement ciblé ([MARKETING](MARKETING.md)) |

## Ma solution en une phrase

**Plus jamais d'inconnus au Club** : une web app réservée aux membres, qui suit le rythme des soirées.

- **Avant** la soirée, chacun sait déjà qui rencontrer, et pourquoi.
- **Pendant**, un QR code prouve la rencontre et un jeu brise la glace.
- **Après**, l'album se remplit et le Club entier mesure qu'il se resserre.

## Ce que fait l'application, pilier par pilier

| Pilier du défi | Ce que j'ai construit |
|---|---|
| 🔍 **Se trouver** | Une carte par membre : entreprise, secteur, ancienneté, langues, passions et agacements, anecdote, « je peux aider sur… » et « je cherche… ». Un album avec recherche et filtres, dont « peut m'aider sur… ». |
| ⚡ **Repérer les synergies** | Avant chaque soirée, « tes 3 rencontres » : trois personnes inconnues, choisies pour leurs passions communes, des secteurs complémentaires et un besoin que l'autre peut combler. Chaque rencontre affiche sa raison et une phrase pour lancer la conversation. |
| 🤝 **Se rencontrer pour de vrai** | Scanner le badge de quelqu'un ajoute sa carte à son album et débloque ses coordonnées (vCard). Chaque soirée a son jeu : un **bingo des rencontres** calculé pour chaque invité à l'apéro, des **tables tournantes** au dîner assis. |
| 🏔️ **Appartenir et garder le lien** | Un **indice de fédération** (la part des membres qui se connaissent) et des paliers collectifs à récompense valaisanne ; des objectifs personnels d'album ; des notes privées sur chaque rencontre ; des annonces, relances et un récapitulatif mensuel des nouveaux membres. |

**Pour l'équipe événements** : un tableau de bord (rencontres, membres isolés, demandes d'invitation, paliers), la
préparation d'une soirée en un clic (rencontres proposées, plan de tables, badges A4 avec QR code, gagnants du bingo),
l'acceptation d'une demande d'invitation qui crée le compte, les remplaçants d'un soir, et une administration qui
s'ouvre sur un mode d'emploi en six gestes.

**Pour les futurs membres** : une vitrine publique qui ne montre aucun nom de membre, et une demande d'invitation en
deux minutes, avec ou sans parrain.

## Trois parcours

**Camille, nouvelle membre.** Elle demande une invitation ; l'équipe l'accepte en un clic et elle reçoit son accès.
Elle swipe ses affinités, indique ce qu'elle peut offrir (le digital) et ce qu'elle cherche (le marché alémanique).
Avant le dîner d'automne, l'application lui présente Lukas : ils aiment tous deux la Petite Arvine, et chacun peut aider
l'autre. Au dîner, elle scanne son badge : sa carte entre dans l'album, ses coordonnées se débloquent, une case de son
bingo se coche, et le Club avance vers son prochain palier.

**Lukas, pilier du Club.** Il reçoit à chaque soirée des personnes nouvelles à rencontrer, dont les nouvelles recrues :
le matching associe volontairement un nouveau membre à un pilier. S'il ne peut pas venir, il propose un remplaçant de son
entreprise, qui reçoit un accès limité à la soirée.

**L'équipe.** Elle crée l'événement (un encart par langue), coche ses animations, le publie. Une semaine avant, elle
clique sur « Préparer » : rencontres, plan de tables et badges sont prêts. Le soir même, elle donne la liste des gagnants
du bingo au bar.

## Ce que j'ai volontairement laissé de côté

- **Un fil d'actualité ou une messagerie** : vides sans animateur, et ils poussent au démarchage.
- **Le paiement en ligne des cotisations** : la facturation reste manuelle aujourd'hui ; TWINT et QR-facture sont prévus.
- **Une application native** avec notifications push : un téléchargement de trop pour 50 personnes (voir
  [ARCHITECTURE](ARCHITECTURE.md)).

## Où en est le projet

Tout ce qui précède fonctionne et est testé sur des données fictives. Avant une vraie mise en service, il reste à
héberger l'application en Suisse, importer les membres actuels, activer l'envoi des e-mails et le stockage durable des
photos : la marche à suivre est dans [EXPLOITATION](EXPLOITATION.md), les coûts dans [ARCHITECTURE](ARCHITECTURE.md).
