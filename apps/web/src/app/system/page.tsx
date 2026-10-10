"use client";

import { ErrorBox, Loading, PageHeader, Panel, StatusBadge } from "@/components/ui";
import { useApi } from "@/hooks/use-api";
import { API_URL, api } from "@/lib/api";
import { label } from "@/lib/format";

const HINTS: Record<string, string> = {
  database: "Start PostgreSQL: docker compose up -d db (or python scripts/dev_db.py start)",
  migrations: "Run: alembic upgrade head (in apps/api)",
  ffmpeg: "Install FFmpeg and put it on PATH, or set STUDIO_FFMPEG_BIN",
  ffprobe: "Install FFmpeg (includes ffprobe) or set STUDIO_FFPROBE_BIN",
  storage: "Check STUDIO_STORAGE_ROOT exists and is writable",
  disk_space: "Free disk space or raise STUDIO_MIN_FREE_DISK_GB",
  worker: "Start a worker: python -m studio.workers.runner (in apps/api)",
};

function Detail({ value }: { value: unknown }) {
  if (typeof value === "string") return <span>{value}</span>;
  return <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-400">{JSON.stringify(value, null, 2)}</pre>;
}

export default function SystemPage() {
  const health = useApi(() => api.readiness(), [], 5000);
  const h = health.data;

  return (
    <>
      <PageHeader
        title="System Health"
        subtitle={<>Readiness checks from <code className="text-zinc-300">{API_URL}/health/ready</code>, refreshed every 5 s</>}
        actions={h && <StatusBadge status={h.ready ? "ok" : "error"} />}
      />
      <ErrorBox error={health.error} onRetry={health.reload} />
      {!h && !health.error && <Loading />}
      {h && (
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(h.checks).map(([name, c]) => (
            <Panel key={name} title={label(name)} actions={<StatusBadge status={c.severity} />}>
              <div className="text-sm text-zinc-300"><Detail value={c.detail} /></div>
              {!c.ok && HINTS[name] && <div className="mt-2 text-xs text-amber-300">{HINTS[name]}</div>}
            </Panel>
          ))}
        </div>
      )}
    </>
  );
}
