#!/bin/bash
# =============================================================================
# WatchLLM - Environment Setup & Validation Script
# =============================================================================
# This script validates that all required environment variables are set
# and tests connections to external services.
#
# Usage:
#   chmod +x scripts/setup-env.sh
#   ./scripts/setup-env.sh [environment]
#
# Arguments:
#   environment: development (default), staging, or production
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment argument
ENVIRONMENT=${1:-development}

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  WatchLLM - Environment Setup & Validation${NC}"
echo -e "${BLUE}  Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# =============================================================================
# Load Environment File
# =============================================================================

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}No .env file found. Checking for environment template...${NC}"
    
    TEMPLATE_FILE="config/environments/${ENVIRONMENT}.env"
    if [ -f "$TEMPLATE_FILE" ]; then
        echo -e "${YELLOW}Found template: ${TEMPLATE_FILE}${NC}"
        echo -e "${YELLOW}Copying to .env...${NC}"
        cp "$TEMPLATE_FILE" .env
        echo -e "${GREEN}✓ Created .env from ${ENVIRONMENT} template${NC}"
        echo -e "${YELLOW}⚠ Please update .env with your actual values!${NC}"
    else
        echo -e "${RED}✗ No template found at ${TEMPLATE_FILE}${NC}"
        echo -e "${RED}  Run: cp .env.example .env${NC}"
        exit 1
    fi
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)
echo -e "${GREEN}✓ Loaded environment from .env${NC}"
echo ""

# =============================================================================
# Validation Functions
# =============================================================================

ERRORS=0
WARNINGS=0

check_required() {
    local var_name=$1
    local var_value=${!var_name}
    local description=$2
    
    if [ -z "$var_value" ] || [ "$var_value" == "your-"* ] || [ "$var_value" == "your_"* ]; then
        echo -e "${RED}✗ ${var_name} is not set${NC}"
        echo -e "  ${description}"
        ((ERRORS++))
        return 1
    else
        echo -e "${GREEN}✓ ${var_name}${NC}"
        return 0
    fi
}

check_optional() {
    local var_name=$1
    local var_value=${!var_name}
    local description=$2
    
    if [ -z "$var_value" ]; then
        echo -e "${YELLOW}○ ${var_name} is not set (optional)${NC}"
        echo -e "  ${description}"
        ((WARNINGS++))
        return 1
    else
        echo -e "${GREEN}✓ ${var_name}${NC}"
        return 0
    fi
}

# =============================================================================
# Validate Required Environment Variables
# =============================================================================

echo -e "${BLUE}Checking Required Environment Variables...${NC}"
echo ""

echo -e "${YELLOW}Database - ClickHouse:${NC}"
check_required "CLICKHOUSE_HOST" "ClickHouse server hostname"
check_required "CLICKHOUSE_PORT" "ClickHouse port (usually 9000)"
check_required "CLICKHOUSE_USER" "ClickHouse username"
check_required "CLICKHOUSE_DATABASE" "ClickHouse database name"

if [ "$ENVIRONMENT" == "production" ]; then
    check_required "CLICKHOUSE_PASSWORD" "ClickHouse password (required in production)"
else
    check_optional "CLICKHOUSE_PASSWORD" "ClickHouse password (optional in development)"
fi
echo ""

echo -e "${YELLOW}Queue - Redis:${NC}"
check_required "REDIS_URL" "Redis connection URL"
echo ""

echo -e "${YELLOW}Authentication - Supabase:${NC}"
check_required "SUPABASE_URL" "Supabase project URL"
check_required "SUPABASE_ANON_KEY" "Supabase anonymous key"
check_required "SUPABASE_SERVICE_KEY" "Supabase service role key"
echo ""

echo -e "${YELLOW}Admin:${NC}"
if [ "$ENVIRONMENT" == "production" ]; then
    check_required "ADMIN_API_KEY" "Admin API key for manual tier upgrades"
else
    check_optional "ADMIN_API_KEY" "Admin API key (required in production)"
fi
echo ""

echo -e "${YELLOW}Frontend:${NC}"
check_required "VITE_API_URL" "Backend API URL for frontend"
check_required "VITE_SUPABASE_URL" "Supabase URL for frontend"
check_required "VITE_SUPABASE_ANON_KEY" "Supabase anon key for frontend"
echo ""

# =============================================================================
# Validate Optional Environment Variables
# =============================================================================

