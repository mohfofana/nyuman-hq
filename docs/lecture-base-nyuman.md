# Brancher les chiffres de l'app : lecture seule de la base Nyuman

HQ affiche les KPI de l'app Nyuman en lisant directement sa base Postgres, **sans toucher au code de nyuman-api**.
Décidé le 10 octobre 2026 : **d'abord la base de staging**, puis la production une fois les chiffres vérifiés.

## Ce que HQ peut voir, et rien d'autre
Un compte Postgres dédié, `hq_lecture`, en lecture seule, qui n'a le droit de lire que ces colonnes :

| Table | Colonnes | Pourquoi |
|---|---|---|
| `"user"` | `id`, `is_active`, `is_deleted` | compter les comptes activés |
| `reservation` | `id`, `provider_id`, `is_deleted` | relier un acompte à son pro |
| `acompte_escrow` | `id`, `reservation_id`, `acompte`, `frais_nyuman`, `promo_compensation`, `status`, `created_at`, `released_at`, `is_deleted` | réservations payées, acomptes, revenu |

Aucun nom, email, téléphone, mot de passe ni adresse : Postgres refuse toute requête qui essaierait de les lire.
HQ ne garde que les 5 totaux, au plus une fois par minute.

## 1. Créer le compte (une personne qui a accès à la base : Kevin a priori)
Le mot de passe est choisi par cette personne et n'est envoyé à personne d'autre qu'au réglage du serveur de HQ.

```sql
CREATE ROLE hq_lecture LOGIN PASSWORD 'mot-de-passe-choisi-par-l-equipe';
ALTER ROLE hq_lecture SET default_transaction_read_only = on;
ALTER ROLE hq_lecture SET statement_timeout = '5s';

GRANT CONNECT ON DATABASE nyuman_db TO hq_lecture;  -- remplacer par le nom de la base de staging
GRANT USAGE ON SCHEMA public TO hq_lecture;

GRANT SELECT (id, is_active, is_deleted) ON "user" TO hq_lecture;
GRANT SELECT (id, provider_id, is_deleted) ON reservation TO hq_lecture;
GRANT SELECT (id, reservation_id, acompte, frais_nyuman, promo_compensation, status, created_at, released_at, is_deleted)
  ON acompte_escrow TO hq_lecture;
```

Pour vérifier que le compte ne voit pas les données personnelles, connecté en `hq_lecture` :

```sql
SELECT email FROM "user" LIMIT 1;  -- doit répondre « permission denied »
```

## 2. Rendre la base joignable depuis HQ
Décidé le 11 octobre : **HQ s'installe sur le serveur de Nyuman, à côté de nyuman-api**, dans le même réseau Docker.
- **En production** : HQ joint Postgres par son nom de service Docker (par exemple `postgres:5432`). Rien n'est ouvert sur internet.
- **Pour tester depuis un PC** : un tunnel SSH vers le serveur, puis `localhost` dans l'adresse ci-dessous.

## 3. Régler HQ
Dans les variables d'environnement du serveur de HQ (ou `api/.env` en local) :

```
NYUMAN_DB_LECTURE_URL=postgresql://hq_lecture:MOT_DE_PASSE@postgres:5432/NOM_DE_LA_BASE
```

Redémarrer HQ. Dans **Réglages**, « Chiffres de l'app Nyuman » passe à « Branchée », et le salon affiche les KPI.
En cas de souci (base injoignable, droit manquant), le salon affiche un message et le reste de HQ continue de marcher.

## 4. Passer à la production
Une fois les chiffres de staging vérifiés : refaire l'étape 1 sur la base de production, puis changer l'adresse.

## L'autre possibilité, mise de côté
Une route `GET /statistiques/hq` dans nyuman-api avait été écrite. Elle est rangée dans un `git stash` du dépôt nyuman-api
(« Route GET /statistiques/hq pour Nyuman HQ »). HQ sait toujours la lire si un jour elle est déployée (`NYUMAN_API_URL`, `NYUMAN_STATS_KEY`).
