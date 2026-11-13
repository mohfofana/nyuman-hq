import { useState } from "react";
import { Link } from "react-router-dom";
import { CalendarClock, CalendarPlus, Check, CheckCircle2, MessageSquare, Pencil, Sparkles, Target, X } from "lucide-react";
import { useSession } from "../lib/session";
import { useLive } from "../lib/live";
import { Avatar, TINTS, tintIndex } from "../components/Avatar";
import { Badge, PresencePill } from "../components/ui";
import { presenceOf } from "../lib/presence";
import type { Member } from "../lib/api";

function Card({ m, onOpen }: { m: Member; onOpen: () => void }) {
  const { me } = useSession();
  const p = presenceOf(m, me);
  const tint = TINTS[tintIndex(m.id)].solid;
  return (
    <div className="group relative overflow-hidden rounded-3xl border border-line/80 bg-white shadow-[0_1px_2px_rgba(30,26,23,0.04)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_16px_32px_-16px_rgba(30,26,23,0.25)]">
      <div className="h-16" style={{ background: `linear-gradient(120deg, ${tint}55, ${tint}22)` }} />
      <button onClick={onOpen} className="block w-full px-5 pb-4 text-left">
        <div className="-mt-9 flex items-end justify-between">
          <Avatar member={m} presence={p} size="lg" ring />
          <PresencePill p={p} />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[17px] font-semibold">{m.name}</span>
          {m.is_head && <Badge tone="orange">Head</Badge>}
          {m.kind === "agent" && <Badge tone="blue">Agent IA</Badge>}
        </div>
        <div className="text-sm text-ink-soft">{m.title}</div>
        <div className="mt-4 flex items-start gap-2 text-sm">
          <Target size={15} className="mt-0.5 shrink-0 text-accent" />
          <span className={m.now_doing ? "text-ink" : "text-ink-muted"}>{m.now_doing || "Rien d'indiqué pour l'instant"}</span>
        </div>
      </button>
      <div className="flex border-t border-line">
        <Link to={`/discussions?avec=${m.id}`} className="flex flex-1 items-center justify-center gap-1.5 py-2.5 text-xs font-medium text-ink-soft transition hover:bg-surface hover:text-accent">
          <MessageSquare size={14} /> Message
        </Link>
        <button onClick={onOpen} className="flex flex-1 items-center justify-center gap-1.5 border-l border-line py-2.5 text-xs font-medium text-ink-soft transition hover:bg-surface hover:text-accent">
          Voir la fiche
        </button>
      </div>
    </div>
  );
}

function Editable({ value, empty, onSave, canEdit }: { value: string; empty: string; onSave: (v: string) => Promise<void>; canEdit: boolean }) {
  const [editing, setEditing] = useState(false);
  const [v, setV] = useState(value);
  if (editing)
    return (
      <form className="mt-1.5 flex gap-2" onSubmit={async (e) => { e.preventDefault(); await onSave(v.trim()); setEditing(false); }}>
        <input autoFocus value={v} onChange={(e) => setV(e.target.value)} className="min-w-0 flex-1 rounded-xl border border-line px-3 py-1.5 text-sm outline-none focus:border-accent" />
        <button className="rounded-xl bg-accent px-2.5 text-white hover:bg-accent-hover" aria-label="Enregistrer"><Check size={16} /></button>
      </form>
    );
  return (
    <div className="mt-1 flex items-start gap-2">
      <span className={`text-sm leading-relaxed ${value ? "" : "text-ink-muted"}`}>{value || empty}</span>
      {canEdit && <button onClick={() => setEditing(true)} aria-label="Modifier" className="rounded-md p-1 text-ink-muted hover:bg-surface hover:text-accent"><Pencil size={13} /></button>}
    </div>
  );
}

