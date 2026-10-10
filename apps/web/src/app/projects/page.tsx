"use client";

import Link from "next/link";
import { useState } from "react";

import { Button, Empty, ErrorBox, LinkButton, Loading, PageHeader, StatusBadge, inputClass } from "@/components/ui";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { label, relative } from "@/lib/format";

export default function ProjectsPage() {
  const [q, setQ] = useState("");
  const [archived, setArchived] = useState(false);
  const list = useApi(() => api.listProjects({ q, archived, limit: 200 }), [q, archived]);

  return (
    <>
      <PageHeader
        title="Projects"
        subtitle={list.data ? `${list.data.total} ${archived ? "archived" : "active"} project(s)` : undefined}
        actions={<LinkButton href="/projects/new" variant="primary">New video project</LinkButton>}
      />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          className={inputClass + " max-w-xs"}
          placeholder="Search name or topic"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search projects"
        />
        <div className="flex rounded-md border border-zinc-700 p-0.5">
          <Button variant={archived ? "ghost" : "secondary"} onClick={() => setArchived(false)}>Active</Button>
          <Button variant={archived ? "secondary" : "ghost"} onClick={() => setArchived(true)}>Archived</Button>
        </div>
      </div>
      <ErrorBox error={list.error} onRetry={list.reload} />
      {list.loading && !list.data ? <Loading /> : list.data?.items.length ? (
        <div className="overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-left text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Language</th>
                <th className="px-4 py-2 font-medium">Platform</th>
                <th className="px-4 py-2 font-medium">Duration</th>
                <th className="px-4 py-2 font-medium">Style</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {list.data.items.map((p) => (
                <tr key={p.id} className="hover:bg-zinc-900/50">
                  <td className="max-w-xs px-4 py-2.5">
                    <Link href={`/projects/${p.id}`} className="block truncate font-medium text-zinc-100 hover:text-sky-300">{p.name}</Link>
                    <div className="truncate text-xs text-zinc-500">{p.topic}</div>
                  </td>
                  <td className="px-4 py-2.5 text-zinc-300">{label(p.language)}</td>
                  <td className="px-4 py-2.5 text-zinc-300">{label(p.platform)}</td>
                  <td className="px-4 py-2.5 tabular-nums text-zinc-300">{p.target_duration_sec}s</td>
                  <td className="px-4 py-2.5 text-zinc-300">{label(p.style)}</td>
                  <td className="px-4 py-2.5"><StatusBadge status={p.archived_at ? "archived" : p.status} /></td>
                  <td className="px-4 py-2.5 text-xs text-zinc-500">{relative(p.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty>{q ? "No projects match your search." : archived ? "No archived projects." : "No projects yet."}</Empty>
      )}
    </>
  );
}
