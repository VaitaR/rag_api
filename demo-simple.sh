#!/bin/bash
set -e

echo "🎯 Starting SIMPLE DEMO mode..."
echo "This demo runs without migrations - just API testing"
echo

# 1. Stop any existing services
echo "�� Stopping any existing services..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.demo.yaml down 2>/dev/null || true

# 2. Start only database
echo "🐳 Starting database..."
docker-compose -f docker-compose.demo.yaml up -d db

# 3. Wait for database
echo "⏳ Waiting for database..."
for i in {1..30}; do
    if docker-compose -f docker-compose.demo.yaml exec -T db pg_isready -U postgres -d rag_api > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    echo "  Attempt $i/30: Database not ready yet..."
    sleep 2
done

# 4. Create tables directly in database
echo "🗄️ Creating database tables..."
docker-compose -f docker-compose.demo.yaml exec -T db psql -U postgres -d rag_api << 'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS bi_entity (
  entity_id           BIGSERIAL PRIMARY KEY,
  entity_type         TEXT NOT NULL CHECK (entity_type IN ('dashboard','chart')),
  superset_id         TEXT,
  dashboard_slug      TEXT,
  title               TEXT NOT NULL,
  description         TEXT,
  domain              TEXT,
  owner               TEXT,
  tags                TEXT[],
  url                 TEXT,
  usage_score         REAL DEFAULT 0,
  last_refresh_ts     TIMESTAMPTZ,
  metadata            JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS bi_chart (
  chart_id            BIGSERIAL PRIMARY KEY,
  parent_dashboard_id BIGINT REFERENCES bi_entity(entity_id) ON DELETE CASCADE,
  superset_chart_id   TEXT,
  title               TEXT NOT NULL,
  viz_type            TEXT,
  sql_text            TEXT,
  metrics             JSONB,
  dimensions          JSONB,
  filters_default     JSONB,
  url                 TEXT
);

CREATE TABLE IF NOT EXISTS bi_chunk (
  chunk_id            BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT REFERENCES bi_entity(entity_id) ON DELETE CASCADE,
  chart_id            BIGINT REFERENCES bi_chart(chart_id) ON DELETE CASCADE,
  scope               TEXT NOT NULL,
  content             TEXT NOT NULL,
  lang                TEXT,
  tsv_en              tsvector,
  tsv_ru              tsvector,
  embedding           vector(3072)
);

CREATE TABLE IF NOT EXISTS query_log (
  qid             BIGSERIAL PRIMARY KEY,
  ts              TIMESTAMPTZ DEFAULT now(),
  user_id         TEXT,
  query_text      TEXT,
  intent_json     JSONB,
  chosen_entity   BIGINT REFERENCES bi_entity(entity_id),
  chosen_chart    BIGINT REFERENCES bi_chart(chart_id),
  scores          JSONB,
  feedback        TEXT
);

-- Insert demo data
INSERT INTO bi_entity (entity_id, entity_type, superset_id, dashboard_slug, title, description, domain, owner, tags, url, usage_score) VALUES
(1, 'dashboard', '1', 'user-retention-dashboard', 'User Retention Dashboard', 'Dashboard showing user retention metrics and cohort analysis', 'product', 'john.doe@company.com', ARRAY['retention', 'cohort', 'users'], 'https://superset.company.com/dashboard/1/', 0.9),
(2, 'dashboard', '2', 'revenue-analytics', 'Revenue Analytics', 'Comprehensive revenue tracking and forecasting dashboard', 'finance', 'jane.smith@company.com', ARRAY['revenue', 'analytics'], 'https://superset.company.com/dashboard/2/', 0.8);

INSERT INTO bi_chunk (entity_id, scope, content, tsv_en, tsv_ru) VALUES
(1, 'title', 'User Retention Dashboard', to_tsvector('english', 'User Retention Dashboard'), to_tsvector('russian', 'User Retention Dashboard')),
(1, 'desc', 'Dashboard showing user retention metrics and cohort analysis', to_tsvector('english', 'Dashboard showing user retention metrics and cohort analysis'), to_tsvector('russian', 'Dashboard showing user retention metrics and cohort analysis')),
(2, 'title', 'Revenue Analytics', to_tsvector('english', 'Revenue Analytics'), to_tsvector('russian', 'Revenue Analytics')),
(2, 'desc', 'Comprehensive revenue tracking and forecasting dashboard', to_tsvector('english', 'Comprehensive revenue tracking and forecasting dashboard'), to_tsvector('russian', 'Comprehensive revenue tracking and forecasting dashboard'));

-- Create indices
CREATE INDEX IF NOT EXISTS idx_bi_chunk_tsv_en ON bi_chunk USING GIN (tsv_en);
CREATE INDEX IF NOT EXISTS idx_bi_chunk_tsv_ru ON bi_chunk USING GIN (tsv_ru);
CREATE INDEX IF NOT EXISTS idx_bi_entity_title_trgm ON bi_entity USING GIN (title gin_trgm_ops);

SQL

# 5. Start FastAPI
echo "🚀 Starting FastAPI..."
docker-compose -f docker-compose.demo.yaml up -d fastapi

# 6. Wait for API
echo "⏳ Waiting for API to start..."
sleep 10

# 7. Test API
echo "�� Testing API..."
echo
echo "=== API Health ==="
curl -s http://localhost:8000/dash/health | jq || echo "API not ready yet"

echo
echo "=== Database Stats ==="
curl -s http://localhost:8000/dash/stats | jq || echo "Stats not ready yet"

echo
echo "=== Test Query ==="
curl -s -X POST "http://localhost:8000/dash/query" \
  -H "Content-Type: application/json" \
  -d '{"q": "retention", "top_k": 3}' | jq || echo "Query failed"

echo
echo "✅ Simple demo completed!"
echo
echo "🌐 API available at: http://localhost:8000"
echo "📖 Interactive docs: http://localhost:8000/docs"
echo "🧪 Run full tests: ./test-api.sh"
echo "📊 Monitor system: ./monitor.sh"
echo
echo "🎯 This demo includes:"
echo "  - 2 sample dashboards with search functionality"
echo "  - Mock embeddings (no OpenAI needed)"
echo "  - Full API endpoints"
echo "  - Query and feedback logging"
