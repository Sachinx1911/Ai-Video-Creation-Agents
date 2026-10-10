# ADR-0004: SQLAlchemy 2 + Alembic + psycopg 3; local filesystem storage

Status: proposed · Date: 2026-10-10

## Decision
- ORM: SQLAlchemy 2.x typed declarative models; sync sessions (FastAPI runs them in a threadpool; simpler and adequate for single-user load).
- Migrations: Alembic, one revision per schema change, never `drop_all` against a real database.
- Driver: psycopg 3 (binary wheel).
- Enums: stored as PostgreSQL `VARCHAR` + `CHECK` constraints (via SQLAlchemy `Enum(native_enum=False)`), which are easier to migrate than native PG enums.
- Media: files on local disk under `STORAGE_ROOT`, DB stores relative key, sha256, size, mime, probed metadata. S3-compatible storage can be added behind a `Storage` interface.

## Consequences
+ Mature, well-documented stack; migrations are reviewable.
− Sync DB access; revisit if concurrency needs grow.
