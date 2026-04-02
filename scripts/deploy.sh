#!/bin/bash

# ══════════════════════════════════════════════════════════════
# Pavlov MVP Deployment Script
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
if [[ ! -f "docker-compose.yml" || ! -f ".env.example" ]]; then
    log_error "This script must be run from the pavlov project root directory"
    exit 1
fi

log_info "Starting Pavlov MVP Deployment..."

# ── Pre-deployment Checks ────────────────────────────────────

log_info "Running pre-deployment checks..."

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    log_error ".env file not found. Please create .env from .env.example:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your production values"
    exit 1
fi

# Source .env file
source .env

# Check critical environment variables
if [[ -z "${ENCRYPTION_KEY:-}" ]]; then
    log_error "ENCRYPTION_KEY is not set in .env file"
    log_info "Generate with: python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    exit 1
fi

if [[ -z "${SECRET_KEY:-}" ]]; then
    log_error "SECRET_KEY is not set in .env file"
    log_info "Generate with: python3 -c 'import secrets; print(secrets.token_hex(32))'"
    exit 1
fi

if [[ -z "${POSTGRES_PASSWORD:-}" || "${POSTGRES_PASSWORD}" == "changeme_use_strong_password" ]]; then
    log_error "POSTGRES_PASSWORD must be changed from default value"
    exit 1
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" || "${ANTHROPIC_API_KEY}" == "your_anthropic_api_key_here" ]]; then
    log_warning "ANTHROPIC_API_KEY not set - AI features will not work"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check if ports are available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "Port 8000 is already in use"
    exit 1
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "Port 3000 is already in use"
    exit 1
fi

log_success "Pre-deployment checks passed"

# ── Create backup directory ──────────────────────────────────
mkdir -p backups

# ── Stop existing containers ─────────────────────────────────
log_info "Stopping existing containers..."
docker-compose down --remove-orphans || true

# ── Build and start services ─────────────────────────────────
log_info "Building and starting services..."
log_info "This may take several minutes on first run..."

# Build images
docker-compose build --no-cache

# Start services
docker-compose up -d

log_info "Waiting for services to start..."

# ── Health checks ────────────────────────────────────────────
log_info "Running health checks..."

# Wait for postgres to be ready
log_info "Waiting for database..."
timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}; do sleep 2; done' || {
    log_error "Database failed to start within 60 seconds"
    docker-compose logs postgres
    exit 1
}

# Wait for backend to be ready
log_info "Waiting for backend API..."
timeout 120 bash -c 'until curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; do sleep 5; done' || {
    log_error "Backend API failed to start within 120 seconds"
    docker-compose logs backend
    exit 1
}

# Wait for frontend to be ready
log_info "Waiting for frontend..."
timeout 60 bash -c 'until curl -f http://localhost:3000/health >/dev/null 2>&1; do sleep 2; done' || {
    log_error "Frontend failed to start within 60 seconds"
    docker-compose logs frontend
    exit 1
}

log_success "All services are running!"

# ── Run health check script ──────────────────────────────────
log_info "Running comprehensive health checks..."
if [[ -f "scripts/health_check.sh" ]]; then
    bash scripts/health_check.sh
else
    log_warning "Health check script not found, skipping detailed checks"
fi

# ── Display deployment summary ───────────────────────────────
echo
log_success "🎉 Pavlov MVP Deployment Complete!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Application URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/api/v1/health"
echo
echo "  Optional Services:"
echo "  PgAdmin:   docker-compose --profile admin up -d"
echo "             http://localhost:5050"
echo "             (admin@pavlov.local / admin)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 Next Steps:"
echo "  • Run health checks: bash scripts/health_check.sh"
echo "  • Create database backup: bash scripts/backup.sh"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo
log_info "Deployment script completed successfully"