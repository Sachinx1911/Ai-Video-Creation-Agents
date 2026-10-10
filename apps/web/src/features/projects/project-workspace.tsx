"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Empty, ErrorBox, KV, Loading, PageHeader, Panel, StatusBadge, cx } from "@/components/ui";
import { AssetGrid } from "@/features/assets/asset-grid";
import { AssetUpload } from "@/features/assets/asset-upload";
import { JobsTable } from "@/features/jobs/jobs-table";
import { ProjectForm, defaultsFrom, toPayload } from "@/features/projects/project-form";
import { useApi } from "@/hooks/use-api";
import { ApiError, api } from "@/lib/api";
import { dateTime, label } from "@/lib/format";
import type { Options, Project } from "@/lib/types";

const TABS = ["summary", "assets", "jobs", "history"] as const;
type Tab = (typeof TABS)[number];

export function ProjectWorkspace({ id }: { id: string }) {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("summary");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<ApiError>();
  const project = useApi(() => api.getProject(id), [id]);
  const options = useApi(() => api.options());
  const p = project.data;

  async function action(fn: () => Promise<Project>, navigate = false) {
    setBusy(true);
    setActionError(undefined);
    try {
      const result = await fn();
      if (navigate) router.push(`/projects/${result.id}`);
      else project.reload();
    } catch (e) {
      setActionError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      setBusy(false);
    }
  }

  if (project.error) return <ErrorBox error={project.error} onRetry={project.reload} />;
  if (!p) return <Loading />;
  const archived = p.archived_at !== null;

  return (
    <>
      <div className="mb-2 text-xs text-zinc-500"><Link href="/projects" className="hover:text-zinc-300">Projects</Link> / {p.name}</div>
      <PageHeader
        title={p.name}
        subtitle={<span className="flex flex-wrap items-center gap-2"><StatusBadge status={archived ? "archived" : p.status} /> revision {p.current_revision} · {label(p.language)} · {label(p.platform)} · {p.target_duration_sec}s · {p.width}×{p.height} @ {p.fps} fps</span>}
        actions={
          <>
            {!archived && !editing && <Button onClick={() => { setTab("summary"); setEditing(true); }}>Edit</Button>}
            <Button disabled={busy} onClick={() => action(() => api.duplicateProject(p.id), true)}>Duplicate</Button>
            {archived ? (
              <Button disabled={busy} onClick={() => action(() => api.restoreProject(p.id))}>Restore</Button>
            ) : (
              <Button variant="danger" disabled={busy} onClick={() => { if (confirm(`Archive "${p.name}"? It becomes read-only; nothing is deleted.`)) void action(() => api.archiveProject(p.id)); }}>Archive</Button>
            )}
          </>
        }
      />
      <ErrorBox error={actionError} />
      {archived && <div className="mb-4 rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-400">This project is archived and read-only. Restore it to make changes.</div>}

      <div className="mb-5 flex gap-1 border-b border-zinc-800">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cx("-mb-px border-b-2 px-3 py-2 text-sm capitalize", tab === t ? "border-sky-500 text-zinc-50" : "border-transparent text-zinc-400 hover:text-zinc-200")}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "summary" && (
        editing && options.data ? (
          <ProjectForm
            options={options.data}
            initial={defaultsFrom(options.data, p)}
            submitLabel="Save changes"
            onSubmit={async (v) => {
              await api.updateProject(p.id, toPayload(v, p));
              setEditing(false);
              project.reload();
            }}
            onCancel={() => setEditing(false)}
          />
        ) : <Summary project={p} />
      )}
      {tab === "assets" && options.data && <AssetsTab project={p} options={options.data} />}
      {tab === "jobs" && <JobsTab projectId={p.id} />}
      {tab === "history" && <HistoryTab projectId={p.id} revision={p.current_revision} />}
    </>
  );
}

function Summary({ project: p }: { project: Project }) {
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Panel title="Brief">
        <KV items={[
          ["Topic", <span key="t" className="whitespace-pre-wrap">{p.topic}</span>],
          ["Description", p.description ?? "—"],
          ["Audience", p.target_audience ?? "—"],
          ["Style", label(p.style)],
          ["Visuals", label(p.visual_method)],
        ]} />
      </Panel>
      <Panel title="Output">
        <KV items={[
          ["Platform", label(p.platform)],
          ["Duration", `${p.target_duration_sec} s`],
          ["Export preset", p.export_preset],
          ["Frame", `${p.width}×${p.height} (${p.aspect_ratio}) @ ${p.fps} fps`],
          ["Voice-over", p.voiceover_enabled ? `on · rate ${p.voice_settings.speaking_rate}${p.voice_settings.tone ? ` · ${p.voice_settings.tone}` : ""}` : "off"],
          ["Captions", p.captions_enabled ? `on · ${p.caption_settings.burn_in ? "burned-in" : "not burned"} · ${p.caption_settings.export_srt ? "SRT" : "no SRT"} · ${p.caption_settings.position}` : "off"],
          ["Branding", [p.branding.brand_name, p.branding.primary_color, p.branding.cta_text].filter(Boolean).join(" · ") || "—"],
          ["Created", dateTime(p.created_at)],
          ["Updated", dateTime(p.updated_at)],
        ]} />
      </Panel>
      <Panel title="Production pipeline" className="lg:col-span-2">
        <p className="text-sm text-zinc-400">
          Research, script, storyboard, generation and rendering are not implemented yet (Phases 2–5). This project currently stores the brief, its revision history and uploaded assets.
        </p>
      </Panel>
    </div>
  );
}

function AssetsTab({ project, options }: { project: Project; options: Options }) {
  const assets = useApi(() => api.listAssets({ project_id: project.id, include_archived: true }), [project.id], 4000);
  return (
    <div className="space-y-5">
      {!project.archived_at && (
        <Panel title="Upload asset">
          <AssetUpload projectId={project.id} options={options} onUploaded={assets.reload} />
        </Panel>
      )}
      <ErrorBox error={assets.error} onRetry={assets.reload} />
      {assets.data ? <AssetGrid assets={assets.data.items} onChanged={assets.reload} /> : <Loading />}
    </div>
  );
}

function JobsTab({ projectId }: { projectId: string }) {
  const jobs = useApi(() => api.listJobs({ project_id: projectId, limit: 100 }), [projectId], 3000);
  return (
    <>
      <ErrorBox error={jobs.error} onRetry={jobs.reload} />
      {jobs.data ? <JobsTable jobs={jobs.data.items} onChanged={jobs.reload} /> : <Loading />}
    </>
  );
}

function HistoryTab({ projectId, revision }: { projectId: string; revision: number }) {
  const revs = useApi(() => api.revisions(projectId), [projectId, revision]);
  if (revs.error) return <ErrorBox error={revs.error} onRetry={revs.reload} />;
  if (!revs.data) return <Loading />;
  if (!revs.data.length) return <Empty>No revisions.</Empty>;
  return (
    <ol className="space-y-2">
      {revs.data.map((r) => (
        <li key={r.id} className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-3">
          <details>
            <summary className="flex cursor-pointer items-center justify-between gap-4 text-sm">
              <span><span className="font-medium text-zinc-100">Revision {r.revision}</span> <span className="text-zinc-400">· {r.change_summary}</span></span>
              <span className="text-xs text-zinc-500">{dateTime(r.created_at)}</span>
            </summary>
            <pre className="mt-3 overflow-x-auto rounded bg-zinc-950 p-3 text-xs text-zinc-300">{JSON.stringify(r.snapshot, null, 2)}</pre>
          </details>
        </li>
      ))}
    </ol>
  );
}
