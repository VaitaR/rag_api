#!/bin/bash
# Quick API test script for macOS

echo "🧪 Quick API Test (Demo Mode - No Auth Required)"
echo "================================================"

# Function to run curl with timeout on macOS
run_with_timeout() {
    local timeout=5
    local cmd="$1"
    
    # Run command in background and get PID
    eval "$cmd" &
    local pid=$!
    
    # Wait for timeout or completion
    local count=0
    while kill -0 $pid 2>/dev/null && [ $count -lt $timeout ]; do
        sleep 1
        ((count++))
    done
    
    # Kill if still running
    if kill -0 $pid 2>/dev/null; then
        kill $pid 2>/dev/null
        echo "❌ Timeout after ${timeout}s"
        return 1
    fi
    
    wait $pid
    return $?
}

echo
echo "1️⃣ Health Check:"
curl -s --max-time 5 http://localhost:8000/dash/health | jq . 2>/dev/null || echo "❌ Error or timeout"

echo
echo "2️⃣ Database Stats:"
curl -s --max-time 5 http://localhost:8000/dash/stats | jq . 2>/dev/null || echo "❌ Error or timeout"

echo
echo "3️⃣ Search 'retention':"
curl -s --max-time 5 -X POST "http://localhost:8000/dash/query" \
  -H "Content-Type: application/json" \
  -d '{"q": "retention", "top_k": 2}' | jq . 2>/dev/null || echo "❌ Error or timeout"

echo
echo "4️⃣ Feedback test:"
curl -s --max-time 5 -X POST "http://localhost:8000/dash/feedback" \
  -H "Content-Type: application/json" \
  -d '{"qid": 1, "entity_id": 1, "feedback": "up"}' | jq . 2>/dev/null || echo "❌ Error or timeout"

echo
echo "✅ Test completed!"
