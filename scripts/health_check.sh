#!/bin/bash

# ══════════════════════════════════════════════════════════════
# Pavlov Health Check Script
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
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

# Function to run a health check
run_check() {
    local name="$1"
    local command="$2"
    local expected_output="${3:-}"
    
    echo -n "  Testing $name... "
    
    if output=$(eval "$command" 2>&1); then
        if [[ -z "$expected_output" || "$output" == *"$expected_output"* ]]; then
            echo -e "${GREEN}✓${NC}"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} (unexpected output)"
            echo "    Expected: $expected_output"
            echo "    Got: $output"
            ((TESTS_WARNING++))
            return 1
        fi
    else
        echo -e "${RED}✗${NC}"
        echo "    Error: $output"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if running from project root
if [[ ! -f "docker-compose.yml" ]]; then
    log_error "This script must be run from the pavlov project root directory"
    exit 1
fi

echo
log_info "🏥 Running Pavlov Health Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Container Status Checks ──────────────────────────────────
log_info "Container Status:"
run_check "PostgreSQL container" "docker-compose ps postgres | grep -q 'Up'" 
run_check "Backend container" "docker-compose ps backend | grep -q 'Up'"
run_check "Frontend container" "docker-compose ps frontend | grep -q 'Up'"

# ── Network Connectivity Checks ──────────────────────────────
log_info "Network Connectivity:"
run_check "Frontend HTTP" "curl -f -s -o /dev/null -w '%{http_code}' http://localhost:3000" "200"
run_check "Frontend health endpoint" "curl -f -s http://localhost:3000/health" "healthy"
run_check "Backend HTTP" "curl -f -s -o /dev/null -w '%{http_code}' http://localhost:8000" "404"  # Expect 404 for root path
run_check "Backend health endpoint" "curl -f -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/health" "200"

# ── API Health Checks ────────────────────────────────────────
log_info "API Health Checks:"

# Basic health check
if curl -f -s http://localhost:8000/api/v1/health > /tmp/health_basic.json 2>&1; then
    if grep -q '"status":"healthy"' /tmp/health_basic.json; then
        log_success "Basic health check"
        ((TESTS_PASSED++))
    else
        log_error "Basic health check failed - status not healthy"
        cat /tmp/health_basic.json
        ((TESTS_FAILED++))
    fi
else
    log_error "Basic health check - endpoint unreachable"
    ((TESTS_FAILED++))
fi

# Detailed health check
if curl -f -s http://localhost:8000/api/v1/health/detailed > /tmp/health_detailed.json 2>&1; then
    log_success "Detailed health endpoint reachable"
    ((TESTS_PASSED++))
    
    # Check database connection
    if grep -q '"database":"healthy"' /tmp/health_detailed.json; then
        log_success "Database connection"
        ((TESTS_PASSED++))
    else
        log_error "Database connection failed"
        ((TESTS_FAILED++))
    fi
    
    # Check AI service (might be warning if no API key)
    if grep -q '"ai_service"' /tmp/health_detailed.json; then
        if grep -q '"ai_service":"healthy"' /tmp/health_detailed.json; then
            log_success "AI service connection"
            ((TESTS_PASSED++))
        else
            log_warning "AI service not available (check ANTHROPIC_API_KEY)"
            ((TESTS_WARNING++))
        fi
    fi
else
    log_error "Detailed health check failed"
    ((TESTS_FAILED++))
fi

# ── Database Checks ───────────────────────────────────────────
log_info "Database Checks:"

# Check database connectivity from container
if docker-compose exec -T postgres psql -U "${POSTGRES_USER:-pavlov_user}" -d "${POSTGRES_DB:-pavlov}" -c "SELECT 1;" > /dev/null 2>&1; then
    log_success "PostgreSQL connection"
    ((TESTS_PASSED++))
else
    log_error "PostgreSQL connection failed"
    ((TESTS_FAILED++))
fi

