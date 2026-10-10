import { Suspense } from "react";

import { Loading } from "@/components/ui";
import { ProjectWorkspace } from "@/features/projects/project-workspace";

export default function ProjectPage({ params }: PageProps<"/projects/[id]">) {
  return (
    <Suspense fallback={<Loading />}>
      {params.then(({ id }) => <ProjectWorkspace id={id} />)}
    </Suspense>
  );
}
