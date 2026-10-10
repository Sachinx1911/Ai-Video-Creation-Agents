# Changelog

## Unreleased: Phase 1 Foundation (in progress)

- Phase 0 docs: requirements register, architecture, ADR-0001..0004, database schema, agent specifications, provider integration notes, implementation plan.
- Backend (`apps/api`): FastAPI app, settings, secret-redacting logs, safe storage paths.
- Migration `0001_foundation`: projects, project_revisions, assets, asset_versions, jobs, job_events, worker_heartbeats, audit_logs.
- Projects API: create, list/search, update with revisions, duplicate, archive and restore.
- Asset registry: streamed upload with sha256 and size limit, versions, download, soft archive, licence note required for music/SFX.
- PostgreSQL job queue: SKIP LOCKED claim, leases and heartbeats, retry with backoff, failure categories, cancel and manual retry, event log.
- Worker process with the `asset.probe` handler (FFprobe validation).
- Health readiness and system overview endpoints.
- Dashboard (`apps/web`): Overview, Projects, New Project, Project Workspace, Asset Library, Jobs, System Health.
- 59 backend tests against real PostgreSQL and FFmpeg.
