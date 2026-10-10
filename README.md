# AI Video Creation Studio

A modular, hybrid cloud + local system that will turn a video brief into a finished, validated MP4. It targets Instagram Reels and YouTube Shorts first.

**Current status: Phase 1 (Foundation), in progress.** Project management, the asset registry, persistent background jobs, health checks and the dashboard work today. AI generation (script, storyboard, images, video, voice) and rendering are **not built yet**. See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Layout

```
apps/api     Python 3.12 · FastAPI · SQLAlchemy · Alembic · worker process (package `studio`)
apps/web     Next.js 16 · React 19 · TypeScript · Tailwind 4 (dashboard)
docs/        requirements, architecture, ADRs, schema, plan
storage/     media files + local dev database (git-ignored)
```

## Prerequisites

- Python 3.12+, Node 20+ (tested with Node 26), FFmpeg + FFprobe on PATH
- PostgreSQL 16, through **either**:
  - Docker: `docker compose up -d db`, **or**
  - no Docker: `python scripts/dev_db.py start` (run inside `apps/api` after installing deps; uses the `pgserver` binaries)

Both listen on `127.0.0.1:5433` with user and password `studio`.

## Setup (first time on a machine)

Backend:

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/python scripts/dev_db.py start
.venv/Scripts/alembic upgrade head
```

On macOS/Linux, use `.venv/bin/` instead of `.venv/Scripts/`.

Frontend:

```bash
cd apps/web
npm install
cp .env.example .env.local
```

## Run (three terminals)

```bash
cd apps/api && .venv/Scripts/python -m uvicorn studio.main:app --host 127.0.0.1 --port 8000
```

```bash
cd apps/api && .venv/Scripts/python -m studio.workers.runner
```

```bash
cd apps/web && npm run dev
```

Open http://localhost:3000. API docs: http://127.0.0.1:8000/docs.

## Tests

```bash
cd apps/api && .venv/Scripts/python -m pytest
```

The backend tests use a real PostgreSQL database (`studio_test`) and real FFmpeg. Nothing is mocked.

```bash
cd apps/web && npx tsc --noEmit && npm run lint && npm run build
```

## Documentation

[Requirements](docs/REQUIREMENTS.md) · [Architecture](docs/ARCHITECTURE.md) · [Database](docs/DATABASE_SCHEMA.md) · [Agents](docs/AGENT_SPECIFICATIONS.md) · [Providers](docs/PROVIDER_INTEGRATION.md) · [Plan](docs/IMPLEMENTATION_PLAN.md) · [ADRs](docs/adr/)
