"use client";

import { useState } from "react";

import { Button, ErrorBox, Loading, PageHeader } from "@/components/ui";
import { JobsTable } from "@/features/jobs/jobs-table";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { label } from "@/lib/format";

const FILTERS = ["", "queued", "running", "awaiting_retry", "failed", "succeeded", "cancelled"];

export default function JobsPage() {
  const [status, setStatus] = useState("");
  const jobs = useApi(() => api.listJobs({ status: status || undefined, limit: 200 }), [status], 3000);

  return (
    <>
      <PageHeader title="Jobs" subtitle="Background work recorded in PostgreSQL. Refreshes every 3 seconds." />
      <div className="mb-4 flex flex-wrap gap-1">
        {FILTERS.map((f) => (
          <Button key={f || "all"} variant={status === f ? "secondary" : "ghost"} onClick={() => setStatus(f)}>
            {f ? label(f) : "All"}
          </Button>
        ))}
      </div>
      <ErrorBox error={jobs.error} onRetry={jobs.reload} />
      {jobs.data ? <JobsTable jobs={jobs.data.items} onChanged={jobs.reload} showProject /> : <Loading />}
    </>
  );
}
