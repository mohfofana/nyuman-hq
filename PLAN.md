# Nyuman HQ : plan de construction (Kwame, 13/11/2026)

À lire avec `BRIEF.md`. Ce plan vise **une première version utilisable en local en environ une semaine**, en commençant par la messagerie et les réunions, comme Mohamed l'a demandé le 13/11.

## Technologie
- **Serveur** : Python + FastAPI (comme `nyuman-api`, pour que Kevin s'y retrouve), base **PostgreSQL**.
- **Temps réel** : WebSocket servi par le même serveur (messages, présence, « en train d'écrire », notifications). Aucun service payant en plus.
- **Interface** : React + Tailwind, web d'abord et utilisable sur téléphone (installable comme une app, notifications du navigateur).
- **Design** : les jetons de `nyuman-dashboard-ui` (blanc, orange #BC600D dosé, encre #211B16, Work Sans, pastilles). Pas de thème à part.
- **Fichiers et images** : sur le disque en local ; en ligne, un stockage compatible S3 (Cloudflare R2 : gratuit jusqu'à 10 Go).
- **Réunions** : lien Google Meet créé par l'API Google Calendar (compte Google de l'équipe) ; si Google n'est pas branché, lien Jitsi automatique.
- **Agents** : membres comme les autres (profil, statut, mentions). En v1 ils écrivent dans HQ par une petite porte d'entrée (un jeton par agent, créé par Mohamed ou Kevin). Pas d'IA qui tourne en boucle.
- **Secrets** : jamais lus par Kwame. Un `.env.example` liste ce qu'il faut ; Mohamed ou Kevin remplissent `.env`.

## Étapes (une étape = un commit, testée dans le navigateur, captures à Mohamed)
1. Socle : serveur, base, connexion (en local : choisir son profil ; en ligne : Google), squelette des écrans.
2. Messagerie : canaux, messages privés, fils, mentions @, réactions, fichiers et images.
3. Messagerie (suite) : présence (en ligne / occupé / absent), notifications, non-lus, recherche.
4. Réunions : planifier, inviter, lien Meet ou Jitsi, rappel avant, compte rendu rattaché (et posté dans le canal).
5. Équipe, tâches, décisions : bureaux (humains + agents), tableau des tâches, salle du conseil, file de validation.
6. Salon et bibliothèque : objectif du trimestre + chiffres de l'app (route en lecture seule demandée à Kodjo), documents avec historique.
7. Finitions téléphone, tests, captures.

## Ce qui coûte de l'argent
| Poste | Local | En ligne (estimation) |
|---|---|---|
| Hébergement serveur + base | 0 | Railway ≈ 10 à 15 $/mois |
| Temps réel | 0 | inclus dans l'hébergement |
| Fichiers | 0 | 0 jusqu'à 10 Go (R2) |
| Google Meet / Calendar | 0 | 0 (projet Google Cloud gratuit) |
| Jitsi | 0 | 0 |
| IA dans HQ | 0 | 0 en v1 (les agents restent les discussions Claude actuelles) |

## Questions ouvertes (posées à Mohamed le 13/11)
Voir le message de Kwame du 13/11 : hébergement, liste des heads, compte Google des réunions, budget IA, connecteurs Notion / HubSpot / Asana.
