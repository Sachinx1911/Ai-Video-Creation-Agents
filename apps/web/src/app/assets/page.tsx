"use client";

import { useState } from "react";

import { ErrorBox, Loading, PageHeader, inputClass } from "@/components/ui";
import { AssetGrid } from "@/features/assets/asset-grid";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { label } from "@/lib/format";

export default function AssetLibraryPage() {
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [archived, setArchived] = useState(false);
  const options = useApi(() => api.options());
  const assets = useApi(() => api.listAssets({ kind: kind || undefined, q, include_archived: archived }), [kind, q, archived], 5000);

  return (
    <>
      <PageHeader title="Asset Library" subtitle={assets.data ? `${assets.data.total} asset(s) across all projects` : undefined} />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input className={inputClass + " max-w-xs"} placeholder="Search by name" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search assets" />
        <select className={inputClass + " max-w-48"} value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Filter by kind">
          <option value="">All kinds</option>
          {options.data?.asset_kinds.map((k) => <option key={k} value={k}>{label(k)}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm text-zinc-400">
          <input type="checkbox" className="accent-sky-500" checked={archived} onChange={(e) => setArchived(e.target.checked)} /> Include archived
        </label>
      </div>
      <p className="mb-4 text-xs text-zinc-500">Upload assets from a project&apos;s Assets tab so every file belongs to a project.</p>
      <ErrorBox error={assets.error} onRetry={assets.reload} />
      {assets.data ? <AssetGrid assets={assets.data.items} onChanged={assets.reload} showProject /> : <Loading />}
    </>
  );
}
