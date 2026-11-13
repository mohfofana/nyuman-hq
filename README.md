# Nyuman HQ

Le QG de l'équipe Nyuman : messagerie, réunions, agenda, projets, fichiers, équipe (humains et agents). Voir `BRIEF.md` et `PLAN.md`.

## Lancer en local
Prérequis : PostgreSQL local avec une base `nyuman_hq` (`createdb nyuman_hq`), Node 20+, Python 3.9+.

```bash
cd server && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --port 8030 --reload
```

```bash
cd web && npm install && npm run dev
```

Puis ouvrir http://localhost:5180. En local, on choisit son profil sans mot de passe (`HQ_DEV_LOGIN=true`).

## Tests
```bash
cd server && createdb nyuman_hq_test && .venv/bin/pytest -q
```

## Secrets
Copier `server/.env.example` en `server/.env` et le remplir soi-même. `.env` n'est jamais commité.
