"use client";

import { useState, type FormEvent } from "react";

import { Button, ErrorBox, Field, Panel, inputClass } from "@/components/ui";
import { ApiError } from "@/lib/api";
import { label } from "@/lib/format";
import type { Options, Project } from "@/lib/types";

export interface ProjectFormValues {
  name: string;
  description: string;
  topic: string;
  target_audience: string;
  language: string;
  platform: string;
  target_duration_sec: number;
  style: string;
  visual_method: string;
  export_preset: string;
  fps: number;
  voiceover_enabled: boolean;
  captions_enabled: boolean;
  speaking_rate: number;
  tone: string;
  pronunciation_notes: string;
  caption_burn_in: boolean;
  caption_export_srt: boolean;
  caption_position: "top" | "center" | "bottom";
  brand_name: string;
  primary_color: string;
  cta_text: string;
  prefer_local: boolean;
}

export function defaultsFrom(options: Options, project?: Project): ProjectFormValues {
  if (project) {
    return {
      name: project.name,
      description: project.description ?? "",
      topic: project.topic,
      target_audience: project.target_audience ?? "",
      language: project.language,
      platform: project.platform,
      target_duration_sec: project.target_duration_sec,
      style: project.style,
      visual_method: project.visual_method,
      export_preset: project.export_preset,
      fps: project.fps,
      voiceover_enabled: project.voiceover_enabled,
      captions_enabled: project.captions_enabled,
      speaking_rate: project.voice_settings.speaking_rate ?? 1,
      tone: project.voice_settings.tone ?? "",
      pronunciation_notes: project.voice_settings.pronunciation_notes ?? "",
      caption_burn_in: project.caption_settings.burn_in ?? true,
      caption_export_srt: project.caption_settings.export_srt ?? true,
      caption_position: project.caption_settings.position ?? "bottom",
      brand_name: project.branding.brand_name ?? "",
      primary_color: project.branding.primary_color ?? "",
      cta_text: project.branding.cta_text ?? "",
      prefer_local: project.provider_preferences.prefer_local ?? false,
    };
  }
  const preset = options.export_presets.find((p) => p.key === options.default_preset_by_platform.instagram_reels);
  return {
    name: "",
    description: "",
    topic: "",
    target_audience: "",
    language: "mr",
    platform: "instagram_reels",
    target_duration_sec: 45,
    style: "cinematic_documentary",
    visual_method: "ai_images_and_video",
    export_preset: preset?.key ?? options.export_presets[0].key,
    fps: preset?.fps ?? 30,
    voiceover_enabled: true,
    captions_enabled: true,
    speaking_rate: 1,
    tone: "",
    pronunciation_notes: "",
    caption_burn_in: true,
    caption_export_srt: true,
    caption_position: "bottom",
    brand_name: "",
    primary_color: "",
    cta_text: "",
    prefer_local: false,
  };
}

const nullIfEmpty = (s: string) => (s.trim() === "" ? null : s.trim());

export function toPayload(v: ProjectFormValues, project?: Project) {
  return {
    name: v.name,
    description: nullIfEmpty(v.description),
    topic: v.topic,
    target_audience: nullIfEmpty(v.target_audience),
    language: v.language,
    platform: v.platform,
    target_duration_sec: Number(v.target_duration_sec),
    style: v.style,
    visual_method: v.visual_method,
    export_preset: v.export_preset,
    fps: Number(v.fps),
    voiceover_enabled: v.voiceover_enabled,
    captions_enabled: v.captions_enabled,
    voice_settings: {
      ...(project?.voice_settings ?? {}),
      speaking_rate: Number(v.speaking_rate),
      tone: nullIfEmpty(v.tone),
      pronunciation_notes: nullIfEmpty(v.pronunciation_notes),
    },
    caption_settings: {
      ...(project?.caption_settings ?? {}),
      burn_in: v.caption_burn_in,
      export_srt: v.caption_export_srt,
      position: v.caption_position,
    },
    branding: {
      ...(project?.branding ?? {}),
      brand_name: nullIfEmpty(v.brand_name),
      primary_color: nullIfEmpty(v.primary_color),
      cta_text: nullIfEmpty(v.cta_text),
    },
    provider_preferences: { ...(project?.provider_preferences ?? {}), prefer_local: v.prefer_local },
  };
}

