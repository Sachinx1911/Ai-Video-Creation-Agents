# Database Schema

PostgreSQL 16 (Docker). Migrations: Alembic in `apps/api/migrations`. Enums stored as `VARCHAR` + `CHECK` (ADR-0004). All timestamps `timestamptz` UTC. Primary keys UUID v4 unless noted.

## Phase 1 tables (implemented in migration `0001_foundation`)

### projects
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| name | varchar(200) not null | |
| description | text | |
| topic | text not null | content brief |
| target_audience | varchar(300) | |
| language | enum `mr,hi,en` | extensible |
| platform | enum `instagram_reels,youtube_shorts` | |
| target_duration_sec | int, CHECK 5–180 | |
| style | enum `cinematic_documentary,photorealistic_commercial,educational_explainer,animation_3d` | |
| visual_method | enum `ai_images,ai_video,ai_images_and_video` | |
| aspect_ratio | varchar(8) | `9:16`, `1:1`, `16:9` |
| export_preset | varchar(64) | key into code-defined presets (Phase 1) |
| width, height, fps | int | resolved from preset, overridable |
| voiceover_enabled / captions_enabled | bool | |
| voice_settings, caption_settings, branding, provider_preferences | jsonb | flexible, schema-validated by Pydantic |
| status | enum `draft,planning,generating,rendering,review,completed,failed` | production stage |
| archived_at | timestamptz null | soft archive, independent of status |
| current_revision | int | |
| created_at, updated_at | timestamptz | |

Indexes: `(archived_at, updated_at desc)`, `status`.

### project_revisions — production history
`id`, `project_id` FK→projects (cascade), `revision` int, `snapshot` jsonb (full settings), `change_summary` text, `created_at`. Unique `(project_id, revision)`.

### assets
`id`, `project_id` FK, `kind` enum `image,video,voice,music,sfx,logo,font,reference_image,subtitle,final_export,other`, `name`, `origin` enum `upload,generated,rendered`, `license_note` text, `scene_id` uuid null (FK added in Phase 2), `current_version` int, `archived_at`, timestamps. Index `(project_id, kind)`.

### asset_versions
`id`, `asset_id` FK, `version` int, `storage_key` (relative path), `original_filename`, `mime_type`, `size_bytes` bigint, `sha256` char(64), `validation_status` enum `pending,valid,invalid`, `validation_error` text, `media_info` jsonb (ffprobe summary: duration, width, height, codecs, streams), `provenance` jsonb (uploader / provider + model + prompt hash), `created_at`. Unique `(asset_id, version)`; index `sha256`.

### jobs — persistent job records and queue (ADR-0002)
`id`, `type` varchar(64), `status` enum `queued,running,awaiting_retry,succeeded,failed,cancelled`, `project_id` FK null, `payload` jsonb, `result` jsonb, `error_category` enum `transient,rate_limited,provider_outage,invalid_request,auth,invalid_output,internal,cancelled,lease_expired` null, `error_message` text, `attempts`, `max_attempts`, `priority` (lower first), `run_after`, `locked_by`, `lease_expires_at`, `cancel_requested` bool, `idempotency_key` unique null, `provider_job_id` null, `created_at`, `started_at`, `finished_at`, `updated_at`.
Indexes: `(status, run_after, priority, created_at)`, `project_id`, `type`.

### job_events (append-only)
`id` bigserial, `job_id` FK, `from_status`, `to_status`, `message`, `data` jsonb, `created_at`. Index `(job_id, id)`.

### worker_heartbeats
`worker_id` varchar PK, `hostname`, `pid`, `job_types` jsonb, `started_at`, `last_seen_at`. Used by health checks; no fake "agent active" indicators.

### audit_logs (append-only)
`id` bigserial, `entity_type`, `entity_id`, `action`, `details` jsonb (never secrets), `created_at`. Index `(entity_type, entity_id)`.

## Planned tables (later phases — NOT implemented)

| Phase | Tables |
|---|---|
| 2 | `script_versions`, `research_briefs` (+ `sources`), `scenes`, `storyboards`, `style_bibles`, `prompts` |
| 3 | `providers`, `provider_capabilities`, `generation_jobs` (1:1 extension of `jobs` with cost, provider ids), `user_settings` |
| 4 | `timelines`, `timeline_clips`, `audio_tracks`, `subtitle_cues`, `export_presets`, `render_jobs`, `exports` |
| 5 | `workflow_runs`, `workflow_tasks` (DAG, checkpoints), `agent_definitions`, `agent_executions`, `qa_results` |
