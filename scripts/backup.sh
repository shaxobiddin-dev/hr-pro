#!/bin/bash
# HR-Pro Database Backup Script
# Usage: ./scripts/backup.sh [daily|weekly|manual]

set -e

BACKUP_TYPE=${1:-manual}
BACKUP_DIR="./docker/postgres/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="hrpro_${BACKUP_TYPE}_${DATE}.sql.gz"

# Load environment variables
if [ -f ".env.prod" ]; then
    source .env.prod
elif [ -f ".env" ]; then
    source .env
fi

DB_NAME=${DB_NAME:-hrpro}
DB_USER=${DB_USER:-hrpro}

echo "========================================"
echo "HR-Pro Database Backup"
echo "========================================"
echo "Type: $BACKUP_TYPE"
echo "Date: $DATE"
echo "Database: $DB_NAME"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Create backup
echo "Creating backup..."
docker-compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U $DB_USER -d $DB_NAME | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

# Check backup size
BACKUP_SIZE=$(ls -lh "${BACKUP_DIR}/${BACKUP_FILE}" | awk '{print $5}')
echo "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Remove old backups (keep last 7 daily, 4 weekly)
echo "Cleaning old backups..."

# Keep last 7 daily backups
ls -t ${BACKUP_DIR}/hrpro_daily_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

# Keep last 4 weekly backups
ls -t ${BACKUP_DIR}/hrpro_weekly_*.sql.gz 2>/dev/null | tail -n +5 | xargs -r rm -f

# Keep last 30 manual backups
ls -t ${BACKUP_DIR}/hrpro_manual_*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm -f

# List remaining backups
echo ""
echo "Current backups:"
ls -lh ${BACKUP_DIR}/*.sql.gz 2>/dev/null || echo "No backups found"

echo ""
echo "========================================"
echo "Backup completed successfully!"
echo "========================================"
