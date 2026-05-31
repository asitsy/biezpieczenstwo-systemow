#!/bin/bash

BACKUP_DIR="/mnt/d/Projects/secure-cloud-drive/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="securedrive_backup_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

echo "Starting backup: $FILENAME"

docker exec securedrive-db pg_dump \
  -U postgres securedrive | gzip > "$BACKUP_DIR/$FILENAME"

echo "Backup saved: $BACKUP_DIR/$FILENAME"

# Удалить бекапы старше 7 дней
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
echo "Old backups cleaned"
