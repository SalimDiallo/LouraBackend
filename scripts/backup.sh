#!/bin/bash
# ========================================
# Automated Backup Script
# ========================================
# Creates backups of database and media files

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Starting backup process...${NC}"

# Backup PostgreSQL database
echo -e "${YELLOW}📦 Backing up database...${NC}"
docker compose exec -T db pg_dump -U loura_user loura_db | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz" || {
    echo -e "${RED}❌ Database backup failed${NC}"
    exit 1
}
DB_SIZE=$(du -h "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz" | cut -f1)
echo -e "${GREEN}✅ Database backup completed ($DB_SIZE)${NC}"

# Backup media files
echo -e "${YELLOW}📸 Backing up media files...${NC}"
docker run --rm \
    -v backend_media_volume:/data \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf "/backup/media_backup_$TIMESTAMP.tar.gz" -C /data . 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Media backup skipped (no media files or volume not found)${NC}"
}

if [ -f "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" ]; then
    MEDIA_SIZE=$(du -h "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" | cut -f1)
    echo -e "${GREEN}✅ Media backup completed ($MEDIA_SIZE)${NC}"
fi

# Backup .env file
echo -e "${YELLOW}⚙️  Backing up configuration...${NC}"
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/env_backup_$TIMESTAMP.txt"
    echo -e "${GREEN}✅ Configuration backup completed${NC}"
fi

# Clean old backups
echo -e "${YELLOW}🧹 Cleaning old backups (older than $RETENTION_DAYS days)...${NC}"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "env_backup_*.txt" -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✅ Old backups cleaned${NC}"

# List backups
echo -e "\n${GREEN}📋 Current backups:${NC}"
ls -lh "$BACKUP_DIR" | tail -n +2

echo -e "\n${GREEN}✅ Backup process completed!${NC}"
echo -e "Backup location: $BACKUP_DIR"
