# Nyuman HQ : plan de construction (Kwame, 13/11/2026, revu le même jour)

À lire avec `BRIEF.md`. Mohamed veut l'équivalent de **Microsoft Teams Business + le suivi de projet de Notion, relié à Claude** (précision transmise par Kodjo le 13/11). Objectif : **une première version utilisable en local**, en commençant par la messagerie et les réunions.

## Ce que HQ contiendra
1. **Messagerie** : canaux, messages privés, fils, mentions @, réactions, fichiers et images, présence (en ligne / occupé / absent), notifications, non-lus, recherche.
2. **Réunions** : planifier, inviter, lien Google Meet (API Google Calendar) ou Jitsi en secours, rappel avant, compte rendu rattaché.
3. **Agenda partagé** : réunions, échéances des tâches, rappels ; synchronisé avec Google Agenda.
4. **Fichiers** : par canal et par projet, aperçu (images, PDF), versions, qui a modifié quoi.
5. **Suivi de projet façon Notion** : pages riches (titres, listes, cases à cocher, tableaux, images), bases de données avec vues **tableau / Kanban / calendrier**, tâches (responsable, échéance, statut) liées aux projets et aux décisions.
6. **Salon** : objectif du trimestre + chiffres de l'app en lecture seule (totaux, sans données personnelles ; route demandée à Kodjo).
7. **Décisions et équipe** : salle du conseil, file de validation, bureaux des humains et des agents.
8. **Branché sur Claude** : un **serveur MCP propre à HQ**, pour que les agents (Kodjo, Adjoua, Koffi, Mariam, Kwame…) lisent et écrivent dans HQ (messages, tâches, documents, décisions) comme aujourd'hui avec Notion. Chaque agent a son jeton et apparaît comme membre.
9. **Pas d'e-mail** : on garde Gmail.

## Présence automatique, comme Teams (demandé par Mohamed le 13/11)
Une pastille sur la photo de chacun, qui change toute seule :
- 🟢 **Disponible** : la personne a HQ ouvert et s'en sert.
- 🟡 **Absent** : HQ ouvert mais rien touché depuis 10 minutes, ou HQ fermé depuis peu (avec « vu il y a 20 min »).
- 🔴 **En réunion** : automatiquement pendant une réunion de l'agenda HQ (de l'heure de début à la fin, ou dès qu'on clique sur le lien).
- ⚪ **Hors ligne** : plus aucune page HQ ouverte.
- On peut choisir à la main **Occupé** ou **Ne pas déranger** (les notifications se taisent), avec un petit message (« En rendez-vous salon jusqu'à 15 h »).
- Les agents ont la même pastille : 🟢 au travail, 🟡 en attente, 🔴 bloqué.
Fonctionne sur ordinateur et sur téléphone, sans service payant (la connexion en direct du serveur suffit). Prévu à l'étape 3, et relié aux réunions à l'étape 4.

## Technologie
- **Serveur** : Python + FastAPI (comme `nyuman-api`), base **PostgreSQL**.
- **Temps réel** : WebSocket servi par le même serveur. Aucun service payant en plus.
- **Interface** : React + Tailwind, web d'abord, utilisable sur téléphone (installable, notifications du navigateur).
- **Éditeur de pages** : un éditeur par blocs libre de droits (type BlockNote / Tiptap), stocké dans notre base.
- **Design** : jetons de `nyuman-dashboard-ui` (blanc, orange #BC600D dosé, encre #211B16, Work Sans, pastilles).
- **Fichiers** : disque en local ; en ligne, stockage compatible S3 (Cloudflare R2, gratuit jusqu'à 10 Go).
- **MCP** : petit serveur MCP en Python qui parle à l'API de HQ avec le jeton de l'agent.
- **Secrets** : jamais lus par Kwame. `.env.example` fourni ; Mohamed ou Kevin remplissent `.env`.

## Étapes (une étape = un commit, testée dans le navigateur, captures à Mohamed)
1. Socle : serveur, base, connexion (en local : choisir son profil ; en ligne : Google), squelette des écrans.
2. Messagerie : canaux, MP, fils, @, réactions, fichiers et images.
3. Messagerie (suite) : présence, notifications, non-lus, recherche.
4. Réunions + agenda : planifier, inviter, Meet ou Jitsi, rappel, compte rendu ; vue agenda.
5. **Serveur MCP** : les agents lisent et écrivent messages et tâches (tôt, pour qu'ils vivent dans HQ dès le début).
6. Projets façon Notion : pages, bases de données, vues tableau / Kanban / calendrier, tâches.
7. Fichiers par canal et par projet (aperçu, versions).
8. Salon, décisions, équipe.
9. Import Notion (si choisi), finitions téléphone, tests.

Estimation : messagerie + réunions utilisables en local en environ une semaine ; l'ensemble en 3 à 4 semaines.

## Ce qui coûte de l'argent
| Poste | Local | En ligne (estimation) |
|---|---|---|
| Hébergement serveur + base | 0 | Railway ≈ 10 à 20 $/mois |
| Temps réel | 0 | inclus |
| Fichiers | 0 | 0 jusqu'à 10 Go (R2), puis ≈ 0,015 $/Go/mois |
| Google Meet / Agenda | 0 | 0 (projet Google Cloud gratuit) |
| Jitsi | 0 | 0 |
| Serveur MCP | 0 | inclus dans l'hébergement |
| IA dans HQ | 0 | 0 en v1 (les agents restent les discussions Claude actuelles) |

À comparer : Teams Business ≈ 6 à 12 $ par personne et par mois, Notion Plus ≈ 10 $ par personne.

## Questions ouvertes (posées à Mohamed le 13/11)
Hébergement, liste des heads, compte Google des réunions, budget IA, Notion (import ou zéro), stockage des fichiers.
