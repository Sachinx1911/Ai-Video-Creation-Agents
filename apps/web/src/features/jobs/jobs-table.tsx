"use client";

import Link from "next/link";
import { Fragment, useState } from "react";

import { Button, Empty, ErrorBox, StatusBadge } from "@/components/ui";
import { useApi } from "@/hooks/use-api";
import { ApiError, api } from "@/lib/api";
import { dateTime, label, relative, shortId } from "@/lib/format";
import type { Job } from "@/lib/types";

function JobEvents({ id }: { id: string }) {
  const job = useApi(() => api.getJob(id), [id], 3000);
  if (job.error) return <ErrorBox error={job.error} />;
  if (!job.data) return <div className="text-xs text-zinc-500">Loading events…</div>;
  const j = job.data;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <div className="mb-1 text-xs font-medium text-zinc-400">Events</div>
        <ol className="space-y-1 text-xs">
          {j.events?.map((e) => (
            <li key={e.id} className="flex gap-2">
              <span className="w-36 shrink-0 text-zinc-500">{dateTime(e.created_at)}</span>
              <span className="text-zinc-300">{e.from_status ?? "∅"} → {e.to_status}</span>
              {e.message && <span className="truncate text-zinc-500">· {e.message}</span>}
            </li>
          ))}
        </ol>
      </div>
      <div className="space-y-2 text-xs">
        <div>
          <div className="mb-1 font-medium text-zinc-400">Payload</div>
          <pre className="overflow-x-auto rounded bg-zinc-950 p-2 text-zinc-300">{JSON.stringify(j.payload, null, 2)}</pre>
        </div>
        {j.result && (
          <div>
            <div className="mb-1 font-medium text-zinc-400">Result</div>
            <pre className="overflow-x-auto rounded bg-zinc-950 p-2 text-zinc-300">{JSON.stringify(j.result, null, 2)}</pre>
          </div>
        )}
        {j.error_message && (
          <div className="rounded border border-red-900 bg-red-950/40 p-2 text-red-200">
            <span className="font-medium">{label(j.error_category)}:</span> {j.error_message}
          </div>
        )}
      </div>
    </div>
  );
}

export function JobsTable({ jobs, onChanged, showProject = false }: { jobs: Job[]; onChanged: () => void; showProject?: boolean }) {
  const [open, setOpen] = useState<string>();
  const [busy, setBusy] = useState<string>();
  const [error, setError] = useState<ApiError>();

  async function act(id: string, fn: (id: string) => Promise<unknown>) {
    setBusy(id);
    setError(undefined);
    try {
      await fn(id);
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      setBusy(undefined);
    }
  }

  if (!jobs.length) return <Empty>No jobs.</Empty>;
  return (
    <div className="space-y-3">
      <ErrorBox error={error} />
      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-left text-xs uppercase tracking-wide text-zinc-500">
            <tr>
              <th className="px-3 py-2 font-medium">Job</th>
              <th className="px-3 py-2 font-medium">Type</th>
              {showProject && <th className="px-3 py-2 font-medium">Project</th>}
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Attempts</th>
              <th className="px-3 py-2 font-medium">Created</th>
              <th className="px-3 py-2 font-medium">Error</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {jobs.map((j) => {
              const cancellable = ["queued", "awaiting_retry", "running"].includes(j.status) && !j.cancel_requested;
              const retryable = j.status === "failed" || j.status === "cancelled";
              return (
                <Fragment key={j.id}>
                  <tr className="hover:bg-zinc-900/50">
                    <td className="px-3 py-2 font-mono text-xs">
                      <button type="button" className="text-sky-400 hover:underline" onClick={() => setOpen(open === j.id ? undefined : j.id)}>
                        {open === j.id ? "▾" : "▸"} {shortId(j.id)}
                      </button>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-zinc-300">{j.type}</td>
                    {showProject && (
                      <td className="px-3 py-2 font-mono text-xs">
                        {j.project_id ? <Link className="text-sky-400 hover:underline" href={`/projects/${j.project_id}`}>{shortId(j.project_id)}</Link> : "—"}
                      </td>
                    )}
                    <td className="px-3 py-2">
                      <StatusBadge status={j.status} />
                      {j.cancel_requested && j.status === "running" && <span className="ml-2 text-xs text-amber-300">cancelling</span>}
                    </td>
                    <td className="px-3 py-2 tabular-nums text-zinc-300">{j.attempts}/{j.max_attempts}</td>
                    <td className="px-3 py-2 text-xs text-zinc-500">{relative(j.created_at)}</td>
                    <td className="max-w-xs truncate px-3 py-2 text-xs text-red-300" title={j.error_message ?? ""}>{j.error_message ?? ""}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-right">
                      {cancellable && <Button variant="ghost" disabled={busy === j.id} onClick={() => act(j.id, api.cancelJob)}>Cancel</Button>}
                      {retryable && <Button variant="ghost" disabled={busy === j.id} onClick={() => act(j.id, api.retryJob)}>Retry</Button>}
                    </td>
                  </tr>
                  {open === j.id && (
                    <tr>
                      <td colSpan={showProject ? 8 : 7} className="bg-zinc-900/40 px-4 py-3">
                        <JobEvents id={j.id} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
