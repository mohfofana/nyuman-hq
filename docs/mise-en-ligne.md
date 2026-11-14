# Mettre Nyuman HQ en ligne

Préparé par Kwame le 13/11/2026. Tout est prêt côté code : il reste à choisir où l'héberger,
à créer la connexion Google et à poser les secrets. Kwame ne lit ni ne pose aucun secret.

## Ce qui change entre le local et la ligne
| | Local (aujourd'hui) | En ligne |
|---|---|---|
| Connexion | on choisit son profil, sans mot de passe | **compte Google**, et seulement les adresses de l'équipe |
| Site | serveur de développement (port 5180) | servi par le même serveur que l'API, une seule adresse |
| Base | PostgreSQL sur le Mac | PostgreSQL dans Docker, sur un disque qui survit aux mises à jour |
| Agents | réveillés sur le Mac | **toujours sur le Mac** (voir plus bas) |

## 1. Avant tout : remplir les adresses de l'équipe
Dans HQ, **Équipe → fiche de chacun → « Adresses pour se connecter »** (réservé aux responsables).
Chacun peut en avoir **plusieurs** : son adresse @nyuman.app et sa perso (Gmail). N'importe laquelle ouvre HQ,
et toutes mènent à la même fiche. Sans aucune adresse, la personne ne pourra pas entrer.
**À faire pendant que HQ tourne encore en local**, sinon plus personne ne peut se connecter.

Filet de sécurité si on oublie : la variable `HQ_BOOTSTRAP_EMAILS` (par exemple
`mon.adresse@gmail.com=mohamed`) laisse entrer cette adresse-là le temps de remplir les fiches. À retirer ensuite.

## 2. Où l'héberger
**Railway** (projet créé le 14/11, GitHub de Mohamed connecté). Le VPS reste possible plus tard ;
le `docker-compose.yml` à la racine sert dans ce cas.

### Railway, pas à pas
1. **Le dépôt GitHub** : Railway déploie depuis GitHub, donc le code doit y être (il n'y est pas encore).
2. **Deux services** dans le projet :
   - **Postgres** : « New → Database → PostgreSQL ». Railway crée `DATABASE_URL` tout seul ; HQ la lit
     sans réglage (y compris la forme `postgres://`).
   - **HQ** : « New → GitHub Repo », choisir le dépôt. Railway voit le `Dockerfile` et construit tout
     (le site est compilé dedans). `PORT` est fourni par Railway, HQ s'y adapte.
3. **Relier la base à HQ** : sur le service HQ, « Variables → Add Reference → Postgres DATABASE_URL ».
4. **Variables à poser sur le service HQ** (voir `server/.env.example`) :
   `HQ_PUBLIC_URL`, `HQ_SESSION_SECRET`, `HQ_GOOGLE_CLIENT_ID`, `HQ_GOOGLE_CLIENT_SECRET`,
   `HQ_DEV_LOGIN=false`, `HQ_COOKIE_SECURE=true`, `HQ_AGENT_WAKE=false`, et au besoin `HQ_BOOTSTRAP_EMAILS`.
5. **Un disque pour les fichiers envoyés** : « Settings → Volumes », monté sur `/data/uploads`.
   Sans lui, les images et pièces jointes disparaissent à chaque mise à jour.
6. **L'adresse** : « Settings → Networking → Custom domain » → `hq.nyuman.app`, puis le CNAME chez Cloudflare.
7. **Sauvegarde hebdomadaire** de la base (demandée par Koffi au vote).

## 3. Ce que Kevin fait côté Google (environ 30 min)
1. **Connexion Google** : un projet Google Cloud (gratuit), identifiant OAuth « Application Web ».
   - Origine autorisée : `https://hq.nyuman.app`
   - Adresse de retour : `https://hq.nyuman.app/api/auth/google/callback`
2. **Un fichier `.env`** à côté du `docker-compose.yml` (voir `server/.env.example`) :
   `HQ_PUBLIC_URL`, `HQ_SESSION_SECRET` (longue phrase au hasard), `HQ_GOOGLE_CLIENT_ID`,
   `HQ_GOOGLE_CLIENT_SECRET`, `HQ_DB_PASSWORD`.
   `HQ_DEV_LOGIN=false`, `HQ_COOKIE_SECURE=true` et `HQ_AGENT_WAKE=false` sont déjà posés dans le compose.
3. Le serveur crée ses tables tout seul au démarrage.
5. **Une sauvegarde par semaine** de la base (demandée par Koffi lors du vote).

## 4. Le dépôt
`~/Documents/nyuman-hq` n'a pas encore de dépôt GitHub. Dites à Kwame où le mettre
(organisation Nyuman ?) et il le prépare — il ne pousse rien sans l'accord de Mohamed.

## 5. Les agents continuent de tourner sur le Mac
Le réveil des agents lance `claude` avec le compte de Mohamed : ça ne peut pas tourner sur un serveur.
Une fois HQ en ligne, les agents répondent tant qu'une discussion Claude est ouverte sur le Mac,
grâce au guetteur (`server/scripts/attendre-message.py`). Si l'on veut qu'ils répondent sans le Mac,
il faudra en reparler : c'est un autre chantier.

## 6. À vérifier le jour J
- [ ] Chaque personne entre avec son compte Google et tombe sur **sa** fiche.
- [ ] Une adresse hors équipe est refusée proprement.
- [ ] Les fichiers déjà envoyés s'ouvrent (volume `hq-uploads`).
- [ ] Les réunions Jitsi s'ouvrent depuis le téléphone.
- [ ] Couper le lien temporaire Cloudflare et retirer `.trycloudflare.com` de `web/vite.config.ts`.
