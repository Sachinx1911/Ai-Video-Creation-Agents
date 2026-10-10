# Implementation Plan

| Phase | Name | Status |
|---|---|---|
| 0 | Discovery & architecture review | done (this document set) |
| 1 | Foundation | in progress: backend + dashboard built, 59 backend tests pass; browser verification and remaining docs pending |
| 2 | Research, script, storyboard | not started — needs approval + LLM provider decision |
| 3 | Media generation (providers, image, video, voice) | not started — needs provider accounts |
| 4 | Automatic rendering (timeline, FFmpeg, audio mix, subtitles, export) | not started |
| 5 | Full automation (orchestrator, QA, recovery, e2e) | not started |
| 6 | Local AI expansion | not started |

Proposed order change vs. master prompt: none. Note: Phase 4 (rendering) depends only on assets, so it could be built before Phase 3 using uploaded sample media if provider accounts are delayed.

## Phase 1 — Foundation

### Scope
1. Repo structure, `.gitignore`, `.env.example`, `docker-compose.yml` (PostgreSQL 16 only).
2. Backend `apps/api` (Python 3.12, FastAPI, SQLAlchemy 2, Alembic, psycopg 3, pydantic-settings).
3. Migration `0001_foundation`: projects, project_revisions, assets, asset_versions, jobs, job_events, worker_heartbeats, audit_logs.
4. Projects API: list/filter, create, get, update (new revision), duplicate, archive, restore, revisions.
5. Asset registry: upload (size/type limits, streaming sha256, safe paths), new version, list, metadata, file download/preview, archive. Validation by a real background job.
6. Job system: state machine, idempotency, claim with `SKIP LOCKED`, lease + heartbeat, lease-expiry recovery, retry with backoff, cancel, manual retry, events.
7. Worker process with one real handler: `asset.probe` (FFprobe → media_info + validation status).
8. Health: liveness, readiness (DB, migrations at head, FFmpeg/FFprobe, storage writable + free space, worker heartbeat), system overview counts.
9. Web `apps/web` (Next.js + TypeScript + Tailwind, dark-first): Overview, Projects, New Project, Project Workspace (summary/edit/duplicate/archive, assets upload + preview, jobs, history), Asset Library, Jobs, System Health. Only screens with working backends appear in navigation.
10. Tests + docs (README, API_REFERENCE, TESTING, DEPLOYMENT, CHANGELOG).

### Out of scope for Phase 1
AI agents, providers, rendering, timeline, orchestrator, auth, Storyboard/Render/Provider screens.

### Acceptance criteria
- AC-1 `docker compose up -d db` + `alembic upgrade head` creates the schema on an empty DB; re-running is a no-op.
- AC-2 Project create/edit/duplicate/archive/restore works via API and UI; each edit adds a revision; data survives API restart.
- AC-3 Invalid input (duration out of range, unknown language, empty name) → HTTP 422 with field errors.
- AC-4 Upload of a real MP4/PNG/WAV stores the file under `STORAGE_ROOT/projects/<id>/…`, records sha256 + size, and the worker sets `validation_status=valid` with probed duration/dimensions. A corrupt or mismatched file ends `invalid` with a reason.
- AC-5 Path traversal filenames and oversize uploads are rejected (tests).
- AC-6 Jobs: illegal transitions rejected; duplicate idempotency key returns the existing job; a job whose worker died is re-queued after lease expiry; transient failures back off and stop at `max_attempts`; permanent failures are not retried; cancel works for queued jobs.
- AC-7 `/api/health/ready` reports each dependency truthfully (verified by stopping the worker → worker check fails).
- AC-8 Dashboard shows only backend data; every visible control performs its action.
- AC-9 Backend test suite passes against real PostgreSQL; frontend type-check, lint and production build pass.
