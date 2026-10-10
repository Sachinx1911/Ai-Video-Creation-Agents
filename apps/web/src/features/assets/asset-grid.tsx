"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { Button, Empty, ErrorBox, StatusBadge } from "@/components/ui";
import { AssetPreview } from "@/features/assets/asset-preview";
import { ApiError, api } from "@/lib/api";
import { bytes, duration, label, relative, shortId } from "@/lib/format";
import type { Asset } from "@/lib/types";

function AssetCard({ asset, onChanged, showProject }: { asset: Asset; onChanged: () => void; showProject: boolean }) {
  const v = asset.latest;
  const mi = v?.media_info ?? {};
  const fileInput = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError>();

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(undefined);
    try {
      await fn();
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/60">
      <AssetPreview asset={asset} className="aspect-video w-full" />
      <div className="flex flex-1 flex-col gap-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-zinc-100" title={asset.name}>{asset.name}</div>
            <div className="text-xs text-zinc-500">
              {label(asset.kind)} · v{asset.current_version}
              {showProject && <> · <Link className="text-sky-400 hover:underline" href={`/projects/${asset.project_id}`}>project {shortId(asset.project_id)}</Link></>}
            </div>
          </div>
          {v && <StatusBadge status={v.validation_status} />}
        </div>
        {v && (
          <div className="text-xs text-zinc-400">
            {[
              mi.width && mi.height ? `${mi.width}×${mi.height}` : null,
              mi.duration_sec ? duration(mi.duration_sec) : null,
              mi.fps ? `${mi.fps} fps` : null,
              mi.video_codec, mi.audio_codec, bytes(v.size_bytes),
            ].filter(Boolean).join(" · ")}
          </div>
        )}
        {v?.validation_error && <div className="text-xs text-red-300">{v.validation_error}</div>}
        {asset.license_note && <div className="text-xs text-zinc-500">License: {asset.license_note}</div>}
        <div className="text-xs text-zinc-600">sha256 {v?.sha256.slice(0, 12)}… · {relative(asset.created_at)}</div>
        <ErrorBox error={error} />
        <div className="mt-auto flex flex-wrap gap-1 pt-1">
          {v && <a className="rounded-md px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800" href={api.assetFileUrl(asset.id, v.version, true)}>Download</a>}
          {!asset.archived_at && (
            <>
              <input
                ref={fileInput}
                type="file"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  e.target.value = "";
                  if (!f) return;
                  const fd = new FormData();
                  fd.append("file", f);
                  void run(() => api.addAssetVersion(asset.id, fd));
                }}
              />
              <Button variant="ghost" className="text-xs" disabled={busy} onClick={() => fileInput.current?.click()}>New version</Button>
            </>
          )}
          {asset.archived_at ? (
            <Button variant="ghost" className="text-xs" disabled={busy} onClick={() => run(() => api.restoreAsset(asset.id))}>Restore</Button>
          ) : (
            <Button variant="ghost" className="text-xs" disabled={busy} onClick={() => run(() => api.archiveAsset(asset.id))}>Archive</Button>
          )}
        </div>
      </div>
    </div>
  );
}

export function AssetGrid({ assets, onChanged, showProject = false }: { assets: Asset[]; onChanged: () => void; showProject?: boolean }) {
  if (!assets.length) return <Empty>No assets.</Empty>;
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {assets.map((a) => <AssetCard key={a.id} asset={a} onChanged={onChanged} showProject={showProject} />)}
    </div>
  );
}
