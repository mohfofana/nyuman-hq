# Nyuman HQ

QG virtuel de Nyuman : humains et agents travaillent ensemble, et chacun voit les autres travailler.
Tout le projet est décrit dans [docs/dossier-de-depart.md](docs/dossier-de-depart.md). Le lire avant de coder.

## Règles de travail
- Répondre en français, avec des mots simples. **Tous** les messages, y compris les petites phrases pendant le travail.
- Demander avant toute action vers l'extérieur (push, mise en ligne, envoi, publication). Un accord ne vaut que pour l'action concernée.
- Ne jamais manipuler de secrets : l'équipe entre elle-même les clés et mots de passe dans les réglages.
- Ne pas supprimer définitivement de fichiers : les mettre à la corbeille.

## Sur ce PC
- App Flutter : `..\nyuman-app`. API FastAPI : `..\nyuman-api`. (Les chemins `/Users/melyohthesun/...` du dossier sont ceux d'un Mac.)
- Le dossier est dans OneDrive : exclure `node_modules` et `.venv` de la synchro le moment venu.
- Les connecteurs branchés (HubSpot « Gamache Média », Make, Railway perso, Notion perso) ne sont **pas** ceux de Nyuman. N'y mettre aucune donnée Nyuman.

## Décisions du 10 octobre 2026
- Hébergement : ~~Railway~~ remplacé le 11 octobre par le serveur de Nyuman (voir plus bas).
- Budget IA de départ : 45 $ par mois pour les 3 premiers agents. Alerte à 36 $, arrêt à 45 $.
  Répartition proposée dans la maquette : Chef de cabinet 10 $, Contradicteur 20 $, Prospection 12 $, réserve 3 $.
- Outils : HQ fait tout au début (documents, tâches, fichier de prospection). On branchera des outils plus tard si besoin.
- Maquette (étape 0), à faire valider par l'équipe : https://claude.ai/artifact/8TVbQHXdAiMcqpmnQv2TVE

## Code
- `api/` : FastAPI, même architecture que nyuman-api (domain, use_cases, adapters, core, drivers). Routes découvertes dans `adapters/core/*/controller/*_controller.py`, toutes protégées sauf `@public`. Tests : `cd api; .venv\Scripts\python -m pytest`.
- `web/` : React + Vite + TypeScript. Tests : `npm test`. Le proxy Vite envoie `/api` vers le port 8000.
- Lancement, réglages et définitions des KPI : [README.md](README.md).
- Sur ce PC : Python 3.12 et Node 24 installés le 10 octobre 2026 (winget). Les chemins contiennent des espaces : appeler `node.exe` ou le python du venv directement, pas `npm.cmd`.

## État au 10 octobre 2026
- Semaine 1 faite en local : connexion (Google + connexion de développement), salon (objectif, KPI, fil), bibliothèque (versions, corbeille), réglages. Pas encore en ligne.
- KPI : **on ne modifie pas nyuman-api.** HQ lit la base Nyuman en lecture seule (`NYUMAN_DB_LECTURE_URL`), avec un compte limité aux colonnes sans données personnelles : [docs/lecture-base-nyuman.md](docs/lecture-base-nyuman.md). Staging d'abord, production ensuite. Le compte et l'accès réseau sont à créer par l'équipe (Kevin).
- La route `GET /statistiques/hq` écrite pour nyuman-api est mise de côté dans un `git stash` de ce dépôt ; nyuman-api est resté sur `development`, sans changement.

## État au 11 octobre 2026
- Nouvelle identité « la maison » (cacao, crème, orange Nyuman ; agents en indigo) : `web/src/styles.css`.
- Accueil = plan de la maison avec la présence en direct (`web/src/components/HousePlan.tsx`), fil et notifications en temps réel.
- Temps réel : flux SSE `GET /api/flux` + `POST /api/presence` (`api/core/realtime/`). En mémoire : **un seul worker**, et uvicorn avec `--timeout-graceful-shutdown 2` (sinon les redémarrages attendent la fin des flux).
- Bureaux ouverts : `/bureaux` et `/bureaux/:id` (fiche de poste des agents dans `web/src/agents.ts`).
- Hébergement décidé le 11 octobre : **sur le serveur de Nyuman, à côté de nyuman-api** (Docker), pour lire la base en interne. Remplace Railway.
- Organisation de Nyuman : le CEO (Mohamed Fofana) et 3 heads qui lui rendent compte, un pôle chacun :
  Sullyvan Koffi (COO, Opérations), Kevin Diakité (CTO, Produit), Abraham Doumbia (CGO, Croissance et marketing).
  Membres et tâches ont un `pole` (direction, operations, produit, croissance). Organigramme dans `/bureaux`.
- Les testeurs TestFlight sont internes et s'envoient leurs retours sur WhatsApp : HQ a un bouton « Signaler un retour »
  (bug, idée, remarque + captures) et une colonne « Retours à trier » dans la salle de projet. L'import App Store Connect
  existe mais reste éteint tant qu'il n'y a pas de testeurs externes (clé ASC_* à entrer par l'équipe).
- Salle de projet ouverte (`/projet`) : tableau des tâches humains et agents, glisser-déposer, liées à l'objectif, filtre par pôle.
- Bureaux : chaque pôle a son objectif (`/api/objectifs/courant?pole=…`, chiffre de l'app ou tenu à la main) et chaque
  humain publie son rapport de la semaine (fait, en cours, bloqué, 3 propositions ; `/api/rapports`). L'organigramme montre
  la jauge de chaque pôle et qui a publié son rapport.
- Les mails @nyuman.app sont **chez Netim, pas chez Google** : connexion principale = lien envoyé par email
  (`POST /api/auth/lien` puis `/connexion#jeton=…`, 15 minutes, une seule fois, 3 liens max par quart d'heure).
  Envoi par SMTP (`SMTP_*`, mot de passe entré par l'équipe) ; sur le PC, le lien s'affiche dans le journal du serveur.
- Membres ajoutés le 11 octobre : Sullyvan Koffi (head, COO, opérations), Abraham Doumbia (head, CGO, croissance),
  Carmel Didi (membre, CFO, pôle opérations). Kevin pas encore ajouté : adresse à confirmer (`kevin.diakité@` avec accent ?).
- Le tableau Google « NYUMAN APP - PHASE PRE-LANCEMENT » est repris dans HQ (décision du 11 octobre : tout passer dans HQ,
  panel des prestataires compris, car c'est avec elles que commencent les tests externes). Import .xlsx dans Réglages
  (`POST /api/import/tableau`, aperçu puis confirmation, repère `ref_externe` contre les doublons). Fait en local le 11 octobre :
  13 tâches, 22 étapes, 12 sujets au conseil, 13 pros, 4 documents « Tableau — … » (rayon Finances). À refaire sur le serveur.
- Ce tableau est ouvert à toute personne qui a le lien, avec les téléphones et emails des prestataires : conseillé à l'équipe
  de passer le partage en « Limité ». Les 3 décisions du 11 octobre y sont en double ; formules cassées (#REF!) dans
  Projection, Jalons et Suivi_Rentabilite_Mensuelle ; la règle des frais Nyuman n'y est pas la même partout.
- Salle du conseil ouverte (`/conseil`, `/api/decisions`) : tout humain propose, seuls les heads votent et tranchent, bilan à 30 jours.
  Panel des pros ouvert (`/pros`, `/api/pros`). Tâches : `priority` (P0-P3) et sous-étapes (`/api/taches/{id}/etapes`).
- Mise en ligne préparée le 11 octobre (pas encore faite) : `Dockerfile`, `deploy/` (compose avec sa propre base Postgres,
  Nginx, sauvegardes, modèle de .env), guide [docs/mise-en-ligne.md](docs/mise-en-ligne.md), tests GitHub (SQLite + Postgres).
  Vérifié : 102 tests aussi sur un vrai Postgres, migrations aller-retour, mode production en local (en-têtes, noindex, 401 partout).
  `nyumangroup` est un compte GitHub personnel (pas une organisation) : mohfofana peut pousser sur nyuman-api mais pas y créer un dépôt.
  Le serveur (VPS, Nginx, Cloudflare, `api.nyuman.com`) est géré par l'équipe ; Claude n'y a pas accès.
- Prochaine étape : les agents (clé Anthropic à entrer par l'équipe), en commençant par le Contradicteur dans la salle du conseil.

## Encore ouvert
- L'adresse exacte de Kevin (sans doute `kevin.diakite@nyuman.app`, sans accent), et les outils de chaque head.
- La boîte Netim qui enverra les liens (ex. `hq@nyuman.app`) et ses réglages SMTP, à entrer par l'équipe sur le serveur.
- Installer HQ sur le serveur de Nyuman (Kevin). L'identifiant OAuth Google devient facultatif.
- Valider la définition de « pro actif » (réservation avec acompte payé dans les 30 derniers jours).
- Failles de sécurité de nyuman-api repérées (routes admin ouvertes à tout compte connecté, listes complètes des utilisateurs avec emails et téléphones, secret JWT par défaut, mots de passe en SHA-256) : proposées comme tâches séparées.
