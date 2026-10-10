# ADR-0002: PostgreSQL-backed job queue instead of Redis + Celery

Status: proposed · Date: 2026-10-10

## Context
The master prompt suggests Redis + Celery. The main machine is Windows; Celery has not officially supported Windows since 4.x (it needs workarounds such as the `solo` pool). The system also requires persistent job records, checkpoints, leases, idempotency and restart recovery — all of which must live in PostgreSQL anyway. Expected throughput is low (tens of jobs per video), but jobs are long (minutes).

## Decision
Use the `jobs` table as the queue. Workers claim with `SELECT … FOR UPDATE SKIP LOCKED`, hold a time-limited lease with heartbeats, and record every transition in `job_events`. Retry/backoff is implemented by setting `run_after`. The worker exposes a `JobQueue` interface so a Redis-based implementation can replace it if throughput ever requires.

## Consequences
+ One fewer service (no Redis), works natively on Windows, job state and queue state cannot diverge.
+ Restart recovery is a query (expired leases).
− Polling interval adds ~1 s latency (acceptable for minute-long jobs). LISTEN/NOTIFY can be added later.
− Not suitable for thousands of jobs/second (not a requirement).
