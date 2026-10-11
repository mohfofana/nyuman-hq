# Nyuman HQ : le dossier de départ

Ce document explique tout ce qu'on veut construire. À lire en entier avant d'écrire la moindre ligne de code.

## 1. Qui on est
- **Nyuman** : app de réservation beauté en Côte d'Ivoire (Abidjan), pour coiffeuses, tresseuses, barbiers et ongles. La cliente réserve et paie un acompte dans l'app. Le pro reçoit l'acompte après la prestation.
- **Phase actuelle** : TestFlight, avant le lancement public.
- **L'équipe connue** : le fondateur, **Kevin** (CTO), **Chris-Sullyvan Koffi** (directeur opérationnel et administratif : juridique et opérations). La liste complète des heads reste à demander.
- **Code existant** :
  - app Flutter : `nyuman-app` (branche `fix/pro-design-system-colors`) ;
  - API FastAPI : `nyuman-api` (branche `agentMohamed`, poussée sur `development` = staging).
- **Langue** : on parle et on répond **en français**, avec des mots simples.

## 2. La vision
Un **QG virtuel** : une maison où toute l'équipe, humains et agents, travaille ensemble sur Nyuman, et où chacun **voit les autres travailler en temps réel**. Ça remplace aussi Notion : on y centralise documents, projets, décisions et chiffres.

**Principe fondateur : les agents sont des membres de l'équipe à part entière, autant que les humains.**
- Chaque agent a un **nom**, un **rôle**, un **avatar**, une **pièce** (son bureau), un **statut** (en train de travailler, en attente, bloqué), des **tâches**, un **historique**.
- On peut lui **assigner une tâche**, le **mentionner**, lui **parler**, le **contredire**. Il peut faire tout ça aussi avec les humains.
- Il **propose** des idées, **prend des initiatives** dans son périmètre, **dit non** quand une idée est mauvaise, **contredit** les heads et les autres agents, chiffres à l'appui.
- Dans l'interface, il apparaît **au même niveau qu'un humain** : fil d'activité, tableau des tâches, réunions, votes du conseil.
- **Une limite non négociable** : à l'intérieur, ce sont des collègues. **Vers l'extérieur** (prospects, clientes, partenaires), un agent ne se fait jamais passer pour un humain.

**Objectif de chaque trimestre** : atteindre un objectif chiffré commun. Tout le monde, humain ou agent, travaille vers lui.

## 3. Les pièces de la maison (écrans)
1. **Le salon (accueil)** : l'objectif du trimestre avec sa jauge en temps réel ; les KPI en direct tirés de l'app Nyuman (utilisateurs inscrits, pros actifs, réservations, acomptes, revenu Nyuman) ; le **fil d'activité de la maison**.
2. **Les bureaux** : une pièce par personne et par agent. On voit ce qu'il fait en ce moment, ses tâches, ses productions. Pour un agent, on le voit travailler en direct (son journal d'actions), et on peut l'interrompre, le corriger ou lui confier autre chose.
3. **La bibliothèque** : tous les documents, façon Notion (contrats, finances, comptes rendus, specs, pitch). Les agents les lisent et les mettent à jour. On voit qui a modifié quoi.
4. **La salle de projet** : tableau des tâches, humains et agents mélangés, chacune rattachée à l'objectif du trimestre.
5. **La salle du conseil** : les propositions (chiffres, risques, avis du Contradicteur, votes des heads), le **journal des décisions** (revu à 30 jours : qui avait raison ?), et la **file de validation** (tout ce qu'un agent veut faire à l'extérieur attend ici un « oui » humain).

## 4. Le cerveau commun
- Un document **« Objectifs Nyuman »** que chaque agent lit avant d'agir :
  - 300 pros actifs à 1 an, 3 000 à 3 ans, 15 000 à 5 ans (plusieurs pays) ;
  - rentable à environ 580 pros actifs, avec la grille « 2 % du prix, minimum 100 FCFA » ;
  - les priorités du trimestre ;
  - ce qu'on ne fait pas (v1 sans avis ni messagerie publics ; file d'attente pour les barbiers seulement dans la mise à jour qui suit la v1).
