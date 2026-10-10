"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";

import { cx } from "@/components/ui";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";

// Only screens whose backend exists are listed. Storyboard, Render Studio,
// Agents, Providers and Final Videos arrive with their phases.
const NAV = [
  { href: "/", label: "Overview" },
  { href: "/projects", label: "Projects" },
  { href: "/assets", label: "Asset Library" },
  { href: "/jobs", label: "Jobs" },
  { href: "/system", label: "System Health" },
];

function NavLinks({ path }: { path: string | null }) {
  return (
    <nav className="flex-1 space-y-0.5 px-2">
      {NAV.map((n) => {
        const active = path !== null && (n.href === "/" ? path === "/" : path.startsWith(n.href));
        return (
          <Link
            key={n.href}
            href={n.href}
            className={cx(
              "block rounded-md px-3 py-1.5 text-sm",
              active ? "bg-zinc-800 text-zinc-50" : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200",
            )}
          >
            {n.label}
          </Link>
        );
      })}
    </nav>
  );
}

function ActiveNavLinks() {
  return <NavLinks path={usePathname()} />;
}

export function Sidebar() {
  const health = useApi(() => api.readiness(), [], 15000);
  const ready = health.data?.ready;

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="px-4 py-4">
        <div className="text-sm font-semibold tracking-tight text-zinc-50">AI Video Studio</div>
        <div className="text-xs text-zinc-500">Production workspace</div>
      </div>
      {/* The pathname is request data: links render statically, highlight streams in. */}
      <Suspense fallback={<NavLinks path={null} />}>
        <ActiveNavLinks />
      </Suspense>
      <Link href="/system" className="m-2 flex items-center gap-2 rounded-md px-3 py-2 text-xs text-zinc-400 hover:bg-zinc-900">
        <span
          className={cx(
            "h-2 w-2 rounded-full",
            health.error ? "bg-red-500" : ready === undefined ? "bg-zinc-600" : ready ? "bg-emerald-500" : "bg-amber-500",
          )}
        />
        {health.error ? "API unreachable" : ready === undefined ? "Checking…" : ready ? "All systems ready" : "Degraded"}
      </Link>
    </aside>
  );
}
