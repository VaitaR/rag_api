#!/bin/bash
set -e

echo "🎯 Starting DEMO mode with test data..."
echo "This will use mock embeddings and sample dashboards for quick testing"
echo

# 1. Stop any existing services
echo "🛑 Stopping any existing services..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.demo.yaml down 2>/dev/null || true

# 2. Start Docker services with demo config
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.demo.yaml up -d

# 3. Wait for database to be ready
echo "⏳ Waiting for database to start..."
echo "Checking database health..."
for i in {1..30}; do
    if docker-compose -f docker-compose.demo.yaml exec -T db pg_isready -U postgres -d rag_api > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    echo "  Attempt $i/30: Database not ready yet..."
    sleep 2
done

# 4. Run migrations inside container
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.demo.yaml exec -T fastapi python -m app.dash_assistant.migrate

# 5. Load demo data inside container
echo "📊 Loading demo data..."
docker-compose -f docker-compose.demo.yaml exec -T fastapi python -m app.dash_assistant.ingestion.index_jobs --complete \
    --dashboards-csv tests/fixtures/superset/dashboards.csv \
    --charts-csv tests/fixtures/superset/charts.csv \
    --md-dir tests/fixtures/superset/md \
    --enrichment-yaml tests/fixtures/superset/enrichment.yaml

# 6. Optimize database inside container
echo "⚡ Optimizing database..."
docker-compose -f docker-compose.demo.yaml exec -T db psql -U postgres -d rag_api -c "ANALYZE;" || echo "Optimization skipped"

# 7. Run health checks
echo "🏥 Running health checks..."
sleep 5

echo
echo "=== API Health ==="
curl -s http://localhost:8000/dash/health | jq || echo "API not ready yet, please wait..."

echo
echo "=== Database Stats ==="
curl -s http://localhost:8000/dash/stats | jq || echo "Stats not ready yet, please wait..."

echo
echo "✅ Demo deployment completed!"
echo
echo "🌐 API available at: http://localhost:8000"
echo "📖 Interactive docs: http://localhost:8000/docs"
echo "🔍 Try a search: curl -X POST 'http://localhost:8000/dash/query' -H 'Content-Type: application/json' -d '{\"q\": \"retention\", \"top_k\": 3}'"
echo
echo "�� Demo includes:"
echo "  - 5 sample dashboards (User Retention, Revenue Analytics, etc.)"
echo "  - 7 sample charts with real metadata"
echo "  - Mock embeddings (no OpenAI API key needed)"
echo "  - Full search and feedback functionality"
echo
echo "🧪 Test the API: ./scripts/test-api.sh"
echo "📊 Monitor system: ./scripts/monitor.sh"
echo "🚀 To switch to production mode later, run: ./scripts/production-start.sh"
