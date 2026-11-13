# Message à envoyer à Kevin (préparé par Kwame, 13/11)

Salut Kevin,

On construit Nyuman HQ, le QG interne de l'équipe (messagerie, réunions, projets), pour remplacer Teams. La messagerie tourne déjà en local sur le Mac. Pour la mettre vraiment en ligne, j'ai besoin de toi pour 3 choses (environ 1 h en tout) :

1. **Connexion Google** : créer un projet Google Cloud (gratuit) avec un identifiant OAuth « Application Web ».
   - Origine autorisée : l'adresse finale de HQ (par exemple `https://hq.nyuman.app`).
   - Adresse de retour : `https://hq.nyuman.app/api/auth/google/callback`.
   - Activer aussi l'API Google Calendar : elle servira à créer les liens Meet des réunions.
   - Mettre toi-même `HQ_GOOGLE_CLIENT_ID` et `HQ_GOOGLE_CLIENT_SECRET` dans les variables de l'hébergeur (jamais dans le code ni dans un message).

2. **Hébergement** : un projet Railway (comme le back-office) avec :
   - un service pour le serveur (`server/`, Python, FastAPI) ;
   - une base PostgreSQL ;
   - le site (`web/`, React, compilé en fichiers statiques).
   - Coût estimé : 10 à 15 $ par mois. Mohamed doit valider la dépense.
   - Variables (voir `server/.env.example`) : `HQ_DATABASE_URL`, `HQ_SESSION_SECRET` (longue phrase aléatoire), `HQ_DEV_LOGIN=false`, `HQ_CORS_ORIGINS`.

3. **Adresse** : un sous-domaine `hq.nyuman.app` qui pointe vers Railway.

Le code est dans le dépôt local `~/Documents/nyuman-hq`, qui n'a pas encore de dépôt GitHub. Dis-moi où tu veux qu'il vive (organisation GitHub de Nyuman ?) et je le prépare.

De mon côté, je branche la connexion Google dans HQ et je coupe la connexion sans mot de passe dès que tu me dis que c'est prêt.

Merci !
