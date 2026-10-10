"use client";

import { useState, type FormEvent } from "react";

import { Button, ErrorBox, Field, inputClass } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { label } from "@/lib/format";
import type { Options } from "@/lib/types";

export function AssetUpload({ projectId, options, onUploaded }: { projectId: string; options: Options; onUploaded: () => void }) {
  const [kind, setKind] = useState("image");
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [license, setLicense] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError>();
  const [inputKey, setInputKey] = useState(0);
  const accept = (options.asset_extensions[kind] ?? []).join(",");

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("kind", kind);
    if (name.trim()) fd.append("name", name.trim());
    if (license.trim()) fd.append("license_note", license.trim());
    setBusy(true);
    setError(undefined);
    try {
      await api.uploadAsset(projectId, fd);
      setFile(null);
      setName("");
      setLicense("");
      setInputKey((k) => k + 1);
      onUploaded();
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError(0, String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <ErrorBox error={error} />
      <div className="grid gap-3 md:grid-cols-[10rem_1fr_1fr_1fr_auto] md:items-end">
        <Field label="Kind">
          <select className={inputClass} value={kind} onChange={(e) => setKind(e.target.value)}>
            {options.asset_kinds.map((k) => <option key={k} value={k}>{label(k)}</option>)}
          </select>
        </Field>
        <Field label="File" hint={accept.replaceAll(",", " ")}>
          <input key={inputKey} type="file" required accept={accept} className="block w-full text-sm text-zinc-400 file:mr-3 file:rounded-md file:border-0 file:bg-zinc-800 file:px-3 file:py-1.5 file:text-sm file:text-zinc-200" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </Field>
        <Field label="Display name">
          <input className={inputClass} maxLength={200} value={name} onChange={(e) => setName(e.target.value)} placeholder="defaults to file name" />
        </Field>
        <Field label="License / source">
          <input className={inputClass} maxLength={2000} value={license} onChange={(e) => setLicense(e.target.value)} placeholder="required for music & SFX" />
        </Field>
        <Button type="submit" variant="primary" disabled={!file || busy}>{busy ? "Uploading…" : "Upload"}</Button>
      </div>
      <p className="text-xs text-zinc-500">Files are hashed and stored under the project folder, then validated by the background worker with FFprobe.</p>
    </form>
  );
}
