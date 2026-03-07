#!/usr/bin/env bash
set -euo pipefail

FORCE=false
BACKUP_FILE=""

for arg in "$@"; do
  if [[ "${arg}" == "--force" ]]; then
    FORCE=true
  elif [[ -z "${BACKUP_FILE}" ]]; then
    BACKUP_FILE="${arg}"
  else
    printf 'Usage: %s [--force] <backup-file>\n' "$0" >&2
    exit 1
  fi
done

if [[ -z "${BACKUP_FILE}" ]]; then
  printf 'Usage: %s [--force] <backup-file>\n' "$0" >&2
  exit 1
fi

if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
  printf 'Error: POSTGRES_PASSWORD environment variable is required.\n' >&2
  exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
  printf 'Error: backup file not found: %s\n' "${BACKUP_FILE}" >&2
  exit 1
fi

if [[ "${FORCE}" != true ]]; then
  printf 'Restore database from %s? This will overwrite existing data. [y/N]: ' "${BACKUP_FILE}"
  read -r confirmation
  if [[ "${confirmation}" != "y" && "${confirmation}" != "Y" ]]; then
    printf 'Restore cancelled.\n'
    exit 0
  fi
fi

docker exec -i -e PGPASSWORD="${POSTGRES_PASSWORD}" laias-postgres \
  psql -U laias laias < "${BACKUP_FILE}"

printf 'Restore completed from: %s\n' "${BACKUP_FILE}"
