// Mirrors the Pydantic response models in apps/api/studio/schemas.

export type Language = "mr" | "hi" | "en";
export type Platform = "instagram_reels" | "youtube_shorts";
export type ProjectStatus =
  | "draft" | "planning" | "generating" | "rendering" | "review" | "completed" | "failed";
export type JobStatus =
  | "queued" | "running" | "awaiting_retry" | "succeeded" | "failed" | "cancelled";
export type ValidationStatus = "pending" | "valid" | "invalid";

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface VoiceSettings {
  voice_id?: string | null;
  gender?: string | null;
  speaking_rate: number;
  tone?: string | null;
  accent?: string | null;
  pronunciation_notes?: string | null;
}

export interface CaptionSettings {
  burn_in: boolean;
  export_srt: boolean;
  max_chars_per_line: number;
  position: "top" | "center" | "bottom";
}

export interface Branding {
  brand_name?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  logo_asset_id?: string | null;
  cta_text?: string | null;
}

export interface ProviderPreferences {
  llm?: string | null;
  image?: string | null;
  video?: string | null;
  tts?: string | null;
  prefer_local: boolean;
}

export interface ProjectSummary {
  id: string;
  name: string;
  topic: string;
  language: Language;
  platform: Platform;
  target_duration_sec: number;
  style: string;
  status: ProjectStatus;
  archived_at: string | null;
  current_revision: number;
  created_at: string;
  updated_at: string;
}

export interface Project extends ProjectSummary {
  description: string | null;
  target_audience: string | null;
  visual_method: string;
  aspect_ratio: string;
  export_preset: string;
  width: number;
  height: number;
  fps: number;
  voiceover_enabled: boolean;
  captions_enabled: boolean;
  voice_settings: VoiceSettings;
  caption_settings: CaptionSettings;
  branding: Branding;
  provider_preferences: ProviderPreferences;
}

export interface ProjectRevision {
  id: string;
  revision: number;
  snapshot: Record<string, unknown>;
  change_summary: string | null;
  created_at: string;
}

export interface MediaInfo {
  family?: string;
  duration_sec?: number | null;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  video_codec?: string | null;
  audio_codec?: string | null;
  sample_rate?: number | null;
  channels?: number | null;
  format_name?: string | null;
}

export interface AssetVersion {
  id: string;
  version: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  validation_status: ValidationStatus;
  validation_error: string | null;
  media_info: MediaInfo;
  provenance: Record<string, unknown>;
  created_at: string;
}

export interface Asset {
  id: string;
  project_id: string;
  kind: string;
  name: string;
  origin: string;
  license_note: string | null;
  scene_id: string | null;
  current_version: number;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  latest: AssetVersion | null;
  versions?: AssetVersion[];
}

export interface JobEvent {
  id: number;
  from_status: string | null;
  to_status: string;
  message: string | null;
  data: Record<string, unknown>;
  created_at: string;
}

export interface Job {
  id: string;
  type: string;
  status: JobStatus;
  project_id: string | null;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_category: string | null;
  error_message: string | null;
  attempts: number;
  max_attempts: number;
  priority: number;
  run_after: string;
  locked_by: string | null;
  lease_expires_at: string | null;
  cancel_requested: boolean;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  updated_at: string;
  events?: JobEvent[];
}

export interface HealthCheck {
  ok: boolean;
  severity: "ok" | "warning" | "error";
  detail: unknown;
}

export interface Readiness {
  ready: boolean;
  checks: Record<string, HealthCheck>;
}

export interface Overview {
  projects: { active: number; archived: number };
  assets: { active: number; invalid_versions: number; stored_bytes: number };
  jobs: Record<JobStatus, number>;
  recent_activity: {
    id: number;
    entity_type: string;
    entity_id: string;
    action: string;
    details: Record<string, unknown>;
    created_at: string;
  }[];
}

export interface ExportPreset {
  key: string;
  label: string;
  aspect_ratio: string;
  width: number;
  height: number;
  fps: number;
}

export interface Options {
  languages: { value: Language; label: string }[];
  platforms: Platform[];
  styles: string[];
  visual_methods: string[];
  project_statuses: ProjectStatus[];
  job_statuses: JobStatus[];
  asset_kinds: string[];
  asset_extensions: Record<string, string[]>;
  export_presets: ExportPreset[];
  default_preset_by_platform: Record<Platform, string>;
}
