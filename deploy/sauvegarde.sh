#!/usr/bin/env bash
# Sauvegarde de la base de HQ et des captures, à lancer chaque nuit (cron), comme pour nyuman-api :
#   0 3 * * * /home/deploy/app/nyuman-hq/deploy/sauvegarde.sh >> /home/deploy/backups/hq.log 2>&1
# Garde 14 jours de sauvegardes.
set -euo pipefail

DEST="${HQ_BACKUP_DIR:-/home/deploy/backups/hq}/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEST"

docker exec nyuman-hq-postgres pg_dump -U hq -d hq --format=custom > "$DEST/hq.dump"
docker run --rm -v nyuman_hq_uploads:/data:ro -v "$DEST":/backup alpine tar czf /backup/uploads.tgz -C /data .

echo "Sauvegarde faite : $DEST ($(du -sh "$DEST" | cut -f1))"
find "$(dirname "$DEST")" -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +
