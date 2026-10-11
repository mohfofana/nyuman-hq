# Nyuman HQ

Le QG virtuel de Nyuman : humains et agents travaillent ensemble, et chacun voit les autres travailler.
Le projet complet est décrit dans [docs/dossier-de-depart.md](docs/dossier-de-depart.md).

## Ce qui marche (semaine 1)
- **Connexion par lien envoyé par email** : on tape son adresse @nyuman.app, on reçoit un lien valable 15 minutes et utilisable une seule fois. Pas de mot de passe. Google reste possible si l'identifiant OAuth est réglé. Seules les adresses ajoutées par un head entrent. Deux droits : head et membre.
- **Le salon** : l'objectif du trimestre avec sa jauge, les KPI en direct de l'app Nyuman, le fil de la maison, le rythme de la semaine.
- **La bibliothèque** : documents en Markdown, rangés par rayon, recherche, historique de chaque version, corbeille (rien n'est supprimé).
- **Les réglages** : l'équipe (humains et agents dans la même liste), ajout de membres, état des branchements.
- **La salle de projet** : tableau des tâches (humains et agents), priorité P0 à P3, sous-étapes avec responsable, livrable et échéance.
- **La salle du conseil** : les sujets à trancher (demande, objectif servi, risques), les votes des heads, le journal des décisions revu à 30 jours. La file de validation des agents viendra avec les agents.
- **Le panel des pros** : fondateurs, ambassadeurs et partenaires, avec contrat/NDA et accès aux tests. Données personnelles : réservé à l'équipe connectée, jamais dans le fil.
- **Reprise du tableau Google** (Réglages, heads) : on envoie le tableau en .xlsx, on voit un aperçu, puis on confirme. Tâches et étapes → salle de projet, décisions → conseil, prestataires → panel, autres onglets → bibliothèque. Relancer n'ajoute que ce qui manque.
- Les trois premiers agents (Chef de cabinet, Contradicteur, Prospection) sont déjà membres de la maison, « en préparation ». Ils travaillent à partir de la semaine 3.

## Organisation
```
api/   serveur Python (FastAPI), même architecture que nyuman-api
  domain/      entités (Membre, Document, Objectif, Evenement) et KPI
  use_cases/   un fichier par action, interfaces des dépôts et des ports
  adapters/    tables SQLAlchemy, dépôts, contrôleurs, *_app_config.py
  core/        réglages, base de données, session, erreurs
  drivers/     application FastAPI, découverte des routes, données de départ
  migrations/  migrations Alembic
  tests/       tests unitaires (use cases) et tests de l'API
web/   interface React (Vite, TypeScript)
```
Comme dans nyuman-api, chaque route exige une session, sauf celles marquées `@public`.

## Lancer HQ sur un PC
Il faut Python 3.12 et Node 22 ou plus.

```bash
cd api
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
copy .env.example .env
.venv\Scripts\python -m uvicorn drivers.main:app --reload --port 8000 --timeout-graceful-shutdown 2
```

Dans un second terminal :

```bash
cd web
npm install
npm run dev
```

Ouvrir http://localhost:5173. En local, `HQ_DEV_LOGIN=true` permet d'entrer avec l'adresse d'un head (listée dans `HQ_HEADS_INITIAUX`) sans Google.
Sans boîte mail réglée (`SMTP_HOST` vide), la connexion par lien marche aussi sur le PC : le lien s'affiche dans le journal du serveur au lieu d'être envoyé.

## Tests
```bash
cd api
.venv\Scripts\python -m pytest
```

```bash
cd web
npm test
```

## Réglages du serveur
Toutes les valeurs sont dans les variables d'environnement (voir `api/.env.example`). **L'équipe entre elle-même les clés** : elles ne passent jamais par le code ni par l'interface.

| Variable | À quoi elle sert |
|---|---|
| `ENVIRONMENT` | `production` sur Railway : interdit la connexion de développement, exige un vrai secret |
| `DATABASE_URL` | Postgres fourni par Railway (SQLite en local par défaut) |
| `HQ_SESSION_SECRET` | signe les sessions, 32 caractères au moins |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | boîte @nyuman.app (chez Netim) qui envoie les liens de connexion. Port 465 (SSL) ou 587 (STARTTLS). Le mot de passe est entré par l'équipe sur le serveur |
| `HQ_PUBLIC_URL` | adresse publique de HQ : les liens envoyés par email y mènent (obligatoire en production si `SMTP_HOST` est rempli) |
| `GOOGLE_CLIENT_ID` | facultatif : identifiant OAuth « Application Web » créé dans la console Google Cloud de Nyuman |
| `HQ_HEADS_INITIAUX` | adresses des premiers heads ; ils ajoutent ensuite les autres dans Réglages |
| `HQ_ORIGINES` | adresses autorisées à écrire depuis un navigateur |
| `NYUMAN_DB_LECTURE_URL` | compte Postgres en lecture seule sur la base Nyuman, limité aux colonnes sans données personnelles ([marche à suivre](docs/lecture-base-nyuman.md)) |
| `NYUMAN_API_URL`, `NYUMAN_STATS_KEY` | autre possibilité, mise de côté : une route statistiques dans nyuman-api |

## Les KPI
HQ les calcule en lisant directement la base de l'app Nyuman, **sans modifier nyuman-api** : une seule requête, au plus une fois par minute, avec un compte qui ne voit aucune donnée personnelle. On commence par la base de staging. Marche à suivre : [docs/lecture-base-nyuman.md](docs/lecture-base-nyuman.md).

| KPI | Définition |
|---|---|
| Utilisateurs inscrits | comptes activés (OTP) et non supprimés |
| Pros actifs (30 jours) | pros avec au moins une réservation dont l'acompte est payé ces 30 derniers jours |
| Réservations payées (7 jours) | acomptes payés ces 7 derniers jours, hors remboursés |
| Acomptes encaissés (7 jours) | somme de ces acomptes |
| Revenu Nyuman (7 jours) | frais Nyuman des acomptes reversés aux pros ces 7 derniers jours, moins les promos prises en charge |

## En production
Marche à suivre complète (serveur de Nyuman, Docker, Nginx, Cloudflare, sauvegardes) : [docs/mise-en-ligne.md](docs/mise-en-ligne.md).

Un seul service suffit : si `web/dist` existe (après `npm run build`), le serveur FastAPI sert aussi l'interface. Les migrations tournent au démarrage.

Toujours lancer uvicorn avec `--timeout-graceful-shutdown 2` et **un seul worker** :
- les flux en direct (`/api/flux`) restent ouverts ; sans ce délai, un redémarrage attend indéfiniment qu'ils se ferment (les écrans se reconnectent seuls) ;
- la présence et la diffusion en direct sont gardées en mémoire, donc partagées seulement à l'intérieur d'un même processus.
