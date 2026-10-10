"use client";

import { api } from "@/lib/api";
import type { Asset } from "@/lib/types";

/** Inline preview served by the API (only for validated media). */
export function AssetPreview({ asset, className = "" }: { asset: Asset; className?: string }) {
  const v = asset.latest;
  if (!v) return null;
  const url = api.assetFileUrl(asset.id, v.version);
  const family = v.media_info.family;
  if (v.validation_status !== "valid") {
    return <div className={`flex items-center justify-center bg-zinc-950 text-xs text-zinc-600 ${className}`}>{v.validation_status === "pending" ? "Validating…" : "No preview"}</div>;
  }
  if (family === "image") {
    // eslint-disable-next-line @next/next/no-img-element -- served by the local API, not optimisable
    return <img src={url} alt={asset.name} className={`bg-zinc-950 object-contain ${className}`} loading="lazy" />;
  }
  if (family === "video") {
    return <video src={url} controls preload="metadata" className={`bg-black ${className}`} />;
  }
  if (family === "audio") {
    return (
      <div className={`flex items-center bg-zinc-950 p-2 ${className}`}>
        <audio src={url} controls preload="none" className="w-full" />
      </div>
    );
  }
  return <div className={`flex items-center justify-center bg-zinc-950 text-xs uppercase text-zinc-500 ${className}`}>{family ?? asset.kind}</div>;
}
