#!/bin/bash
# HR-Pro Database Restore Script
# Usage: ./scripts/restore.sh <backup_file>

set -e

BACKUP_FILE=$1
BACKUP_DIR="./docker/postgres/backups"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh ${BACKUP_DIR}/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

# Check if backup file exists
if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}" ] && [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Determine full path
if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    FULL_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
else
    FULL_PATH="${BACKUP_FILE}"
fi

# Load environment variables
if [ -f ".env.prod" ]; then
    source .env.prod
elif [ -f ".env" ]; then
    source .env
fi

DB_NAME=${DB_NAME:-hrpro}
DB_USER=${DB_USER:-hrpro}

echo "========================================"
echo "HR-Pro Database Restore"
echo "========================================"
echo "Backup file: $FULL_PATH"
echo "Database: $DB_NAME"
echo ""
echo "WARNING: This will DROP and RECREATE the database!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Stop web containers to prevent connections
echo "Stopping web containers..."
docker-compose -f docker-compose.prod.yml stop web celery celery-beat

# Drop and recreate database
echo "Recreating database..."
docker-compose -f docker-compose.prod.yml exec -T db \
    psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker-compose -f docker-compose.prod.yml exec -T db \
    psql -U $DB_USER -d postgres -c "CREATE DATABASE ${DB_NAME};"

# Restore backup
echo "Restoring backup..."
gunzip -c "$FULL_PATH" | docker-compose -f docker-compose.prod.yml exec -T db \
    psql -U $DB_USER -d $DB_NAME

# Restart web containers
echo "Starting web containers..."
docker-compose -f docker-compose.prod.yml start web celery celery-beat

echo ""
echo "========================================"
echo "Restore completed successfully!"
echo "========================================"
