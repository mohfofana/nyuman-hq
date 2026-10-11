# Mettre Nyuman HQ en ligne (privé, pour l'équipe seulement)

HQ s'installe sur le serveur de Nyuman, à côté de nyuman-api, de la même façon : Docker, Nginx devant, Cloudflare pour le HTTPS.
Il a **sa propre base** (rien n'est écrit dans celle de l'app) et n'est joignable que par une adresse, par exemple `hq.nyuman.com`.

## Ce qui rend HQ privé
- **Personne n'entre sans y avoir été invité** : seules les adresses ajoutées par un head dans Réglages peuvent se connecter.
  Pas d'inscription, pas de mot de passe : on reçoit un lien par email, valable 15 minutes, utilisable une seule fois.
- Toutes les données passent par des routes qui exigent une session. La page d'accueil seule est publique, et elle ne contient rien.
- Invisible des moteurs de recherche (`robots.txt`, en-tête `noindex`), impossible à afficher dans un autre site, HTTPS obligatoire.
- La base de HQ n'a aucun port ouvert ; HQ n'écoute que sur le serveur lui-même (`127.0.0.1:8002`), derrière Nginx.
- La connexion de développement est refusée en production : HQ ne démarre pas si elle est activée.

## Avant de commencer (l'équipe)
1. **Le code sur GitHub**, dans le dépôt privé `mohfofana/nyuman-hq` (Kevin y est invité pour le cloner sur le serveur).
2. **L'adresse** : dans Cloudflare, un enregistrement `A` `hq` vers l'IP du serveur, proxy activé (nuage orange),
   même réglage SSL que `api.nyuman.com`.
3. **La boîte d'envoi des liens** chez Netim (ex. `hq@nyuman.app`), et ses réglages SMTP (serveur, port 465, utilisateur, mot de passe).
4. **Un accès SSH** au serveur (compte `deploy`).

## Installation (une fois, sur le serveur)
```bash
cd /home/deploy/app
git clone https://github.com/mohfofana/nyuman-hq.git
cd nyuman-hq/deploy

# Réglages : copier le modèle puis le remplir (mots de passe générés sur place, jamais envoyés par message)
cp env.production.example .env
openssl rand -hex 32   # → HQ_POSTGRES_PASSWORD
openssl rand -hex 32   # → HQ_SESSION_SECRET
nano .env              # + SMTP_*, HQ_PUBLIC_URL, HQ_ORIGINES

# Le port 8002 doit être libre (8000 et 8001 : nyuman-api)
sudo ss -ltnp | grep 8002 || echo "8002 libre"

# Construire et démarrer HQ et sa base
docker compose -f docker-compose.prod.yml up -d --build
docker logs -f nyuman-hq          # attendre « Application startup complete »
curl -s http://127.0.0.1:8002/api/sante   # → {"ok":true}
```

### Nginx
```bash
sudo cp /home/deploy/app/nyuman-hq/deploy/nginx-hq.conf /etc/nginx/sites-available/nyuman-hq
sudo nano /etc/nginx/sites-available/nyuman-hq   # vérifier server_name (hq.nyuman.com)
sudo ln -s /etc/nginx/sites-available/nyuman-hq /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Sauvegardes chaque nuit
```bash
chmod +x /home/deploy/app/nyuman-hq/deploy/sauvegarde.sh
crontab -e
# ajouter :
0 3 * * * /home/deploy/app/nyuman-hq/deploy/sauvegarde.sh >> /home/deploy/backups/hq.log 2>&1
```

## Premier passage (le fondateur)
1. Ouvrir `https://hq.nyuman.com`, taper `mohamed.fofana@nyuman.app`, cliquer le lien reçu.
2. **Réglages → Faire entrer quelqu'un** : Sullyvan (head, COO, Opérations), Kevin (head, CTO, Produit),
   Abraham (head, CGO, Croissance), Carmel (membre, CFO, Opérations). Chacun se connecte ensuite avec son adresse.
3. **Réglages → Reprendre le tableau Google** : le tableau téléchargé en .xlsx. Aperçu, puis confirmation.
4. Passer le partage du tableau Google en « Limité » : HQ le remplace.

## Mettre à jour HQ
```bash
cd /home/deploy/app/nyuman-hq && git pull
cd deploy && docker compose -f docker-compose.prod.yml up -d --build hq
```
Les migrations de la base tournent toutes seules au démarrage. Les écrans ouverts se reconnectent seuls.

## Plus tard : les chiffres de l'app (lecture seule)
Créer le compte `hq_lecture` (staging d'abord) : [lecture-base-nyuman.md](lecture-base-nyuman.md), puis renseigner
`NYUMAN_DB_LECTURE_URL` dans `deploy/.env`. Le plus propre : relier le conteneur `nyuman-hq` au réseau Docker de nyuman-api
(`docker network ls`, puis un réseau `external` dans le compose) et viser le conteneur Postgres par son nom, plutôt qu'un port publié.

## À vérifier au passage sur le serveur (nyuman-api)
Les compositions de nyuman-api publient Postgres (5432), Redis (6379, sans mot de passe) et MinIO (9000/9001) sur toutes les
interfaces. Docker contourne ufw : si le pare-feu Hetzner ne les bloque pas, ils sont joignables depuis Internet.
Vérifier avec `sudo ss -ltnp` et le pare-feu Hetzner, puis les limiter à `127.0.0.1` (tâche proposée à part).
