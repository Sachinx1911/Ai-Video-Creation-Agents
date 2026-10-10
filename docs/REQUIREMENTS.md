# Requirements Register

Source: Master Project Prompt (received 2026-10-10). Status values:
`confirmed` (stated by owner) · `proposed` (technical decision awaiting approval) · `assumption` (not yet confirmed) · `future` · `excluded`.
Implementation status: `not started` · `in progress` · `done (verified)` · `blocked`.

Priority: P0 = foundation / blocking, P1 = core pipeline, P2 = important, P3 = later.

## 1. Repository status (Phase 0 inspection, 2026-10-10)

- Project folder was **empty**: no source code, no git history, no docs. Everything is greenfield.
- Host machine (measured): AMD Ryzen 7 7435HS, 15.8 GB RAM, NVIDIA RTX 3050 Laptop **4 GB VRAM**, ~34 GB free on `D:`, Windows 11.
- Installed: Python 3.12.10 / 3.14.3, Node 26.3, npm 11, pnpm 11, git 2.54, FFmpeg + FFprobe 9.0.2 (gyan.dev full build), Docker 29.7 CLI.
- Not installed: PostgreSQL, Redis, Ollama.
- Docker Desktop daemon **fails to start** (stale `sailor-ingest.sock` error). PostgreSQL is planned through Docker Compose, so this blocks database tests until fixed.

## 2. Confirmed requirements

| ID | Requirement | Pri | Depends on | Acceptance criteria (summary) | Phase | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Project CRUD: create, edit, duplicate, archive, reopen. All brief fields from §4.1 | P0 | REQ-040 | API + UI perform each action; data survives restart | 1 | not started |
| REQ-002 | Project version / production history | P1 | REQ-001 | Each settings change creates an immutable revision row | 1 | not started |
| REQ-003 | No permanent asset deletion without explicit user action + safeguards | P0 | REQ-010 | No delete endpoint without confirmation; archive is soft | 1 | not started |
| REQ-004 | Research & fact-checking agent with sources, uncertainty, verified/assumed split | P1 | REQ-030 | Output schema has `claims[]` with `source_refs` + `confidence` | 2 | not started |
| REQ-005 | Script agent: hook, scenes, CTA, timing estimate, pronunciation notes; Marathi/Hindi/English | P1 | REQ-004 | Duration estimate within ±15% of target using language-specific speaking rate | 2 | not started |
| REQ-006 | Storyboard agent: per-scene fields in §4.4 | P1 | REQ-005 | Every scene links to a script segment; schema-validated | 2 | not started |
| REQ-007 | Visual director: shared project style bible + continuity refs | P1 | REQ-006 | Style bible stored and injected into all image/video prompts | 2 | not started |
| REQ-008 | Image generation agent via provider adapters, versioned assets | P1 | REQ-030, REQ-010 | Real image received, validated, linked to scene | 3 | not started |
| REQ-009 | Video generation agent: async jobs, polling, timeouts, capability validation | P1 | REQ-030, REQ-020 | Real clip received, probed, linked to scene | 3 | not started |
| REQ-010 | Asset registry: files on disk, DB holds path/key, hash, metadata, provenance | P0 | REQ-040 | Upload → stored under project dir → sha256 + ffprobe metadata recorded | 1 | not started |
| REQ-011 | Voice-over agent: cloud + local TTS adapters, segment timing | P1 | REQ-030 | Audio file per segment, measured duration stored | 3 | not started |
| REQ-012 | Audio/sound design: music, ducking, loudness, peak check; licensed assets only | P2 | REQ-011 | Mixed track passes peak/loudness checks; license field required on music assets | 4 | not started |
| REQ-013 | Editing agent emits validated timeline spec (not free-form commands) | P1 | REQ-006, REQ-010 | Timeline schema validated; missing refs / gaps / negative durations rejected | 4 | not started |
| REQ-014 | FFmpeg render engine from parameterized ops; no shell strings | P1 | REQ-013 | Argument lists built in code; `subprocess` with `shell=False` only | 4 | not started |
| REQ-015 | Export presets (default 1080×1920, H.264/AAC MP4, configurable fps) | P1 | REQ-014 | Preset table; output verified by ffprobe | 4 | not started |
| REQ-016 | Render queue, progress, cancellation, logs, temp cleanup | P1 | REQ-020 | Render job visible with progress; cancel stops process | 4 | not started |
| REQ-017 | QA agent: objective technical checks + QA report (pass/warn/fail) | P1 | REQ-015 | Report covers streams, duration, resolution, black/silence detect | 5 | not started |
| REQ-018 | Publishing metadata (title, caption, hashtags, SRT) — no auto-upload | P2 | REQ-005 | Metadata generated; clearly labelled "not published" | 5 | not started |
| REQ-020 | Persistent job records with states submitted/queued/running/succeeded/failed/cancelled/awaiting_retry | P0 | REQ-040 | Illegal transitions rejected; state survives restart | 1 | not started |
| REQ-021 | Retry with exponential backoff, failure categories, dead-letter | P1 | REQ-020 | Permanent errors not retried; max attempts honoured | 1 (core) / 3 | not started |
| REQ-022 | Idempotency / duplicate-job prevention; no double-charging providers | P0 | REQ-020 | Unique idempotency key; provider job id stored before polling | 1 (core) / 3 | not started |
| REQ-023 | Checkpoints + resume after restart; per-scene recovery | P1 | REQ-020 | Killing worker mid-job → job reclaimed after lease expiry | 1 (lease) / 5 | not started |
| REQ-024 | Orchestrator: dependency DAG, parallel safe tasks, event log | P1 | REQ-020..023 | Brief → final MP4 with no manual steps (mock + real) | 5 | not started |
| REQ-030 | Provider abstraction with capability discovery and explicit unsupported responses | P1 | — | Each adapter declares capabilities; unsupported → typed error | 3 | not started |
| REQ-031 | Secrets only via env / secret store; never in UI, logs, frontend | P0 | — | `SecretStr` config; log redaction test | 1 | not started |
| REQ-032 | Provider manager screen (status, capabilities, model selection) | P2 | REQ-030 | Shows real adapter status | 3 | not started |
| REQ-040 | PostgreSQL primary DB with versioned migrations; never reset existing DB | P0 | Docker/Postgres | `alembic upgrade head` from empty and from previous revision | 1 | blocked (Docker) |
| REQ-041 | Media files outside DB; path-traversal-safe storage | P0 | — | Paths resolved and checked to be inside storage root | 1 | not started |
| REQ-042 | Health checks (DB, FFmpeg, storage, worker heartbeat) | P0 | REQ-040 | `/health/ready` reports each dependency truthfully | 1 | not started |
| REQ-050 | Dark-first studio dashboard; all numbers from backend; no decorative controls | P0 | REQ-001 | Every visible control works; no hard-coded metrics | 1+ | not started |
| REQ-051 | Screens A–J (Overview … Settings) | P1 | various | Each screen ships only with its backing feature | 1–6 | not started |
| REQ-060 | Security: input validation, upload limits/type checks, no shell exec of AI output, audit log | P0 | — | Tests for traversal, oversize upload, wrong type | 1+ | not started |
| REQ-070 | Testing: unit, integration, workflow, rendering, e2e; mocks clearly labelled | P0 | — | `TESTING.md` lists suites + what is mocked | 1+ | not started |
| REQ-071 | Reproducible e2e test rendering a small video from synthetic local assets | P1 | REQ-014 | CI-runnable test produces MP4 verified by ffprobe | 4 | not started |
| REQ-080 | Documentation set (§18) kept current | P0 | — | Docs reflect actual behaviour | all | in progress |
| REQ-090 | Local AI migration plan; no offline claims without offline test | P3 | REQ-030 | Benchmarks + offline test report | 6 | not started |