# Check if Alembic migrations are applied
if docker-compose exec -T postgres psql -U "${POSTGRES_USER:-pavlov_user}" -d "${POSTGRES_DB:-pavlov}" -c "SELECT version_num FROM alembic_version LIMIT 1;" > /tmp/migration_check.txt 2>&1; then
    if grep -q "version_num" /tmp/migration_check.txt; then
        LATEST_MIGRATION=$(grep -v "version_num" /tmp/migration_check.txt | grep -v "^-" | grep -v "^(" | grep -v "^$" | head -n1 | xargs)
        if [[ -n "$LATEST_MIGRATION" ]]; then
            log_success "Database migrations applied (latest: $LATEST_MIGRATION)"
            ((TESTS_PASSED++))
        else
            log_warning "No migrations found in alembic_version table"
            ((TESTS_WARNING++))
        fi
    else
        log_error "Could not check migration status"
        ((TESTS_FAILED++))
    fi
else
    log_warning "Migration table check failed (might be normal on fresh install)"
    ((TESTS_WARNING++))
fi

# ── Performance Checks ────────────────────────────────────────
log_info "Performance Checks:"

# Response time check
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null http://localhost:8000/api/v1/health)
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    log_success "API response time (${RESPONSE_TIME}s)"
    ((TESTS_PASSED++))
elif (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
    log_warning "API response time slow (${RESPONSE_TIME}s)"
    ((TESTS_WARNING++))
else
    log_error "API response time too slow (${RESPONSE_TIME}s)"
    ((TESTS_FAILED++))
fi

# Memory usage check
BACKEND_MEMORY=$(docker stats pavlov_backend --no-stream --format "{{.MemUsage}}" | cut -d'/' -f1 | sed 's/[^0-9.]//g')
if [[ -n "$BACKEND_MEMORY" ]]; then
    if (( $(echo "$BACKEND_MEMORY < 500" | bc -l) )); then
        log_success "Backend memory usage (${BACKEND_MEMORY}MB)"
        ((TESTS_PASSED++))
    elif (( $(echo "$BACKEND_MEMORY < 1000" | bc -l) )); then
        log_warning "Backend memory usage high (${BACKEND_MEMORY}MB)"
        ((TESTS_WARNING++))
    else
        log_error "Backend memory usage very high (${BACKEND_MEMORY}MB)"
        ((TESTS_FAILED++))
    fi
fi

# ── Security Checks ───────────────────────────────────────────
log_info "Security Checks:"

# Check that database port is not exposed
if lsof -i :5432 | grep -q LISTEN; then
    log_warning "PostgreSQL port 5432 exposed to host (consider using internal networking only)"
    ((TESTS_WARNING++))
else
    log_success "PostgreSQL port not exposed to host"
    ((TESTS_PASSED++))
fi

# Check environment variable security
source .env 2>/dev/null || true
if [[ "${SECRET_KEY:-}" == "generate_with_python_secrets_token_hex_32" ]]; then
    log_error "SECRET_KEY still using default value"
    ((TESTS_FAILED++))
else
    log_success "SECRET_KEY configured"
    ((TESTS_PASSED++))
fi

if [[ "${ENCRYPTION_KEY:-}" == "generate_with_fernet_generate_key" ]]; then
    log_error "ENCRYPTION_KEY still using default value"
    ((TESTS_FAILED++))
else
    log_success "ENCRYPTION_KEY configured"
    ((TESTS_PASSED++))
fi

# ── Cleanup ───────────────────────────────────────────────────
rm -f /tmp/health_*.json /tmp/migration_check.txt

# ── Summary ───────────────────────────────────────────────────
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED + TESTS_WARNING))

if [[ $TESTS_FAILED -eq 0 && $TESTS_WARNING -eq 0 ]]; then
    log_success "🎉 All health checks passed! ($TESTS_PASSED/$TOTAL_TESTS)"
    echo
    echo "✅ Pavlov is running optimally"
    exit 0
elif [[ $TESTS_FAILED -eq 0 ]]; then
    log_warning "⚠️  Health checks completed with warnings"
    echo "   Passed: $TESTS_PASSED"
    echo "   Warnings: $TESTS_WARNING"
    echo
    echo "⚠️  Pavlov is running but some issues need attention"
    exit 1
else
    log_error "❌ Health checks failed"
    echo "   Passed: $TESTS_PASSED"
    echo "   Failed: $TESTS_FAILED" 
    echo "   Warnings: $TESTS_WARNING"
    echo
    echo "🚨 Critical issues found - please check logs:"
    echo "   docker-compose logs backend"
    echo "   docker-compose logs frontend"
    echo "   docker-compose logs postgres"
    exit 2
fi