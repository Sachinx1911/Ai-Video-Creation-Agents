# ADR-0001: Modular monolith with separate worker processes

Status: proposed · Date: 2026-10-10

## Context
Single developer, single laptop (Windows, 16 GB RAM), long-running media/AI jobs, future need to split services.

## Decision
One Python package `studio` (FastAPI app + worker entry point) and one Next.js app. Workers are separate OS processes started from the same codebase. Module boundaries (agents, providers, media, orchestrator) are packages with one-directional imports. No Kubernetes, Kafka or microservices.

## Consequences
+ One install, one migration history, shared models. Simple local dev.
+ Workers can be scaled/separated by job type later.
− Must enforce import boundaries by convention and review.
