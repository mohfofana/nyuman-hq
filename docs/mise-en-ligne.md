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
Dans HQ, **Équipe → fiche de chacun → « Adresse Google pour se connecter »** (réservé aux responsables).
Sans adresse, la personne ne pourra pas entrer. Une adresse Gmail convient ; on passera à @nyuman.app plus tard.
**À faire pendant que HQ tourne encore en local**, sinon plus personne ne peut se connecter.

## 2. Où l'héberger (décision de Mohamed)
- **Sur le VPS qui héberge déjà `nyuman-api`** : Docker y tourne déjà, Kevin connaît la machine. **Coût supplémentaire : ~0 €.** Recommandé.
- **Sur Railway**, comme le back-office : plus simple à surveiller, **10 à 15 $ par mois**.

## 3. Ce que Kevin fait (environ 1 h)
1. **Connexion Google** : un projet Google Cloud (gratuit), identifiant OAuth « Application Web ».
   - Origine autorisée : `https://hq.nyuman.app`
   - Adresse de retour : `https://hq.nyuman.app/api/auth/google/callback`
2. **Un fichier `.env`** à côté du `docker-compose.yml` (voir `server/.env.example`) :
   `HQ_PUBLIC_URL`, `HQ_SESSION_SECRET` (longue phrase au hasard), `HQ_GOOGLE_CLIENT_ID`,
   `HQ_GOOGLE_CLIENT_SECRET`, `HQ_DB_PASSWORD`.
   `HQ_DEV_LOGIN=false`, `HQ_COOKIE_SECURE=true` et `HQ_AGENT_WAKE=false` sont déjà posés dans le compose.
3. **Démarrer** : `docker compose up -d --build` (le serveur crée les tables tout seul).
4. **L'adresse** : `hq.nyuman.app` vers la machine, en HTTPS.
5. **Une sauvegarde par semaine** de la base (demandée par Koffi lors du vote) :
   `docker compose exec -T db pg_dump -U hq hq | gzip > hq-$(date +%F).sql.gz`

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
