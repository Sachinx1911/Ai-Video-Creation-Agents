import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { label } from "@/lib/format";

export function cx(...c: (string | false | null | undefined)[]): string {
  return c.filter(Boolean).join(" ");
}

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-sky-500 text-zinc-950 hover:bg-sky-400 disabled:bg-sky-500/40",
  secondary: "border border-zinc-700 bg-zinc-900 text-zinc-100 hover:bg-zinc-800 disabled:opacity-50",
  danger: "border border-red-900 bg-red-950/40 text-red-300 hover:bg-red-950 disabled:opacity-50",
  ghost: "text-zinc-300 hover:bg-zinc-800 disabled:opacity-50",
};

export function Button({
  variant = "secondary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      type="button"
      {...props}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed",
        VARIANTS[variant],
        className,
      )}
    />
  );
}

export function LinkButton({ href, children, variant = "secondary" }: { href: string; children: ReactNode; variant?: Variant }) {
  return (
    <Link
      href={href}
      className={cx("inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors", VARIANTS[variant])}
    >
      {children}
    </Link>
  );
}

export function Panel({ title, actions, children, className }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={cx("rounded-lg border border-zinc-800 bg-zinc-900/60", className)}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-zinc-800 px-4 py-3">
          <h2 className="text-sm font-semibold text-zinc-200">{title}</h2>
          <div className="flex items-center gap-2">{actions}</div>
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="truncate text-xl font-semibold text-zinc-50">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-zinc-400">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

const STATUS_TONE: Record<string, string> = {
  // jobs
  queued: "bg-zinc-800 text-zinc-300",
  running: "bg-sky-950 text-sky-300 ring-1 ring-sky-800",
  awaiting_retry: "bg-amber-950 text-amber-300",
  succeeded: "bg-emerald-950 text-emerald-300",
  failed: "bg-red-950 text-red-300",
  cancelled: "bg-zinc-800 text-zinc-500",
  // validation
  pending: "bg-zinc-800 text-zinc-300",
  valid: "bg-emerald-950 text-emerald-300",
  invalid: "bg-red-950 text-red-300",
  // projects
  draft: "bg-zinc-800 text-zinc-300",
  planning: "bg-violet-950 text-violet-300",
  generating: "bg-sky-950 text-sky-300",
  rendering: "bg-sky-950 text-sky-300",
  review: "bg-amber-950 text-amber-300",
  completed: "bg-emerald-950 text-emerald-300",
  archived: "bg-zinc-800 text-zinc-500",
  // health
  ok: "bg-emerald-950 text-emerald-300",
  warning: "bg-amber-950 text-amber-300",
  error: "bg-red-950 text-red-300",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cx("inline-flex items-center whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium", STATUS_TONE[status] ?? "bg-zinc-800 text-zinc-300")}>
      {label(status)}
    </span>
  );
}

export function Stat({ label: l, value, hint, tone }: { label: string; value: ReactNode; hint?: ReactNode; tone?: "warn" | "bad" }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{l}</div>
      <div className={cx("mt-1 text-2xl font-semibold tabular-nums", tone === "bad" ? "text-red-300" : tone === "warn" ? "text-amber-300" : "text-zinc-50")}>
        {value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-zinc-500">{hint}</div>}
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: { message: string } | undefined; onRetry?: () => void }) {
  if (!error) return null;
  return (
    <div role="alert" className="flex items-start justify-between gap-4 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
      <span>{error.message}</span>
      {onRetry && <Button variant="ghost" onClick={onRetry}>Retry</Button>}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-md border border-dashed border-zinc-800 px-4 py-8 text-center text-sm text-zinc-500">{children}</div>;
}

export function Loading() {
  return <div className="py-6 text-sm text-zinc-500">Loading…</div>;
}

export function Field({ label: l, error, hint, children }: { label: string; error?: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-zinc-400">{l}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-zinc-500">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-red-300">{error}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-sky-500 focus:outline-none";

export function KV({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
      {items.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="text-zinc-500">{k}</dt>
          <dd className="min-w-0 break-words text-zinc-200">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
