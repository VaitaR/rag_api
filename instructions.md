### Project instructions for LLM Agent (Cursor)

Keep this file short and practical. Update it whenever you change structure or flows.

### TL;DR
- Run demo (no auth): `make demo` → health at `/dash/health`, docs at `/docs`.
- Run prod helper: `make prod` (auth on unless `DEMO_MODE=true`).
- Start base stack: `make docker-up` → `make migrate`.
- Load sample data: `make ingest-complete` (uses `tests/fixtures/superset/*`).
- Tests: `make test-all` or `pytest -q` (ensure DB up: `make docker-db && make migrate`).
- Lint/type-check: `make lint` or `ruff check app/ tests/` and `mypy app/`.

### Layout (what is where)
- Root
  - `main.py`: FastAPI app entrypoint (includes routes, middleware, startup tasks).
  - `Dockerfile`, `docker-compose.yaml`, `docker-compose.demo.yaml`, `docker-compose.dev.yaml`.
  - `Makefile`: common tasks (docker, migrations, ingestion, shortcuts).
  - `scripts/`: operational scripts used by Makefile and docs
    - `demo-start.sh`, `production-start.sh`, `monitor.sh`, `test-api.sh`, `setup_env.sh`, `test_ci_locally.sh`.
  - `data/production/`: user-provided CSV/MD/YAML for prod ingestion.
  - `uploads/`: runtime temp uploads for document embedding API (configurable via `RAG_UPLOAD_DIR`).
  - `tests/`: unit/integration/E2E tests (superset fixtures in `tests/fixtures/superset/`).

- `app/` (ID-based RAG + shared infra)
  - `config.py`: global env/config, embeddings (LangChain), logger, vector store factory usage.
  - `middleware.py`: auth middleware (skipped if `DEMO_MODE=true`).
  - `routes/`
    - `document_routes.py`: ID-based RAG endpoints (`/documents`, `/query`, `/embed*`).
    - `pgvector_routes.py`: optional debug/db routes (enabled when `DEBUG_RAG_API=true`).
  - `services/`
    - `database.py`: main PG pool + pgvector index helpers.
    - `vector_store/`: async pgvector and other backends + `factory.py`.
  - `utils/`: loaders, health checks.

- `app/dash_assistant/` (dashboard search feature)
  - `migrations/*.sql`: schema for dash assistant. Only add schema changes here (SQL files, ordered).
  - `migrate.py`: executes migrations (tracks in `dash_migrations`).
  - `db.py`: asyncpg pool for dash assistant (uses same DSN as main config).
  - `ingestion/`: CSV/MD/YAML loaders + `index_jobs.py` CLI to run pipeline.
  - `indexing/embedder.py`: embeddings for ingestion (MOCK/OpenAI; independent of main LangChain embeddings).
  - `serving/`
    - `routes.py`: Dash API (`/dash/ingest`, `/dash/query`, `/dash/feedback`, `/dash/health`, `/dash/stats`).
    - `answer_builder.py`, `retriever.py`: RRF search and structured answers.
  - `slack/`: Slack blocks + routes (health and interactions if enabled).

### Runtime modes
- Demo: `docker-compose -f docker-compose.demo.yaml up -d` (or `make demo`).
  - `DEMO_MODE=true`, mock embeddings, no auth, sample data ingestion.
- Base/Prod-like: `docker-compose up -d` → `make migrate` → ingest your `data/production/*`.
  - Auth enforced by middleware unless `DEMO_MODE=true`.

### Core flows (how modules connect)
- ID-based RAG (documents API)
  - Requests → `main.py` → `app/routes/document_routes.py` → vector store in `app/services/vector_store/*`.
  - Uploads stored under `RAG_UPLOAD_DIR`; text split via `langchain_text_splitters`.

- Dash Assistant (dashboard search)
  - Ingestion: `python -m app.dash_assistant.ingestion.index_jobs --complete ...`
    - CSV (`dashboards.csv`, `charts.csv`), MD dir (`md/`), enrichment (`enrichment.yaml`).
    - Writes to PG tables (`bi_entity`, `bi_chart`, `bi_chunk`).
  - Query: `POST /dash/query` → `serving/retriever.py` (FTS + Vector + Trigram) → RRF → `answer_builder.py`.
  - Feedback: `POST /dash/feedback` updates `query_log`.
  - Health/Stats: `/dash/health`, `/dash/stats` (counts and coverage).

### Data contracts
- Ingestion CLI and `/dash/ingest` expect absolute paths; validate existence before load.
- `bi_chunk.embedding` uses pgvector (dimension:
  - Demo: 3072 (MOCK). Prod standard: 1536 (OpenAI text-embedding-3-small).
)

### Testing strategy (short)
- Unit (fast): mock DB and vector store; prefer `EMBEDDINGS_PROVIDER=MOCK`.
- Integration: with running PG (`make docker-db && make migrate`).
- E2E: demo stack or base stack with fixtures; avoid creating multiple event loops.

### Migrations policy (dash assistant)
- Only SQL in `app/dash_assistant/migrations/*.sql`.
- Use `python -m app.dash_assistant.migrate` to apply; do not inline DDL elsewhere.

### Env essentials
- PG: `POSTGRES_*` and `DB_HOST/DB_PORT`.
- Embeddings (main app): `EMBEDDINGS_PROVIDER`, `OPENAI_API_KEY` (or MOCK).
- Dash embeddings (ingestion): configured via `app/dash_assistant/config.py` defaults (MOCK/OpenAI).
- Demo toggle: `DEMO_MODE=true` to bypass auth.

### Conventions for edits
- Keep feature code next to its domain:
  - Dash query logic → `app/dash_assistant/serving/`.
  - Dash ingestion/parsers → `app/dash_assistant/ingestion/`.
  - Document APIs → `app/routes/document_routes.py`.
- If schema changes are needed, add a new `.sql` file and run migrate.
- Prefer async I/O; do not use `print`; use logger from `app/config.py` or `structlog` (dash assistant).
- Add/adjust tests in `tests/` for any new behavior; keep them deterministic (MOCK embeddings for CI).

### Useful commands
```bash
# Stack
make docker-up            # db + api
make docker-down
make docker-db            # db only
make migrate              # dash assistant migrations

# Data
make ingest-complete      # load sample superset fixtures

# Demo / Prod helpers
make demo                 # demo stack and ingestion
make prod                 # production helper script
make monitor              # monitoring dashboard
make test-api             # API smoke tests

# QA
make test-all             # all tests
make lint                 # ruff + mypy
make ci-local             # full CI locally
pytest -q                 # run tests directly
ruff check app/ tests/    # lint directly
mypy app/                 # types directly

# Scripts (moved to scripts/ directory)
make setup-env            # environment setup helper
```


