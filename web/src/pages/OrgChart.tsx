import { useEffect, useRef, useState } from "react";
import { Check, Clock, Pencil, Sparkles, UserPlus } from "lucide-react";
import { orgApi, type Member, type Org, type Position } from "../lib/api";
import { useSession } from "../lib/session";
import { useLive } from "../lib/live";
import { Avatar } from "../components/Avatar";
import { presenceOf } from "../lib/presence";

const DEPT_DOT: Record<string, string> = {
  "Direction générale": "bg-accent",
  "Croissance": "bg-sun",
  "Opérations": "bg-blue",
  "Finance": "bg-online",
  "Produit et technique": "bg-[#8B6FD6]",
};

export function useOrg() {
  const { subscribe } = useLive();
  const [org, setOrg] = useState<Org | null>(null);
  useEffect(() => { orgApi.get().then(setOrg); }, []);
  useEffect(() => subscribe((ev) => { if (ev.type === "org.updated") orgApi.get().then(setOrg); }), [subscribe]);
  return { org, setOrg };
}

function Picker({ p, members, onSave, onClose }: { p: Position; members: Member[]; onSave: (h: string[], s: string[]) => void; onClose: () => void }) {
  const [holders, setHolders] = useState(p.holder_ids);
  const [support, setSupport] = useState(p.support_ids);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const close = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) onClose(); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [onClose]);
  const row = (m: Member, on: boolean, toggle: () => void) => (
    <button key={m.id} onClick={toggle} className={`flex w-full items-center gap-2.5 rounded-xl px-2 py-1.5 text-left text-sm ${on ? "bg-accent-soft" : "hover:bg-surface"}`}>
      <Avatar member={m} size="sm" /><span className="flex-1">{m.name}</span>
      <span className={`flex h-5 w-5 items-center justify-center rounded-full border ${on ? "border-accent bg-accent text-white" : "border-line"}`}>{on && <Check size={12} />}</span>
    </button>
  );
  const flip = (list: string[], set: (x: string[]) => void, id: string) => set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  return (
    <div ref={ref} className="absolute left-0 right-0 top-full z-30 mt-2 rounded-2xl border border-line bg-white p-3 shadow-2xl">
      <div className="px-1 pb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Tient le poste</div>
      {members.filter((m) => m.kind === "human").map((m) => row(m, holders.includes(m.id), () => flip(holders, setHolders, m.id)))}
      <div className="px-1 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Appuyé par (agents)</div>
      {members.filter((m) => m.kind === "agent").map((m) => row(m, support.includes(m.id), () => flip(support, setSupport, m.id)))}
      <button onClick={() => onSave(holders, support)} className="mt-3 w-full rounded-full bg-accent py-2 text-sm font-semibold text-white hover:bg-accent-hover">Enregistrer</button>
    </div>
  );
}

