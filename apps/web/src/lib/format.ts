export const LABELS: Record<string, string> = {
  mr: "Marathi",
  hi: "Hindi",
  en: "English",
  instagram_reels: "Instagram Reels",
  youtube_shorts: "YouTube Shorts",
  cinematic_documentary: "Cinematic documentary",
  photorealistic_commercial: "Photorealistic commercial",
  educational_explainer: "Educational explainer",
  animation_3d: "3D animation",
  ai_images: "AI images",
  ai_video: "AI video clips",
  ai_images_and_video: "AI images + video clips",
  reference_image: "Reference image",
  final_export: "Final export",
  sfx: "Sound effect",
  awaiting_retry: "Awaiting retry",
};

export function label(value: string | null | undefined): string {
  if (!value) return "—";
  return LABELS[value] ?? value.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

export function bytes(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function duration(sec: number | null | undefined): string {
  if (sec === null || sec === undefined) return "—";
  if (sec < 60) return `${sec.toFixed(sec < 10 ? 2 : 1)} s`;
  const m = Math.floor(sec / 60);
  return `${m}m ${Math.round(sec - m * 60)}s`;
}

export function dateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function relative(iso: string | null | undefined): string {
  if (!iso) return "—";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 0) return `in ${Math.ceil(-diff)}s`;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return dateTime(iso);
}

export function shortId(id: string): string {
  return id.slice(0, 8);
}
