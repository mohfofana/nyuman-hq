# Nyuman HQ en ligne

**HQ est en ligne depuis le 14/11/2026** : **https://teams.nyuman.app**
Projet Railway `nyuman-hq`, espace **Nyuman** (à côté de `nyuman-backoffice`) : un service `hq`
(construit depuis le Dockerfile du dépôt `mohfofana/nyuman-hq`), une base PostgreSQL, et un disque
`fichiers-hq` monté sur `/data/uploads` pour les pièces jointes.

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

Quand quelqu'un arrive sur HQ avec une adresse inconnue, il **se présente lui-même** : HQ lui montre les
fiches sans adresse, il choisit la sienne, et un responsable confirme d'un clic depuis son espace
(« Quelqu'un veut rejoindre HQ »). Personne n'entre sans cette confirmation.

Quand on ne connaît pas l'adresse de quelqu'un : sur sa fiche, **« Envoyer un lien d'invitation »**.
On lui envoie le lien (WhatsApp) ; il se connecte avec Google et son adresse se range toute seule.
Valable 7 jours, une seule fois, et seul un responsable peut en créer.

Filet de sécurité si on oublie : la variable `HQ_BOOTSTRAP_EMAILS` (par exemple
`mon.adresse@gmail.com=mohamed`) laisse entrer cette adresse-là le temps de remplir les fiches. À retirer ensuite.

## 2. Où l'héberger
**Railway** (projet créé le 14/11, GitHub de Mohamed connecté). Le VPS reste possible plus tard ;
le `docker-compose.yml` à la racine sert dans ce cas.

### Ce qui reste à faire (Kevin)
0. **La connexion par e-mail** — c'est elle qui fait entrer l'équipe, car le courrier de `nyuman.app`
   est chez **Netim**, pas chez Google : les adresses @nyuman.app ne sont donc pas des comptes Google.
   Créer (ou réutiliser) une boîte `hq@nyuman.app` chez Netim, puis poser sur le service `hq` dans Railway :
   `HQ_SMTP_HOST=smtp.netim.net`, `HQ_SMTP_PORT=587`, `HQ_SMTP_USER=hq@nyuman.app`,
   `HQ_SMTP_PASSWORD=…` (le mot de passe de la boîte, posé par Kevin seul),
   `HQ_MAIL_FROM=Nyuman HQ <hq@nyuman.app>`.
   Penser aussi à autoriser Railway dans le SPF de `nyuman.app`, sinon les messages partiront en indésirables.
1. **La connexion Google** — en plus, pour ceux qui n'ont pas encore leur adresse pro. Dans un projet Google Cloud, un
   identifiant OAuth « Application Web » :
   - Origine autorisée : `https://teams.nyuman.app`
   - Adresse de retour : `https://teams.nyuman.app/api/auth/google/callback`
   Puis, sur le service `hq` dans Railway, poser `HQ_GOOGLE_CLIENT_ID` et `HQ_GOOGLE_CLIENT_SECRET`.

2. **L'accès de Railway au dépôt** : le dépôt est privé et Railway n'arrive pas encore à le lire, donc
   les mises à jour ne partent pas toutes seules. Installer l'app GitHub de Railway sur
   `mohfofana/nyuman-hq`. En attendant, on déploie à la main : `railway up --service hq`.
3. ~~L'adresse~~ : fait le 14/11 — `teams.nyuman.app` pointe sur le service, `HQ_PUBLIC_URL` suit.
4. **Une sauvegarde par semaine** de la base (demandée par Koffi au vote).

### Ce qui est déjà réglé
- `HQ_DEV_LOGIN=false` : la connexion sans mot de passe est coupée (vérifié : elle répond 404).
- `HQ_COOKIE_SECURE=true`, `HQ_AGENT_WAKE=false`, `HQ_UPLOAD_DIR=/data/uploads`, `DATABASE_URL` reliée.
- La clé qui signe les sessions est fabriquée par HQ lui-même au premier démarrage : aucun humain ne la manipule.
- La liste de l'équipe n'est pas lisible sans être connecté.

### Si un jour on repasse sur le VPS
1. **Le dépôt GitHub** : Railway déploie depuis GitHub, donc le code doit y être.
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
