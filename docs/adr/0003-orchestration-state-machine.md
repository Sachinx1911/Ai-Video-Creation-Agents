# ADR-0003: Custom persisted state machine for orchestration (LangGraph re-evaluated in Phase 5)

Status: proposed · Date: 2026-10-10

## Context
The pipeline is mostly a deterministic DAG (brief → research → script → storyboard → per-scene generation → render → QA), with long asynchronous provider jobs and per-scene recovery. The state of record must be in PostgreSQL alongside jobs and assets.

## Decision
Phase 1–4 do not need an orchestration framework. Phase 5 implements a workflow run + task DAG persisted in PostgreSQL, executed through the job queue. LangGraph will be evaluated at the start of Phase 5 only for agent-internal loops (e.g. script critique/revision), not as the system of record. Only one orchestration mechanism will be adopted.

## Consequences
+ No framework lock-in; checkpoints are ordinary rows.
− We write and test the DAG scheduler ourselves.