function Select({ value, onChange, options, ...rest }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; "aria-label"?: string }) {
  return (
    <select className={inputClass} value={value} onChange={(e) => onChange(e.target.value)} {...rest}>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Check({ checked, onChange, children }: { checked: boolean; onChange: (v: boolean) => void; children: string }) {
  return (
    <label className="flex items-center gap-2 text-sm text-zinc-300">
      <input type="checkbox" className="h-4 w-4 accent-sky-500" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {children}
    </label>
  );
}

export function ProjectForm({
  options,
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  options: Options;
  initial: ProjectFormValues;
  submitLabel: string;
  onSubmit: (v: ProjectFormValues) => Promise<void>;
  onCancel?: () => void;
}) {
  const [v, setV] = useState(initial);
  const [error, setError] = useState<ApiError>();
  const [saving, setSaving] = useState(false);
  const set = <K extends keyof ProjectFormValues>(k: K, val: ProjectFormValues[K]) => setV((s) => ({ ...s, [k]: val }));
  const fe = (field: string) => error?.fieldErrors[field];

  const onPreset = (key: string) => {
    const p = options.export_presets.find((x) => x.key === key);
    setV((s) => ({ ...s, export_preset: key, fps: p?.fps ?? s.fps }));
  };

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(undefined);
    try {
      await onSubmit(v);
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError(0, String(err)));
    } finally {
      setSaving(false);
    }
  }

  const opts = (values: string[]) => values.map((x) => ({ value: x, label: label(x) }));

  return (
    <form onSubmit={submit} className="space-y-5">
      <ErrorBox error={error} />
      <Panel title="Brief">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Project name *" error={fe("name")}>
            <input className={inputClass} required maxLength={200} value={v.name} onChange={(e) => set("name", e.target.value)} />
          </Field>
          <Field label="Target audience" error={fe("target_audience")}>
            <input className={inputClass} maxLength={300} value={v.target_audience} onChange={(e) => set("target_audience", e.target.value)} placeholder="e.g. first-time home buyers in Navi Mumbai" />
          </Field>
          <div className="md:col-span-2">
            <Field label="Topic / content brief *" error={fe("topic")} hint="What should the video communicate? Facts will be research-checked in Phase 2.">
              <textarea className={inputClass + " min-h-24"} required minLength={3} maxLength={5000} value={v.topic} onChange={(e) => set("topic", e.target.value)} />
            </Field>
          </div>
          <div className="md:col-span-2">
            <Field label="Description" error={fe("description")}>
              <textarea className={inputClass + " min-h-16"} maxLength={5000} value={v.description} onChange={(e) => set("description", e.target.value)} />
            </Field>
          </div>
        </div>
      </Panel>

      <Panel title="Format">
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Language" error={fe("language")}>
            <Select value={v.language} onChange={(x) => set("language", x)} options={options.languages.map((l) => ({ value: l.value, label: l.label }))} />
          </Field>
          <Field label="Platform" error={fe("platform")}>
            <Select value={v.platform} onChange={(x) => set("platform", x)} options={opts(options.platforms)} />
          </Field>
          <Field label="Target duration (seconds)" error={fe("target_duration_sec")} hint="5–180 s">
            <input className={inputClass} type="number" min={5} max={180} required value={v.target_duration_sec} onChange={(e) => set("target_duration_sec", Number(e.target.value))} />
          </Field>
          <Field label="Style" error={fe("style")}>
            <Select value={v.style} onChange={(x) => set("style", x)} options={opts(options.styles)} />
          </Field>
          <Field label="Visual generation" error={fe("visual_method")}>
            <Select value={v.visual_method} onChange={(x) => set("visual_method", x)} options={opts(options.visual_methods)} />
          </Field>
          <Field label="Export preset" error={fe("export_preset")}>
            <Select value={v.export_preset} onChange={onPreset} options={options.export_presets.map((p) => ({ value: p.key, label: p.label }))} />
          </Field>
          <Field label="Frame rate" error={fe("fps")}>
            <input className={inputClass} type="number" min={1} max={120} value={v.fps} onChange={(e) => set("fps", Number(e.target.value))} />
          </Field>
        </div>
      </Panel>

      <div className="grid gap-5 md:grid-cols-2">
        <Panel title="Voice-over">
          <div className="space-y-3">
            <Check checked={v.voiceover_enabled} onChange={(x) => set("voiceover_enabled", x)}>Voice-over enabled</Check>
            <Field label="Speaking rate" error={fe("voice_settings.speaking_rate")} hint="0.5 – 2.0 (1.0 = normal)">
              <input className={inputClass} type="number" step={0.05} min={0.5} max={2} value={v.speaking_rate} onChange={(e) => set("speaking_rate", Number(e.target.value))} />
            </Field>
            <Field label="Tone / delivery" error={fe("voice_settings.tone")}>
              <input className={inputClass} maxLength={100} value={v.tone} onChange={(e) => set("tone", e.target.value)} placeholder="e.g. calm, authoritative" />
            </Field>
            <Field label="Pronunciation notes" error={fe("voice_settings.pronunciation_notes")}>
              <textarea className={inputClass} maxLength={2000} value={v.pronunciation_notes} onChange={(e) => set("pronunciation_notes", e.target.value)} />
            </Field>
          </div>
        </Panel>
        <Panel title="Captions & branding">
          <div className="space-y-3">
            <Check checked={v.captions_enabled} onChange={(x) => set("captions_enabled", x)}>Captions enabled</Check>
            <Check checked={v.caption_burn_in} onChange={(x) => set("caption_burn_in", x)}>Burn captions into video</Check>
            <Check checked={v.caption_export_srt} onChange={(x) => set("caption_export_srt", x)}>Export SRT file</Check>
            <Field label="Caption position">
              <Select value={v.caption_position} onChange={(x) => set("caption_position", x as ProjectFormValues["caption_position"])} options={opts(["top", "center", "bottom"])} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Brand name" error={fe("branding.brand_name")}>
                <input className={inputClass} maxLength={200} value={v.brand_name} onChange={(e) => set("brand_name", e.target.value)} />
              </Field>
              <Field label="Primary colour" error={fe("branding.primary_color")} hint="#RRGGBB">
                <input className={inputClass} pattern="#[0-9A-Fa-f]{6}" value={v.primary_color} onChange={(e) => set("primary_color", e.target.value)} placeholder="#0EA5E9" />
              </Field>
            </div>
            <Field label="Call to action text" error={fe("branding.cta_text")}>
              <input className={inputClass} maxLength={300} value={v.cta_text} onChange={(e) => set("cta_text", e.target.value)} />
            </Field>
            <Check checked={v.prefer_local} onChange={(x) => set("prefer_local", x)}>Prefer local AI where available (applies from Phase 3)</Check>
          </div>
        </Panel>
      </div>

      <div className="flex justify-end gap-2">
        {onCancel && <Button onClick={onCancel}>Cancel</Button>}
        <Button type="submit" variant="primary" disabled={saving}>{saving ? "Saving…" : submitLabel}</Button>
      </div>
    </form>
  );
}
