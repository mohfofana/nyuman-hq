import type { ReactNode } from "react";
import { PRESENCE_COLOR, PRESENCE_LABEL, type Presence } from "../lib/presence";

const PILL: Record<Presence, string> = {
  online: "bg-[#E3F6EA] text-[#18794A]",
  away: "bg-[#FFF4D1] text-[#8A6400]",
  meeting: "bg-[#FDE6E2] text-[#B5321F]",
  busy: "bg-[#FDE6E2] text-[#B5321F]",
  dnd: "bg-[#FDE6E2] text-[#B5321F]",
  offline: "bg-surface-2/70 text-ink-muted",
};

export function PresencePill({ p, label }: { p: Presence; label?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${PILL[p]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${PRESENCE_COLOR[p]} ${p === "online" ? "animate-pulse" : ""}`} />
      {label ?? PRESENCE_LABEL[p]}
    </span>
  );
}

export function Badge({ tone, children }: { tone: "orange" | "blue"; children: ReactNode }) {
  const c = tone === "orange" ? "bg-accent-soft text-accent" : "bg-blue-soft text-blue";
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${c}`}>{children}</span>;
}

export function Panel({ title, action, children, className = "" }: {
  title?: string; action?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`rounded-3xl border border-line/80 bg-white p-5 shadow-[0_1px_2px_rgba(30,26,23,0.04),0_8px_24px_-12px_rgba(30,26,23,0.08)] ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && <h2 className="text-[15px] font-semibold">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function SoonTag({ children = "Bientôt" }: { children?: ReactNode }) {
  return <span className="rounded-full bg-surface px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-muted">{children}</span>;
}