function PositionCard({ p, members, canEdit, onSave, lead }: {
  p: Position; members: Member[]; canEdit: boolean; onSave: (p: Position, h: string[], s: string[]) => Promise<void>; lead?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const holders = p.holder_ids.map((id) => members.find((m) => m.id === id)).filter(Boolean) as Member[];
  const support = p.support_ids.map((id) => members.find((m) => m.id === id)).filter(Boolean) as Member[];
  return (
    <div className={`relative rounded-2xl border bg-white p-4 shadow-[0_1px_2px_rgba(30,26,23,0.04)] transition hover:shadow-md ${lead ? "border-line ring-1 ring-accent/10" : "border-line"}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="rounded-md bg-surface px-1.5 py-0.5 text-[10px] font-bold text-ink-soft">N° {p.id}</span>
        <span className="inline-flex items-center gap-1 text-[11px] text-ink-muted"><Clock size={11} /> {p.hours} h/sem.</span>
      </div>
      <div className={`mt-2 font-semibold leading-snug ${lead ? "text-[15px]" : "text-sm"}`}>{p.title}</div>
      <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-ink-soft">{p.mission}</p>
      <div className="mt-3 flex items-center gap-2">
        {holders.length ? holders.map((m) => (
          <span key={m.id} className="flex items-center gap-2 rounded-full bg-surface py-0.5 pl-0.5 pr-2.5 text-xs font-medium">
            <Avatar member={m} presence={presenceOf(m)} size="sm" />{m.name.split(" ")[0]}
          </span>
        )) : (
          <span className="flex items-center gap-1.5 rounded-full border border-dashed border-ink-muted/40 px-2.5 py-1 text-xs text-ink-muted">À pourvoir</span>
        )}
        {canEdit && (
          <button onClick={() => setEditing(!editing)} aria-label="Placer quelqu'un" title="Placer quelqu'un"
            className="ml-auto rounded-full p-1.5 text-ink-muted hover:bg-surface hover:text-accent">
            {holders.length ? <Pencil size={14} /> : <UserPlus size={15} />}
          </button>
        )}
      </div>
      {support.length > 0 && (
        <div className="mt-2 flex flex-wrap items-center gap-1">
          {support.map((m) => (
            <span key={m.id} className="inline-flex items-center gap-1 rounded-full bg-blue-soft px-2 py-0.5 text-[10px] font-semibold text-blue">
              <Sparkles size={10} /> {m.name}
            </span>
          ))}
        </div>
      )}
      {editing && <Picker p={p} members={members} onClose={() => setEditing(false)} onSave={async (h, s) => { await onSave(p, h, s); setEditing(false); }} />}
    </div>
  );
}

export function OrgChart() {
  const { me, members } = useSession();
  useLive();
  const { org, setOrg } = useOrg();
  if (!org || !me) return null;
  const pos = (id: number) => org.positions.find((p) => p.id === id)!;
  const save = async (p: Position, h: string[], s: string[]) => setOrg(await orgApi.set(p.id, h, s));
  const leads = org.positions.filter((p) => p.reports_to === 1 && p.department !== "Direction générale");
  const filled = org.positions.filter((p) => p.holder_ids.length).length;
  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 rounded-2xl bg-white p-4 text-sm shadow-sm ring-1 ring-line">
        <span><b>{org.positions.length}</b> postes · <b>{org.departments.length}</b> départements · <b>{filled}</b> pourvu{filled > 1 ? "s" : ""}</span>
        <span className="ml-auto flex flex-wrap gap-3">
          {org.departments.map((d) => <span key={d} className="inline-flex items-center gap-1.5 text-xs text-ink-soft"><span className={`h-2 w-2 rounded-full ${DEPT_DOT[d]}`} />{d}</span>)}
        </span>
      </div>
      {!me.is_head && <p className="mt-2 text-xs text-ink-muted">Seuls les heads placent les personnes sur les postes.</p>}

      <div className="mt-6 flex flex-col items-center">
        <div className="grid w-full max-w-2xl gap-4 sm:grid-cols-2">
          <PositionCard p={pos(1)} members={members} canEdit={me.is_head} onSave={save} lead />
          <div className="relative">
            <span className="absolute -left-4 top-1/2 hidden h-px w-4 border-t border-dashed border-ink-muted/40 sm:block" />
            <PositionCard p={pos(2)} members={members} canEdit={me.is_head} onSave={save} />
          </div>
        </div>
        <div className="h-6 w-px bg-line" />
        <div className="hidden h-px w-[calc(100%-25%)] bg-line lg:block" />
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {leads.map((lead) => {
          const team = org.positions.filter((p) => p.reports_to === lead.id);
          return (
            <div key={lead.id} className="flex flex-col">
              <div className="mx-auto hidden h-5 w-px bg-line lg:block" />
              <div className="mb-2 flex items-center gap-2 px-1">
                <span className={`h-2.5 w-2.5 rounded-full ${DEPT_DOT[lead.department]}`} />
                <span className="text-xs font-semibold uppercase tracking-wide text-ink-soft">{lead.department}</span>
              </div>
              <PositionCard p={lead} members={members} canEdit={me.is_head} onSave={save} lead />
              {team.length > 0 && (
                <div className="ml-4 mt-2 space-y-2 border-l-2 border-line pl-3">
                  {team.map((p) => <PositionCard key={p.id} p={p} members={members} canEdit={me.is_head} onSave={save} />)}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <p className="mt-6 text-xs text-ink-muted">Source : « Fiches de poste NYUMAN » (12/11). Les agents n'occupent jamais un poste : ils appuient la personne qui le tient.</p>
    </div>
  );
}
