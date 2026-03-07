#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${1:-/backups}"
RETENTION_DAYS="${2:-7}"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_FILE="${BACKUP_DIR}/laias_backup_${TIMESTAMP}.sql"

if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
  printf 'Error: POSTGRES_PASSWORD environment variable is required.\n' >&2
  exit 1
fi

if ! [[ "${RETENTION_DAYS}" =~ ^[0-9]+$ ]]; then
  printf 'Error: retention days must be a non-negative integer.\n' >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" laias-postgres \
  pg_dump -U laias laias > "${BACKUP_FILE}"

find "${BACKUP_DIR}" -type f -name 'laias_backup_*.sql' -mtime +"${RETENTION_DAYS}" -delete

printf 'Backup created: %s\n' "${BACKUP_FILE}"
