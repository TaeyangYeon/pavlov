#!/bin/bash

# ══════════════════════════════════════════════════════════════
# Pavlov Database Backup Script
# ══════════════════════════════════════════════════════════════

set -euo pipefail  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from project root
if [[ ! -f "docker-compose.yml" ]]; then
    log_error "This script must be run from the pavlov project root directory"
    exit 1
fi

# Load environment variables
if [[ ! -f ".env" ]]; then
    log_error ".env file not found"
    exit 1
fi

source .env

# Check if postgres container is running
if ! docker-compose ps postgres | grep -q "Up"; then
    log_error "PostgreSQL container is not running. Please start it first:"
    echo "  docker-compose up -d postgres"
    exit 1
fi

# Create backup directory
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/pavlov_backup_${TIMESTAMP}.sql"

log_info "Creating database backup..."
log_info "Database: ${POSTGRES_DB}"
log_info "Backup file: ${BACKUP_FILE}"

# Create database dump
if docker-compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    > "$BACKUP_FILE"; then
    
    log_success "Database backup created successfully"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup size: ${BACKUP_SIZE}"
    
    # Compress backup
    log_info "Compressing backup..."
    if gzip "$BACKUP_FILE"; then
        COMPRESSED_FILE="${BACKUP_FILE}.gz"
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        log_success "Backup compressed to: ${COMPRESSED_FILE}"
        log_info "Compressed size: ${COMPRESSED_SIZE}"
        BACKUP_FILE="$COMPRESSED_FILE"
    else
        log_warning "Failed to compress backup, keeping uncompressed version"
    fi
else
    log_error "Failed to create database backup"
    exit 1
fi

# ── Cleanup old backups ──────────────────────────────────────
log_info "Cleaning up old backups (keeping last 7)..."

# Count existing backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "pavlov_backup_*.sql*" | wc -l)
log_info "Current backup count: ${BACKUP_COUNT}"

if [[ $BACKUP_COUNT -gt 7 ]]; then
    # Remove oldest backups, keeping only the 7 most recent
    find "$BACKUP_DIR" -name "pavlov_backup_*.sql*" -type f -printf '%T+ %p\n' | \
        sort | \
        head -n -7 | \
        cut -d' ' -f2- | \
        while read -r old_backup; do
            log_info "Removing old backup: $(basename "$old_backup")"
            rm -f "$old_backup"
        done
    log_success "Old backups cleaned up"
else
    log_info "No old backups to clean up"
fi

# ── Backup verification ──────────────────────────────────────
log_info "Verifying backup integrity..."

# Test if the backup file exists and is not empty
if [[ -f "$BACKUP_FILE" && -s "$BACKUP_FILE" ]]; then
    # If compressed, test the compression
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        if gzip -t "$BACKUP_FILE"; then
            log_success "Backup file integrity verified (compressed)"
        else
            log_error "Backup file is corrupted (compression test failed)"
            exit 1
        fi
    else
        log_success "Backup file integrity verified"
    fi
else
    log_error "Backup file is empty or does not exist"
    exit 1
fi

# ── Display backup summary ───────────────────────────────────
echo
log_success "🗄️  Database Backup Complete!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Backup Details:"
echo "  File:      $(basename "$BACKUP_FILE")"
echo "  Location:  $BACKUP_FILE"
echo "  Size:      $(du -h "$BACKUP_FILE" | cut -f1)"
echo "  Database:  ${POSTGRES_DB}"
echo "  Created:   $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 Restore Instructions:"
echo "  # Stop the application"
echo "  docker-compose down"
echo "  "
echo "  # Start only PostgreSQL"
echo "  docker-compose up -d postgres"
echo "  "
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "  # Restore from compressed backup"
    echo "  gunzip -c \"$BACKUP_FILE\" | docker-compose exec -T postgres psql -U \${POSTGRES_USER} -d postgres"
else
    echo "  # Restore from backup"
    echo "  docker-compose exec -T postgres psql -U \${POSTGRES_USER} -d postgres < \"$BACKUP_FILE\""
fi
echo "  "
echo "  # Restart the application"
echo "  docker-compose up -d"
echo

# List all available backups
echo "📋 Available Backups:"
find "$BACKUP_DIR" -name "pavlov_backup_*.sql*" -type f -printf '%T+ %p\n' | \
    sort -r | \
    while read -r timestamp filepath; do
        filename=$(basename "$filepath")
        size=$(du -h "$filepath" | cut -f1)
        echo "  $filename ($size)"
    done

echo
log_info "Backup script completed successfully"