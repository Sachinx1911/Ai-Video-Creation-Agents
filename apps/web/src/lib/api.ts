import type {
  Asset, Job, Options, Overview, Page, Project, ProjectRevision, ProjectSummary, Readiness,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string, public fieldErrors: Record<string, string> = {}) {
    super(message);
  }
}

type FastApiDetail = { loc?: (string | number)[]; msg?: string }[] | string | undefined;

async function parseError(res: Response): Promise<ApiError> {
  let body: { detail?: FastApiDetail; error?: string } = {};
  try {
    body = await res.json();
  } catch {
    /* non-JSON error body */
  }
  const fieldErrors: Record<string, string> = {};
  let message = `${res.status} ${res.statusText}`;
  if (Array.isArray(body.detail)) {
    for (const d of body.detail) {
      const field = (d.loc ?? []).filter((p) => p !== "body").join(".");
      if (field) fieldErrors[field] = d.msg ?? "invalid";
    }
    message = body.detail.map((d) => `${(d.loc ?? []).slice(1).join(".")}: ${d.msg}`).join("; ");
  } else if (typeof body.detail === "string") {
    message = body.detail;
  }
  return new ApiError(res.status, message, fieldErrors);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError(0, `Cannot reach the API at ${API_URL}. Is the backend running?`);
  }
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  options: () => request<Options>("/meta/options"),
  overview: () => request<Overview>("/system/overview"),
  readiness: async (): Promise<Readiness> => {
    // 503 still carries the check details, so read the body either way.
    try {
      const res = await fetch(`${API_URL}/health/ready`, { cache: "no-store" });
      return (await res.json()) as Readiness;
    } catch {
      throw new ApiError(0, `Cannot reach the API at ${API_URL}. Is the backend running?`);
    }
  },

  listProjects: (p: { archived?: boolean; q?: string; status?: string; limit?: number } = {}) =>
    request<Page<ProjectSummary>>(`/projects${qs(p)}`),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (body: unknown) => request<Project>("/projects", json("POST", body)),
  updateProject: (id: string, body: unknown) => request<Project>(`/projects/${id}`, json("PATCH", body)),
  duplicateProject: (id: string, name?: string) =>
    request<Project>(`/projects/${id}/duplicate`, json("POST", name ? { name } : {})),
  archiveProject: (id: string) => request<Project>(`/projects/${id}/archive`, { method: "POST" }),
  restoreProject: (id: string) => request<Project>(`/projects/${id}/restore`, { method: "POST" }),
  revisions: (id: string) => request<ProjectRevision[]>(`/projects/${id}/revisions`),

  listAssets: (p: { project_id?: string; kind?: string; q?: string; include_archived?: boolean } = {}) =>
    request<Page<Asset>>(`/assets${qs(p)}`),
  getAsset: (id: string) => request<Asset>(`/assets/${id}`),
  uploadAsset: (projectId: string, form: FormData) =>
    request<Asset>(`/projects/${projectId}/assets`, { method: "POST", body: form }),
  addAssetVersion: (assetId: string, form: FormData) =>
    request<Asset>(`/assets/${assetId}/versions`, { method: "POST", body: form }),
  archiveAsset: (id: string) => request<Asset>(`/assets/${id}/archive`, { method: "POST" }),
  restoreAsset: (id: string) => request<Asset>(`/assets/${id}/restore`, { method: "POST" }),
  assetFileUrl: (assetId: string, version: number, download = false) =>
    `${API_URL}/assets/${assetId}/versions/${version}/file${download ? "?download=true" : ""}`,

  listJobs: (p: { status?: string; project_id?: string; type?: string; limit?: number } = {}) =>
    request<Page<Job>>(`/jobs${qs(p)}`),
  getJob: (id: string) => request<Job>(`/jobs/${id}`),
  cancelJob: (id: string) => request<Job>(`/jobs/${id}/cancel`, { method: "POST" }),
  retryJob: (id: string) => request<Job>(`/jobs/${id}/retry`, { method: "POST" }),
};
