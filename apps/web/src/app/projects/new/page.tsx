"use client";

import { useRouter } from "next/navigation";

import { ErrorBox, Loading, PageHeader } from "@/components/ui";
import { ProjectForm, defaultsFrom, toPayload } from "@/features/projects/project-form";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const options = useApi(() => api.options());

  return (
    <>
      <PageHeader title="New video project" subtitle="Define the brief. Script and storyboard generation arrive in Phase 2." />
      <ErrorBox error={options.error} onRetry={options.reload} />
      {options.data ? (
        <ProjectForm
          options={options.data}
          initial={defaultsFrom(options.data)}
          submitLabel="Create project"
          onSubmit={async (v) => {
            const p = await api.createProject(toPayload(v));
            router.push(`/projects/${p.id}`);
          }}
          onCancel={() => router.push("/projects")}
        />
      ) : !options.error && <Loading />}
    </>
  );
}
