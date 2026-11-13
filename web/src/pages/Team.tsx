import { useState } from "react";
import { X } from "lucide-react";
import { useSession } from "../lib/session";
import { Avatar } from "../components/Avatar";
import { PRESENCE_LABEL, presenceOf } from "../lib/presence";
import type { Member } from "../lib/api";

function Row({ m, onOpen }: { m: Member; onOpen: () => void }) {
  const { me } = useSession();
  const p = presenceOf(m, me);
  return (
    <button onClick={onOpen} className="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left hover:bg-surface">
      <Avatar member={m} presence={p} />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2 text-sm font-medium">
          {m.name}
          {m.is_head && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-[10px] font-medium text-ink-soft">Head</span>}
        </span>
        <span className="block truncate text-xs text-ink-soft">{m.title}{m.now_doing ? ` · ${m.now_doing}` : ""}</span>
      </span>
      <span className="hidden text-xs text-ink-muted sm:block">{PRESENCE_LABEL[p]}</span>
    </button>
  );
}

function Fiche({ m, onClose }: { m: Member; onClose: () => void }) {
  const { me } = useSession();
  const p = presenceOf(m, me);
  const Line = ({ label, value, empty }: { label: string; value: string; empty: string }) => (
    <div className="border-t border-line py-4">
      <div className="text-xs font-medium uppercase tracking-wide text-ink-muted">{label}</div>
      <div className={`mt-1 text-sm ${value ? "" : "text-ink-muted"}`}>{value || empty}</div>
    </div>
  );
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/20" onClick={onClose}>
      <aside className="h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} aria-label="Fermer" className="float-right rounded-full p-1 text-ink-soft hover:bg-surface"><X size={20} /></button>
        <Avatar member={m} presence={p} size="lg" />
        <h2 className="mt-4 text-xl font-semibold">{m.name}</h2>
        <div className="text-sm text-ink-soft">{m.title}{m.kind === "agent" ? " · Agent" : ""}</div>
        <div className="mt-2 text-sm">{PRESENCE_LABEL[p]}{m.status_message ? ` — ${m.status_message}` : ""}</div>
        <div className="mt-6">
          <Line label="Son rôle" value={m.role} empty="—" />
          <Line label="En ce moment" value={m.now_doing} empty="Rien d'indiqué" />
          <Line label="Créneaux" value={m.schedule} empty="Pas encore indiqués" />
          <Line label="Terminé récemment" value="" empty="Apparaîtra ici avec le suivi de projet." />
        </div>
      </aside>
    </div>
  );
}

export function Team() {
  const { members } = useSession();
  const [open, setOpen] = useState<Member | null>(null);
  const humans = members.filter((m) => m.kind === "human");
  const agents = members.filter((m) => m.kind === "agent");
  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="text-2xl font-semibold">Équipe</h1>
      <p className="mt-1 text-sm text-ink-soft">Humains et agents, au même niveau.</p>
      <h2 className="mt-6 px-3 text-xs font-medium uppercase tracking-wide text-ink-muted">Personnes · {humans.length}</h2>
      <div className="mt-1">{humans.map((m) => <Row key={m.id} m={m} onOpen={() => setOpen(m)} />)}</div>
      <h2 className="mt-6 px-3 text-xs font-medium uppercase tracking-wide text-ink-muted">Agents · {agents.length}</h2>
      <div className="mt-1">{agents.map((m) => <Row key={m.id} m={m} onOpen={() => setOpen(m)} />)}</div>
      {open && <Fiche m={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
