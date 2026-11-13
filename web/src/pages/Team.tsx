import { useState } from "react";
import { CalendarClock, CheckCircle2, Sparkles, Target, X } from "lucide-react";
import { useSession } from "../lib/session";
import { Avatar } from "../components/Avatar";
import { PRESENCE_COLOR, PRESENCE_LABEL, presenceOf, type Presence } from "../lib/presence";
import type { Member } from "../lib/api";

const PILL: Record<Presence, string> = {
  online: "bg-[#E3F6EA] text-[#18794A]",
  away: "bg-[#FFF4D1] text-[#8A6400]",
  meeting: "bg-[#FDE6E2] text-[#B5321F]",
  busy: "bg-[#FDE6E2] text-[#B5321F]",
  dnd: "bg-[#FDE6E2] text-[#B5321F]",
  offline: "bg-surface text-ink-muted",
};

function PresencePill({ p }: { p: Presence }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${PILL[p]}`}>
      <span className={`h-2 w-2 rounded-full ${PRESENCE_COLOR[p]}`} />{PRESENCE_LABEL[p]}
    </span>
  );
}

function Card({ m, onOpen }: { m: Member; onOpen: () => void }) {
  const { me } = useSession();
  const p = presenceOf(m, me);
  return (
    <button onClick={onOpen}
      className="group flex flex-col rounded-3xl border border-line bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-md">
      <div className="flex items-start justify-between">
        <Avatar member={m} presence={p} />
        <PresencePill p={p} />
      </div>
      <div className="mt-4 flex items-center gap-2">
        <span className="font-semibold">{m.name}</span>
        {m.is_head && <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-semibold text-accent">Head</span>}
        {m.kind === "agent" && <span className="rounded-full bg-blue-soft px-2 py-0.5 text-[10px] font-semibold text-blue">Agent IA</span>}
      </div>
      <div className="text-sm text-ink-soft">{m.title}</div>
      <div className="mt-4 rounded-2xl bg-surface px-3 py-2.5 text-xs">
        <span className="font-medium text-ink-soft">En ce moment · </span>
        <span className={m.now_doing ? "text-ink" : "text-ink-muted"}>{m.now_doing || "rien d'indiqué"}</span>
      </div>
    </button>
  );
}

function Fiche({ m, onClose }: { m: Member; onClose: () => void }) {
  const { me } = useSession();
  const p = presenceOf(m, me);
  const Block = ({ icon: Icon, tone, label, value, empty }: {
    icon: typeof Target; tone: string; label: string; value: string; empty: string;
  }) => (
    <div className="flex gap-3 rounded-2xl border border-line p-4">
      <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon size={18} /></span>
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</div>
        <div className={`mt-1 text-sm leading-relaxed ${value ? "" : "text-ink-muted"}`}>{value || empty}</div>
      </div>
    </div>
  );
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-ink/25 backdrop-blur-[2px]" onClick={onClose}>
      <aside className="h-full w-full max-w-md overflow-y-auto bg-white shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="relative h-28 bg-gradient-to-r from-accent-bright to-[#E8913A]">
          <button onClick={onClose} aria-label="Fermer" className="absolute right-4 top-4 rounded-full bg-white/20 p-1.5 text-white hover:bg-white/30"><X size={18} /></button>
        </div>
        <div className="-mt-10 px-6 pb-8">
          <Avatar member={m} presence={p} size="lg" ring />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <h2 className="text-2xl font-semibold">{m.name}</h2>
            {m.kind === "agent" && <span className="rounded-full bg-blue-soft px-2 py-0.5 text-[11px] font-semibold text-blue">Agent IA</span>}
            {m.is_head && <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-semibold text-accent">Head</span>}
          </div>
          <div className="text-ink-soft">{m.title}</div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <PresencePill p={p} />
            {m.status_message && <span className="text-sm text-ink-soft">« {m.status_message} »</span>}
          </div>
          <div className="mt-6 space-y-3">
            <Block icon={m.kind === "agent" ? Sparkles : Target} tone="bg-accent-soft text-accent" label="Son rôle" value={m.role} empty="—" />
            <Block icon={Target} tone="bg-sun-soft text-[#9A6B00]" label="En ce moment" value={m.now_doing} empty="Rien d'indiqué" />
            <Block icon={CalendarClock} tone="bg-blue-soft text-blue" label="Créneaux" value={m.schedule} empty="Pas encore indiqués" />
            <Block icon={CheckCircle2} tone="bg-[#E3F6EA] text-[#18794A]" label="Terminé récemment" value="" empty="Apparaîtra ici avec le suivi de projet." />
          </div>
        </div>
      </aside>
    </div>
  );
}

export function Team() {
  const { members, me } = useSession();
  const [open, setOpen] = useState<Member | null>(null);
  const humans = members.filter((m) => m.kind === "human");
  const agents = members.filter((m) => m.kind === "agent");
  const available = members.filter((m) => presenceOf(m, me) === "online").length;
  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-8 sm:py-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Équipe</h1>
          <p className="mt-1 text-ink-soft">Humains et agents, au même niveau.</p>
        </div>
        <div className="flex gap-2">
          <span className="rounded-full bg-white px-3 py-1.5 text-sm shadow-sm"><b>{humans.length}</b> personnes</span>
          <span className="rounded-full bg-white px-3 py-1.5 text-sm shadow-sm"><b>{agents.length}</b> agents</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-sm shadow-sm">
            <span className="h-2 w-2 rounded-full bg-online" /><b>{available}</b> disponible{available > 1 ? "s" : ""}
          </span>
        </div>
      </div>
      <h2 className="mt-8 text-sm font-semibold text-ink-soft">Personnes</h2>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{humans.map((m) => <Card key={m.id} m={m} onOpen={() => setOpen(m)} />)}</div>
      <h2 className="mt-8 text-sm font-semibold text-ink-soft">Agents</h2>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{agents.map((m) => <Card key={m.id} m={m} onOpen={() => setOpen(m)} />)}</div>
      {open && <Fiche m={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
