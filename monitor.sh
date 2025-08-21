#!/bin/bash

echo "📊 Dash Assistant Monitoring Dashboard"
echo "======================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8000"

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local name=$2
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$status" -eq 200 ]; then
        echo -e "${GREEN}✅ $name${NC}"
        return 0
    else
        echo -e "${RED}❌ $name (HTTP $status)${NC}"
        return 1
    fi
}

# System Status
echo -e "${BLUE}🏥 System Health${NC}"
check_endpoint "/dash/health" "API Health"
check_endpoint "/dash/stats" "Database Stats"
check_endpoint "/slack/health" "Slack Integration"
echo

# Docker Status
echo -e "${BLUE}🐳 Docker Services${NC}"
docker-compose ps
echo

# Database Stats
echo -e "${BLUE}📊 Database Statistics${NC}"
curl -s "$BASE_URL/dash/stats" | jq -r '
"Dashboards: \(.dashboards)
Charts: \(.charts)  
Chunks: \(.chunks)
Embeddings: \(.chunks_with_embeddings)
Coverage: \(.embedding_coverage | round)%"
' 2>/dev/null || echo "Stats not available"
echo

# Recent Logs
echo -e "${BLUE}📝 Recent Logs (last 10 lines)${NC}"
docker-compose logs --tail=10 fastapi 2>/dev/null || echo "Logs not available"
echo

# Resource Usage
echo -e "${BLUE}💾 Resource Usage${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "Docker stats not available"
echo

echo "🔄 Auto-refresh: watch -n 5 ./monitor.sh"
