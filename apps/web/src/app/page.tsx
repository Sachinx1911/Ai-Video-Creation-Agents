"use client";

import Link from "next/link";

import { Empty, ErrorBox, LinkButton, Loading, PageHeader, Panel, Stat, StatusBadge } from "@/components/ui";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { bytes, label, relative } from "@/lib/format";

export default function OverviewPage() {
  const overview = useApi(() => api.overview(), [], 5000);
  const projects = useApi(() => api.listProjects({ limit: 6 }), [], 10000);
  const health = useApi(() => api.readiness(), [], 10000);
  const o = overview.data;

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle="Live status of projects, assets and background jobs"
        actions={<LinkButton href="/projects/new" variant="primary">New video project</LinkButton>}
      />
      <ErrorBox error={overview.error} onRetry={overview.reload} />

      {o && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
          <Stat label="Active projects" value={o.projects.active} hint={`${o.projects.archived} archived`} />
          <Stat label="Assets" value={o.assets.active} hint={bytes(o.assets.stored_bytes) + " stored"} />
          <Stat label="Invalid asset versions" value={o.assets.invalid_versions} tone={o.assets.invalid_versions ? "warn" : undefined} />
          <Stat label="Running jobs" value={o.jobs.running} hint={`${o.jobs.queued} queued · ${o.jobs.awaiting_retry} retrying`} />
          <Stat label="Failed jobs" value={o.jobs.failed} tone={o.jobs.failed ? "bad" : undefined} />
          <Stat label="Completed jobs" value={o.jobs.succeeded} />
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Panel title="Recent projects" className="lg:col-span-2" actions={<Link href="/projects" className="text-xs text-sky-400 hover:underline">All projects</Link>}>
          {projects.loading && !projects.data ? <Loading /> : projects.data?.items.length ? (
            <ul className="divide-y divide-zinc-800">
              {projects.data.items.map((p) => (
                <li key={p.id}>
                  <Link href={`/projects/${p.id}`} className="flex items-center justify-between gap-4 py-2.5 hover:bg-zinc-900/50">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-zinc-100">{p.name}</div>
                      <div className="truncate text-xs text-zinc-500">
                        {label(p.language)} · {label(p.platform)} · {p.target_duration_sec}s · updated {relative(p.updated_at)}
                      </div>
                    </div>
                    <StatusBadge status={p.status} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>No projects yet. <Link className="text-sky-400 hover:underline" href="/projects/new">Create the first one</Link>.</Empty>
          )}
        </Panel>

        <Panel title="System health" actions={<Link href="/system" className="text-xs text-sky-400 hover:underline">Details</Link>}>
          <ErrorBox error={health.error} />
          {health.data && (
            <ul className="space-y-2 text-sm">
              {Object.entries(health.data.checks).map(([name, c]) => (
                <li key={name} className="flex items-center justify-between">
                  <span className="text-zinc-300">{label(name)}</span>
                  <StatusBadge status={c.severity} />
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel title="Recent activity" className="mt-6">
        {o?.recent_activity.length ? (
          <ul className="space-y-1.5 text-sm">
            {o.recent_activity.map((a) => (
              <li key={a.id} className="flex justify-between gap-4">
                <span className="text-zinc-300">
                  <span className="text-zinc-500">{a.entity_type}</span> {a.action}
                  {typeof a.details?.name === "string" && <span className="text-zinc-400"> · {a.details.name}</span>}
                  {Array.isArray(a.details?.fields) && <span className="text-zinc-500"> · {(a.details.fields as string[]).join(", ")}</span>}
                </span>
                <span className="shrink-0 text-xs text-zinc-500">{relative(a.created_at)}</span>
              </li>
            ))}
          </ul>
        ) : o ? <Empty>No activity recorded yet.</Empty> : <Loading />}
      </Panel>
    </>
  );
}