## 3. Proposed technical decisions (awaiting approval — see `docs/adr/`)

| ID | Decision | ADR |
|---|---|---|
| DEC-001 | Modular monolith: one Python package (`studio`) + separate worker process + Next.js web app | ADR-0001 |
| DEC-002 | **PostgreSQL-backed job queue** (`SELECT … FOR UPDATE SKIP LOCKED` + leases) instead of Redis + Celery | ADR-0002 |
| DEC-003 | Custom persisted state machine for orchestration; re-evaluate LangGraph in Phase 5 | ADR-0003 |
| DEC-004 | SQLAlchemy 2 + Alembic + psycopg 3; Pydantic v2 schemas | ADR-0004 |
| DEC-005 | Local filesystem storage under a single configured root, keyed by project/asset id | ADR-0004 |
| DEC-006 | Single-user local app in Phase 1 (bind to 127.0.0.1, no auth); multi-user design deferred | ADR-0001 |

## 4. Assumptions (NOT confirmed — please confirm or correct)

- A-01: Single user, runs on this laptop; not exposed to the internet.
- A-02: No cloud provider accounts / API keys exist yet; provider choice happens in Phase 3.
- A-03: Monthly cloud budget unknown → cost tracking designed in, limits unset.
- A-04: Music/SFX will come from user-supplied licensed files or a licensed library, not AI-scraped audio.
- A-05: UI language English; content languages Marathi, Hindi, English.

## 5. Unresolved questions (can be deferred unless marked)

- Q-01 (Phase 3, essential then): Which cloud providers/accounts are available (LLM, image, video, TTS)? Budget per video?
- Q-02 (Phase 2): Should research use live web search (needs a search API) or only user-supplied sources?
- Q-03 (Phase 3): Preferred Marathi voice — cloud premium vs. local; is quality or offline more important?
- Q-04 (Phase 4): Branding assets (logo, fonts, colours) available?
- Q-05: Is the repo going to a GitHub remote?

## 6. Architectural conflicts / deviations from the master prompt

- C-01: Prompt suggests Redis + Celery. **Celery does not officially support Windows**, and this is the primary dev machine. Proposal DEC-002 removes Redis/Celery for now; the queue interface is abstract so a Redis-based queue can be added later.
- C-02: Prompt folder layout has top-level `agents/`, `providers/`, `workers/`, `media_engine/`. Proposed layout places these as sub-packages of one Python package under `apps/api/studio/` (single install, shared models/config, no path hacks). Logical boundaries are identical.

## 7. Risks and limitations

- R-01: 4 GB VRAM — local image/video diffusion (SDXL, video models) is impractical at production quality; local LLMs limited to small quantised models. Cloud is required for image/video generation initially.
- R-02: Marathi TTS quality varies strongly between providers; local Marathi TTS options limited → must be evaluated with real samples.
- R-03: AI video providers differ in duration (often 5–10 s clips), aspect ratios, cost and async behaviour; APIs change frequently. All provider facts must be re-verified at integration time.
- R-04: Disk space: only ~34 GB free; video assets grow fast → retention + temp cleanup policies needed.
- R-05: Docker Desktop currently broken on this machine (blocks Postgres).
- R-06: Fact-sensitive topics (e.g. CIDCO / government / real estate) need sources; without a search API the Research agent can only work from supplied material.

## 8. Future requirements

Auto-publishing via official platform APIs; multi-user auth and project isolation; S3-compatible storage; local LLM/TTS/ASR (Phase 6).

## 9. Explicitly excluded (current scope)

Kubernetes, Kafka, microservices split; unofficial social-media upload automation; executing AI-generated code or shell commands.