echo -e "${BLUE}Checking Optional Environment Variables...${NC}"
echo ""

echo -e "${YELLOW}Monitoring:${NC}"
check_optional "SENTRY_DSN" "Sentry DSN for error tracking (recommended)"
check_optional "VITE_SENTRY_DSN" "Sentry DSN for frontend"
echo ""

# =============================================================================
# Test Connections
# =============================================================================

echo -e "${BLUE}Testing Service Connections...${NC}"
echo ""

# Test Redis connection
echo -e "${YELLOW}Testing Redis connection...${NC}"
if command -v redis-cli &> /dev/null; then
    # Extract host and port from URL
    REDIS_HOST=$(echo $REDIS_URL | sed -E 's/redis:\/\/([^:@]+:)?([^@]+@)?([^:]+):([0-9]+).*/\3/')
    REDIS_PORT=$(echo $REDIS_URL | sed -E 's/redis:\/\/([^:@]+:)?([^@]+@)?([^:]+):([0-9]+).*/\4/')
    
    if timeout 5 redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis connection successful${NC}"
    else
        echo -e "${YELLOW}○ Redis connection failed (may be network/auth issue)${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}○ redis-cli not installed, skipping Redis test${NC}"
    ((WARNINGS++))
fi
echo ""

# Test ClickHouse connection
echo -e "${YELLOW}Testing ClickHouse connection...${NC}"
if command -v curl &> /dev/null; then
    HTTP_PORT=$((CLICKHOUSE_PORT - 877))  # 9000 -> 8123
    CH_URL="http://${CLICKHOUSE_HOST}:${HTTP_PORT}"
    
    if [ -n "$CLICKHOUSE_PASSWORD" ]; then
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
            "${CH_URL}/?query=SELECT%201&user=${CLICKHOUSE_USER}&password=${CLICKHOUSE_PASSWORD}" 2>/dev/null || echo "000")
    else
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
            "${CH_URL}/?query=SELECT%201" 2>/dev/null || echo "000")
    fi
    
    if [ "$RESPONSE" == "200" ]; then
        echo -e "${GREEN}✓ ClickHouse connection successful${NC}"
    elif [ "$RESPONSE" == "000" ]; then
        echo -e "${YELLOW}○ ClickHouse connection failed (server not reachable)${NC}"
        echo -e "  Tried: ${CH_URL}"
        ((WARNINGS++))
    else
        echo -e "${YELLOW}○ ClickHouse connection returned HTTP ${RESPONSE}${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}○ curl not installed, skipping ClickHouse test${NC}"
    ((WARNINGS++))
fi
echo ""

# Test Supabase connection
echo -e "${YELLOW}Testing Supabase connection...${NC}"
if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
        "${SUPABASE_URL}/rest/v1/" \
        -H "apikey: ${SUPABASE_ANON_KEY}" 2>/dev/null || echo "000")
    
    if [ "$RESPONSE" == "200" ] || [ "$RESPONSE" == "401" ]; then
        echo -e "${GREEN}✓ Supabase connection successful${NC}"
    elif [ "$RESPONSE" == "000" ]; then
        echo -e "${YELLOW}○ Supabase connection failed (server not reachable)${NC}"
        ((WARNINGS++))
    else
        echo -e "${YELLOW}○ Supabase connection returned HTTP ${RESPONSE}${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}○ curl not installed, skipping Supabase test${NC}"
    ((WARNINGS++))
fi
echo ""

# =============================================================================
# Summary
# =============================================================================

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗ ${ERRORS} error(s) found${NC}"
    echo -e "${RED}  Please fix the errors above before starting the services.${NC}"
    echo ""
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}○ ${WARNINGS} warning(s) found${NC}"
    echo -e "${YELLOW}  Services may work, but some features might be limited.${NC}"
    echo ""
else
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
fi

echo -e "${GREEN}Environment setup complete for: ${ENVIRONMENT}${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Start Redis:      docker run -d --name redis -p 6379:6379 redis:7"
echo "  2. Start ClickHouse: docker run -d --name clickhouse -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server"
echo "  3. Run schema:       clickhouse-client < infra/clickhouse/schema.sql"
echo "  4. Start services:   python run_ingest.py & python run_processor.py & python run_ui_backend.py"
echo "  5. Start frontend:   cd web && npm run dev"
echo ""
