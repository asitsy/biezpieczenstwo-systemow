#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: bash restore.sh /mnt/d/Projects/secure-cloud-drive/backups/<backup_file.sql.gz>"
  exit 1
fi

echo "Restoring from: $1"

gunzip -c "$1" | docker exec -i securedrive-db \
  psql -U postgres securedrive

echo "Restore complete!"