- Une **mémoire partagée** : décisions, contrats, chiffres, comptes rendus.
- Chaque proposition d'agent dit **quel objectif elle sert, avec quel chiffre**, **pourquoi elle pourrait échouer**, et **ce qu'il ferait à la place**.
- Référence chiffrée : la page « Finances Nyuman » (https://claude.ai/artifact/WMETTf5eJfCbWhW72qRrXS). Le contexte des paiements : « Négo FeexPay » (https://claude.ai/artifact/Jj7WLavaHSQc27GMVGgNcK).

## 5. Les agents (premiers membres)
| Agent | Pour qui | Fait seul | Propose (à valider) |
|---|---|---|---|
| Chef de cabinet | Direction | Point du lundi, rassemble les propositions, repère les conflits | L'ordre du jour de la réunion hebdo |
| Contradicteur | Tous | Relit chaque proposition importante, dit non avec chiffres et alternative | Peut bloquer jusqu'à ce qu'un humain tranche |
| Croissance et prospection | Commercial et opérations | Trouve et qualifie salons et barbiers (sources publiques, recommandations), tient le CRM, prépare les messages, suit les relances | Les envois (un humain envoie depuis le compte officiel) |
| Contenu et vidéo | Marketing | Scripts, montages à partir des vraies vidéos des pros (avec accord), calendrier | Chaque publication, chaque dépense de pub |
| Finance | Direction | Trésorerie, modèle financier, contrôle des paiements | Changements de prix ou de frais |
| Juridique et partenariats | Sullyvan | Contrats, risques, amendements, conformité BCEAO et données | Positions de négo, envois de contrats |
| Produit et tech | Kevin | Tri des retours et bugs, specs, QA, relecture de code | Les mises en ligne |
| Investisseurs | Direction | Rapport mensuel, data room, pitch | Chaque envoi |
| Idées et veille | Chaque head | 3 idées chiffrées par head et par semaine, veille concurrents et règles | Les idées retenues deviennent des tâches |

On démarre avec **Chef de cabinet, Contradicteur et Prospection**, puis on ajoute les autres un par un.

## 6. Les niveaux de liberté
- **Seul** : chercher, analyser, rédiger, créer des tâches, mettre à jour le CRM, poster en interne.
- **Avec un « oui » d'un head** : tout envoi à l'extérieur, publication, dépense, changement de prix, contrat, mise en ligne.
- **Délégué dans un cadre précis** (une fois les preuves faites) : par exemple publier seul un calendrier déjà validé, avec un budget plafonné.
- **Jamais** : payer, signer, se faire passer pour un humain à l'extérieur, inventer des clientes ou des avis, utiliser des données personnelles hors cadre, contourner les règles d'une plateforme (pas de messages privés automatiques en masse sur Instagram ou TikTok).

## 7. Le rythme
- Lundi : chaque agent publie son rapport et 3 propositions.
- Mardi : le Contradicteur passe.
- Mercredi : réunion de 30 minutes, les heads décident.
- Jeudi et vendredi : exécution.
- Vendredi : bilan.
- Chaque trimestre : 1 à 3 objectifs chiffrés, un plan des agents, puis un bilan.

## 8. Les coûts (règles obligatoires)
- **La plupart des écrans n'utilisent pas l'IA** : tableaux de bord, documents, tâches, fil d'activité et file de validation sont du logiciel classique. Voir un agent travailler, c'est afficher son journal d'actions.
- Les agents se réveillent **sur événement** ou **à heure fixe**, jamais en boucle.
- **Le bon modèle par tâche**, via une couche d'aiguillage :
  - open source (Llama, Mistral, Qwen…) pour trier, classer, extraire, résumer court ;
  - embeddings open source pour la recherche dans les documents ;
  - Whisper pour la voix ;
  - Claude Haiku ou Sonnet pour la plupart des agents ;
  - Claude Opus seulement pour les grosses décisions, les contrats et le Contradicteur.
- **Cache** du contexte commun, **traitement groupé** (Batch) pour le non urgent, **mémoire résumée** plutôt que l'historique complet, **chiffres déjà calculés** par le serveur.
- **Budget par agent et par mois** : alerte à 80 %, arrêt à 100 %. Un **compteur visible** dans HQ : ce que coûte chaque agent et ce qu'il rapporte.
- Ordre de grandeur estimé : 35 à 65 $ par mois d'IA pour 4 agents au début, 150 à 400 $ avec 8 à 10 agents. À mesurer pour de vrai.

## 9. Technique proposée
- Nouveau projet `nyuman-hq` (ce dossier).
- Serveur : Python + FastAPI, même organisation que `nyuman-api` (architecture propre, use cases, tests).
- Interface : application web React, avec les couleurs Nyuman (orange principal #BC600D, dosé) et la police Work Sans.
- Agents : kit de développement d'agents de Claude (Agent SDK), outils branchés par MCP (à confirmer).
- Temps réel : WebSocket ou équivalent, pour le fil d'activité et les bureaux.
- Connexion : comptes Google de l'équipe, avec des rôles (head, membre).
- KPI : une route « statistiques » **en lecture seule**, avec des totaux seulement et aucune donnée personnelle, à ajouter à `nyuman-api`.

## 10. Plan de la première version (environ 4 semaines)
0. **D'abord une maquette visuelle** (salon, bureau d'un agent, salle du conseil) à faire valider par l'équipe.
1. Semaine 1 : connexion, salon (objectif + KPI en direct), bibliothèque.
2. Semaine 2 : salle de projet (tâches humains + agents) et fil d'activité.
3. Semaine 3 : Chef de cabinet et Contradicteur, avec budget et compteur.
4. Semaine 4 : salle du conseil (file de validation, journal des décisions) et agent Prospection.

## 11. Règles de travail avec le fondateur
- Répondre en français, simplement.
- Demander avant toute action vers l'extérieur : push, mise en ligne, envoi, publication. Un accord ne vaut que pour l'action concernée.
- **Ne jamais manipuler de secrets.** Les clés API (Anthropic, outils) et mots de passe sont entrés par l'équipe elle-même dans les réglages.
- Ne pas supprimer définitivement de fichiers : les mettre à la corbeille.
- Questions de départ et réponses (10 octobre 2026) :
  - Où héberger HQ ? → Railway, compte Nyuman.
  - Qui sont les heads, et quels sont leurs outils ? → à compléter.
  - Les connecteurs Notion, HubSpot et Asana disponibles sont-ils bien ceux de Nyuman ? → Non. HQ fait tout au début.
  - Quel budget IA mensuel au départ ? → 45 $.
