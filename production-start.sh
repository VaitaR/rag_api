#!/bin/bash
set -e

echo "🚀 Starting PRODUCTION mode with your data..."
echo "This will use real OpenAI embeddings and your custom data"
echo

# Check if production config exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found!"
    echo "Please create it first with your production settings."
    exit 1
fi

# Check if user data exists
USER_DATA_DIR="data/production"
if [ ! -d "$USER_DATA_DIR" ]; then
    echo "📁 Creating production data directory..."
    mkdir -p "$USER_DATA_DIR"
    
    echo "📋 Please add your data files to $USER_DATA_DIR/:"
    echo "  - dashboards.csv (your dashboard metadata)"
    echo "  - charts.csv (your chart metadata)"  
    echo "  - enrichment.yaml (your enrichment rules)"
    echo "  - md/ (directory with markdown documentation)"
    echo
    echo "You can copy the demo files as a starting point:"
    echo "  cp tests/fixtures/superset/* $USER_DATA_DIR/"
    echo
    read -p "Press Enter when your data is ready, or Ctrl+C to cancel..."
fi

# 1. Setup production environment
echo "�� Setting up production environment..."
cp .env.production .env

echo "⚠️  Please ensure you have configured:"
echo "  - RAG_OPENAI_API_KEY (your OpenAI API key)"
echo "  - POSTGRES_PASSWORD (secure database password)"
echo "  - JWT_SECRET (secure JWT secret)"
echo "  - SLACK_SIGNING_SECRET (if using Slack)"
echo
read -p "Press Enter to continue, or Ctrl+C to edit .env first..."

# 2. Start Docker services
echo "🐳 Starting Docker services..."
make docker-up

# 3. Wait for database
echo "⏳ Waiting for database..."
sleep 15

# 4. Run migrations
echo "🗄️ Running database migrations..."
make migrate

# 5. Load production data
echo "📊 Loading your production data..."
if [ -f "$USER_DATA_DIR/dashboards.csv" ] && [ -f "$USER_DATA_DIR/charts.csv" ]; then
    python -m app.dash_assistant.ingestion.index_jobs --complete \
        --dashboards-csv "$USER_DATA_DIR/dashboards.csv" \
        --charts-csv "$USER_DATA_DIR/charts.csv" \
        --md-dir "$USER_DATA_DIR/md" \
        --enrichment-yaml "$USER_DATA_DIR/enrichment.yaml"
else
    echo "⚠️  Production data files not found, loading demo data instead..."
    make ingest-complete
fi

# 6. Optimize database
echo "⚡ Optimizing database..."
make optimize-db

# 7. Run health checks
echo "🏥 Running health checks..."
echo
echo "=== API Health ==="
curl -s http://localhost:8000/dash/health | jq

echo
echo "=== Database Stats ==="
curl -s http://localhost:8000/dash/stats | jq

echo
echo "✅ Production deployment completed!"
echo
echo "🌐 API available at: http://localhost:8000"
echo "📖 Interactive docs: http://localhost:8000/docs"
echo "🔍 Test search: curl -X POST 'http://localhost:8000/dash/query' -H 'Content-Type: application/json' -d '{\"q\": \"your search term\", \"top_k\": 3}'"
echo
echo "🎯 Production features:"
echo "  - Real OpenAI embeddings"
echo "  - Your custom dashboards and charts"
echo "  - Production-grade logging"
echo "  - Slack integration (if configured)"