function Fiche({ m, onClose }: { m: Member; onClose: () => void }) {
  const { me, updateMe } = useSession();
  const p = presenceOf(m, me);
  const mine = me?.id === m.id;
  const tint = TINTS[tintIndex(m.id)].solid;
  const rows = [
    { icon: m.kind === "agent" ? Sparkles : Target, tone: "bg-accent-soft text-accent", label: "Son rôle", node: <div className="mt-1 text-sm leading-relaxed">{m.role}</div> },
    { icon: Target, tone: "bg-sun-soft text-[#9A6B00]", label: "En ce moment",
      node: <Editable value={m.now_doing} empty="Rien d'indiqué" canEdit={mine} onSave={(v) => updateMe({ now_doing: v })} /> },
    { icon: CalendarClock, tone: "bg-blue-soft text-blue", label: "Créneaux",
      node: <Editable value={m.schedule} empty={mine ? "Indiquez quand vous travaillez pour Nyuman" : "Pas encore indiqués"} canEdit={mine} onSave={(v) => updateMe({ schedule: v })} /> },
    { icon: CheckCircle2, tone: "bg-[#E3F6EA] text-[#18794A]", label: "Terminé récemment",
      node: <div className="mt-1 text-sm text-ink-muted">Apparaîtra ici avec le suivi de projet.</div> },
  ];
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/30 backdrop-blur-[3px]" onClick={onClose}>
      <aside className="slide-in h-full w-full max-w-md overflow-y-auto bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="relative h-32" style={{ background: `linear-gradient(120deg, ${tint}, ${tint}66)` }}>
          <button onClick={onClose} aria-label="Fermer" className="absolute right-4 top-4 rounded-full bg-white/70 p-1.5 text-ink hover:bg-white"><X size={18} /></button>
        </div>
        <div className="-mt-12 px-6 pb-8">
          <Avatar member={m} presence={p} size="xl" ring />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-semibold">{m.name}</h2>
            {m.is_head && <Badge tone="orange">Head</Badge>}
            {m.kind === "agent" && <Badge tone="blue">Agent IA</Badge>}
          </div>
          <div className="text-ink-soft">{m.title}</div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <PresencePill p={p} />
            {m.status_message && <span className="text-sm text-ink-soft">« {m.status_message} »</span>}
          </div>
          {!mine && (
            <div className="mt-5 grid grid-cols-2 gap-2">
              <Link to={`/discussions?avec=${m.id}`} className="flex items-center justify-center gap-2 rounded-full bg-accent py-2.5 text-sm font-semibold text-white shadow-sm shadow-accent/30 hover:bg-accent-hover">
                <MessageSquare size={16} /> Message
              </Link>
              <Link to={`/agenda?nouvelle=1&avec=${m.id}`} className="flex items-center justify-center gap-2 rounded-full border border-line py-2.5 text-sm font-semibold hover:bg-surface">
                <CalendarPlus size={16} /> Réunion
              </Link>
            </div>
          )}
          <div className="mt-6 space-y-3">
            {rows.map(({ icon: Icon, tone, label, node }) => (
              <div key={label} className="flex gap-3 rounded-2xl border border-line p-4">
                <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon size={18} /></span>
                <div className="min-w-0 flex-1">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">{label}</div>
                  {node}
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}

const FILTERS = [
  { id: "all", label: "Tout le monde" },
  { id: "human", label: "Personnes" },
  { id: "agent", label: "Agents" },
] as const;

export function Team() {
  const { members, me } = useSession();
  useLive();
  const [openId, setOpenId] = useState<string | null>(null);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["id"]>("all");
  const shown = members.filter((m) => filter === "all" || m.kind === filter);
  const available = members.filter((m) => presenceOf(m, me) === "online").length;
  const open = members.find((m) => m.id === openId) ?? null;
  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Équipe</h1>
          <p className="mt-1 text-ink-soft">
            {members.filter((m) => m.kind === "human").length} personnes et {members.filter((m) => m.kind === "agent").length} agents, au même niveau
            <span className="mx-2 text-line">|</span>
            <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-online" />{available} disponible{available > 1 ? "s" : ""}</span>
          </p>
        </div>
        <div className="flex rounded-full bg-white p-1 shadow-sm ring-1 ring-line">
          {FILTERS.map((f) => (
            <button key={f.id} onClick={() => setFilter(f.id)}
              className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition ${filter === f.id ? "bg-accent text-white shadow-sm" : "text-ink-soft hover:text-ink"}`}>
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-6 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {shown.map((m) => <Card key={m.id} m={m} onOpen={() => setOpenId(m.id)} />)}
      </div>
      {open && <Fiche m={open} onClose={() => setOpenId(null)} />}
    </div>
  );
}
