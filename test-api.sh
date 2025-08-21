#!/bin/bash

echo "🧪 Testing Dash Assistant API..."
echo

BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "  $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    # Split response and status code
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq 200 ]; then
        echo -e "  ${GREEN}✅ Success ($status_code)${NC}"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "  ${RED}❌ Failed ($status_code)${NC}"
        echo "$body"
    fi
    echo
}

# Test 1: Health Check
test_endpoint "GET" "/dash/health" "" "API Health Check"

# Test 2: Stats
test_endpoint "GET" "/dash/stats" "" "Database Statistics"

# Test 3: Search Query
test_endpoint "POST" "/dash/query" '{"q": "retention analysis", "top_k": 3}' "Search for 'retention analysis'"

# Test 4: Another Search Query  
test_endpoint "POST" "/dash/query" '{"q": "revenue dashboard", "top_k": 2}' "Search for 'revenue dashboard'"

# Test 5: Feedback (using mock qid)
test_endpoint "POST" "/dash/feedback" '{"qid": 1, "entity_id": 1, "feedback": "up"}' "Submit positive feedback"

# Test 6: Slack Health (if available)
test_endpoint "GET" "/slack/health" "" "Slack Integration Health"

echo "🎯 API Testing completed!"
echo
echo "💡 Tips:"
echo "  - If any tests fail, check docker logs: docker-compose logs fastapi"
echo "  - View API docs at: $BASE_URL/docs"
echo "  - Monitor with: ./monitor.sh"
